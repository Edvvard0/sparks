from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from apps.admin_app.models import (
    User, TaskCategory, TaskSubcategory, Task, TaskGenderTarget,
    CompletedTask, DailyUserTask, Transaction
)


class Command(BaseCommand):
    help = 'Создает тестовые данные для админки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Количество пользователей для создания (по умолчанию: 20)',
        )
        parser.add_argument(
            '--tasks',
            type=int,
            default=50,
            help='Количество заданий для создания (по умолчанию: 50)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаю создание тестовых данных...'))
        
        # Создаем категории
        categories = self.create_categories()
        
        # Создаем подкатегории
        subcategories = self.create_subcategories(categories)
        
        # Создаем пользователей
        users = self.create_users(options['users'])
        
        # Создаем задания
        tasks = self.create_tasks(options['tasks'], categories, subcategories)
        
        # Создаем выполненные задания
        self.create_completed_tasks(users, tasks)
        
        # Создаем ежедневные задания
        self.create_daily_tasks(users, tasks)
        
        # Создаем транзакции
        self.create_transactions(users)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Успешно создано:'))
        self.stdout.write(f'   - {len(categories)} категорий')
        self.stdout.write(f'   - {len(subcategories)} подкатегорий')
        self.stdout.write(f'   - {len(users)} пользователей')
        self.stdout.write(f'   - {len(tasks)} заданий')
        self.stdout.write(self.style.SUCCESS('\nТестовые данные готовы!'))

    def create_categories(self):
        """Создает категории заданий"""
        category_names = [
            'Романтика',
            'Творчество',
            'Игры и челленджи',
            'Время вместе',
            'Интим',
            'Эмоции',
            'Флирт',
            'Что-то новое',
        ]
        
        categories = []
        for name in category_names:
            category, created = TaskCategory.objects.get_or_create(
                name=name,
                defaults={
                    'slug': self.slugify(name),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'   ✓ Создана категория: {name}')
            categories.append(category)
        
        return categories

    def create_subcategories(self, categories):
        """Создает подкатегории"""
        subcategory_map = {
            'Творчество': ['Фото', 'Картина', 'Поделки', 'Музыка'],
            'Игры и челленджи': ['Настольные игры', 'Видеоигры', 'Квесты', 'Спортивные'],
            'Время вместе': ['Прогулки', 'Фильмы', 'Ужин', 'Путешествия'],
            'Романтика': ['Свидания', 'Подарки', 'Письма', 'Сюрпризы'],
            'Интим': ['Близость', 'Массаж', 'Романтика', 'Эксперименты'],
            'Эмоции': ['Поддержка', 'Объятия', 'Разговоры', 'Внимание'],
            'Флирт': ['Комплименты', 'Игры', 'Сообщения', 'Встречи'],
            'Что-то новое': ['Эксперименты', 'Приключения', 'Хобби', 'Обучение'],
        }
        
        subcategories = []
        for category in categories:
            sub_names = subcategory_map.get(category.name, [])
            for sub_name in sub_names:
                subcategory, created = TaskSubcategory.objects.get_or_create(
                    category=category,
                    name=sub_name,
                    defaults={
                        'slug': self.slugify(sub_name),
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(f'   ✓ Создана подкатегория: {category.name} - {sub_name}')
                subcategories.append(subcategory)
        
        return subcategories

    def create_users(self, count):
        """Создает пользователей"""
        genders = ['male', 'female', 'couple']
        first_names_male = ['Александр', 'Дмитрий', 'Максим', 'Иван', 'Сергей', 'Андрей', 'Алексей', 'Владимир']
        first_names_female = ['Елена', 'Мария', 'Анна', 'Ольга', 'Татьяна', 'Наталья', 'Екатерина', 'Ирина']
        last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Соколов']
        
        users = []
        for i in range(count):
            gender = random.choice(genders)
            
            if gender == 'couple':
                name = f"{random.choice(first_names_male)} и {random.choice(first_names_female)} {random.choice(last_names)}"
            elif gender == 'male':
                name = f"{random.choice(first_names_male)} {random.choice(last_names)}"
            else:
                name = f"{random.choice(first_names_female)} {random.choice(last_names)}"
            
            username = f"user_{i+1}_{random.randint(1000, 9999)}"
            tg_id = 1000000000 + i + 1
            
            user, created = User.objects.get_or_create(
                tg_id=tg_id,
                defaults={
                    'username': username,
                    'name': name,
                    'gender': gender,
                    'is_active': True,
                    'balance': random.randint(0, 500),
                    'last_daily_bonus': timezone.now().date() - timedelta(days=random.randint(0, 7)),
                }
            )
            if created:
                self.stdout.write(f'   ✓ Создан пользователь: {name} ({gender})')
            users.append(user)
        
        return users

    def create_tasks(self, count, categories, subcategories):
        """Создает задания"""
        task_templates = [
            {
                'title': 'Скажи ей "Сегодня хочется быть ближе, чем обычно..."',
                'description': 'Произнесите эту фразу и посмотрите на реакцию. Это поможет создать романтическую атмосферу.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Сделайте совместное фото',
                'description': 'Выберите красивое место и сделайте несколько совместных фотографий. Сохраните лучшую.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Напишите письмо с признанием',
                'description': 'Напишите письмо, в котором выразите свои чувства. Можно отправить или просто прочитать вслух.',
                'gender_targets': ['male', 'female', 'couple', 'all'],
            },
            {
                'title': 'Приготовьте ужин вместе',
                'description': 'Выберите рецепт и приготовьте ужин вместе. Это отличный способ провести время.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Сыграйте в настольную игру',
                'description': 'Выберите игру, которая нравится обоим, и проведите вечер за игрой.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Сделайте массаж',
                'description': 'Подарите друг другу расслабляющий массаж. Используйте ароматические масла.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Напишите список из 10 причин, почему вы цените партнера',
                'description': 'Возьмите лист бумаги и напишите 10 конкретных причин. Поделитесь друг с другом.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Посмотрите закат вместе',
                'description': 'Найдите место с хорошим видом и проведите время, наблюдая за закатом.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Создайте плейлист для партнера',
                'description': 'Составьте плейлист из песен, которые напоминают вам о ваших отношениях.',
                'gender_targets': ['couple', 'all'],
            },
            {
                'title': 'Сделайте что-то новое вместе',
                'description': 'Выберите активность, которую вы никогда не делали вместе, и попробуйте её.',
                'gender_targets': ['couple', 'all'],
            },
        ]
        
        tasks = []
        for i in range(count):
            template = random.choice(task_templates)
            category = random.choice(categories)
            category_subs = [s for s in subcategories if s.category == category]
            subcategory = random.choice(category_subs) if category_subs else None
            
            task = Task.objects.create(
                title=f"{template['title']} #{i+1}" if i >= len(task_templates) else template['title'],
                description=template['description'],
                category=category,
                subcategory=subcategory,
                is_active=random.choice([True, True, True, False]),  # 75% активных
            )
            
            # Добавляем категории для фильтрации
            task_categories = random.sample(list(categories), random.randint(1, 3))
            task.categories.set(task_categories)
            
            # Добавляем gender_targets
            for gender_target in template['gender_targets']:
                TaskGenderTarget.objects.get_or_create(
                    task=task,
                    gender_target=gender_target
                )
            
            if i < 10:
                self.stdout.write(f'   ✓ Создано задание: {task.title}')
            tasks.append(task)
        
        return tasks

    def create_completed_tasks(self, users, tasks):
        """Создает выполненные задания"""
        completed_count = 0
        for user in random.sample(users, min(len(users), len(users) // 2)):
            user_tasks = random.sample(tasks, random.randint(1, min(10, len(tasks))))
            for task in user_tasks:
                completed_date = timezone.now() - timedelta(days=random.randint(0, 30))
                completed_time = timezone.now() - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                CompletedTask.objects.get_or_create(
                    user=user,
                    task=task,
                    defaults={
                        'completed_at': completed_time.replace(
                            year=completed_date.year,
                            month=completed_date.month,
                            day=completed_date.day
                        )
                    }
                )
                completed_count += 1
        
        self.stdout.write(f'   ✓ Создано {completed_count} выполненных заданий')

    def create_daily_tasks(self, users, tasks):
        """Создает ежедневные задания"""
        today = timezone.now().date()
        daily_count = 0
        
        for user in random.sample(users, min(len(users), len(users) // 3)):
            # Создаем задания на сегодня
            user_tasks = random.sample(tasks, min(3, len(tasks)))
            for i, task in enumerate(user_tasks):
                DailyUserTask.objects.get_or_create(
                    user=user,
                    task=task,
                    date=today,
                    defaults={
                        'is_free': i < 3,  # Первые 3 бесплатные
                        'is_completed': random.choice([True, False]),
                    }
                )
                daily_count += 1
            
            # Создаем задания за последние дни
            for day_offset in range(1, 8):
                date = today - timedelta(days=day_offset)
                user_tasks = random.sample(tasks, random.randint(1, min(5, len(tasks))))
                for task in user_tasks:
                    DailyUserTask.objects.get_or_create(
                        user=user,
                        task=task,
                        date=date,
                        defaults={
                            'is_free': random.choice([True, False]),
                            'is_completed': random.choice([True, False]),
                        }
                    )
                    daily_count += 1
        
        self.stdout.write(f'   ✓ Создано {daily_count} ежедневных заданий')

    def create_transactions(self, users):
        """Создает транзакции"""
        transaction_types = ['purchase', 'bonus', 'task_payment']
        payment_methods = ['yookassa', 'daily_bonus', 'system']
        statuses = ['completed', 'pending', 'failed']
        
        transaction_count = 0
        for user in random.sample(users, min(len(users), len(users) // 2)):
            for _ in range(random.randint(1, 5)):
                transaction_type = random.choice(transaction_types)
                payment_method = random.choice(payment_methods) if transaction_type == 'purchase' else random.choice(['daily_bonus', 'system'])
                
                Transaction.objects.create(
                    user=user,
                    amount=random.choice([50, 100, 150, 200, 300]),
                    transaction_type=transaction_type,
                    payment_method=payment_method,
                    status=random.choice(statuses),
                    description=f"Тестовая транзакция {transaction_type}",
                    created_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                )
                transaction_count += 1
        
        self.stdout.write(f'   ✓ Создано {transaction_count} транзакций')

    def slugify(self, text):
        """Простая функция для создания слага"""
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        
        text = text.lower()
        result = ''
        for char in text:
            if char in translit_map:
                result += translit_map[char]
            elif char.isalnum():
                result += char
            elif char == ' ':
                result += '-'
        
        return result

