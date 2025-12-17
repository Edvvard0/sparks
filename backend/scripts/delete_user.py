"""
Скрипт для удаления пользователя из базы данных
Запуск: python scripts/delete_user.py
"""
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.daily import CompletedTask, DailyFreeTask, DailyBonus
from app.models.transaction import Transaction
from app.models.user import UserCategory


def delete_user(tg_id: int):
    """Удаление пользователя и всех связанных данных"""
    db: Session = SessionLocal()
    
    try:
        # Находим пользователя
        user = db.query(User).filter(User.tg_id == tg_id).first()
        
        if not user:
            print(f"❌ Пользователь с tg_id {tg_id} не найден в базе данных")
            return False
        
        print(f"📋 Найден пользователь:")
        print(f"   tg_id: {user.tg_id}")
        print(f"   Имя: {user.first_name} {user.last_name or ''}")
        print(f"   Username: @{user.username}" if user.username else "   Username: не указан")
        print(f"   Баланс: {user.balance}")
        print(f"   Дата создания: {user.created_at}")
        
        # Подсчитываем связанные данные
        completed_tasks_count = db.query(CompletedTask).filter(CompletedTask.user_id == tg_id).count()
        daily_free_tasks_count = db.query(DailyFreeTask).filter(DailyFreeTask.user_id == tg_id).count()
        daily_bonuses_count = db.query(DailyBonus).filter(DailyBonus.user_id == tg_id).count()
        transactions_count = db.query(Transaction).filter(Transaction.user_id == tg_id).count()
        interests_count = db.query(UserCategory).filter(UserCategory.user_id == tg_id).count()
        
        print(f"\n📊 Связанные данные:")
        print(f"   Выполненных заданий: {completed_tasks_count}")
        print(f"   Записей о бесплатных заданиях: {daily_free_tasks_count}")
        print(f"   Ежедневных бонусов: {daily_bonuses_count}")
        print(f"   Транзакций: {transactions_count}")
        print(f"   Интересов: {interests_count}")
        
        # Подтверждение удаления
        print(f"\n⚠️  ВНИМАНИЕ: Будут удалены все данные пользователя!")
        print(f"   Это действие нельзя отменить!")
        
        # Удаляем все связанные данные вручную перед удалением пользователя
        print(f"\n🗑️  Удаление связанных данных...")
        
        # Удаляем выполненные задания
        if completed_tasks_count > 0:
            db.query(CompletedTask).filter(CompletedTask.user_id == tg_id).delete()
            print(f"   ✓ Удалено выполненных заданий: {completed_tasks_count}")
        
        # Удаляем записи о бесплатных заданиях
        if daily_free_tasks_count > 0:
            db.query(DailyFreeTask).filter(DailyFreeTask.user_id == tg_id).delete()
            print(f"   ✓ Удалено записей о бесплатных заданиях: {daily_free_tasks_count}")
        
        # Удаляем ежедневные бонусы
        if daily_bonuses_count > 0:
            db.query(DailyBonus).filter(DailyBonus.user_id == tg_id).delete()
            print(f"   ✓ Удалено ежедневных бонусов: {daily_bonuses_count}")
        
        # Удаляем транзакции
        if transactions_count > 0:
            db.query(Transaction).filter(Transaction.user_id == tg_id).delete()
            print(f"   ✓ Удалено транзакций: {transactions_count}")
        
        # Удаляем интересы пользователя
        if interests_count > 0:
            db.query(UserCategory).filter(UserCategory.user_id == tg_id).delete()
            print(f"   ✓ Удалено интересов: {interests_count}")
        
        # Теперь удаляем пользователя
        print(f"\n🗑️  Удаление пользователя...")
        db.delete(user)
        db.commit()
        
        print(f"\n✅ Пользователь с tg_id {tg_id} успешно удален из базы данных")
        print(f"   Все связанные данные также удалены")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка при удалении пользователя: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Основная функция"""
    tg_id = 5254325840
    
    print("=" * 60)
    print("Удаление пользователя из базы данных")
    print("=" * 60)
    print(f"\n🎯 Целевой tg_id: {tg_id}\n")
    
    success = delete_user(tg_id)
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Операция завершена успешно")
    else:
        print("✗ Операция завершена с ошибками")
    print("=" * 60)


if __name__ == "__main__":
    main()

