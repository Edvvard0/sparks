from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.task import Task, TaskTranslation
from app.models.language import Language
import time

# Попытка импортировать переводчики
TRANSLATORS_AVAILABLE = {}
try:
    from deep_translator import MyMemoryTranslator, GoogleTranslator
    TRANSLATORS_AVAILABLE['mymemory'] = True
    TRANSLATORS_AVAILABLE['google'] = True
except ImportError:
    TRANSLATORS_AVAILABLE['mymemory'] = False
    TRANSLATORS_AVAILABLE['google'] = False
    print("Warning: deep-translator not available")


class TranslationService:
    def __init__(self):
        """Инициализация сервиса перевода с несколькими бесплатными переводчиками"""
        self.translators = []
        
        # Приоритет 1: MyMemory с API ключом (если есть)
        if TRANSLATORS_AVAILABLE.get('mymemory') and settings.MYMEMORY_API_KEY:
            try:
                self.translators.append({
                    'name': 'MyMemory (API)',
                    'translator': MyMemoryTranslator(api_key=settings.MYMEMORY_API_KEY),
                    'priority': 1
                })
            except:
                pass
        
        # Приоритет 2: MyMemory без ключа (бесплатно, есть лимиты)
        if TRANSLATORS_AVAILABLE.get('mymemory'):
            try:
                self.translators.append({
                    'name': 'MyMemory (Free)',
                    'translator': MyMemoryTranslator(),
                    'priority': 2
                })
            except:
                pass
        
        # Приоритет 3: Google Translate (бесплатно, может быть заблокирован)
        if TRANSLATORS_AVAILABLE.get('google'):
            try:
                self.translators.append({
                    'name': 'Google Translate',
                    'translator': GoogleTranslator(),
                    'priority': 3
                })
            except:
                pass
        
        # Сортируем по приоритету
        self.translators.sort(key=lambda x: x['priority'])
    
    def translate_text(self, text: str, source_lang: str, target_lang: str, max_retries: int = 3) -> str:
        """
        Перевод текста через бесплатные API с автоматическим fallback
        
        Args:
            text: Текст для перевода
            source_lang: Исходный язык (например, 'ru')
            target_lang: Целевой язык (например, 'en')
            max_retries: Максимальное количество попыток с разными переводчиками
            
        Returns:
            Переведенный текст
        """
        if not text or not text.strip():
            return text
        
        # Если нет доступных переводчиков
        if not self.translators:
            print(f"[Translation] No translators available, returning original text")
            return text
        
        # Маппинг языков для разных переводчиков
        lang_map = {
            'ru': 'russian',
            'en': 'english',
            'es': 'spanish'
        }
        
        source_mapped = lang_map.get(source_lang, source_lang)
        target_mapped = lang_map.get(target_lang, target_lang)
        
        # Пробуем каждый переводчик по очереди
        last_error = None
        for attempt, translator_info in enumerate(self.translators[:max_retries], 1):
            try:
                translator = translator_info['translator']
                translator_name = translator_info['name']
                
                # Небольшая задержка между попытками для избежания rate limiting
                if attempt > 1:
                    time.sleep(0.5)
                
                # Все переводчики из deep-translator используют одинаковый интерфейс
                result = translator.translate(text, source=source_lang, target=target_lang)
                
                if result and result.strip() and result != text:
                    print(f"[Translation] Successfully translated using {translator_name}: {source_lang} -> {target_lang}")
                    return result.strip()
                else:
                    print(f"[Translation] Empty result from {translator_name}, trying next translator")
                    
            except Exception as e:
                last_error = e
                print(f"[Translation] Error with {translator_info['name']}: {e}, trying next translator")
                continue
        
        # Если все переводчики не сработали
        print(f"[Translation] All translators failed. Last error: {last_error}")
        print(f"[Translation] Returning original text with language marker")
        return f"[{target_lang.upper()}] {text}"
    
    def translate_task(self, db: Session, task_id: int, source_lang: str = 'ru') -> None:
        """
        Перевод задания на все языки и сохранение в БД
        
        Args:
            db: Сессия БД
            task_id: ID задания
            source_lang: Исходный язык (по умолчанию 'ru')
        """
        # Получаем задание с русским переводом
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"[Translation] Task {task_id} not found")
            return
        
        # Получаем русский перевод (source)
        source_translation = db.query(TaskTranslation).join(Language).filter(
            TaskTranslation.task_id == task_id,
            Language.code == source_lang
        ).first()
        
        if not source_translation:
            print(f"[Translation] No source translation (lang={source_lang}) found for task {task_id}")
            return
        
        # Получаем языки для перевода (en, es)
        target_languages = db.query(Language).filter(
            Language.code.in_(['en', 'es']),
            Language.is_active == True
        ).all()
        
        if not target_languages:
            print(f"[Translation] No target languages found")
            return
        
        translations_created = 0
        for target_lang in target_languages:
            # Проверяем, есть ли уже перевод
            existing = db.query(TaskTranslation).filter(
                TaskTranslation.task_id == task_id,
                TaskTranslation.language_id == target_lang.id
            ).first()
            
            if existing:
                print(f"[Translation] Translation for task {task_id} to {target_lang.code} already exists")
                continue  # Перевод уже существует
            
            print(f"[Translation] Translating task {task_id} from {source_lang} to {target_lang.code}...")
            
            # Переводим title и description
            translated_title = self.translate_text(
                source_translation.title,
                source_lang,
                target_lang.code
            )
            
            # Небольшая задержка между переводами для избежания rate limiting
            time.sleep(0.3)
            
            translated_description = self.translate_text(
                source_translation.description,
                source_lang,
                target_lang.code
            )
            
            # Создаем перевод
            translation = TaskTranslation(
                task_id=task_id,
                language_id=target_lang.id,
                title=translated_title,
                description=translated_description
            )
            db.add(translation)
            translations_created += 1
        
        if translations_created > 0:
            db.commit()
            print(f"[Translation] Successfully created {translations_created} translation(s) for task {task_id}")
        else:
            print(f"[Translation] No new translations created for task {task_id}")

