from sqlalchemy import Column, Integer, BigInteger, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CompletedTask(Base):
    __tablename__ = "completed_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="completed_tasks")
    task = relationship("Task", back_populates="completed_by")

    __table_args__ = (
        UniqueConstraint('user_id', 'task_id', name='uq_completed_task'),
    )


class DailyFreeTask(Base):
    __tablename__ = "daily_free_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    count = Column(Integer, default=0, nullable=False)  # Максимум 3 бесплатных задания
    paid_available = Column(Integer, default=0, nullable=False)  # Купленные дополнительные задания на день
    last_reset = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="daily_free_tasks")

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_daily_free_task'),
    )


class DailyBonus(Base):
    __tablename__ = "daily_bonuses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    day_number = Column(Integer, nullable=False)  # 1-7
    bonus_amount = Column(Integer, nullable=False)  # Сумма бонуса
    claimed_at = Column(DateTime(timezone=True), server_default=func.now())
    date = Column(Date, nullable=False)  # Дата получения бонуса

    # Relationships
    user = relationship("User", back_populates="daily_bonuses")

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_daily_bonus'),
    )

