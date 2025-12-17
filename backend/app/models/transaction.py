from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    TASK_PAYMENT = "task_payment"
    BONUS = "bonus"
    REFUND = "refund"


class PaymentMethod(str, enum.Enum):
    TON = "ton"
    DAILY_BONUS = "daily_bonus"
    SYSTEM = "system"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)  # Положительное = пополнение, отрицательное = списание
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    yookassa_payment_id = Column(String(255), nullable=True, index=True)  # Оставляем для совместимости, но не используем
    ton_transaction_hash = Column(String(64), nullable=True, index=True)  # Хеш транзакции в TON
    ton_from_address = Column(String(48), nullable=True)  # Адрес отправителя
    ton_to_address = Column(String(48), nullable=True)  # Адрес получателя
    ton_amount = Column(String(20), nullable=True)  # Сумма в nanotons
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")

