"""
Сервис для работы с TON Connect и TON платежами
"""
import hashlib
import hmac
import time
import requests
import re
import urllib.parse
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.transaction import Transaction, TransactionStatus
from app.models.user import User


class TONService:
    """Сервис для работы с TON"""
    
    @staticmethod
    def generate_auth_message() -> str:
        """
        Генерация сообщения для подписи при авторизации через TON Connect
        
        Returns:
            Сообщение для подписи
        """
        timestamp = int(time.time())
        message = f"Sparks App Auth\nTimestamp: {timestamp}"
        return message
    
    @staticmethod
    def verify_signature(wallet_address: str, signature: str, message: str) -> bool:
        """
        Проверка подписи сообщения от TON кошелька
        
        Args:
            wallet_address: Адрес кошелька
            signature: Подпись сообщения
            message: Сообщение которое было подписано
            
        Returns:
            True если подпись валидна
        """
        # Для базовой версии упрощаем проверку
        # В продакшене нужно использовать реальную проверку подписи через Ed25519
        try:
            # Базовая проверка формата
            if not wallet_address or not signature or not message:
                return False
            
            # Проверка формата адреса TON
            # TON адреса могут быть в форматах:
            # - EQ... (user-friendly)
            # - 0:... (raw)
            # - UQ... (bounceable)
            # - kQ... (testnet)
            wallet_address_upper = wallet_address.upper()
            valid_prefixes = ['EQ', '0:', 'UQ', 'KQ']
            is_valid_address = any(wallet_address_upper.startswith(prefix) for prefix in valid_prefixes)
            
            if not is_valid_address:
                # Проверяем если это raw формат (начинается с 0:)
                if not wallet_address.startswith('0:'):
                    # Проверяем длину (TON адреса обычно 48 символов в raw формате или 36 в user-friendly)
                    if len(wallet_address) < 30:
                        return False
            
            # Для базовой версии принимаем любую подпись если адрес валидный
            # TODO: Реальная проверка подписи через pytoniq или tonpy
            # Пример:
            # from pytoniq import Address
            # from pytoniq.crypto import verify_signature
            # address = Address(wallet_address)
            # # Проверка подписи Ed25519...
            
            return True
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False
    
    @staticmethod
    def convert_rub_to_ton(rub_amount: int, min_ton_amount_nanotons: Optional[int] = None) -> str:
        """
        Конвертация рублей в TON (nanotons)
        
        Args:
            rub_amount: Сумма в рублях
            min_ton_amount_nanotons: Минимальная сумма в nanotons (если указана, используется она)
            
        Returns:
            Сумма в nanotons (строка)
        """
        # TODO: Использовать реальный курс из БД или API
        # Пока используем фиксированный курс (примерно 250 руб за TON)
        # 1 TON = 1,000,000,000 nanotons
        
        if min_ton_amount_nanotons:
            # Если указана минимальная сумма, используем её
            return str(min_ton_amount_nanotons)
        
        # Фиксированный курс (можно вынести в конфиг или БД)
        TON_TO_RUB_RATE = 250.0  # 1 TON = 250 руб
        
        # Вычисляем сумму в TON
        ton_amount = rub_amount / TON_TO_RUB_RATE
        
        # Конвертируем в nanotons
        nanotons = int(ton_amount * 1_000_000_000)
        
        # Проверяем минимальную сумму
        min_nanotons = settings.TON_MIN_AMOUNT_NANOTONS
        if nanotons < min_nanotons:
            nanotons = min_nanotons
        
        return str(nanotons)
    
    @staticmethod
    def generate_deep_link(to_address: str, amount_nanotons: str, comment: Optional[str] = None) -> str:
        """
        Генерация deep link для перевода TON
        
        Args:
            to_address: Адрес получателя
            amount_nanotons: Сумма в nanotons
            comment: Комментарий к переводу (опционально)
            
        Returns:
            Deep link для открытия кошелька
        """
        # РЕЖИМ СИМУЛЯЦИИ: в тестовом режиме можно использовать testnet адреса
        # Для testnet deep link будет работать с testnet кошельками
        if settings.TON_NETWORK == "testnet":
            # В testnet можно использовать специальные тестовые адреса
            # Но deep link формат остается тем же
            pass
        
        # Формат deep link для TON: ton://transfer/{address}?amount={nanotons}&text={comment}
        deep_link = f"ton://transfer/{to_address}?amount={amount_nanotons}"
        
        if comment:
            # Кодируем комментарий для URL
            encoded_comment = urllib.parse.quote(comment)
            deep_link += f"&text={encoded_comment}"
        
        return deep_link
    
    @staticmethod
    async def check_transaction(transaction_hash: str) -> Optional[Dict]:
        """
        Проверка транзакции в блокчейне TON
        
        Args:
            transaction_hash: Хеш транзакции
            
        Returns:
            Данные транзакции или None если не найдена
        """
        try:
            # Используем TON API для проверки транзакции
            api_url = settings.TON_API_URL
            api_key = settings.TON_API_KEY
            
            # Если используется testnet, меняем URL API
            if settings.TON_NETWORK == "testnet":
                # Для testnet используем testnet API
                api_url = api_url.replace("tonapi.io/v2", "testnet.tonapi.io/v2")
            
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Запрос к TON API для получения транзакции
            # Формат зависит от используемого API (tonapi.io, toncenter.com и т.д.)
            url = f"{api_url}/blockchain/transactions/{transaction_hash}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"TON API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error checking transaction: {e}")
            return None
    
    @staticmethod
    def verify_transaction_payment(
        transaction_data: Dict,
        expected_to_address: str,
        expected_amount_nanotons: str,
        expected_from_address: Optional[str] = None
    ) -> bool:
        """
        Проверка что транзакция соответствует ожидаемому платежу
        
        Args:
            transaction_data: Данные транзакции из блокчейна
            expected_to_address: Ожидаемый адрес получателя
            expected_amount_nanotons: Ожидаемая сумма в nanotons
            expected_from_address: Ожидаемый адрес отправителя (опционально)
            
        Returns:
            True если транзакция соответствует ожиданиям
        """
        try:
            # Проверка зависит от формата ответа TON API
            # Пример для tonapi.io:
            if 'account' in transaction_data:
                to_address = transaction_data['account'].get('address', '')
                if to_address != expected_to_address:
                    return False
            
            if 'in_msg' in transaction_data:
                in_msg = transaction_data['in_msg']
                amount = str(in_msg.get('value', 0))
                if amount != expected_amount_nanotons:
                    return False
                
                if expected_from_address:
                    from_address = in_msg.get('source', {}).get('address', '')
                    if from_address != expected_from_address:
                        return False
            
            return True
            
        except Exception as e:
            print(f"Error verifying transaction payment: {e}")
            return False
    
    @staticmethod
    async def monitor_pending_payments(db: Session) -> None:
        """
        Периодическая проверка всех pending TON платежей
        
        Args:
            db: Сессия БД
        """
        try:
            # Получаем все pending транзакции с методом оплаты TON
            from app.models.transaction import PaymentMethod
            
            pending_transactions = db.query(Transaction).filter(
                Transaction.payment_method == PaymentMethod.TON,
                Transaction.status == TransactionStatus.PENDING,
                Transaction.ton_transaction_hash.isnot(None)
            ).all()
            
            for transaction in pending_transactions:
                if not transaction.ton_transaction_hash:
                    continue
                
                # Проверяем транзакцию в блокчейне
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
                        # Транзакция подтверждена - обновляем статус
                        transaction.status = TransactionStatus.COMPLETED
                        
                        # Пополняем баланс пользователя
                        user = db.query(User).filter(User.tg_id == transaction.user_id).first()
                        if user:
                            # Проверяем если это lifetime подписка
                            is_lifetime = False
                            if transaction.description and "lifetime" in transaction.description.lower():
                                is_lifetime = True
                            elif isinstance(transaction.amount, str) and transaction.amount.lower() == "lifetime":
                                is_lifetime = True
                            else:
                                # Проверяем по пакету через описание
                                from app.services.payment_service import PaymentService
                                packages = PaymentService.get_packages()
                                match = re.search(r'пакет #(\d+)', transaction.description or '')
                                if match:
                                    package_id = int(match.group(1))
                                    package = next((pkg for pkg in packages if pkg["id"] == package_id), None)
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
                        print(f"TON payment confirmed: transaction {transaction.id}, user {transaction.user_id}")
            
        except Exception as e:
            print(f"Error monitoring pending payments: {e}")
            db.rollback()

