from pydantic import BaseModel
from typing import List
from datetime import datetime


class LanguageResponse(BaseModel):
    code: str
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LanguageListResponse(BaseModel):
    languages: List[LanguageResponse]

