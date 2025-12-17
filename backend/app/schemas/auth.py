"""
Схемы для авторизации через TON Connect
"""
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user import UserResponse


class TonConnectRequest(BaseModel):
    """Запрос на подключение через TON Connect"""
    wallet_address: str = Field(..., description="Адрес TON кошелька")
    signature: str = Field(..., description="Подпись сообщения")
    message: str = Field(..., description="Сообщение которое было подписано")
    timestamp: Optional[int] = Field(None, description="Временная метка")


class TonConnectResponse(BaseModel):
    """Ответ на подключение через TON Connect"""
    success: bool
    user: Optional[UserResponse] = None
    message: Optional[str] = None


class TonProofGenerateResponse(BaseModel):
    """Ответ на генерацию payload для TON Proof"""
    payload: str


class TonProofCheckRequest(BaseModel):
    """Запрос на проверку TON Proof"""
    address: str = Field(..., description="Адрес кошелька")
    network: str = Field(..., description="Сеть (mainnet/testnet)")
    proof: dict = Field(..., description="Объект proof от кошелька")


class TonProofCheckResponse(BaseModel):
    """Ответ на проверку TON Proof"""
    success: bool
    user: Optional[UserResponse] = None
    token: Optional[str] = None
    message: Optional[str] = None
