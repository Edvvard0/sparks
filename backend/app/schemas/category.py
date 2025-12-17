from pydantic import BaseModel
from typing import List


class CategoryBase(BaseModel):
    slug: str
    color: str


class CategoryResponse(BaseModel):
    id: int
    slug: str
    name: str
    color: str
    is_active: bool

    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    categories: List[CategoryResponse]

