from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CategoryInfo(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    category_id: int


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    category: CategoryInfo
    is_free: bool
    is_completed: bool

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    free_remaining: int
    paid_available: int = 0


class TaskCompleteRequest(BaseModel):
    pass  # task_id берется из пути


class TaskCompleteResponse(BaseModel):
    success: bool
    message: str
    balance: int


class TaskPurchaseResponse(BaseModel):
    success: bool
    message: str
    balance: int
    free_remaining: int
    paid_available: int


class DailyFreeCountResponse(BaseModel):
    remaining: int
    reset_at: datetime
    paid_available: int = 0

