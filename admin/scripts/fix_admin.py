"""
Скрипт для исправления проблем с админкой
"""
import sys
import os
from pathlib import Path

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def check_database():
    """Проверка подключения к БД"""
    print("=" * 50)
    print("Проверка подключения к БД")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            # Проверяем таблицу completed_tasks
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completed_tasks'")
            result = cursor.fetchone()
            
            if result:
                print("[OK] Таблица completed_tasks найдена")
                
                # Проверяем структуру таблицы
                cursor.execute("PRAGMA table_info(completed_tasks)")
                columns = cursor.fetchall()
                print(f"\nСтруктура таблицы completed_tasks:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # Проверяем количество записей
                cursor.execute("SELECT COUNT(*) FROM completed_tasks")
                count = cursor.fetchone()[0]
                print(f"\nКоличество записей: {count}")
                
            else:
                print("[ERROR] Таблица completed_tasks НЕ найдена!")
                return False
            
            # Проверяем все таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"\nВсего таблиц в БД: {len(tables)}")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке БД: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database()

