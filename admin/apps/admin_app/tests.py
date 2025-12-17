"""
Тесты для админки Django
"""
from django.test import TestCase, Client
from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import datetime

from .models import (
    Language,
    User as AdminUser, UserCategory,
    TaskCategory, CategoryTranslation,
    Task, TaskTranslation, TaskGenderTarget,
    CompletedTask,
    DailyFreeTask, DailyBonus,
    Transaction
)
from .admin import (
    LanguageAdmin,
    UserAdmin,
    TaskCategoryAdmin,
    TaskAdmin,
    CategoryTranslationAdmin,
    TaskTranslationAdmin,
    TaskGenderTargetAdmin,
    CompletedTaskAdmin,
    DailyFreeTaskAdmin,
    DailyBonusAdmin,
    TransactionAdmin,
    UserCategoryAdmin
)

User = get_user_model()  # Django User для суперпользователя
# AdminUser - это наша модель пользователя из admin_app


class AdminTestCase(TestCase):
    """Базовый класс для тестов админки"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем суперпользователя
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Создаем клиент и логинимся
        self.client = Client()
        self.client.force_login(self.superuser)
        
        # Создаем базовые данные
        self.setup_base_data()
    
    def create_all_tables(self):
        """Создание всех необходимых таблиц для тестов"""
        with connection.cursor() as cursor:
            # Проверяем и создаем таблицу languages
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='languages'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE languages (
                        id INTEGER PRIMARY KEY,
                        code VARCHAR(10) UNIQUE NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL
                    )
                """)
            
            # Проверяем и создаем таблицу task_categories
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_categories'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE task_categories (
                        id INTEGER PRIMARY KEY,
                        slug VARCHAR(100) UNIQUE NOT NULL,
                        color VARCHAR(7) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL
                    )
                """)
            
            # Проверяем и создаем таблицу category_translations
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category_translations'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE category_translations (
                        id INTEGER PRIMARY KEY,
                        category_id INTEGER NOT NULL,
                        language_id INTEGER NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        FOREIGN KEY (category_id) REFERENCES task_categories(id),
                        FOREIGN KEY (language_id) REFERENCES languages(id),
                        UNIQUE(category_id, language_id)
                    )
                """)
            
            # Проверяем и создаем таблицу users
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE users (
                        tg_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        first_name VARCHAR(255) NOT NULL,
                        last_name VARCHAR(255),
                        gender VARCHAR(10) NOT NULL,
                        language_id INTEGER NOT NULL,
                        password VARCHAR(255),
                        is_admin BOOLEAN NOT NULL DEFAULT 0,
                        balance INTEGER NOT NULL DEFAULT 0,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        wallet_address VARCHAR(48) UNIQUE,
                        has_lifetime_subscription BOOLEAN NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (language_id) REFERENCES languages(id)
                    )
                """)
            
            # Проверяем и создаем таблицу user_categories
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_categories'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE user_categories (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        category_id INTEGER NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(tg_id),
                        FOREIGN KEY (category_id) REFERENCES task_categories(id),
                        UNIQUE(user_id, category_id)
                    )
                """)
            
            # Проверяем и создаем таблицу tasks
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE tasks (
                        id INTEGER PRIMARY KEY,
                        category_id INTEGER NOT NULL,
                        is_free BOOLEAN NOT NULL DEFAULT 0,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY (category_id) REFERENCES task_categories(id)
                    )
                """)
            
            # Проверяем и создаем таблицу task_translations
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_translations'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE task_translations (
                        id INTEGER PRIMARY KEY,
                        task_id INTEGER NOT NULL,
                        language_id INTEGER NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        description TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(id),
                        FOREIGN KEY (language_id) REFERENCES languages(id),
                        UNIQUE(task_id, language_id)
                    )
                """)
            
            # Проверяем и создаем таблицу task_gender_targets
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_gender_targets'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE task_gender_targets (
                        id INTEGER PRIMARY KEY,
                        task_id INTEGER NOT NULL,
                        gender VARCHAR(10) NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(id),
                        UNIQUE(task_id, gender)
                    )
                """)
            
            # Проверяем и создаем таблицу completed_tasks
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completed_tasks'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE completed_tasks (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        task_id INTEGER NOT NULL,
                        completed_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(tg_id),
                        FOREIGN KEY (task_id) REFERENCES tasks(id)
                    )
                """)
            
            # Проверяем и создаем таблицу daily_free_tasks
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_free_tasks'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE daily_free_tasks (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        date DATE NOT NULL,
                        count INTEGER NOT NULL DEFAULT 0,
                        paid_available INTEGER NOT NULL DEFAULT 0,
                        last_reset DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(tg_id),
                        UNIQUE(user_id, date)
                    )
                """)
            
            # Проверяем и создаем таблицу daily_bonuses
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_bonuses'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE daily_bonuses (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        day_number INTEGER NOT NULL,
                        bonus_amount INTEGER NOT NULL,
                        claimed_at DATETIME NOT NULL,
                        date DATE NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(tg_id),
                        UNIQUE(user_id, date)
                    )
                """)
            
            # Проверяем и создаем таблицу transactions
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
            if cursor.fetchone() is None:
                cursor.execute("""
                    CREATE TABLE transactions (
                        id INTEGER PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        transaction_type VARCHAR(20) NOT NULL,
                        amount INTEGER NOT NULL,
                        payment_method VARCHAR(20),
                        yookassa_payment_id VARCHAR(255),
                        ton_transaction_hash VARCHAR(64),
                        ton_from_address VARCHAR(48),
                        ton_to_address VARCHAR(48),
                        ton_amount VARCHAR(20),
                        status VARCHAR(20) NOT NULL DEFAULT 'pending',
                        description VARCHAR(500),
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(tg_id)
                    )
                """)
    
    def setup_base_data(self):
        """Создание базовых данных для тестов"""
        from django.utils import timezone
        now = timezone.now()
        
        # Создаем все необходимые таблицы
        self.create_all_tables()
        
        # Создаем языки
        with connection.cursor() as cursor:
            # Проверяем количество языков
            cursor.execute("SELECT COUNT(*) FROM languages")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Вставляем базовые языки
                cursor.execute("""
                    INSERT INTO languages (id, code, name, is_active, created_at)
                    VALUES (1, 'ru', 'Русский', 1, ?)
                """, [now])
                cursor.execute("""
                    INSERT INTO languages (id, code, name, is_active, created_at)
                    VALUES (2, 'en', 'English', 1, ?)
                """, [now])
                cursor.execute("""
                    INSERT INTO languages (id, code, name, is_active, created_at)
                    VALUES (3, 'es', 'Español', 1, ?)
                """, [now])
        
        # Получаем языки
        self.language_ru = Language.objects.get(code='ru')
        self.language_en = Language.objects.get(code='en')
        self.language_es = Language.objects.get(code='es')


