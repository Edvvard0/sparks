from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.transaction import TransactionType, PaymentMethod, TransactionStatus


class TransactionBase(BaseModel):
    amount: int
    transaction_type: TransactionType
    status: TransactionStatus


class TonPaymentCreateRequest(BaseModel):
    package_id: int


class TonPaymentCreateResponse(BaseModel):
    transaction_id: int
    ton_amount: str  # Сумма в nanotons
    ton_address: str  # Адрес получателя
    comment: Optional[str] = None  # Комментарий для транзакции


class TonPaymentStatusResponse(BaseModel):
    status: str  # pending, completed, failed, not_found
    transaction_hash: Optional[str] = None
    confirmed: bool
    message: Optional[str] = None


class BalanceResponse(BaseModel):
    balance: int


class PackageResponse(BaseModel):
    id: int
    amount: int | str  # может быть 'lifetime'
    price: int
    min_ton_amount: Optional[str] = None  # Минимальная сумма в TON (nanotons)
    original_price: Optional[int] = None
    discount: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None


class PackageListResponse(BaseModel):
    packages: List[PackageResponse]

