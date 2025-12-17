from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import date
from typing import Dict, List, Optional
from app.models.user import User
from app.models.task import Task, TaskTranslation, TaskGenderTarget, GenderTarget, CategoryTranslation, TaskCategory
from app.models.daily import CompletedTask, DailyFreeTask
from app.models.transaction import Transaction, TransactionType, PaymentMethod, TransactionStatus
from app.models.language import Language


class TaskService:
    @staticmethod
    def get_tasks_for_user(
        db: Session,
        user: User,
        limit: int = 10,
        offset: int = 0,
        category_id: Optional[int] = None
    ) -> Dict:
        """
        Получение списка заданий для пользователя
        
        Args:
            db: Сессия БД
            user: Пользователь
            limit: Лимит заданий
            offset: Смещение
            category_id: Фильтр по категории (опционально)
            
        Returns:
            Словарь с заданиями и метаданными
        """
        # Получаем категории интересов пользователя
        # Проверяем, что interests не None и не пустой
        # Если interests не загружены, загружаем их явно
        if user.interests is None:
            # Если отношения не загружены, загружаем их
            from sqlalchemy.orm import joinedload
            db.refresh(user, ['interests'])
        
        user_category_ids = [uc.category_id for uc in (user.interests or [])]
        
        # Получаем выполненные задания
        completed_task_ids = [
            ct.task_id for ct in db.query(CompletedTask.task_id).filter(
                CompletedTask.user_id == user.tg_id
            ).all()
        ]
        
        # Базовый запрос заданий
        query = db.query(Task).filter(
            Task.is_active == True
        )
        
        # Фильтр по категориям интересов
        if user_category_ids:
            query = query.filter(Task.category_id.in_(user_category_ids))
        
        # Фильтр по категории (если указана)
        if category_id:
            query = query.filter(Task.category_id == category_id)
        
        # Фильтр по полу пользователя
        # Задание должно быть для 'all' или для пола пользователя
        gender_filter = or_(
            TaskGenderTarget.gender == GenderTarget.ALL,
            TaskGenderTarget.gender == user.gender.value
        )
        
        task_ids_with_gender = db.query(TaskGenderTarget.task_id).filter(
            gender_filter
        ).distinct().all()
        task_ids_with_gender = [t[0] for t in task_ids_with_gender]
        
        query = query.filter(Task.id.in_(task_ids_with_gender))
        
        # Исключаем выполненные задания
        if completed_task_ids:
            query = query.filter(~Task.id.in_(completed_task_ids))
        
        # Получаем общее количество
        total = query.count()
        
        # Получаем задания с пагинацией
        tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
        
        # Получаем информацию о бесплатных заданиях
        today = date.today()
        daily_task = db.query(DailyFreeTask).filter(
            and_(
                DailyFreeTask.user_id == user.tg_id,
                DailyFreeTask.date == today
            )
        ).first()
        
        # Если записи нет, создаем её с count=0 (для нового пользователя)
        if not daily_task:
            daily_task = DailyFreeTask(
                user_id=user.tg_id,
                date=today,
                count=0,
                paid_available=0
            )
            db.add(daily_task)
            db.commit()
            db.refresh(daily_task)
        
        free_count = daily_task.count if daily_task else 0
        free_remaining = max(0, 3 - free_count)
        # Обрабатываем случай, когда paid_available может быть None (для старых записей)
        paid_available = (daily_task.paid_available if daily_task and daily_task.paid_available is not None else 0)
        total_available = free_remaining + paid_available
        
        # Ограничиваем количество заданий до общего доступного лимита
        # Пользователь может получить только столько заданий, сколько у него осталось бесплатных попыток + купленных
        max_tasks_to_return = total_available
        tasks = tasks[:max_tasks_to_return] if max_tasks_to_return > 0 else []
        
        # Формируем ответ с переводами
        task_responses = []
        for task in tasks:
            # Получаем перевод на язык пользователя
            translation = db.query(TaskTranslation).filter(
                and_(
                    TaskTranslation.task_id == task.id,
                    TaskTranslation.language_id == user.language_id
                )
            ).first()
            
            # Если перевода нет, используем русский (fallback)
            if not translation:
                ru_language = db.query(Language).filter(Language.code == 'ru').first()
                if ru_language:
                    translation = db.query(TaskTranslation).filter(
                        and_(
                            TaskTranslation.task_id == task.id,
                            TaskTranslation.language_id == ru_language.id
                        )
                    ).first()
            
            if not translation:
                continue  # Пропускаем задания без перевода
            
            # Определяем, бесплатное ли задание (сначала бесплатные, затем купленные)
            is_free = len(task_responses) < free_remaining
            
            # Получаем категорию
            category = db.query(TaskCategory).filter(TaskCategory.id == task.category_id).first()
            category_translation = db.query(CategoryTranslation).filter(
                and_(
                    CategoryTranslation.category_id == task.category_id,
                    CategoryTranslation.language_id == user.language_id
                )
            ).first()
            
            category_name = category.slug if category else ""
            if category_translation:
                category_name = category_translation.name
            
            task_responses.append({
                "id": task.id,
                "title": translation.title,
                "description": translation.description,
                "category": {
                    "id": task.category_id,
                    "name": category_name,
                    "color": category.color if category else "#000000"
                },
                "is_free": is_free,
                "is_completed": False
            })
        
        return {
            "tasks": task_responses,
            "total": total,
            "free_remaining": free_remaining,
            "paid_available": paid_available
        }
    
    @staticmethod
    def complete_task(db: Session, user: User, task_id: int) -> Dict:
        """
        Выполнение задания пользователем
        
        Args:
            db: Сессия БД
            user: Пользователь
            task_id: ID задания
            
        Returns:
            Результат выполнения
        """
        # Проверяем, не выполнено ли уже
        existing = db.query(CompletedTask).filter(
            and_(
                CompletedTask.user_id == user.tg_id,
                CompletedTask.task_id == task_id
            )
        ).first()
        
        if existing:
            return {
                "success": False,
                "message": "Задание уже выполнено",
                "balance": user.balance
            }
        
        # Получаем задание
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {
                "success": False,
                "message": "Задание не найдено",
                "balance": user.balance
            }
        
        # Проверяем, бесплатное ли задание
        today = date.today()
        daily_task = db.query(DailyFreeTask).filter(
            and_(
                DailyFreeTask.user_id == user.tg_id,
                DailyFreeTask.date == today
            )
        ).first()
        
        if not daily_task:
            daily_task = DailyFreeTask(
                user_id=user.tg_id,
                date=today,
                count=0,
                paid_available=0
            )
            db.add(daily_task)
            db.flush()
        
        is_free = daily_task.count < 3
        # Обрабатываем случай, когда paid_available может быть None (для старых записей)
        paid_available_value = daily_task.paid_available if daily_task.paid_available is not None else 0
        has_paid_slot = paid_available_value > 0
        
        if is_free:
            # Бесплатное задание - увеличиваем счетчик
            daily_task.count += 1
        elif has_paid_slot:
            # Используем купленный слот без дополнительного списания
            # Убеждаемся, что paid_available не None перед уменьшением
            if daily_task.paid_available is None:
                daily_task.paid_available = 0
            daily_task.paid_available -= 1
        else:
            # Нет бесплатных и купленных слотов
            return {
                "success": False,
                "message": "Бесплатные задания закончились. Купите дополнительное задание за 10 искр.",
                "balance": user.balance
            }
        
        # Создаем запись о выполнении
        completed_task = CompletedTask(
            user_id=user.tg_id,
            task_id=task_id
        )
        db.add(completed_task)
        
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": "Задание выполнено",
            "balance": user.balance
        }

    @staticmethod
    def purchase_extra_task(db: Session, user: User) -> Dict:
        """
        Покупка дополнительного задания за 10 искр
        """
        COST = 10
        if user.balance < COST:
            return {
                "success": False,
                "message": "Недостаточно искр для покупки задания",
                "balance": user.balance,
                "free_remaining": 0,
                "paid_available": 0
            }
        
        today = date.today()
        daily_task = db.query(DailyFreeTask).filter(
            and_(
                DailyFreeTask.user_id == user.tg_id,
                DailyFreeTask.date == today
            )
        ).first()

        if not daily_task:
            daily_task = DailyFreeTask(
                user_id=user.tg_id,
                date=today,
                count=0,
                paid_available=0
            )
            db.add(daily_task)
            db.flush()

        # Списываем баланс и увеличиваем количество купленных слотов
        user.balance -= COST
        # Обрабатываем случай, когда paid_available может быть None (для старых записей)
        if daily_task.paid_available is None:
            daily_task.paid_available = 0
        daily_task.paid_available += 1

        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.tg_id,
            amount=-COST,
            transaction_type=TransactionType.PURCHASE,
            payment_method=PaymentMethod.SYSTEM,
            status=TransactionStatus.COMPLETED,
            description="Покупка дополнительного задания за 10 искр"
        )
        db.add(transaction)

        db.commit()
        db.refresh(user)
        db.refresh(daily_task)

        free_remaining = max(0, 3 - daily_task.count)
        # Убеждаемся, что paid_available не None перед возвратом
        paid_available_value = daily_task.paid_available if daily_task.paid_available is not None else 0

        return {
            "success": True,
            "message": "Дополнительное задание приобретено",
            "balance": user.balance,
            "free_remaining": free_remaining,
            "paid_available": paid_available_value
        }

