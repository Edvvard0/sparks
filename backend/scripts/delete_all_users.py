"""
Скрипт для удаления всех пользователей из базы данных
Запуск: python scripts/delete_all_users.py
"""
import sys
import os
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.daily import CompletedTask, DailyFreeTask, DailyBonus
from app.models.transaction import Transaction
from app.models.user import UserCategory


def delete_all_users(confirm: bool = False):
    """Удаление всех пользователей и всех связанных данных"""
    # Определяем стандартный путь к БД (backend/sparks.db)
    backend_dir = Path(__file__).parent.parent
    db_path = backend_dir / "sparks.db"
    
    if not db_path.exists():
        print(f"\n❌ Файл базы данных не найден: {db_path.resolve()}")
        print(f"   Убедитесь, что база данных создана и инициализирована.")
        print(f"   Для создания БД запустите миграции:")
        print(f"   cd backend && alembic upgrade head")
        return False
    
    print(f"📁 Используется база данных: {db_path.resolve()}")
    
    # Создаем прямое подключение к БД с правильным путем
    database_url = f"sqlite:///{db_path.resolve()}"
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Подсчитываем всех пользователей
        total_users = db.query(User).count()
        
        if total_users == 0:
            print("ℹ️  В базе данных нет пользователей")
            return True
        
        print(f"📊 Найдено пользователей: {total_users}")
        
        # Подсчитываем связанные данные
        total_completed_tasks = db.query(CompletedTask).count()
        total_daily_free_tasks = db.query(DailyFreeTask).count()
        total_daily_bonuses = db.query(DailyBonus).count()
        total_transactions = db.query(Transaction).count()
        total_interests = db.query(UserCategory).count()
        
        print(f"\n📊 Связанные данные:")
        print(f"   Выполненных заданий: {total_completed_tasks}")
        print(f"   Записей о бесплатных заданиях: {total_daily_free_tasks}")
        print(f"   Ежедневных бонусов: {total_daily_bonuses}")
        print(f"   Транзакций: {total_transactions}")
        print(f"   Интересов: {total_interests}")
        
        # Подтверждение удаления
        print(f"\n⚠️  ВНИМАНИЕ: Будут удалены ВСЕ пользователи и ВСЕ связанные данные!")
        print(f"   Это действие нельзя отменить!")
        
        if not confirm:
            print(f"\n❓ Для подтверждения удаления всех пользователей")
            print(f"   запустите скрипт с флагом --confirm:")
            print(f"   python scripts/delete_all_users.py --confirm")
            return False
        
        # Удаляем все связанные данные
        print(f"\n🗑️  Удаление связанных данных...")
        
        deleted_completed_tasks = 0
        deleted_daily_free_tasks = 0
        deleted_daily_bonuses = 0
        deleted_transactions = 0
        deleted_interests = 0
        
        # Удаляем выполненные задания
        if total_completed_tasks > 0:
            deleted_completed_tasks = db.query(CompletedTask).delete()
            print(f"   ✓ Удалено выполненных заданий: {deleted_completed_tasks}")
        
        # Удаляем записи о бесплатных заданиях
        if total_daily_free_tasks > 0:
            deleted_daily_free_tasks = db.query(DailyFreeTask).delete()
            print(f"   ✓ Удалено записей о бесплатных заданиях: {deleted_daily_free_tasks}")
        
        # Удаляем ежедневные бонусы
        if total_daily_bonuses > 0:
            deleted_daily_bonuses = db.query(DailyBonus).delete()
            print(f"   ✓ Удалено ежедневных бонусов: {deleted_daily_bonuses}")
        
        # Удаляем транзакции
        if total_transactions > 0:
            deleted_transactions = db.query(Transaction).delete()
            print(f"   ✓ Удалено транзакций: {deleted_transactions}")
        
        # Удаляем интересы пользователей
        if total_interests > 0:
            deleted_interests = db.query(UserCategory).delete()
            print(f"   ✓ Удалено интересов: {deleted_interests}")
        
        # Теперь удаляем всех пользователей
        print(f"\n🗑️  Удаление всех пользователей...")
        deleted_users = db.query(User).delete()
        db.commit()
        
        print(f"\n✅ Успешно удалено:")
        print(f"   Пользователей: {deleted_users}")
        print(f"   Выполненных заданий: {deleted_completed_tasks}")
        print(f"   Записей о бесплатных заданиях: {deleted_daily_free_tasks}")
        print(f"   Ежедневных бонусов: {deleted_daily_bonuses}")
        print(f"   Транзакций: {deleted_transactions}")
        print(f"   Интересов: {deleted_interests}")
        
        return True
        
    except OperationalError as e:
        db.rollback()
        error_msg = str(e)
        if "unable to open database file" in error_msg.lower():
            print(f"\n❌ Ошибка: Не удалось открыть файл базы данных")
            print(f"   Путь: {db_path.resolve()}")
            print(f"   Проверьте права доступа к файлу и директории")
        elif "no such table" in error_msg.lower():
            print(f"\n❌ Ошибка: Таблицы в базе данных не найдены")
            print(f"   База данных не инициализирована.")
            print(f"   Для инициализации БД запустите миграции:")
            print(f"   cd backend && alembic upgrade head")
        else:
            print(f"\n❌ Ошибка подключения к базе данных: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка при удалении пользователей: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Основная функция"""
    import sys
    
    # Проверяем наличие флага --confirm
    confirm = '--confirm' in sys.argv or '-c' in sys.argv
    
    print("=" * 60)
    print("Удаление всех пользователей из базы данных")
    print("=" * 60)
    print()
    
    success = delete_all_users(confirm=confirm)
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Операция завершена успешно")
    else:
        print("✗ Операция не выполнена (требуется подтверждение)")
    print("=" * 60)


if __name__ == "__main__":
    main()

