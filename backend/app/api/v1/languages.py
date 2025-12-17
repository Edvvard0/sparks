from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.language import LanguageListResponse, LanguageResponse
from app.models.language import Language

router = APIRouter()


@router.get("/", response_model=LanguageListResponse)
async def get_languages(
    db: Session = Depends(get_db)
):
    """Получение списка доступных языков"""
    languages = db.query(Language).filter(
        Language.is_active == True
    ).all()
    
    return LanguageListResponse(
        languages=[
            LanguageResponse(
                code=lang.code,
                name=lang.name,
                is_active=lang.is_active,
                created_at=lang.created_at
            )
            for lang in languages
        ]
    )

