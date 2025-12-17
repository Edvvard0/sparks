"""
Скрипт для полной очистки базы данных
Удаляет файл БД и пересоздает его с миграциями
Запуск: python backend/scripts/reset_database.py --confirm
"""
import sys
import os
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from app.core.database import Base
from app.models import *  # Импортируем все модели


def reset_database(confirm: bool = False):
    """Полная очистка и пересоздание базы данных"""
    # Определяем стандартный путь к БД (backend/sparks.db)
    backend_dir = Path(__file__).parent.parent
    db_path = backend_dir / "sparks.db"
    
    if not confirm:
        print("=" * 60)
        print("⚠️  ВНИМАНИЕ: Это удалит ВСЮ базу данных!")
        print("=" * 60)
        print(f"\n📁 Файл БД: {db_path.resolve()}")
        print(f"\n❓ Для подтверждения запустите скрипт с флагом --confirm:")
        print(f"   python backend/scripts/reset_database.py --confirm")
        return False
    
    print("=" * 60)
    print("Полная очистка базы данных")
    print("=" * 60)
    print(f"\n📁 Файл БД: {db_path.resolve()}")
    
    # Удаляем файл БД, если существует
    if db_path.exists():
        print(f"\n🗑️  Удаление файла БД...")
        db_path.unlink()
        print(f"   ✓ Файл удален")
    else:
        print(f"\nℹ️  Файл БД не найден, создаем новый")
    
    # Создаем новую БД
    print(f"\n🔄 Создание новой БД...")
    database_url = f"sqlite:///{db_path.resolve()}"
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    print(f"   ✓ Таблицы созданы")
    
    print(f"\n✅ База данных успешно очищена и пересоздана!")
    print(f"   Теперь нужно запустить миграции и заполнить начальные данные:")
    print(f"   cd backend && alembic upgrade head")
    print(f"   python scripts/seed_data.py")
    
    return True


def main():
    """Основная функция"""
    import sys
    
    # Проверяем наличие флага --confirm
    confirm = '--confirm' in sys.argv or '-c' in sys.argv
    
    success = reset_database(confirm=confirm)
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Операция завершена успешно")
    else:
        print("✗ Операция не выполнена (требуется подтверждение)")
    print("=" * 60)


if __name__ == "__main__":
    main()

