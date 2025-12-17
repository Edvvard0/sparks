from sqlalchemy import Column, BigInteger, String, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    COUPLE = "couple"


class User(Base):
    __tablename__ = "users"

    tg_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(255), nullable=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    gender = Column(SQLEnum(Gender), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    password = Column(String(255), nullable=True)  # Хешированный пароль для админов
    is_admin = Column(Boolean, default=False, nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    wallet_address = Column(String(48), nullable=True, unique=True, index=True)  # TON адрес кошелька
    has_lifetime_subscription = Column(Boolean, default=False, nullable=False)  # Флаг lifetime подписки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    language = relationship("Language", back_populates="users")
    interests = relationship("UserCategory", back_populates="user", cascade="all, delete-orphan")
    completed_tasks = relationship("CompletedTask", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    daily_free_tasks = relationship("DailyFreeTask", back_populates="user")
    daily_bonuses = relationship("DailyBonus", back_populates="user")


class UserCategory(Base):
    __tablename__ = "user_categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("task_categories.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="interests")
    category = relationship("TaskCategory", back_populates="users")

    __table_args__ = (
        UniqueConstraint('user_id', 'category_id', name='uq_user_category'),
    )

