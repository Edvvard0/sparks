from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.category import CategoryListResponse, CategoryResponse
from app.models.task import TaskCategory, CategoryTranslation
from app.models.language import Language
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    language_code: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка категорий"""
    # Определяем язык
    
    if language_code:
        language = db.query(Language).filter(Language.code == language_code).first()
    elif user:
        language = user.language
    else:
        language = db.query(Language).filter(Language.code == 'en').first()
    
    if not language:
        language = db.query(Language).filter(Language.code == 'en').first()
    
    # Получаем категории
    categories = db.query(TaskCategory).filter(
        TaskCategory.is_active == True
    ).all()
    
    result = []
    for category in categories:
        # Получаем перевод
        translation = db.query(CategoryTranslation).filter(
            CategoryTranslation.category_id == category.id,
            CategoryTranslation.language_id == language.id
        ).first()
        
        name = category.slug
        if translation:
            name = translation.name
        
        result.append(CategoryResponse(
            id=category.id,
            slug=category.slug,
            name=name,
            color=category.color,
            is_active=category.is_active
        ))
    
    return CategoryListResponse(categories=result)

