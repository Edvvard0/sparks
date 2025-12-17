from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import pytz
from app.core.database import get_db
from app.core.dependencies import get_current_user_required, get_current_user
from app.schemas.task import (
    TaskListResponse,
    TaskResponse,
    TaskCompleteResponse,
    DailyFreeCountResponse,
    TaskPurchaseResponse
)
from app.services.task_service import TaskService
from app.models.user import User
from app.models.daily import DailyFreeTask
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category_id: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка заданий для пользователя
    
    Возвращает максимум 3 задания (или меньше, если у пользователя осталось меньше бесплатных попыток).
    Выполненные задания автоматически исключаются из ответа.
    """
    result = TaskService.get_tasks_for_user(
        db=db,
        user=user,
        limit=limit,  # Используем limit для внутреннего запроса, но ограничим результат до free_remaining
        offset=offset,
        category_id=category_id
    )
    return TaskListResponse(**result)


@router.get("/daily-free-count", response_model=DailyFreeCountResponse)
async def get_daily_free_count(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Получение количества оставшихся бесплатных заданий"""
    from datetime import date
    from app.models.daily import DailyFreeTask
    
    today = date.today()
    daily_task = db.query(DailyFreeTask).filter(
        DailyFreeTask.user_id == user.tg_id,
        DailyFreeTask.date == today
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
    
    count = daily_task.count if daily_task else 0
    remaining = max(0, 3 - count)
    # Обрабатываем случай, когда paid_available может быть None (для старых записей)
    paid_available = daily_task.paid_available if daily_task and daily_task.paid_available is not None else 0
    
    # Время сброса - следующий день в 00:00 МСК
    moscow_tz = pytz.timezone(settings.TIMEZONE)
    from datetime import timedelta
    tomorrow = today + timedelta(days=1)
    reset_at = moscow_tz.localize(datetime.combine(tomorrow, datetime.min.time()))
    
    return DailyFreeCountResponse(
        remaining=remaining,
        reset_at=reset_at,
        paid_available=paid_available
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение конкретного задания"""
    from app.models.task import Task, TaskTranslation
    from app.models.language import Language
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Получаем перевод
    translation = db.query(TaskTranslation).filter(
        TaskTranslation.task_id == task_id,
        TaskTranslation.language_id == user.language_id
    ).first()
    
    # Fallback на русский
    if not translation:
        ru_language = db.query(Language).filter(Language.code == 'ru').first()
        if ru_language:
            translation = db.query(TaskTranslation).filter(
                TaskTranslation.task_id == task_id,
                TaskTranslation.language_id == ru_language.id
            ).first()
    
    if not translation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Translation not found")
    
    # Проверяем, выполнено ли
    from app.models.daily import CompletedTask
    is_completed = db.query(CompletedTask).filter(
        CompletedTask.user_id == user.tg_id,
        CompletedTask.task_id == task_id
    ).first() is not None
    
    # Получаем категорию
    from app.models.task import TaskCategory, CategoryTranslation
    category = db.query(TaskCategory).filter(TaskCategory.id == task.category_id).first()
    category_translation = db.query(CategoryTranslation).filter(
        CategoryTranslation.category_id == category.id,
        CategoryTranslation.language_id == user.language_id
    ).first()
    
    category_name = category.slug
    if (category_translation):
        category_name = category_translation.name
    
    # Проверяем, бесплатное ли
    from datetime import date
    today = date.today()
    daily_task = db.query(DailyFreeTask).filter(
        DailyFreeTask.user_id == user.tg_id,
        DailyFreeTask.date == today
    ).first()
    
    free_count = daily_task.count if daily_task else 0
    is_free = free_count < 3
    
    return TaskResponse(
        id=task.id,
        title=translation.title,
        description=translation.description,
        category={
            "id": category.id,
            "name": category_name,
            "color": category.color
        },
        is_free=is_free,
        is_completed=is_completed
    )


@router.post("/{task_id}/complete", response_model=TaskCompleteResponse)
async def complete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Выполнение задания"""
    result = TaskService.complete_task(db, user, task_id)
    return TaskCompleteResponse(**result)


@router.post("/purchase-extra", response_model=TaskPurchaseResponse)
async def purchase_extra_task(
    user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Покупка дополнительного задания за 10 искр"""
    result = TaskService.purchase_extra_task(db, user)
    return TaskPurchaseResponse(**result)

