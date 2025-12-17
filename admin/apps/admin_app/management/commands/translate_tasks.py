"""
Команда для автоматического перевода заданий на другие языки

Использование:
    python manage.py translate_tasks                    # Перевести все задания без переводов
    python manage.py translate_tasks --task-id 1       # Перевести конкретное задание
    python manage.py translate_tasks --all             # Перевести все задания (включая уже переведенные)
"""

from django.core.management.base import BaseCommand
from django.db import connection
import sys
import os

# Добавляем путь к бэкенду
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


class Command(BaseCommand):
    help = 'Автоматический перевод заданий на другие языки (en, es)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-id',
            type=int,
            help='ID конкретного задания для перевода',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Перевести все задания, включая уже переведенные',
        )

    def handle(self, *args, **options):
        try:
            from app.services.translation_service import TranslationService
            from app.core.database import SessionLocal
            from app.models.task import Task, TaskTranslation
            from app.models.language import Language
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка импорта модулей бэкенда: {e}')
            )
            self.stdout.write(
                self.style.WARNING('Убедитесь что backend установлен и доступен')
            )
            return

        db = SessionLocal()
        translation_service = TranslationService()

        try:
            if options['task_id']:
                # Переводим конкретное задание
                task_id = options['task_id']
                task = db.query(Task).filter(Task.id == task_id).first()
                
                if not task:
                    self.stdout.write(
                        self.style.ERROR(f'Задание с ID {task_id} не найдено')
                    )
                    return
                
                self.stdout.write(f'Перевод задания #{task_id}...')
                translation_service.translate_task(db, task_id, source_lang='ru')
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Задание #{task_id} переведено')
                )
            else:
                # Переводим все задания
                tasks = db.query(Task).all()
                translated_count = 0
                skipped_count = 0
                
                for task in tasks:
                    # Проверяем есть ли русский перевод
                    ru_language = db.query(Language).filter(Language.code == 'ru').first()
                    if not ru_language:
                        continue
                    
                    ru_translation = db.query(TaskTranslation).filter(
                        TaskTranslation.task_id == task.id,
                        TaskTranslation.language_id == ru_language.id
                    ).first()
                    
                    if not ru_translation:
                        self.stdout.write(
                            self.style.WARNING(f'Задание #{task.id}: нет русского перевода, пропускаем')
                        )
                        skipped_count += 1
                        continue
                    
                    # Проверяем есть ли уже переводы на другие языки
                    if not options['all']:
                        en_language = db.query(Language).filter(Language.code == 'en').first()
                        es_language = db.query(Language).filter(Language.code == 'es').first()
                        
                        en_translation = None
                        es_translation = None
                        
                        if en_language:
                            en_translation = db.query(TaskTranslation).filter(
                                TaskTranslation.task_id == task.id,
                                TaskTranslation.language_id == en_language.id
                            ).first()
                        
                        if es_language:
                            es_translation = db.query(TaskTranslation).filter(
                                TaskTranslation.task_id == task.id,
                                TaskTranslation.language_id == es_language.id
                            ).first()
                        
                        # Если есть все переводы - пропускаем
                        if en_translation and es_translation:
                            skipped_count += 1
                            continue
                    
                    # Переводим задание
                    self.stdout.write(f'Перевод задания #{task.id}...')
                    translation_service.translate_task(db, task.id, source_lang='ru')
                    translated_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Переведено заданий: {translated_count}\n'
                        f'  Пропущено: {skipped_count}'
                    )
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при переводе: {e}')
            )
            import traceback
            traceback.print_exc()
        finally:
            db.close()

