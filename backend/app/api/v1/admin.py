from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.schemas.user import UserResponse
from app.models.user import User
from app.utils.user_utils import user_to_response

router = APIRouter()


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=UserResponse)
async def admin_login(
    data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """Авторизация администратора"""
    from app.core.dependencies import get_current_admin
    
    try:
        user = await get_current_admin(data.username, data.password, db)
        return user_to_response(user, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

