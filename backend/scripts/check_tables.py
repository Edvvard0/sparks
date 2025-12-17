"""
Скрипт для проверки и создания всех таблиц в БД
"""
import sys
import os
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import engine, Base
from app.models import *  # Импортируем все модели
import sqlite3

def check_tables():
    """Проверка существования таблиц"""
    db_path = Path(__file__).parent.parent.parent / 'sparks.db'
    
    if not db_path.exists():
        print(f"[ERROR] База данных не найдена: {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Получаем список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    # Список ожидаемых таблиц
    expected_tables = {
        'users', 'languages', 'task_categories', 'category_translations',
        'tasks', 'task_translations', 'task_gender_targets',
        'completed_tasks', 'daily_free_tasks', 'daily_bonuses',
        'transactions', 'user_categories'
    }
    
    print("=" * 50)
    print("Проверка таблиц в БД")
    print("=" * 50)
    print(f"\nБаза данных: {db_path}")
    print(f"\nСуществующие таблицы ({len(existing_tables)}):")
    for table in sorted(existing_tables):
        print(f"  [OK] {table}")
    
    missing_tables = expected_tables - existing_tables
    if missing_tables:
        print(f"\n[ERROR] Отсутствующие таблицы ({len(missing_tables)}):")
        for table in sorted(missing_tables):
            print(f"  - {table}")
    else:
        print("\n[OK] Все ожидаемые таблицы существуют!")
    
    conn.close()
    return len(missing_tables) == 0

def create_tables():
    """Создание всех таблиц"""
    print("\n" + "=" * 50)
    print("Создание таблиц")
    print("=" * 50)
    
    try:
        Base.metadata.create_all(engine)
        print("[OK] Все таблицы проверены/созданы")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Проверка и создание таблиц в БД\n")
    
    # Проверяем таблицы
    all_exist = check_tables()
    
    # Если есть отсутствующие, создаем их
    if not all_exist:
        print("\nСоздание отсутствующих таблиц...")
        if create_tables():
            print("\nПовторная проверка...")
            check_tables()
    else:
        print("\nВсе таблицы на месте, создание не требуется.")

