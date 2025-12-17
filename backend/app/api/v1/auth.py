from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import secrets
import hashlib
from app.core.database import get_db
from app.core.dependencies import get_current_user_required as get_current_user
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import (
    TonConnectRequest, 
    TonConnectResponse,
    TonProofGenerateResponse,
    TonProofCheckRequest,
    TonProofCheckResponse
)
from app.services.user_service import UserService
from app.services.ton_service import TONService
from app.models.user import User, Gender
from app.models.language import Language
from app.utils.user_utils import user_to_response

router = APIRouter()

# In-memory кэш для payload (в продакшене использовать Redis)
_payload_cache: dict[str, dict] = {}


@router.post("/register", response_model=UserResponse)
async def register(
    data: UserCreate,
    db: Session = Depends(get_db),
    tg_id_header: Optional[int] = Header(None, alias="X-Telegram-User-ID"),
    tg_username_header: Optional[str] = Header(None, alias="X-Telegram-Username")
):
    """
    Регистрация нового пользователя
    
    Может работать как с tg_id (из Telegram Mini App), так и с wallet_address
    Если есть wallet_address, но нет tg_id - генерируем tg_id из wallet_address
    (только для случаев, когда приложение запущено не в Telegram)
    """
    # Используем данные из заголовков если они переданы и не указаны в data
    if tg_id_header and not data.tg_id:
        data.tg_id = tg_id_header
    if tg_username_header and not data.username:
        data.username = tg_username_header
    
    # Если есть wallet_address, но нет tg_id - генерируем tg_id из wallet_address
    # Это происходит только если приложение запущено не в Telegram Mini App
    if data.wallet_address and not data.tg_id:
        tg_id_hash = int(hashlib.md5(data.wallet_address.encode()).hexdigest()[:15], 16)
        
        # Проверяем что такого tg_id нет
        while db.query(User).filter(User.tg_id == tg_id_hash).first():
            tg_id_hash += 1
        
        data.tg_id = tg_id_hash
    
    try:
        user = UserService.create_user(db, data)
        
        # Обновляем username из заголовков если передан
        # НЕ обновляем tg_id - это первичный ключ и нарушит внешние ключи
        updated = False
        if tg_username_header and tg_username_header != user.username:
            user.username = tg_username_header
            updated = True
        
        if updated:
            db.commit()
            db.refresh(user)
        
        # Формируем ответ
        return user_to_response(user, db)
    except Exception as e:
        db.rollback()
        print(f"[Register] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_me(
    tg_id: Optional[str] = Header(None, alias="X-Telegram-User-ID"),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
):
    """
    Получение текущего пользователя или автоматическая регистрация по tg_id
    
    Если пользователь не найден, но есть tg_id из Telegram - создаем пользователя автоматически
    """
    # Сначала пытаемся найти существующего пользователя
    user = None
    
    # Ищем по wallet_address (если указан)
    if wallet_address:
        wallet_address_clean = str(wallet_address).strip()
        if wallet_address_clean:
            user = db.query(User).options(joinedload(User.interests)).filter(User.wallet_address == wallet_address_clean).first()
    
    # Если не найден по wallet_address, ищем по tg_id
    if not user and tg_id:
        try:
            user_tg_id = int(str(tg_id).strip())
            user = db.query(User).options(joinedload(User.interests)).filter(User.tg_id == user_tg_id).first()
        except (ValueError, TypeError):
            pass
    
    # Если пользователь не найден - возвращаем 404
    # Пользователь должен быть создан через /register после прохождения онбординга
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first."
        )
    
    # Проверяем активность
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is not active")
    
    # Обновляем связи для получения актуальных данных
    db.refresh(user)
    
    return user_to_response(user, db)


@router.get("/verify")
async def verify(
    tg_id: int
):
    """Проверка существования пользователя"""
    db = next(get_db())
    user = db.query(User).filter(User.tg_id == tg_id).first()
    return {"exists": user is not None, "is_active": user.is_active if user else False}


