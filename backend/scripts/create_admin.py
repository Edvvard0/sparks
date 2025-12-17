"""
Скрипт для создания администратора в базе данных

Использование:
    python scripts/create_admin.py
    python scripts/create_admin.py --username admin --password admin123
    python scripts/create_admin.py --username admin --password admin123 --tg-id 999999999
"""

import sys
import os
import argparse
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, Gender
from app.models.language import Language
from app.services.user_service import UserService


def create_admin(
    username: str = "admin",
    password: str = "admin123",
    tg_id: int = 999999999,
    first_name: str = "Администратор",
    last_name: str = "Системы"
):
    """
    Создание администратора в базе данных
    
    Args:
        username: Имя пользователя для входа
        password: Пароль (будет захеширован)
        tg_id: Telegram ID (должен быть уникальным)
        first_name: Имя администратора
        last_name: Фамилия администратора
    """
    db = SessionLocal()
    try:
        print("=" * 50)
        print("Создание администратора")
        print("=" * 50)
        
        # Получаем русский язык (или английский если русского нет)
        language = db.query(Language).filter(Language.code == 'ru').first()
        if not language:
            language = db.query(Language).filter(Language.code == 'en').first()
        
        if not language:
            print("❌ Ошибка: Языки не найдены в базе данных")
            print("   Запустите сначала: python scripts/seed_data.py")
            return False
        
        print(f"✓ Используется язык: {language.name} ({language.code})")
        
        # Проверяем, существует ли уже админ с таким username
        existing_admin = db.query(User).filter(
            User.username == username,
            User.is_admin == True
        ).first()
        
        if existing_admin:
            print(f"⚠️  Администратор с username '{username}' уже существует")
            print(f"   tg_id: {existing_admin.tg_id}")
            print(f"   is_admin: {existing_admin.is_admin}")
            print(f"   is_active: {existing_admin.is_active}")
            
            # Спрашиваем, обновить ли пароль
            response = input("\nОбновить пароль? (y/n): ").strip().lower()
            if response == 'y':
                password_hash = UserService.get_password_hash(password)
                existing_admin.password = password_hash
                db.commit()
                print(f"✅ Пароль обновлен для администратора '{username}'")
                return True
            else:
                print("❌ Отменено")
                return False
        
        # Проверяем, существует ли пользователь с таким tg_id
        existing_user = db.query(User).filter(User.tg_id == tg_id).first()
        if existing_user:
            print(f"⚠️  Пользователь с tg_id={tg_id} уже существует")
            print(f"   username: {existing_user.username}")
            print(f"   is_admin: {existing_user.is_admin}")
            
            response = input("\nПреобразовать в администратора? (y/n): ").strip().lower()
            if response == 'y':
                # Преобразуем существующего пользователя в админа
                password_hash = UserService.get_password_hash(password)
                existing_user.username = username
                existing_user.password = password_hash
                existing_user.is_admin = True
                existing_user.is_active = True
                db.commit()
                print(f"✅ Пользователь преобразован в администратора")
                print(f"   Username: {username}")
                print(f"   Password: {password}")
                return True
            else:
                print("❌ Отменено")
                return False
        
        # Хешируем пароль
        print(f"✓ Хеширование пароля...")
        password_hash = UserService.get_password_hash(password)
        
        # Создаем администратора
        print(f"✓ Создание администратора...")
        admin = User(
            tg_id=tg_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            gender=Gender.MALE,
            language_id=language.id,
            password=password_hash,
            is_admin=True,
            balance=0,
            is_active=True,
            wallet_address=None
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n" + "=" * 50)
        print("✅ Администратор успешно создан!")
        print("=" * 50)
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   tg_id: {admin.tg_id}")
        print(f"   is_admin: {admin.is_admin}")
        print(f"   is_active: {admin.is_active}")
        print(f"   Language: {language.name}")
        print("\n💡 Теперь вы можете авторизоваться через API:")
        print(f"   POST http://localhost:8000/api/v1/admin/login")
        print(f"   Body: {{'username': '{username}', 'password': '{password}'}}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка при создании администратора: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Создание администратора в базе данных')
    parser.add_argument('--username', type=str, default='admin', help='Имя пользователя (по умолчанию: admin)')
    parser.add_argument('--password', type=str, default='admin123', help='Пароль (по умолчанию: admin123)')
    parser.add_argument('--tg-id', type=int, default=999999999, help='Telegram ID (по умолчанию: 999999999)')
    parser.add_argument('--first-name', type=str, default='Администратор', help='Имя (по умолчанию: Администратор)')
    parser.add_argument('--last-name', type=str, default='Системы', help='Фамилия (по умолчанию: Системы)')
    
    args = parser.parse_args()
    
    create_admin(
        username=args.username,
        password=args.password,
        tg_id=args.tg_id,
        first_name=args.first_name,
        last_name=args.last_name
    )


if __name__ == "__main__":
    main()

