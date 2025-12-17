"""
Скрипт для инициализации системных таблиц Django в общей БД
Запускает миграции Django для системных приложений (auth, sessions, contenttypes, admin)
"""
import os
import sys
import django
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.core.management.commands import migrate

def check_django_tables():
    """Проверяет наличие системных таблиц Django"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
    
    django_tables = [
        'django_migrations',
        'django_content_type',
        'auth_user',
        'auth_group',
        'auth_permission',
        'auth_group_permissions',
        'auth_user_groups',
        'auth_user_user_permissions',
        'django_session',
        'django_admin_log',
    ]
    
    missing_tables = [t for t in django_tables if t not in tables]
    return missing_tables, tables

def init_django_tables():
    """Инициализирует системные таблицы Django"""
    print("Проверка системных таблиц Django...")
    missing_tables, all_tables = check_django_tables()
    
    if missing_tables:
        print(f"Найдены отсутствующие таблицы: {', '.join(missing_tables)}")
        print("Применение миграций Django для системных приложений...")
        
        # Применяем миграции для системных приложений
        try:
            execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
            print("✓ Миграции применены успешно")
        except Exception as e:
            print(f"✗ Ошибка при применении миграций: {e}")
            return False
    else:
        print("✓ Все системные таблицы Django уже существуют")
    
    # Проверяем результат
    missing_tables_after, all_tables_after = check_django_tables()
    if missing_tables_after:
        print(f"⚠ После миграций все еще отсутствуют таблицы: {', '.join(missing_tables_after)}")
    else:
        print("✓ Все системные таблицы Django созданы")
    
    print(f"\nВсего таблиц в БД: {len(all_tables_after)}")
    print("Системные таблицы Django:")
    django_tables = [t for t in all_tables_after if t.startswith('django_') or t.startswith('auth_')]
    for table in sorted(django_tables):
        print(f"  - {table}")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("Инициализация системных таблиц Django в общей БД")
    print("=" * 60)
    
    success = init_django_tables()
    
    if success:
        print("\n✓ Инициализация завершена успешно")
        print("\nТеперь можно:")
        print("1. Создать суперпользователя: python manage.py createsuperuser")
        print("2. Запустить админку: python manage.py runserver")
    else:
        print("\n✗ Инициализация завершена с ошибками")
        sys.exit(1)

