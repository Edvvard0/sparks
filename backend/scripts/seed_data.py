"""
Скрипт для заполнения базы данных тестовыми данными
Запуск: python scripts/seed_data.py
"""
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.language import Language
from app.models.task import TaskCategory, CategoryTranslation, Task, TaskTranslation, TaskGenderTarget, GenderTarget
from app.models.user import User, Gender
from app.services.user_service import UserService
from app.services.translation_service import TranslationService
from datetime import datetime


def create_languages(db: Session):
    """Создание языков"""
    languages_data = [
        {"code": "ru", "name": "Русский"},
        {"code": "en", "name": "English"},
        {"code": "es", "name": "Español"},
    ]
    
    for lang_data in languages_data:
        existing = db.query(Language).filter(Language.code == lang_data["code"]).first()
        if not existing:
            language = Language(**lang_data, is_active=True)
            db.add(language)
            print(f"✓ Создан язык: {lang_data['name']} ({lang_data['code']})")
        else:
            print(f"→ Язык уже существует: {lang_data['name']} ({lang_data['code']})")
    
    db.commit()


def create_categories(db: Session):
    """Создание категорий заданий с переводами"""
    categories_data = [
        {
            "slug": "romance",
            "color": "#FFC700",  # Желтый
            "translations": {
                "ru": "Романтика",
                "en": "Romance",
                "es": "Romance"
            }
        },
        {
            "slug": "new",
            "color": "#6049EC",  # Фиолетовый
            "translations": {
                "ru": "Что-то новое",
                "en": "Something new",
                "es": "Algo nuevo"
            }
        },
        {
            "slug": "emotions",
            "color": "#EB454E",  # Красный
            "translations": {
                "ru": "Эмоции",
                "en": "Emotions",
                "es": "Emociones"
            }
        },
        {
            "slug": "time",
            "color": "#FFC700",
            "translations": {
                "ru": "Время вместе",
                "en": "Time together",
                "es": "Tiempo juntos"
            }
        },
        {
            "slug": "games",
            "color": "#FFC700",
            "translations": {
                "ru": "Игры и челенджы",
                "en": "Games and challenges",
                "es": "Juegos y desafíos"
            }
        },
        {
            "slug": "intimate",
            "color": "#EB454E",
            "translations": {
                "ru": "Интим",
                "en": "Intimate",
                "es": "Íntimo"
            }
        },
        {
            "slug": "flirt",
            "color": "#6049EC",
            "translations": {
                "ru": "Флирт",
                "en": "Flirt",
                "es": "Coquetear"
            }
        },
        {
            "slug": "creativity",
            "color": "#FFC700",
            "translations": {
                "ru": "Творчество",
                "en": "Creativity",
                "es": "Creatividad"
            }
        },
        {
            "slug": "adventure",
            "color": "#6049EC",
            "translations": {
                "ru": "Приключения",
                "en": "Adventure",
                "es": "Aventura"
            }
        },
        {
            "slug": "travel",
            "color": "#FFC700",
            "translations": {
                "ru": "Путешествия",
                "en": "Travel",
                "es": "Viajes"
            }
        },
        {
            "slug": "sport",
            "color": "#EB454E",
            "translations": {
                "ru": "Спорт",
                "en": "Sport",
                "es": "Deporte"
            }
        },
        {
            "slug": "cooking",
            "color": "#6049EC",
            "translations": {
                "ru": "Кулинария",
                "en": "Cooking",
                "es": "Cocina"
            }
        },
    ]
    
    # Получаем языки
    languages = {lang.code: lang for lang in db.query(Language).all()}
    
    for cat_data in categories_data:
        # Создаем категорию
        category = db.query(TaskCategory).filter(TaskCategory.slug == cat_data["slug"]).first()
        if not category:
            category = TaskCategory(
                slug=cat_data["slug"],
                color=cat_data["color"],
                is_active=True
            )
            db.add(category)
            db.flush()
            print(f"✓ Создана категория: {cat_data['slug']}")
        else:
            print(f"→ Категория уже существует: {cat_data['slug']}")
        
        # Создаем переводы
        for lang_code, name in cat_data["translations"].items():
            if lang_code not in languages:
                continue
            
            existing_translation = db.query(CategoryTranslation).filter(
                CategoryTranslation.category_id == category.id,
                CategoryTranslation.language_id == languages[lang_code].id
            ).first()
            
            if not existing_translation:
                translation = CategoryTranslation(
                    category_id=category.id,
                    language_id=languages[lang_code].id,
                    name=name
                )
                db.add(translation)
    
    db.commit()
    print("✓ Все категории созданы")


