"""
Утилиты для работы с пользователями
"""
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse
from app.models.user import User
from app.models.task import CategoryTranslation


def user_to_response(user: User, db: Session = None) -> UserResponse:
    """
    Преобразование модели User в UserResponse
    
    Args:
        user: Модель пользователя
        
    Returns:
        UserResponse объект
    """
    # Получаем переводы категорий на языке пользователя
    interests = []
    for uc in user.interests:
        # Ищем перевод категории на языке пользователя
        category_translation = None
        
        # Если есть доступ к БД, делаем запрос напрямую (быстрее)
        if db:
            category_translation = db.query(CategoryTranslation).filter(
                CategoryTranslation.category_id == uc.category.id,
                CategoryTranslation.language_id == user.language_id
            ).first()
        else:
            # Fallback на relationship (может быть медленнее)
            for translation in uc.category.translations:
                if translation.language_id == user.language_id:
                    category_translation = translation
                    break
        
        # Используем перевод если есть, иначе slug
        category_name = category_translation.name if category_translation else uc.category.slug
        
        interests.append({
            "id": uc.category.id,
            "slug": uc.category.slug,
            "name": category_name,
            "color": uc.category.color
        })
    
    return UserResponse(
        tg_id=user.tg_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        balance=user.balance,
        language={
            "code": user.language.code,
            "name": user.language.name
        },
        interests=interests,
        is_admin=user.is_admin,
        wallet_address=user.wallet_address,
        has_lifetime_subscription=user.has_lifetime_subscription,
        created_at=user.created_at
    )

