from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from app.models.user import User, UserCategory, Gender
from app.models.language import Language
from app.models.task import TaskCategory
from app.models.daily import DailyFreeTask
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:
        """
        Создание нового пользователя
        
        Args:
            db: Сессия БД
            data: Данные для создания пользователя
            
        Returns:
            Созданный пользователь
        """
        # Проверяем, существует ли пользователь
        # Сначала по tg_id, затем по wallet_address
        existing_user = None
        if data.tg_id:
            existing_user = db.query(User).filter(User.tg_id == data.tg_id).first()
        if not existing_user and data.wallet_address:
            existing_user = db.query(User).filter(User.wallet_address == data.wallet_address).first()
        
        if existing_user:
            # Пользователь существует - обновляем категории интересов если они переданы
            if data.category_ids:
                # Удаляем старые связи с категориями
                db.query(UserCategory).filter(UserCategory.user_id == existing_user.tg_id).delete()
                
                # Добавляем новые категории
                categories = db.query(TaskCategory).filter(
                    TaskCategory.id.in_(data.category_ids),
                    TaskCategory.is_active == True
                ).all()
                
                for category in categories:
                    user_category = UserCategory(
                        user_id=existing_user.tg_id,
                        category_id=category.id
                    )
                    db.add(user_category)
                
                # Обновляем username если передан
                if data.username and data.username != existing_user.username:
                    existing_user.username = data.username
                
                db.commit()
                db.refresh(existing_user)
            
            return existing_user
        
        # Определяем язык
        language_code = data.language_code or 'en'
        language = db.query(Language).filter(Language.code == language_code).first()
        if not language:
            # Если язык не найден, используем английский
            language = db.query(Language).filter(Language.code == 'en').first()
        
        # Создаем пользователя
        user = User(
            tg_id=data.tg_id,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            gender=data.gender,
            language_id=language.id,
            wallet_address=data.wallet_address,
            is_admin=False,
            balance=0,
            is_active=True,
            has_lifetime_subscription=False
        )
        db.add(user)
        db.flush()
        
        # Связываем с категориями (1-5)
        categories = db.query(TaskCategory).filter(
            TaskCategory.id.in_(data.category_ids),
            TaskCategory.is_active == True
        ).all()
        
        for category in categories:
            user_category = UserCategory(
                user_id=user.tg_id,
                category_id=category.id
            )
            db.add(user_category)
        
        # Инициализируем DailyFreeTask для сегодня
        today = date.today()
        daily_task = DailyFreeTask(
            user_id=user.tg_id,
            date=today,
            count=0
        )
        db.add(daily_task)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_interests(db: Session, user: User, category_ids: list[int]) -> User:
        """
        Обновление интересов пользователя
        
        Args:
            db: Сессия БД
            user: Пользователь
            category_ids: Список ID категорий (1-5)
            
        Returns:
            Обновленный пользователь
        """
        # Удаляем старые связи
        db.query(UserCategory).filter(UserCategory.user_id == user.tg_id).delete()
        
        # Добавляем новые категории
        categories = db.query(TaskCategory).filter(
            TaskCategory.id.in_(category_ids),
            TaskCategory.is_active == True
        ).all()
        
        for category in categories:
            user_category = UserCategory(
                user_id=user.tg_id,
                category_id=category.id
            )
            db.add(user_category)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_language(db: Session, user: User, language_code: str) -> User:
        """
        Обновление языка пользователя
        
        Args:
            db: Сессия БД
            user: Пользователь
            language_code: Код языка
            
        Returns:
            Обновленный пользователь
        """
        language = db.query(Language).filter(
            Language.code == language_code,
            Language.is_active == True
        ).first()
        
        if language:
            user.language_id = language.id
            db.commit()
            db.refresh(user)
        
        return user
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)