@router.post("/ton/connect", response_model=TonConnectResponse)
async def ton_connect(
    data: TonConnectRequest,
    db: Session = Depends(get_db)
):
    """
    Авторизация через TON Connect
    
    Проверяет подпись сообщения от TON кошелька и создает/находит пользователя
    """
    # Проверяем подпись
    if not TONService.verify_signature(data.wallet_address, data.signature, data.message):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Ищем пользователя по wallet_address
    user = db.query(User).filter(User.wallet_address == data.wallet_address).first()
    
    if user:
        # Пользователь найден - обновляем данные если нужно
        db.refresh(user)
    else:
        # Создаем нового пользователя
        # Для TON пользователей без Telegram используем дефолтные значения
        default_language = db.query(Language).filter(Language.code == 'en').first()
        if not default_language:
            default_language = db.query(Language).first()
        
        if not default_language:
            raise HTTPException(status_code=500, detail="No default language found")
        
        # Генерируем временный tg_id на основе wallet_address (hash)
        import hashlib
        tg_id_hash = int(hashlib.md5(data.wallet_address.encode()).hexdigest()[:15], 16)
        
        # Проверяем что такого tg_id нет
        while db.query(User).filter(User.tg_id == tg_id_hash).first():
            tg_id_hash += 1
        
        user = User(
            tg_id=tg_id_hash,
            username=None,
            first_name="TON User",
            last_name=None,
            gender=Gender.MALE,  # Дефолтное значение
            language_id=default_language.id,
            wallet_address=data.wallet_address,
            is_admin=False,
            balance=0,
            is_active=True,
            has_lifetime_subscription=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Формируем ответ
    return TonConnectResponse(
        success=True,
        user=user_to_response(user, db)
    )


@router.post("/ton-proof/generate", response_model=TonProofGenerateResponse)
async def generate_ton_proof_payload(
    db: Session = Depends(get_db)
):
    """
    Генерация payload для TON Proof
    
    Payload - это случайная строка, которая будет подписана кошельком
    """
    import time
    
    # Генерируем случайный payload (32 байта в hex)
    payload = secrets.token_hex(32)
    
    # Сохраняем payload в кэш с временем жизни (TTL = 20 минут)
    ttl_seconds = 20 * 60
    created_at = time.time()
    _payload_cache[payload] = {
        "created_at": created_at,
        "ttl": ttl_seconds
    }
    
    print(f"[TON Proof] Generated payload: {payload[:50]}... (cache size: {len(_payload_cache)})")
    
    # Очищаем старые payload из кэша
    current_time = time.time()
    expired_keys = [
        key for key, value in _payload_cache.items()
        if current_time - value["created_at"] > value["ttl"]
    ]
    if expired_keys:
        print(f"[TON Proof] Cleaning {len(expired_keys)} expired payloads from cache")
        for key in expired_keys:
            del _payload_cache[key]
    
    return TonProofGenerateResponse(payload=payload)


@router.post("/ton-proof/check", response_model=TonProofCheckResponse)
async def check_ton_proof(
    data: TonProofCheckRequest,
    tg_id: Optional[int] = Header(None, alias="X-Telegram-User-ID"),
    db: Session = Depends(get_db)
):
    """
    Проверка TON Proof и авторизация пользователя
    
    Args:
        data: Данные proof от кошелька
            - address: адрес кошелька
            - network: сеть (mainnet/testnet)
            - proof: объект proof с полями:
                - timestamp: время создания
                - domain: домен приложения
                - payload: payload который был подписан
                - signature: подпись
                - state_init: state init кошелька (для получения публичного ключа)
    """
    import time
    
    # Проверяем что payload существует в кэше
    proof_payload = data.proof.get("payload")
    print(f"[TON Proof] Checking proof for address: {data.address}")
    print(f"[TON Proof] Payload from request: {proof_payload[:50] if proof_payload else None}...")
    print(f"[TON Proof] Payload full length: {len(proof_payload) if proof_payload else 0}")
    print(f"[TON Proof] Payload cache keys count: {len(_payload_cache)}")
    
    # Показываем первые несколько payload из кэша для отладки
    if _payload_cache:
        cache_samples = list(_payload_cache.keys())[:3]
        print(f"[TON Proof] Sample payloads in cache:")
        for i, cached_payload in enumerate(cache_samples):
            print(f"[TON Proof]   [{i}] {cached_payload[:50]}... (length: {len(cached_payload)})")
            print(f"[TON Proof]   [{i}] Match: {cached_payload == proof_payload}")
    
    if not proof_payload:
        print("[TON Proof] ERROR: No payload in proof")
        raise HTTPException(
            status_code=401,
            detail="Invalid proof: missing payload"
        )
    
    # Проверяем точное совпадение payload
    if proof_payload not in _payload_cache:
        print(f"[TON Proof] ERROR: Payload not found in cache")
        print(f"[TON Proof] Request payload type: {type(proof_payload)}")
        print(f"[TON Proof] Request payload value: {repr(proof_payload[:100])}")
        
        # Проверяем есть ли похожие payload (для отладки)
        similar_payloads = [k for k in _payload_cache.keys() if k.startswith(proof_payload[:10])]
        if similar_payloads:
            print(f"[TON Proof] Found similar payloads (first 10 chars match): {len(similar_payloads)}")
        
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired payload. Please reconnect your wallet."
        )
    
    # Удаляем использованный payload из кэша (одноразовое использование)
    del _payload_cache[proof_payload]
    
    # Для базовой версии упрощаем проверку proof
    # В продакшене нужна реальная криптографическая проверка через Ed25519
    # Проверяем базовые поля proof
    signature = data.proof.get("signature")
    proof_timestamp = data.proof.get("timestamp")
    
    print(f"[TON Proof] Proof fields check:")
    print(f"[TON Proof] - Has signature: {bool(signature)}")
    print(f"[TON Proof] - Has timestamp: {bool(proof_timestamp)}")
    
    if not signature or not proof_timestamp:
        print("[TON Proof] ERROR: Missing signature or timestamp")
        raise HTTPException(
            status_code=401,
            detail="Invalid proof format: missing signature or timestamp"
        )
    
    # Проверяем timestamp (не старше 10 минут)
    current_timestamp = int(time.time())
    timestamp_diff = abs(current_timestamp - proof_timestamp)
    print(f"[TON Proof] Timestamp check: current={current_timestamp}, proof={proof_timestamp}, diff={timestamp_diff}s")
    
    if timestamp_diff > 600:  # 10 минут
        print(f"[TON Proof] ERROR: Proof timestamp expired (diff={timestamp_diff}s)")
        raise HTTPException(
            status_code=401,
            detail="Proof timestamp expired. Please reconnect your wallet."
        )
    
    # Ищем пользователя сначала по tg_id (если передан), затем по wallet_address
    user = None
    
    # Сначала ищем по tg_id (приоритет - пользователь уже зарегистрирован)
    if tg_id:
        try:
            user = db.query(User).filter(User.tg_id == tg_id).first()
            if user:
                print(f"[TON Proof] Found user by tg_id: tg_id={user.tg_id}, current wallet_address={user.wallet_address}")
                # Обновляем wallet_address если он отличается
                if user.wallet_address != data.address:
                    print(f"[TON Proof] Updating wallet_address: {user.wallet_address} -> {data.address}")
                    user.wallet_address = data.address
                    db.commit()
                    db.refresh(user)
                    print(f"[TON Proof] Wallet address updated successfully")
        except Exception as e:
            print(f"[TON Proof] Error searching by tg_id: {e}")
    
    # Если не найден по tg_id, ищем по wallet_address
    if not user:
        user = db.query(User).filter(User.wallet_address == data.address).first()
        if user:
            print(f"[TON Proof] Found user by wallet_address: tg_id={user.tg_id}, wallet_address={user.wallet_address}")
    
    # Если пользователь не найден - НЕ создаем нового
    # Пользователь должен быть зарегистрирован через /register после онбординга
    if not user:
        print(f"[TON Proof] User not found. tg_id={tg_id}, wallet_address={data.address}")
        print(f"[TON Proof] User must register first through /register endpoint after onboarding")
        # Возвращаем успешный результат, но без пользователя
        # Фронтенд обработает это и сохранит wallet_address для использования при регистрации
        return TonProofCheckResponse(
            success=True,
            user=None,
            token=None,
            message="User not found. Please register first."
        )
    
    print(f"[TON Proof] Authentication successful for user: tg_id={user.tg_id}, wallet_address={user.wallet_address}")
    
    # Пользователь найден или создан - возвращаем его
    db.refresh(user)
    print(f"[TON Proof] Authentication successful for wallet: {data.address}")
    return TonProofCheckResponse(
        success=True,
        user=user_to_response(user, db),
        token=None,  # Можно добавить JWT токен если нужен
        message="Authentication successful"
    )


@router.patch("/wallet/disconnect", response_model=UserResponse)
async def disconnect_wallet(
    tg_id: Optional[int] = Header(None, alias="X-Telegram-User-ID"),
    db: Session = Depends(get_db)
):
    """
    Отключение TON кошелька от профиля пользователя
    
    Устанавливает wallet_address в null для текущего пользователя
    """
    if not tg_id:
        raise HTTPException(
            status_code=400,
            detail="Telegram User ID required"
        )
    
    # Ищем пользователя по tg_id
    user = db.query(User).filter(User.tg_id == tg_id).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Устанавливаем wallet_address в null
    user.wallet_address = None
    db.commit()
    db.refresh(user)
    
    print(f"[Wallet Disconnect] Wallet disconnected for user: tg_id={user.tg_id}")
    
    return user_to_response(user, db)

