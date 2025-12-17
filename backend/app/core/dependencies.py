from fastapi import Header, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.services.user_service import UserService


def get_current_user_required(
    tg_id: Optional[str] = Header(None, alias="X-Telegram-User-ID"),
    tg_id_query: Optional[int] = Query(None, alias="tg_id"),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя по tg_id или wallet_address (обязательно)
    
    Args:
        tg_id: Telegram ID из заголовка X-Telegram-User-ID (строка, будет преобразована в int)
        tg_id_query: Telegram ID из query параметра (альтернатива)
        wallet_address: TON адрес кошелька из заголовка X-Wallet-Address
        db: Сессия БД
        
    Returns:
        Пользователь
        
    Raises:
        HTTPException: Если ни tg_id ни wallet_address не указаны или пользователь не найден
    """
    user = None
    
    # Сначала проверяем wallet_address (приоритет для TON пользователей)
    if wallet_address:
        wallet_address_clean = str(wallet_address).strip()
        if wallet_address_clean:
            user = db.query(User).options(joinedload(User.interests)).filter(User.wallet_address == wallet_address_clean).first()
            if user:
                if not user.is_active:
                    raise HTTPException(status_code=403, detail="User is not active")
                return user
    
    # Если не найден по wallet_address, ищем по tg_id
    user_tg_id = None
    if tg_id is not None:
        # Убираем пробелы и проверяем, что это не пустая строка
        tg_id_clean = str(tg_id).strip()
        if tg_id_clean:
            try:
                user_tg_id = int(tg_id_clean)
            except (ValueError, TypeError):
                raise HTTPException(status_code=422, detail="Invalid tg_id format. Must be a valid integer")
    
    # Используем tg_id из заголовка или из query параметра
    user_tg_id = user_tg_id or tg_id_query
    
    if user_tg_id:
        user = db.query(User).options(joinedload(User.interests)).filter(User.tg_id == user_tg_id).first()
        if user:
            if not user.is_active:
                raise HTTPException(status_code=403, detail="User is not active")
            return user
    
    # Если пользователь не найден ни по одному из способов
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication. Provide X-Telegram-User-ID header or X-Wallet-Address header"
        )
    
    return user


async def get_current_user(
    tg_id: Optional[str] = Header(None, alias="X-Telegram-User-ID"),
    tg_id_query: Optional[int] = Query(None, alias="tg_id"),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Получение текущего пользователя по tg_id или wallet_address (опционально)
    
    Args:
        tg_id: Telegram ID из заголовка X-Telegram-User-ID (строка, будет преобразована в int)
        tg_id_query: Telegram ID из query параметра (альтернатива)
        wallet_address: TON адрес кошелька из заголовка X-Wallet-Address
        db: Сессия БД
        
    Returns:
        Пользователь или None если не указан ни tg_id ни wallet_address
        
    Raises:
        HTTPException: Если пользователь не найден или неактивен
    """
    user = None
    
    # Сначала проверяем wallet_address (приоритет для TON пользователей)
    if wallet_address:
        wallet_address_clean = str(wallet_address).strip()
        if wallet_address_clean:
            user = db.query(User).options(joinedload(User.interests)).filter(User.wallet_address == wallet_address_clean).first()
            if user:
                if not user.is_active:
                    return None
                return user
    
    # Если не найден по wallet_address, ищем по tg_id
    user_tg_id = None
    if tg_id is not None:
        # Убираем пробелы и проверяем, что это не пустая строка
        tg_id_clean = str(tg_id).strip()
        if tg_id_clean:
            try:
                user_tg_id = int(tg_id_clean)
            except (ValueError, TypeError):
                # Если не удалось преобразовать, возвращаем None (опциональный параметр)
                return None
    
    # Используем tg_id из заголовка или из query параметра
    user_tg_id = user_tg_id or tg_id_query
    
    if user_tg_id:
        user = db.query(User).options(joinedload(User.interests)).filter(User.tg_id == user_tg_id).first()
        if user:
            if not user.is_active:
                return None
            return user
    
    return None


async def get_current_admin(
    username: str,
    password: str,
    db: Session = Depends(get_db)
) -> User:
    """
    Получение администратора по username и password
    
    Args:
        username: Имя пользователя
        password: Пароль
        db: Сессия БД
        
    Returns:
        Пользователь-администратор
        
    Raises:
        HTTPException: Если данные невалидны
    """
    user = db.query(User).filter(
        User.username == username,
        User.is_admin == True
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.password:
        raise HTTPException(status_code=401, detail="Password not set")
    
    if not UserService.verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is not active")
    
    return user
