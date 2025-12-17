from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from app.models.user import Gender


class UserBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    gender: Gender


class UserCreate(BaseModel):
    tg_id: Optional[int] = None
    wallet_address: Optional[str] = None
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    gender: Gender
    category_ids: List[int] = Field(..., min_items=1, max_items=5)
    language_code: Optional[str] = None
    
    @validator('wallet_address', always=True)
    def validate_identifier(cls, v, values):
        """Проверяем что указан хотя бы один идентификатор"""
        tg_id = values.get('tg_id')
        wallet_address = v
        if not tg_id and not wallet_address:
            raise ValueError('Either tg_id or wallet_address must be provided')
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserInterestsUpdate(BaseModel):
    category_ids: List[int] = Field(..., min_items=1, max_items=5)


class UserLanguageUpdate(BaseModel):
    language_code: str


class LanguageInfo(BaseModel):
    code: str
    name: str

    class Config:
        from_attributes = True


class CategoryInfo(BaseModel):
    id: int
    slug: str
    name: str
    color: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    tg_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    gender: Gender
    balance: int
    language: LanguageInfo
    interests: List[CategoryInfo]
    is_admin: bool
    wallet_address: Optional[str] = None
    has_lifetime_subscription: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