def create_sample_tasks(db: Session):
    """Создание примерных заданий"""
    # Получаем категории и языки
    romance_category = db.query(TaskCategory).filter(TaskCategory.slug == "romance").first()
    games_category = db.query(TaskCategory).filter(TaskCategory.slug == "games").first()
    intimate_category = db.query(TaskCategory).filter(TaskCategory.slug == "intimate").first()
    
    if not romance_category or not games_category or not intimate_category:
        print("⚠ Категории не найдены, сначала создайте категории")
        return
    
    ru_language = db.query(Language).filter(Language.code == "ru").first()
    en_language = db.query(Language).filter(Language.code == "en").first()
    es_language = db.query(Language).filter(Language.code == "es").first()
    
    tasks_data = [
        {
            "category": romance_category,
            "gender_targets": [GenderTarget.ALL],
            "translations": {
                "ru": {
                    "title": "Скажи ей",
                    "description": '"Сегодня хочется быть ближе, чем обычно…" — и посмотри на реакцию'
                },
                "en": {
                    "title": "Tell her",
                    "description": '"Today I want to be closer than usual..." — and watch the reaction'
                },
                "es": {
                    "title": "Dile",
                    "description": '"Hoy quiero estar más cerca de lo habitual..." — y observa la reacción'
                }
            }
        },
        {
            "category": games_category,
            "gender_targets": [GenderTarget.ALL, GenderTarget.COUPLE],
            "translations": {
                "ru": {
                    "title": "Игра в вопросы",
                    "description": "Задайте друг другу по 5 вопросов, на которые вы еще не знаете ответов"
                },
                "en": {
                    "title": "Question game",
                    "description": "Ask each other 5 questions you don't know the answers to yet"
                },
                "es": {
                    "title": "Juego de preguntas",
                    "description": "Háganse 5 preguntas mutuamente que aún no conocen las respuestas"
                }
            }
        },
        {
            "category": intimate_category,
            "gender_targets": [GenderTarget.COUPLE],
            "translations": {
                "ru": {
                    "title": "Массаж",
                    "description": "Сделайте друг другу расслабляющий массаж с ароматическими маслами"
                },
                "en": {
                    "title": "Massage",
                    "description": "Give each other a relaxing massage with aromatic oils"
                },
                "es": {
                    "title": "Masaje",
                    "description": "Háganse un masaje relajante mutuamente con aceites aromáticos"
                }
            }
        },
        {
            "category": romance_category,
            "gender_targets": [GenderTarget.MALE, GenderTarget.FEMALE],
            "translations": {
                "ru": {
                    "title": "Письмо",
                    "description": "Напишите друг другу письмо о том, что вы цените в ваших отношениях"
                },
                "en": {
                    "title": "Letter",
                    "description": "Write each other a letter about what you value in your relationship"
                },
                "es": {
                    "title": "Carta",
                    "description": "Escríbanse una carta sobre lo que valoran en su relación"
                }
            }
        },
        {
            "category": games_category,
            "gender_targets": [GenderTarget.ALL],
            "translations": {
                "ru": {
                    "title": "Угадай мелодию",
                    "description": "Включите музыку и угадывайте исполнителей и названия песен"
                },
                "en": {
                    "title": "Guess the song",
                    "description": "Turn on music and guess the artists and song titles"
                },
                "es": {
                    "title": "Adivina la canción",
                    "description": "Pongan música y adivinen los artistas y títulos de las canciones"
                }
            }
        },
    ]
    
    for task_data in tasks_data:
        # Создаем задание
        task = Task(
            category_id=task_data["category"].id,
            is_active=True
        )
        db.add(task)
        db.flush()
        
        # Создаем переводы
        for lang_code, lang_obj in [("ru", ru_language), ("en", en_language), ("es", es_language)]:
            if lang_code in task_data["translations"] and lang_obj:
                translation = TaskTranslation(
                    task_id=task.id,
                    language_id=lang_obj.id,
                    title=task_data["translations"][lang_code]["title"],
                    description=task_data["translations"][lang_code]["description"]
                )
                db.add(translation)
        
        # Создаем gender targets
        for gender_target in task_data["gender_targets"]:
            target = TaskGenderTarget(
                task_id=task.id,
                gender=gender_target
            )
            db.add(target)
        
        print(f"✓ Создано задание: {task_data['translations']['ru']['title']}")
    
    db.commit()
    print("✓ Все задания созданы")


def create_test_user(db: Session):
    """Создание тестового пользователя"""
    # Проверяем, есть ли уже пользователь
    existing = db.query(User).filter(User.tg_id == 123456789).first()
    if existing:
        print("→ Тестовый пользователь уже существует")
        return
    
    ru_language = db.query(Language).filter(Language.code == "ru").first()
    if not ru_language:
        print("⚠ Язык 'ru' не найден")
        return
    
    # Получаем категории для интересов
    categories = db.query(TaskCategory).filter(
        TaskCategory.slug.in_(["romance", "games", "intimate"])
    ).limit(3).all()
    
    if len(categories) < 3:
        print("⚠ Недостаточно категорий для создания пользователя")
        return
    
    # Создаем пользователя
    user = User(
        tg_id=123456789,
        username="test_user",
        first_name="Тестовый",
        last_name="Пользователь",
        gender=Gender.COUPLE,
        language_id=ru_language.id,
        is_admin=False,
        balance=100,
        is_active=True
    )
    db.add(user)
    db.flush()
    
    # Добавляем интересы
    from app.models.user import UserCategory
    for category in categories:
        user_category = UserCategory(
            user_id=user.tg_id,
            category_id=category.id
        )
        db.add(user_category)
    
    db.commit()
    print(f"✓ Создан тестовый пользователь: {user.first_name} {user.last_name} (tg_id: {user.tg_id})")
    print(f"  Баланс: {user.balance}, Интересы: {len(categories)}")


def main():
    """Основная функция"""
    print("=" * 50)
    print("Заполнение базы данных тестовыми данными")
    print("=" * 50)
    
    # Создаем таблицы если их нет
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("\n1. Создание языков...")
        create_languages(db)
        
        print("\n2. Создание категорий...")
        create_categories(db)
        
        print("\n3. Создание заданий...")
        create_sample_tasks(db)
        
        print("\n4. Создание тестового пользователя...")
        create_test_user(db)
        
        print("\n" + "=" * 50)
        print("✓ Все тестовые данные успешно созданы!")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()

