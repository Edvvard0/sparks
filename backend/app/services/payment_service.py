from sqlalchemy.orm import Session
from typing import Dict, Optional
import re
import time
from app.models.user import User
from app.models.transaction import Transaction, TransactionType, PaymentMethod, TransactionStatus
from app.core.config import settings
# TONService импортируется внутри методов чтобы избежать циклической зависимости


class PaymentService:
    @staticmethod
    def create_ton_payment(
        db: Session,
        user: User,
        package_id: int
    ) -> Dict:
        """
        Создание TON платежа
        
        Args:
            db: Сессия БД
            user: Пользователь
            package_id: ID пакета
            
        Returns:
            Словарь с данными платежа (transaction_id, ton_deep_link, ton_amount, ton_address)
        """
        # Получаем информацию о пакете
        packages = PaymentService.get_packages()
        package = next((pkg for pkg in packages if pkg["id"] == package_id), None)
        
        if not package:
            raise ValueError(f"Package {package_id} not found")
        
        amount = package["amount"]
        price = package["price"]
        min_ton_amount = package.get("min_ton_amount_nanotons")
        
        # Конвертируем цену в TON (nanotons)
        from app.services.ton_service import TONService
        ton_amount_nanotons = TONService.convert_rub_to_ton(price, min_ton_amount)
        
        # Определяем amount для транзакции
        transaction_amount = amount if isinstance(amount, int) else 0
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.tg_id,
            amount=transaction_amount,
            transaction_type=TransactionType.PURCHASE,
            payment_method=PaymentMethod.TON,
            status=TransactionStatus.PENDING,
            description=f"Покупка {amount} искр (пакет #{package_id})",
            ton_to_address=settings.TON_WALLET_ADDRESS,
            ton_amount=ton_amount_nanotons,
            ton_from_address=user.wallet_address  # Адрес отправителя (если есть)
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Генерируем комментарий для транзакции
        comment = f"Payment for package {package_id}, transaction {transaction.id}"
        
        return {
            "transaction_id": transaction.id,
            "ton_amount": str(ton_amount_nanotons),  # В nanotons как строка
            "ton_address": settings.TON_WALLET_ADDRESS,
            "comment": comment
        }
    
    @staticmethod
    async def check_ton_payment_status(
        db: Session,
        transaction_id: int,
        user: User
    ) -> Dict:
        """
        Проверка статуса TON платежа
        
        Args:
            db: Сессия БД
            transaction_id: ID транзакции
            user: Пользователь
            
        Returns:
            Словарь со статусом платежа
        """
        print(f"[Payment Service] Checking transaction {transaction_id} for user {user.tg_id}")
        
        # Получаем транзакцию
        transaction = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user.tg_id,
            Transaction.payment_method == PaymentMethod.TON
        ).first()
        
        if not transaction:
            print(f"[Payment Service] ERROR: Transaction {transaction_id} not found for user {user.tg_id}")
            return {
                "status": "not_found",
                "message": "Transaction not found"
            }
        
        print(f"[Payment Service] Transaction found: id={transaction.id}, status={transaction.status}, amount={transaction.amount}")
        print(f"[Payment Service] Transaction created_at: {transaction.created_at}")
        
        if transaction.status == TransactionStatus.COMPLETED:
            print(f"[Payment Service] Transaction {transaction_id} already completed")
            return {
                "status": "completed",
                "transaction_hash": transaction.ton_transaction_hash,
                "confirmed": True
            }
        
        if transaction.status == TransactionStatus.FAILED:
            print(f"[Payment Service] Transaction {transaction_id} already failed")
            return {
                "status": "failed",
                "confirmed": False
            }
        
        # Если есть хеш транзакции, проверяем в блокчейне
        if transaction.ton_transaction_hash:
            from app.services.ton_service import TONService
            tx_data = await TONService.check_transaction(transaction.ton_transaction_hash)
            
            if tx_data:
                # Проверяем что транзакция соответствует ожидаемому платежу
                expected_to = transaction.ton_to_address or settings.TON_WALLET_ADDRESS
                expected_amount = transaction.ton_amount or "0"
                
                if TONService.verify_transaction_payment(
                    tx_data,
                    expected_to,
                    expected_amount,
                    transaction.ton_from_address
                ):
                    # Транзакция подтверждена
                    transaction.status = TransactionStatus.COMPLETED
                    
                    # Проверяем если это lifetime подписка
                    is_lifetime = False
                    if transaction.description and "lifetime" in transaction.description.lower():
                        is_lifetime = True
                    elif isinstance(transaction.amount, str) and transaction.amount.lower() == "lifetime":
                        is_lifetime = True
                    else:
                        # Проверяем по пакету через описание
                        packages = PaymentService.get_packages()
                        match = re.search(r'пакет #(\d+)', transaction.description or '')
                        if match:
                            package_id_match = int(match.group(1))
                            package = next((pkg for pkg in packages if pkg["id"] == package_id_match), None)
                            if package and package.get("amount") == "lifetime":
                                is_lifetime = True
                    
                    if is_lifetime:
                        # Для lifetime подписки только устанавливаем флаг, баланс не пополняем
                        user.has_lifetime_subscription = True
                    else:
                        # Для обычных пакетов пополняем баланс
                        if isinstance(transaction.amount, int) and transaction.amount > 0:
                            user.balance += transaction.amount
                    
                    db.commit()
                    
                    return {
                        "status": "completed",
                        "transaction_hash": transaction.ton_transaction_hash,
                        "confirmed": True
                    }
        
        print(f"[Payment Service] Transaction {transaction_id} is still pending")
        return {
            "status": "pending",
            "confirmed": False,
            "message": "Payment is pending confirmation"
        }
    
    @staticmethod
    def get_packages() -> list[Dict]:
        """
        Получение списка доступных пакетов искр
        
        Returns:
            Список пакетов с минимальными суммами в TON
        """
        # Пакеты заданы статически, можно вынести в БД позже
        # Минимальные суммы в TON (nanotons) для каждого пакета
        # TODO: Уточнить минимальные суммы у пользователя
        packages = [
            {
                "id": 1,
                "amount": 50,
                "price": 49,
                "min_ton_amount_nanotons": 200000000,  # 0.2 TON (примерно, нужно уточнить)
                "discount": None,
                "original_price": None,
                "title": None,
                "description": None
            },
            {
                "id": 2,
                "amount": 150,
                "price": 147,
                "min_ton_amount_nanotons": 600000000,  # 0.6 TON (примерно, нужно уточнить)
                "discount": None,
                "original_price": None,
                "title": None,
                "description": None
            },
            {
                "id": 3,
                "amount": 300,
                "price": 245,
                "min_ton_amount_nanotons": 1000000000,  # 1.0 TON (примерно, нужно уточнить)
                "discount": 20,
                "original_price": 294,
                "title": None,
                "description": None
            },
            {
                "id": 4,
                "amount": "lifetime",
                "price": 1996,
                "min_ton_amount_nanotons": 8000000000,  # 8.0 TON (примерно, нужно уточнить)
                "discount": 40,
                "original_price": 4990,
                "title": "Разовый платёж",
                "description": "Доступ навсегда, без подписки и скрытых платежей"
            }
        ]
        return packages
