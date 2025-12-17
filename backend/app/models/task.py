from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class GenderTarget(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    COUPLE = "couple"
    ALL = "all"


class TaskCategory(Base):
    __tablename__ = "task_categories"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=False)  # HEX color
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    translations = relationship("CategoryTranslation", back_populates="category", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="category")
    users = relationship("UserCategory", back_populates="category")


class CategoryTranslation(Base):
    __tablename__ = "category_translations"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("task_categories.id", ondelete="CASCADE"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)

    # Relationships
    category = relationship("TaskCategory", back_populates="translations")
    language = relationship("Language", back_populates="category_translations")

    __table_args__ = (
        UniqueConstraint('category_id', 'language_id', name='uq_category_translation'),
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("task_categories.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    category = relationship("TaskCategory", back_populates="tasks")
    translations = relationship("TaskTranslation", back_populates="task", cascade="all, delete-orphan")
    gender_targets = relationship("TaskGenderTarget", back_populates="task", cascade="all, delete-orphan")
    completed_by = relationship("CompletedTask", back_populates="task")


class TaskTranslation(Base):
    __tablename__ = "task_translations"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(String(2000), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="translations")
    language = relationship("Language", back_populates="task_translations")

    __table_args__ = (
        UniqueConstraint('task_id', 'language_id', name='uq_task_translation'),
    )


class TaskGenderTarget(Base):
    __tablename__ = "task_gender_targets"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    gender = Column(SQLEnum(GenderTarget), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="gender_targets")

    __table_args__ = (
        UniqueConstraint('task_id', 'gender', name='uq_task_gender_target'),
    )