class LanguageAdminTest(AdminTestCase):
    """Тесты для LanguageAdmin"""
    
    def test_language_list_view(self):
        """Тест отображения списка языков"""
        url = reverse('admin:admin_app_language_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Русский')
    
    def test_language_add_view(self):
        """Тест добавления нового языка"""
        url = reverse('admin:admin_app_language_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_language_create(self):
        """Тест создания языка через админку"""
        url = reverse('admin:admin_app_language_add')
        data = {
            'id': 4,
            'code': 'de',
            'name': 'Deutsch',
            'is_active': True
        }
        response = self.client.post(url, data)
        # Проверяем что язык создан
        self.assertTrue(Language.objects.filter(code='de').exists())
    
    def test_activate_languages_action(self):
        """Тест действия активации языков"""
        # Создаем неактивный язык
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO languages (id, code, name, is_active, created_at)
                VALUES (4, 'de', 'Deutsch', 0, datetime('now'))
            """)
        
        language = Language.objects.get(code='de')
        self.assertFalse(language.is_active)
        
        # Активируем через действие
        admin = LanguageAdmin(Language, site)
        queryset = Language.objects.filter(code='de')
        admin.activate_languages(None, queryset)
        
        language.refresh_from_db()
        self.assertTrue(language.is_active)
    
    def test_deactivate_languages_action(self):
        """Тест действия деактивации языков"""
        language = Language.objects.get(code='ru')
        self.assertTrue(language.is_active)
        
        # Деактивируем через действие
        admin = LanguageAdmin(Language, site)
        queryset = Language.objects.filter(code='ru')
        admin.deactivate_languages(None, queryset)
        
        language.refresh_from_db()
        self.assertFalse(language.is_active)


class UserAdminTest(AdminTestCase):
    """Тесты для UserAdmin"""
    
    def test_user_list_view(self):
        """Тест отображения списка пользователей"""
        # Создаем тестового пользователя
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (tg_id, username, first_name, last_name, gender, language_id, balance, is_admin, is_active, has_lifetime_subscription, created_at, updated_at)
                VALUES (123456789, 'testuser', 'Test', 'User', 'male', 1, 100, 0, 1, 0, datetime('now'), datetime('now'))
            """)
        
        url = reverse('admin:admin_app_user_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_user_add_view(self):
        """Тест добавления нового пользователя"""
        url = reverse('admin:admin_app_user_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_user_create(self):
        """Тест создания пользователя через админку"""
        url = reverse('admin:admin_app_user_add')
        data = {
            'tg_id': 987654321,
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'gender': 'female',
            'language': self.language_ru.id,
            'balance': 0,
            'is_admin': False,
            'is_active': True,
            'has_lifetime_subscription': False
        }
        response = self.client.post(url, data)
        # Проверяем что пользователь создан
        self.assertTrue(AdminUser.objects.filter(tg_id=987654321).exists())


class TaskCategoryAdminTest(AdminTestCase):
    """Тесты для TaskCategoryAdmin - критично для проверки проблемы с сохранением"""
    
    def test_category_list_view(self):
        """Тест отображения списка категорий"""
        url = reverse('admin:admin_app_taskcategory_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_category_add_view(self):
        """Тест добавления новой категории"""
        url = reverse('admin:admin_app_taskcategory_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_category_create_without_translations(self):
        """Тест создания категории без переводов"""
        url = reverse('admin:admin_app_taskcategory_add')
        data = {
            'slug': 'test-category',
            'color': '#FF0000',
            'is_active': True,
            'categorytranslation_set-TOTAL_FORMS': '0',
            'categorytranslation_set-INITIAL_FORMS': '0',
            'categorytranslation_set-MIN_NUM_FORMS': '0',
            'categorytranslation_set-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(url, data)
        # Проверяем что запрос успешен (редирект 302 или 200 если есть ошибки валидации)
        if response.status_code == 200:
            # Если форма не прошла валидацию, выводим ошибки
            if hasattr(response, 'context') and response.context:
                if 'adminform' in response.context:
                    form = response.context['adminform'].form
                    if form.errors:
                        print(f"\n=== FORM ERRORS ===")
                        print(f"Form errors: {form.errors}")
                        print(f"Form non_field_errors: {form.non_field_errors()}")
                if 'inline_admin_formsets' in response.context:
                    for formset_wrapper in response.context['inline_admin_formsets']:
                        formset = formset_wrapper.formset
                        if formset.errors:
                            print(f"\n=== FORMSET ERRORS ===")
                            for i, form in enumerate(formset.forms):
                                if form.errors:
                                    print(f"Form {i} errors: {form.errors}")
                            print(f"Formset non_form_errors: {formset.non_form_errors()}")
        self.assertIn(response.status_code, [200, 302], f"Response status: {response.status_code}, content: {response.content[:500]}")
        # Проверяем что категория создана
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM task_categories WHERE slug = 'test-category'")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1, f"Category not created. Response status: {response.status_code}, Response: {response.content[:500]}")
    
    def test_category_create_with_translations(self):
        """Тест создания категории с переводами - критичный тест"""
        url = reverse('admin:admin_app_taskcategory_add')
        data = {
            'slug': 'love-category',
            'color': '#FFC700',
            'is_active': True,
            'categorytranslation_set-TOTAL_FORMS': '2',
            'categorytranslation_set-INITIAL_FORMS': '0',
            'categorytranslation_set-MIN_NUM_FORMS': '0',
            'categorytranslation_set-MAX_NUM_FORMS': '1000',
            'categorytranslation_set-0-language': self.language_ru.id,
            'categorytranslation_set-0-name': 'Любовь',
            'categorytranslation_set-1-language': self.language_en.id,
            'categorytranslation_set-1-name': 'Love',
        }
        response = self.client.post(url, data)
        # Проверяем что запрос успешен
        self.assertIn(response.status_code, [200, 302], f"Response status: {response.status_code}, content: {response.content[:500]}")
        
        # Проверяем что категория создана
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM task_categories WHERE slug = 'love-category'")
            result = cursor.fetchone()
            self.assertIsNotNone(result, f"Категория должна быть создана. Response: {response.content[:500]}")
            category_id = result[0]
            
            # Проверяем что переводы созданы
            cursor.execute("""
                SELECT COUNT(*) FROM category_translations 
                WHERE category_id = ? AND language_id IN (?, ?)
            """, [category_id, self.language_ru.id, self.language_en.id])
            count = cursor.fetchone()[0]
            self.assertEqual(count, 2, "Должны быть созданы 2 перевода")
    
    def test_category_edit_with_translations(self):
        """Тест редактирования категории с переводами"""
        # Создаем категорию
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO task_categories (id, slug, color, is_active, created_at)
                VALUES (1, 'test-edit', '#FF0000', 1, datetime('now'))
            """)
            cursor.execute("""
                INSERT INTO category_translations (id, category_id, language_id, name)
                VALUES (1, 1, ?, 'Тест')
            """, [self.language_ru.id])
        
        category = TaskCategory.objects.get(slug='test-edit')
        url = reverse('admin:admin_app_taskcategory_change', args=[category.id])
        
        # Редактируем категорию
        data = {
            'slug': 'test-edit-updated',
            'color': '#00FF00',
            'is_active': True,
            'categorytranslation_set-TOTAL_FORMS': '2',
            'categorytranslation_set-INITIAL_FORMS': '1',
            'categorytranslation_set-MIN_NUM_FORMS': '0',
            'categorytranslation_set-MAX_NUM_FORMS': '1000',
            'categorytranslation_set-0-id': '1',
            'categorytranslation_set-0-language': self.language_ru.id,
            'categorytranslation_set-0-name': 'Тест Обновленный',
            'categorytranslation_set-1-language': self.language_en.id,
            'categorytranslation_set-1-name': 'Test Updated',
        }
        response = self.client.post(url, data)
        # Проверяем что запрос успешен
        self.assertIn(response.status_code, [200, 302], f"Response status: {response.status_code}, content: {response.content[:500]}")
        
        # Проверяем что категория обновлена
        category.refresh_from_db()
        self.assertEqual(category.slug, 'test-edit-updated', f"Category slug not updated. Current slug: {category.slug}, Response: {response.content[:500]}")
        self.assertEqual(category.color, '#00FF00')
        
        # Проверяем что переводы обновлены
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM category_translations 
                WHERE category_id = ? AND language_id IN (?, ?)
            """, [category.id, self.language_ru.id, self.language_en.id])
            count = cursor.fetchone()[0]
            self.assertEqual(count, 2, "Должны быть 2 перевода")
    
    def test_activate_categories_action(self):
        """Тест действия активации категорий"""
        # Создаем неактивную категорию
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO task_categories (id, slug, color, is_active, created_at)
                VALUES (2, 'inactive', '#FF0000', 0, datetime('now'))
            """)
        
        category = TaskCategory.objects.get(slug='inactive')
        self.assertFalse(category.is_active)
        
        # Активируем через действие
        admin = TaskCategoryAdmin(TaskCategory, site)
        queryset = TaskCategory.objects.filter(slug='inactive')
        admin.activate_categories(None, queryset)
        
        category.refresh_from_db()
        self.assertTrue(category.is_active)
    
    def test_deactivate_categories_action(self):
        """Тест действия деактивации категорий"""
        # Создаем активную категорию
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO task_categories (id, slug, color, is_active, created_at)
                VALUES (3, 'active', '#FF0000', 1, datetime('now'))
            """)
        
        category = TaskCategory.objects.get(slug='active')
        self.assertTrue(category.is_active)
        
        # Деактивируем через действие
        admin = TaskCategoryAdmin(TaskCategory, site)
        queryset = TaskCategory.objects.filter(slug='active')
        admin.deactivate_categories(None, queryset)
        
        category.refresh_from_db()
        self.assertFalse(category.is_active)


class TaskAdminTest(AdminTestCase):
    """Тесты для TaskAdmin"""
    
    def setUp(self):
        """Дополнительная настройка для тестов задач"""
        super().setUp()
        # Создаем категорию для задач
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO task_categories (id, slug, color, is_active, created_at)
                VALUES (10, 'test-category', '#FF0000', 1, datetime('now'))
            """)
        self.category = TaskCategory.objects.get(slug='test-category')
    
    def test_task_list_view(self):
        """Тест отображения списка задач"""
        url = reverse('admin:admin_app_task_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_task_add_view(self):
        """Тест добавления новой задачи"""
        url = reverse('admin:admin_app_task_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_task_create_without_translations(self):
        """Тест создания задачи без переводов"""
        url = reverse('admin:admin_app_task_add')
        data = {
            'category': self.category.id,
            'is_active': True,
            'tasktranslation_set-TOTAL_FORMS': '0',
            'tasktranslation_set-INITIAL_FORMS': '0',
            'tasktranslation_set-MIN_NUM_FORMS': '0',
            'tasktranslation_set-MAX_NUM_FORMS': '1000',
            'taskgendertarget_set-TOTAL_FORMS': '0',
            'taskgendertarget_set-INITIAL_FORMS': '0',
            'taskgendertarget_set-MIN_NUM_FORMS': '0',
            'taskgendertarget_set-MAX_NUM_FORMS': '1000',
        }
        response = self.client.post(url, data)
        # Проверяем что запрос успешен
        self.assertIn(response.status_code, [200, 302], f"Response status: {response.status_code}, content: {response.content[:500]}")
        # Проверяем что задача создана
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE category_id = ?", [self.category.id])
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0, f"Task not created. Response: {response.content[:500]}")
    
    def test_task_create_with_translations(self):
        """Тест создания задачи с переводами"""
        url = reverse('admin:admin_app_task_add')
        data = {
            'category': self.category.id,
            'is_active': True,
            'tasktranslation_set-TOTAL_FORMS': '2',
            'tasktranslation_set-INITIAL_FORMS': '0',
            'tasktranslation_set-MIN_NUM_FORMS': '0',
            'tasktranslation_set-MAX_NUM_FORMS': '1000',
            'tasktranslation_set-0-language': self.language_ru.id,
            'tasktranslation_set-0-title': 'Тестовая задача',
            'tasktranslation_set-0-description': 'Описание тестовой задачи',
            'tasktranslation_set-1-language': self.language_en.id,
            'tasktranslation_set-1-title': 'Test Task',
            'tasktranslation_set-1-description': 'Test task description',
            'taskgendertarget_set-TOTAL_FORMS': '1',
            'taskgendertarget_set-INITIAL_FORMS': '0',
            'taskgendertarget_set-MIN_NUM_FORMS': '0',
            'taskgendertarget_set-MAX_NUM_FORMS': '1000',
            'taskgendertarget_set-0-gender': 'male',
        }
        response = self.client.post(url, data)
        # Проверяем что запрос успешен
        self.assertIn(response.status_code, [200, 302], f"Response status: {response.status_code}, content: {response.content[:500]}")
        
        # Проверяем что задача создана
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM tasks WHERE category_id = ?", [self.category.id])
            result = cursor.fetchone()
            self.assertIsNotNone(result, f"Задача должна быть создана. Response: {response.content[:500]}")
            task_id = result[0]
            
            # Проверяем что переводы созданы
            cursor.execute("""
                SELECT COUNT(*) FROM task_translations 
                WHERE task_id = ? AND language_id IN (?, ?)
            """, [task_id, self.language_ru.id, self.language_en.id])
            count = cursor.fetchone()[0]
            self.assertEqual(count, 2, "Должны быть созданы 2 перевода")
            
            # Проверяем что гендерные цели созданы
            cursor.execute("""
                SELECT COUNT(*) FROM task_gender_targets 
                WHERE task_id = ? AND gender = 'male'
            """, [task_id])
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1, "Должна быть создана гендерная цель")
    
    def test_activate_tasks_action(self):
        """Тест действия активации задач"""
        # Создаем неактивную задачу
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tasks (id, category_id, is_active, created_at)
                VALUES (100, ?, 0, datetime('now'))
            """, [self.category.id])
        
        task = Task.objects.get(id=100)
        self.assertFalse(task.is_active)
        
        # Активируем через действие
        admin = TaskAdmin(Task, site)
        queryset = Task.objects.filter(id=100)
        admin.activate_tasks(None, queryset)
        
        task.refresh_from_db()
        self.assertTrue(task.is_active)
    
    def test_deactivate_tasks_action(self):
        """Тест действия деактивации задач"""
        # Создаем активную задачу
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tasks (id, category_id, is_active, created_at)
                VALUES (101, ?, 1, datetime('now'))
            """, [self.category.id])
        
        task = Task.objects.get(id=101)
        self.assertTrue(task.is_active)
        
        # Деактивируем через действие
        admin = TaskAdmin(Task, site)
        queryset = Task.objects.filter(id=101)
        admin.deactivate_tasks(None, queryset)
        
        task.refresh_from_db()
        self.assertFalse(task.is_active)


class CompletedTaskAdminTest(AdminTestCase):
    """Тесты для CompletedTaskAdmin"""
    
    def setUp(self):
        """Дополнительная настройка"""
        super().setUp()
        # Создаем пользователя
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (tg_id, username, first_name, last_name, gender, language_id, balance, is_admin, is_active, has_lifetime_subscription, created_at, updated_at)
                VALUES (111111111, 'testuser', 'Test', 'User', 'male', 1, 100, 0, 1, 0, datetime('now'), datetime('now'))
            """)
        self.user = AdminUser.objects.get(tg_id=111111111)
        
        # Создаем категорию и задачу
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO task_categories (id, slug, color, is_active, created_at)
                VALUES (20, 'test-cat', '#FF0000', 1, datetime('now'))
            """)
            cursor.execute("""
                INSERT INTO tasks (id, category_id, is_active, created_at)
                VALUES (200, 20, 1, datetime('now'))
            """)
        self.task = Task.objects.get(id=200)
    
    def test_completed_task_list_view(self):
        """Тест отображения списка выполненных задач"""
        # Создаем выполненную задачу
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO completed_tasks (id, user_id, task_id, completed_at)
                VALUES (1, ?, ?, datetime('now'))
            """, [self.user.tg_id, self.task.id])
        
        url = reverse('admin:admin_app_completedtask_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class DailyFreeTaskAdminTest(AdminTestCase):
    """Тесты для DailyFreeTaskAdmin"""
    
    def setUp(self):
        """Дополнительная настройка"""
        super().setUp()
        # Создаем пользователя
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (tg_id, username, first_name, last_name, gender, language_id, balance, is_admin, is_active, has_lifetime_subscription, created_at, updated_at)
                VALUES (222222222, 'testuser2', 'Test', 'User', 'male', 1, 100, 0, 1, 0, datetime('now'), datetime('now'))
            """)
        self.user = AdminUser.objects.get(tg_id=222222222)
    
    def test_daily_free_task_list_view(self):
        """Тест отображения списка ежедневных бесплатных задач"""
        # Создаем запись
        today = timezone.now().date()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO daily_free_tasks (id, user_id, date, count, paid_available, last_reset)
                VALUES (1, ?, ?, 3, 0, datetime('now'))
            """, [self.user.tg_id, today])
        
        url = reverse('admin:admin_app_dailyfreetask_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class DailyBonusAdminTest(AdminTestCase):
    """Тесты для DailyBonusAdmin"""
    
    def setUp(self):
        """Дополнительная настройка"""
        super().setUp()
        # Создаем пользователя
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (tg_id, username, first_name, last_name, gender, language_id, balance, is_admin, is_active, has_lifetime_subscription, created_at, updated_at)
                VALUES (333333333, 'testuser3', 'Test', 'User', 'male', 1, 100, 0, 1, 0, datetime('now'), datetime('now'))
            """)
        self.user = AdminUser.objects.get(tg_id=333333333)
    
    def test_daily_bonus_list_view(self):
        """Тест отображения списка ежедневных бонусов"""
        # Создаем запись
        today = timezone.now().date()
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO daily_bonuses (id, user_id, day_number, bonus_amount, claimed_at, date)
                VALUES (1, ?, 1, 100, datetime('now'), ?)
            """, [self.user.tg_id, today])
        
        url = reverse('admin:admin_app_dailybonus_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TransactionAdminTest(AdminTestCase):
    """Тесты для TransactionAdmin"""
    
    def setUp(self):
        """Дополнительная настройка"""
        super().setUp()
        # Создаем пользователя
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (tg_id, username, first_name, last_name, gender, language_id, balance, is_admin, is_active, has_lifetime_subscription, created_at, updated_at)
                VALUES (444444444, 'testuser4', 'Test', 'User', 'male', 1, 100, 0, 1, 0, datetime('now'), datetime('now'))
            """)
        self.user = AdminUser.objects.get(tg_id=444444444)
    
    def test_transaction_list_view(self):
        """Тест отображения списка транзакций"""
        # Создаем транзакцию
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO transactions (id, user_id, amount, transaction_type, status, created_at)
                VALUES (1, ?, 100, 'purchase', 'completed', datetime('now'))
            """, [self.user.tg_id])
        
        url = reverse('admin:admin_app_transaction_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class AdminIntegrationTest(AdminTestCase):
    """Интеграционные тесты для проверки взаимодействия компонентов админки"""
    
    def test_full_category_workflow(self):
        """Полный цикл работы с категорией: создание, редактирование, удаление"""
        # 1. Создаем категорию с переводами
        url = reverse('admin:admin_app_taskcategory_add')
        data = {
            'slug': 'workflow-test',
            'color': '#FFC700',
            'is_active': True,
            'categorytranslation_set-TOTAL_FORMS': '3',
            'categorytranslation_set-INITIAL_FORMS': '0',
            'categorytranslation_set-MIN_NUM_FORMS': '0',
            'categorytranslation_set-MAX_NUM_FORMS': '1000',
            'categorytranslation_set-0-language': self.language_ru.id,
            'categorytranslation_set-0-name': 'Тест',
            'categorytranslation_set-1-language': self.language_en.id,
            'categorytranslation_set-1-name': 'Test',
            'categorytranslation_set-2-language': self.language_es.id,
            'categorytranslation_set-2-name': 'Prueba',
        }
        response = self.client.post(url, data)
        # Проверяем что запрос успешен
        if response.status_code == 200:
            # Если форма не прошла валидацию, выводим ошибки
            if hasattr(response, 'context') and response.context:
                if 'adminform' in response.context:
                    form = response.context['adminform'].form
                    if form.errors:
                        print(f"\n=== FORM ERRORS ===")
                        print(f"Form errors: {form.errors}")
                        print(f"Form non_field_errors: {form.non_field_errors()}")
                if 'inline_admin_formsets' in response.context:
                    for formset_wrapper in response.context['inline_admin_formsets']:
                        formset = formset_wrapper.formset
                        if formset.errors:
                            print(f"\n=== FORMSET ERRORS ===")
                            for i, form in enumerate(formset.forms):
                                if form.errors:
                                    print(f"Form {i} errors: {form.errors}")
                            print(f"Formset non_form_errors: {formset.non_form_errors()}")
        self.assertIn(response.status_code, [200, 302], f"Response status: {response.status_code}, content: {response.content[:500]}")
        
        # Проверяем создание - если статус 200, значит форма не прошла валидацию
        if response.status_code == 200:
            # Проверяем, существует ли категория в БД
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM task_categories WHERE slug = 'workflow-test'")
                count = cursor.fetchone()[0]
                if count == 0:
                    self.fail(f"Category not created. Response status: {response.status_code}. Check form errors above.")
        
        category = TaskCategory.objects.get(slug='workflow-test')
        self.assertIsNotNone(category)
        
        # 2. Редактируем категорию
        edit_url = reverse('admin:admin_app_taskcategory_change', args=[category.id])
        edit_data = {
            'slug': 'workflow-test-updated',
            'color': '#00FF00',
            'is_active': True,
            'categorytranslation_set-TOTAL_FORMS': '3',
            'categorytranslation_set-INITIAL_FORMS': '3',
            'categorytranslation_set-MIN_NUM_FORMS': '0',
            'categorytranslation_set-MAX_NUM_FORMS': '1000',
            'categorytranslation_set-0-id': str(category.translations.filter(language=self.language_ru).first().id),
            'categorytranslation_set-0-language': self.language_ru.id,
            'categorytranslation_set-0-name': 'Тест Обновленный',
            'categorytranslation_set-1-id': str(category.translations.filter(language=self.language_en).first().id),
            'categorytranslation_set-1-language': self.language_en.id,
            'categorytranslation_set-1-name': 'Test Updated',
            'categorytranslation_set-2-id': str(category.translations.filter(language=self.language_es).first().id),
            'categorytranslation_set-2-language': self.language_es.id,
            'categorytranslation_set-2-name': 'Prueba Actualizada',
        }
        response = self.client.post(edit_url, edit_data)
        
        # Проверяем обновление
        category.refresh_from_db()
        self.assertEqual(category.slug, 'workflow-test-updated')
        self.assertEqual(category.color, '#00FF00')
    
    def test_full_task_workflow(self):
        """Полный цикл работы с задачей: создание, редактирование"""
        # Создаем категорию
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO task_categories (id, slug, color, is_active, created_at)
                VALUES (30, 'task-workflow', '#FF0000', 1, datetime('now'))
            """)
        category = TaskCategory.objects.get(slug='task-workflow')
        
        # Создаем задачу с переводами и гендерными целями
        url = reverse('admin:admin_app_task_add')
        data = {
            'category': category.id,
            'is_active': True,
            'tasktranslation_set-TOTAL_FORMS': '2',
            'tasktranslation_set-INITIAL_FORMS': '0',
            'tasktranslation_set-MIN_NUM_FORMS': '0',
            'tasktranslation_set-MAX_NUM_FORMS': '1000',
            'tasktranslation_set-0-language': self.language_ru.id,
            'tasktranslation_set-0-title': 'Тестовая задача',
            'tasktranslation_set-0-description': 'Описание',
            'tasktranslation_set-1-language': self.language_en.id,
            'tasktranslation_set-1-title': 'Test Task',
            'tasktranslation_set-1-description': 'Description',
            'taskgendertarget_set-TOTAL_FORMS': '2',
            'taskgendertarget_set-INITIAL_FORMS': '0',
            'taskgendertarget_set-MIN_NUM_FORMS': '0',
            'taskgendertarget_set-MAX_NUM_FORMS': '1000',
            'taskgendertarget_set-0-gender': 'male',
            'taskgendertarget_set-1-gender': 'female',
        }
        response = self.client.post(url, data)
        # Проверяем что запрос успешен
        self.assertIn(response.status_code, [200, 302], f"Response status: {response.status_code}, content: {response.content[:500]}")
        
        # Проверяем создание
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM tasks WHERE category_id = ?", [category.id])
            result = cursor.fetchone()
            self.assertIsNotNone(result, f"Task not created. Response: {response.content[:500]}")
            task_id = result[0]
            
            # Проверяем переводы
            cursor.execute("""
                SELECT COUNT(*) FROM task_translations WHERE task_id = ?
            """, [task_id])
            translation_count = cursor.fetchone()[0]
            self.assertEqual(translation_count, 2)
            
            # Проверяем гендерные цели
            cursor.execute("""
                SELECT COUNT(*) FROM task_gender_targets WHERE task_id = ?
            """, [task_id])
            gender_count = cursor.fetchone()[0]
            self.assertEqual(gender_count, 2)
