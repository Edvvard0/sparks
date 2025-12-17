from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from app.core.config import settings

# Создание URL для подключения к SQLite БД
# Используем абсолютный путь для надежности
db_path = Path(settings.DATABASE_PATH)

# Определяем директорию backend (где находится этот файл)
backend_dir = Path(__file__).parent.parent.parent

# Если путь абсолютный и начинается с /app/data (Docker путь), используем локальный путь
if db_path.is_absolute() and str(db_path).startswith("/app/data"):
    # Это Docker путь, используем путь в backend/ директории
    db_path = backend_dir / "sparks.db"
elif not db_path.is_absolute():
    # Используем БД в backend/ директории (общую для админки и бэкенда)
    db_path = backend_dir / db_path
    
    # Создаем директорию для БД, если её нет
    db_path.parent.mkdir(parents=True, exist_ok=True)
elif db_path.is_absolute() and not db_path.exists():
    # Если абсолютный путь не существует, пробуем стандартное расположение в backend/
    standard_path = backend_dir / "sparks.db"
    if standard_path.exists():
        db_path = standard_path
    else:
        # Если и стандартного пути нет, используем backend/ директорию
        db_path = backend_dir / "sparks.db"

DATABASE_URL = f"sqlite:///{db_path.resolve()}"

# Создаем engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={
        "check_same_thread": False,  # Нужно для SQLite в многопоточности
    },
    pool_pre_ping=True,
)

# Включаем foreign keys для SQLite через event listener
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Включаем поддержку foreign keys в SQLite"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

