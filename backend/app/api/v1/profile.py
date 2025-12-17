from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user_required as get_current_user
from app.schemas.user import UserResponse, UserUpdate, UserInterestsUpdate, UserLanguageUpdate
from app.schemas.task import TaskResponse
from app.services.user_service import UserService
from app.models.user import User
from app.utils.user_utils import user_to_response

router = APIRouter()


@router.get("/", response_model=UserResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение профиля пользователя"""
    db.refresh(user)
    
    return user_to_response(user, db)


@router.put("/", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    
    db.commit()
    db.refresh(user)
    
    return user_to_response(user, db)


@router.put("/interests", response_model=UserResponse)
async def update_interests(
    data: UserInterestsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление интересов пользователя"""
    user = UserService.update_interests(db, user, data.category_ids)
    db.refresh(user)
    
    return user_to_response(user, db)


@router.put("/language", response_model=UserResponse)
async def update_language(
    data: UserLanguageUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление языка пользователя"""
    user = UserService.update_language(db, user, data.language_code)
    db.refresh(user)
    
    return user_to_response(user, db)


@router.get("/history", response_model=list[TaskResponse])
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение истории выполненных заданий"""
    from app.models.daily import CompletedTask
    from app.models.task import Task, TaskTranslation, TaskCategory, CategoryTranslation
    
    completed_tasks = db.query(CompletedTask).filter(
        CompletedTask.user_id == user.tg_id
    ).order_by(CompletedTask.completed_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for ct in completed_tasks:
        task = ct.task
        translation = db.query(TaskTranslation).filter(
            TaskTranslation.task_id == task.id,
            TaskTranslation.language_id == user.language_id
        ).first()
        
        if not translation:
            from app.models.language import Language
            ru_language = db.query(Language).filter(Language.code == 'ru').first()
            if ru_language:
                translation = db.query(TaskTranslation).filter(
                    TaskTranslation.task_id == task.id,
                    TaskTranslation.language_id == ru_language.id
                ).first()
        
        if not translation:
            continue
        
        category = db.query(TaskCategory).filter(TaskCategory.id == task.category_id).first()
        category_translation = db.query(CategoryTranslation).filter(
            CategoryTranslation.category_id == category.id,
            CategoryTranslation.language_id == user.language_id
        ).first()
        
        category_name = category.slug
        if category_translation:
            category_name = category_translation.name
        
        result.append(TaskResponse(
            id=task.id,
            title=translation.title,
            description=translation.description,
            category={
                "id": category.id,
                "name": category_name,
                "color": category.color
            },
            is_free=False,
            is_completed=True
        ))
    
    return result

