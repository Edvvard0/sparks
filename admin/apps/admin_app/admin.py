from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
import logging
from .models import (
    Language,
    User, UserCategory,
    TaskCategory, CategoryTranslation,
    Task, TaskTranslation, TaskGenderTarget,
    CompletedTask,
    DailyFreeTask, DailyBonus,
    Transaction
)

# Настраиваем logger для отладки
logger = logging.getLogger(__name__)

# Настраиваем заголовки стандартного admin site
admin.site.site_header = 'Админка Telegram Mini App'
admin.site.site_title = 'Админка'
admin.site.index_title = 'Панель управления'

# Сохраняем оригинальный index метод
_original_index = admin.site.index

def custom_index(self, request, extra_context=None):
    """Переопределяем главную страницу админки для показа дашборда"""
    extra_context = extra_context or {}
    # Получаем статистику
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    completed_today = CompletedTask.objects.filter(
        completed_at__date=today
    ).count()
    
    completed_yesterday = CompletedTask.objects.filter(
        completed_at__date=yesterday
    ).count()
    
    completed_week = CompletedTask.objects.filter(
        completed_at__date__gte=week_ago
    ).count()
    
    completed_month = CompletedTask.objects.filter(
        completed_at__date__gte=month_ago
    ).count()
    
    total_users = User.objects.count()
    active_users_today = DailyFreeTask.objects.filter(
        date=today
    ).values('user').distinct().count()
    
    total_tasks = Task.objects.count()
    active_tasks = Task.objects.filter(is_active=True).count()
    
    extra_context['stats'] = {
        'completed_today': completed_today,
        'completed_yesterday': completed_yesterday,
        'completed_week': completed_week,
        'completed_month': completed_month,
        'total_users': total_users,
        'active_users_today': active_users_today,
        'total_tasks': total_tasks,
        'active_tasks': active_tasks,
    }
    
    return _original_index(request, extra_context)

# Переопределяем index метод
admin.site.index = custom_index.__get__(admin.site, admin.AdminSite)


# ============================================================================
# Language Admin
# ============================================================================

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    verbose_name = 'Язык'
    verbose_name_plural = 'Языки'
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'code', 'name', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
    actions = ['activate_languages', 'deactivate_languages']
    
    def activate_languages(self, request, queryset):
        queryset.update(is_active=True)
    activate_languages.short_description = 'Активировать выбранные языки'
    
    def deactivate_languages(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_languages.short_description = 'Деактивировать выбранные языки'


# ============================================================================
# UserCategory Inline
# ============================================================================

class UserCategoryInline(admin.TabularInline):
    model = UserCategory
    extra = 0  # Не показывать пустые формы по умолчанию
    fields = ['id', 'category', 'created_at']
    readonly_fields = ['created_at']
    verbose_name = 'Интерес'
    verbose_name_plural = 'Интересы'
    
    def get_readonly_fields(self, request, obj=None):
        """ID должен быть readonly только для существующих объектов"""
        readonly = ['created_at']
        if obj and obj.pk:
            readonly.append('id')
        return readonly
    
    def get_formset(self, request, obj=None, **kwargs):
        """Переопределяем формсет для правильной обработки managed=False"""
        formset_class = super().get_formset(request, obj, **kwargs)
        
        # Сохраняем ссылку на оригинальный класс формы
        OriginalForm = formset_class.form
        
        # Создаем кастомную форму
        class CustomUserCategoryForm(OriginalForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Делаем поле id необязательным для всех записей
                if 'id' in self.fields:
                    self.fields['id'].required = False
                    # Если это существующая запись, устанавливаем id из instance
                    if self.instance and self.instance.pk:
                        self.initial['id'] = self.instance.pk
                        # Также устанавливаем в data если его там нет
                        if hasattr(self, 'data') and self.data:
                            prefix = self.prefix if hasattr(self, 'prefix') else ''
                            id_key = f'{prefix}-id' if prefix else 'id'
                            if id_key not in self.data:
                                # Создаем копию data и добавляем id
                                from django.utils.datastructures import MultiValueDict
                                if isinstance(self.data, MultiValueDict):
                                    self.data = self.data.copy()
                                else:
                                    self.data = self.data.copy() if hasattr(self.data, 'copy') else dict(self.data)
                                self.data[id_key] = str(self.instance.pk)
            
            def full_clean(self):
                """Переопределяем full_clean чтобы пропустить валидацию id для существующих записей"""
                # Сохраняем оригинальное значение required для id
                id_required_original = None
                if 'id' in self.fields:
                    id_required_original = self.fields['id'].required
                    # Если это существующая запись, делаем id необязательным
                    if self.instance and self.instance.pk:
                        self.fields['id'].required = False
                
                try:
                    super().full_clean()
                finally:
                    # Восстанавливаем оригинальное значение
                    if id_required_original is not None:
                        self.fields['id'].required = id_required_original
                    
                    # Если это существующая запись и id не указан, устанавливаем его
                    if self.instance and self.instance.pk:
                        if 'id' not in self.cleaned_data or not self.cleaned_data['id']:
                            self.cleaned_data['id'] = self.instance.pk
        
        # Создаем кастомный формсет класс
        class CustomUserCategoryFormset(formset_class):
            form = CustomUserCategoryForm
            
            def clean(self):
                """Валидация формсета с проверкой дубликатов"""
                # Вызываем оригинальный clean если он есть
                try:
                    super().clean()
                except:
                    pass
                
                if any(self.errors):
                    return
                
                # Проверяем дубликаты только среди новых записей (без ID)
                categories_seen = set()
                for form in self.forms:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        category = form.cleaned_data.get('category')
                        if category:
                            category_id = category.id if hasattr(category, 'id') else category
                            # Проверяем дубликаты только для новых записей (без ID)
                            form_id = form.cleaned_data.get('id')
                            if not form_id and category_id in categories_seen:
                                from django.core.exceptions import ValidationError
                                raise ValidationError(f'Категория уже добавлена.')
                            if not form_id:
                                categories_seen.add(category_id)
        
        return CustomUserCategoryFormset


# ============================================================================
# User Admin
# ============================================================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    verbose_name = 'Пользователь'
    verbose_name_plural = 'Пользователи'
    list_display = ['tg_id', 'username', 'get_full_name', 'gender', 'language', 'balance', 'wallet_address', 'is_active', 'created_at']
    list_filter = ['gender', 'is_active', 'is_admin', 'language', 'has_lifetime_subscription', 'created_at']
    search_fields = ['tg_id', 'username', 'first_name', 'last_name', 'wallet_address']
    readonly_fields = ['tg_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('tg_id', 'username', 'first_name', 'last_name', 'gender', 'language')
        }),
        ('Права доступа', {
            'fields': ('is_admin', 'is_active', 'password')
        }),
        ('Финансы', {
            'fields': ('balance', 'wallet_address', 'has_lifetime_subscription')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [UserCategoryInline]
    actions = ['activate_users', 'deactivate_users', 'reset_balance']
    
    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем форму для правильной обработки managed=False"""
        form_class = super().get_form(request, obj, **kwargs)
        
        # Создаем кастомную форму
        class CustomUserForm(form_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
                # Если редактируем существующего пользователя, делаем gender необязательным
                if self.instance and self.instance.pk:
                    if 'gender' in self.fields:
                        self.fields['gender'].required = False
                    
                    # Загружаем данные из БД если они не установлены
                    try:
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT gender, language_id FROM users WHERE tg_id = %s", [self.instance.tg_id])
                            row = cursor.fetchone()
                            if row:
                                # Устанавливаем значения в объект и форму
                                if row[0] and not self.instance.gender:
                                    self.instance.gender = row[0]
                                    if 'gender' in self.fields:
                                        self.initial['gender'] = row[0]
                                
                                if row[1] and not self.instance.language_id:
                                    from apps.admin_app.models import Language
                                    try:
                                        language = Language.objects.get(id=row[1])
                                        self.instance.language = language
                                        if 'language' in self.fields:
                                            self.initial['language'] = language
                                    except Language.DoesNotExist:
                                        pass
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"[UserAdmin] Error loading user data: {e}")
        
        return CustomUserForm
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Переопределяем changeform_view для логирования ошибок валидации"""
        import logging
        logger = logging.getLogger(__name__)
        
        if request.method == 'POST':
            logger.info(f"[UserAdmin] POST request received for user tg_id={object_id}")
        
        response = super().changeform_view(request, object_id, form_url, extra_context)
        
        # Если форма не прошла валидацию (статус 200 вместо 302), логируем ошибки
        if request.method == 'POST' and response.status_code == 200:
            if hasattr(response, 'context_data'):
                context_data = response.context_data
                if 'adminform' in context_data:
                    form = context_data['adminform'].form
                    if form.errors:
                        logger.error(f"[UserAdmin] Form validation errors: {form.errors}")
                        # Выводим каждую ошибку отдельно
                        for field, errors in form.errors.items():
                            logger.error(f"[UserAdmin] Field '{field}' errors: {errors}")
                
                if 'inline_admin_formsets' in context_data:
                    for formset_wrapper in context_data['inline_admin_formsets']:
                        formset = formset_wrapper.formset
                        if formset.errors:
                            logger.error(f"[UserAdmin] Formset errors: {formset.errors}")
                            for i, form_errors in enumerate(formset.errors):
                                if form_errors:
                                    logger.error(f"[UserAdmin] Formset form #{i} errors: {form_errors}")
                        if formset.non_form_errors():
                            logger.error(f"[UserAdmin] Formset non_form_errors: {formset.non_form_errors()}")
        
        return response
    
    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name or ''}".strip()
        return name or '-'
    get_full_name.short_description = 'Имя'
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение модели для правильной обработки managed=False"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[UserAdmin] save_model called, change={change}, obj.tg_id={obj.tg_id if obj else None}")
        
        # Если редактируем существующего пользователя, загружаем недостающие данные из БД
        if change and obj.pk:
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT gender, language_id, balance FROM users WHERE tg_id = %s", [obj.tg_id])
                    row = cursor.fetchone()
                    if row:
                        # Если gender не указан в форме, загружаем из БД
                        if not obj.gender and row[0]:
                            obj.gender = row[0]
                            logger.info(f"[UserAdmin] Set gender={obj.gender} from database")
                        
                        # Если language не указан, загружаем из БД
                        if not obj.language_id and row[1]:
                            obj.language_id = row[1]
                            logger.info(f"[UserAdmin] Set language_id={obj.language_id} from database")
            except Exception as e:
                logger.error(f"[UserAdmin] Error getting user data from DB: {e}")
        
        # Если gender не установлен, получаем из формы
        if not obj.gender:
            if hasattr(form, 'cleaned_data') and 'gender' in form.cleaned_data and form.cleaned_data['gender']:
                obj.gender = form.cleaned_data['gender']
                logger.info(f"[UserAdmin] Set gender={obj.gender} from form")
        
        # Убеждаемся, что language_id установлен из ForeignKey
        if obj.language:
            if hasattr(obj.language, 'id'):
                obj.language_id = obj.language.id
            elif isinstance(obj.language, int):
                obj.language_id = obj.language
            logger.info(f"[UserAdmin] Set language_id={obj.language_id} from language")
        
        if not obj.language_id:
            # Пытаемся получить language_id из формы
            if hasattr(form, 'cleaned_data') and 'language' in form.cleaned_data and form.cleaned_data['language']:
                lang = form.cleaned_data['language']
                obj.language_id = lang.id if hasattr(lang, 'id') else lang
                logger.info(f"[UserAdmin] Set language_id={obj.language_id} from form")
            elif change and obj.pk:
                # Если language_id не установлен, пытаемся получить из существующего объекта
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT language_id FROM users WHERE tg_id = %s", [obj.tg_id])
                        row = cursor.fetchone()
                        if row:
                            obj.language_id = row[0]
                            logger.info(f"[UserAdmin] Set language_id={obj.language_id} from database")
                except Exception as e:
                    logger.error(f"[UserAdmin] Error getting language_id from DB: {e}")
        
        # Если language_id не установлен, это критично только для новых пользователей
        if not obj.language_id and not change:
            logger.error(f"[UserAdmin] language_id is not set! obj.language={obj.language}")
            raise ValueError("Cannot save User: language_id is not set")
        
        # Если gender не установлен, это критично только для новых пользователей
        if not obj.gender and not change:
            logger.error(f"[UserAdmin] gender is not set!")
            raise ValueError("Cannot save User: gender is not set")
        
        # Устанавливаем updated_at
        from django.utils import timezone
        obj.updated_at = timezone.now()
        
        # Сохраняем объект
        logger.info(f"[UserAdmin] Saving user tg_id={obj.tg_id}, balance={obj.balance}, gender={obj.gender}, language_id={obj.language_id}")
        try:
            obj.save()
            logger.info(f"[UserAdmin] User saved successfully")
        except Exception as e:
            logger.error(f"[UserAdmin] Error saving user: {e}", exc_info=True)
            raise
    
    def save_related(self, request, form, formsets, change):
        """Переопределяем сохранение связанных объектов (inline форм)"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Сначала сохраняем основную модель если она еще не сохранена
        if form.instance and not form.instance.pk:
            logger.warning(f"[UserAdmin] Main user not saved yet, saving first...")
            form.instance.save()
            logger.info(f"[UserAdmin] Main user saved with tg_id={form.instance.tg_id}")
        
        # Затем сохраняем все формсеты
        for formset in formsets:
            logger.info(f"[UserAdmin] Calling save_formset for {formset.model.__name__}")
            self.save_formset(request, form, formset, change)
    
    def save_formset(self, request, form, formset, change):
        """Переопределяем сохранение формсета для правильной обработки связанных объектов"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[UserAdmin] save_formset called for {formset.model.__name__}, change={change}")
        logger.info(f"[UserAdmin] Formset errors: {formset.errors if hasattr(formset, 'errors') else 'No errors attr'}")
        logger.info(f"[UserAdmin] Formset non_form_errors: {formset.non_form_errors() if hasattr(formset, 'non_form_errors') else 'No non_form_errors attr'}")
        
        # Проверяем ошибки формсета перед сохранением
        if hasattr(formset, 'errors') and formset.errors:
            logger.error(f"[UserAdmin] Formset has errors: {formset.errors}")
        if hasattr(formset, 'non_form_errors') and formset.non_form_errors():
            logger.error(f"[UserAdmin] Formset has non_form_errors: {formset.non_form_errors()}")
        
        # Убеждаемся что основной объект сохранен
        if form.instance and not form.instance.pk:
            logger.warning(f"[UserAdmin] Main user not saved yet, saving now...")
            form.instance.save()
            logger.info(f"[UserAdmin] Main user saved with tg_id={form.instance.tg_id}")
        
        # Для UserCategory обрабатываем формы вручную через SQL
        if formset.model.__name__ == 'UserCategory':
            from django.db import connection
            
            # Удаляем объекты помеченные для удаления
            for obj in formset.deleted_objects:
                logger.info(f"[UserAdmin] Deleting UserCategory: {obj}")
                if obj.pk:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM user_categories WHERE id = %s", [obj.id])
            
            # Обрабатываем формы
            for form_idx, form_instance in enumerate(formset.forms):
                if form_instance.cleaned_data and not form_instance.cleaned_data.get('DELETE', False):
                    category = form_instance.cleaned_data.get('category')
                    if category:
                        category_id = category.id if hasattr(category, 'id') else category
                        form_id = form_instance.cleaned_data.get('id')
                        
                        if form_id:
                            # Обновляем существующую запись
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE user_categories 
                                    SET category_id = %s 
                                    WHERE id = %s AND user_id = %s
                                """, [category_id, form_id, form.instance.tg_id])
                            logger.info(f"[UserAdmin] Updated UserCategory id={form_id}")
                        else:
                            # Создаем новую запись
                            # Проверяем, не существует ли уже такая запись
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    SELECT COUNT(*) FROM user_categories 
                                    WHERE user_id = %s AND category_id = %s
                                """, [form.instance.tg_id, category_id])
                                exists = cursor.fetchone()[0] > 0
                                
                                if not exists:
                                    # Генерируем ID
                                    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM user_categories")
                                    new_id = cursor.fetchone()[0]
                                    
                                    # Вставляем новую запись
                                    from django.utils import timezone
                                    cursor.execute("""
                                        INSERT INTO user_categories (id, user_id, category_id, created_at)
                                        VALUES (%s, %s, %s, %s)
                                    """, [new_id, form.instance.tg_id, category_id, timezone.now()])
                                    logger.info(f"[UserAdmin] Created UserCategory id={new_id}")
                                else:
                                    logger.warning(f"[UserAdmin] UserCategory already exists, skipping")
        else:
            # Для других формсетов используем стандартную обработку
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            for instance in instances:
                if instance:
                    instance.save()
        
        # Сохраняем изменения в формсете (many-to-many поля)
        if hasattr(formset, 'save_m2m'):
            try:
                formset.save_m2m()
            except AttributeError:
                pass
    
    def activate_users(self, request, queryset):
        """Активировать выбранных пользователей"""
        from django.db import connection
        from django.utils import timezone
        
        for user in queryset:
            user.is_active = True
            user.updated_at = timezone.now()
            user.save()
        self.message_user(request, f"Активировано пользователей: {queryset.count()}")
    activate_users.short_description = 'Активировать выбранных пользователей'
    
    def deactivate_users(self, request, queryset):
        """Деактивировать выбранных пользователей"""
        from django.utils import timezone
        
        for user in queryset:
            user.is_active = False
            user.updated_at = timezone.now()
            user.save()
        self.message_user(request, f"Деактивировано пользователей: {queryset.count()}")
    deactivate_users.short_description = 'Деактивировать выбранных пользователей'
    
    def reset_balance(self, request, queryset):
        """Сбросить баланс выбранных пользователей"""
        from django.utils import timezone
        
        for user in queryset:
            user.balance = 0
            user.updated_at = timezone.now()
            user.save()
        self.message_user(request, f"Баланс сброшен для пользователей: {queryset.count()}")
    reset_balance.short_description = 'Сбросить баланс'


# ============================================================================
# CategoryTranslation Inline
# ============================================================================

class CategoryTranslationInline(admin.TabularInline):
    model = CategoryTranslation
    extra = 1
    fields = ['language', 'name']
    verbose_name = 'Перевод'
    verbose_name_plural = 'Переводы'
    
    def get_readonly_fields(self, request, obj=None):
        # Для новых объектов не делаем поля readonly
        if obj is None:
            return []
        return []
    
    def get_formset(self, request, obj=None, **kwargs):
        """Переопределяем формсет чтобы правильно обрабатывать сохранение"""
        logger.info(f"[CategoryTranslationInline] get_formset called, obj.pk={obj.pk if obj else None}")
        formset = super().get_formset(request, obj, **kwargs)
        
        # Сохраняем ссылку на оригинальный класс формы
        OriginalForm = formset.form
        
        class CustomCategoryTranslationForm(OriginalForm):
            """Кастомная форма для переводов категорий"""
            def save(self, commit=True):
                """Переопределяем сохранение формы"""
                logger.info(f"[CategoryTranslationForm] save called, commit={commit}, category_id={getattr(self.instance, 'category_id', None)}")
                # Если основная категория не сохранена, не сохраняем перевод
                if not hasattr(self.instance, 'category_id') or not self.instance.category_id:
                    logger.warning(f"[CategoryTranslationForm] category_id not set, returning instance without saving")
                    # Возвращаем экземпляр без сохранения
                    # Django попытается сохранить его позже, но мы перехватим это в save_formset
                    return self.instance
                logger.info(f"[CategoryTranslationForm] category_id set, saving normally")
                return super().save(commit=commit)
            
            def save_m2m(self):
                """Переопределяем save_m2m для совместимости с Django admin"""
                # Для CategoryTranslation нет many-to-many полей, поэтому метод пустой
                pass
        
        class CustomCategoryTranslationFormset(formset):
            form = CustomCategoryTranslationForm
            
            def save_new(self, form, commit=True):
                """Переопределяем сохранение новых объектов"""
                logger.info(f"[CategoryTranslationFormset] save_new called, commit={commit}, instance.pk={self.instance.pk if self.instance else None}")
                
                # Убеждаемся что основная категория сохранена
                if not self.instance or not self.instance.pk:
                    logger.warning(f"[CategoryTranslationFormset] Main category not saved, creating instance without saving")
                    # Создаем экземпляр, но НЕ сохраняем его
                    # Django попытается сохранить его позже, но мы перехватим это в форме
                    instance = form.save(commit=False)
                    # НЕ устанавливаем category_id и НЕ сохраняем
                    # Сохранение произойдет позже через save_formset в TaskCategoryAdmin
                    return instance
                
                # Устанавливаем category_id перед сохранением
                instance = form.save(commit=False)
                instance.category_id = self.instance.pk
                logger.info(f"[CategoryTranslationFormset] Setting category_id={instance.category_id}")
                if commit:
                    instance.save()
                    logger.info(f"[CategoryTranslationFormset] Translation saved with id={instance.id}")
                return instance
        
        return CustomCategoryTranslationFormset


# ============================================================================
# TaskCategory Admin
# ============================================================================

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    verbose_name = 'Категория заданий'
    verbose_name_plural = 'Категории заданий'
    list_display = ['id', 'get_name', 'slug', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['slug']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('slug', 'color', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
    inlines = [CategoryTranslationInline]
    actions = ['activate_categories', 'deactivate_categories']
    
    def get_readonly_fields(self, request, obj=None):
        """ID должен быть readonly только для существующих объектов"""
        readonly = ['created_at']
        if obj and obj.pk:
            readonly.append('id')
        return readonly
    
    def get_fieldsets(self, request, obj=None):
        """Динамически добавляем поле ID только для существующих объектов"""
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.pk:  # Если объект существует, добавляем ID
            # Преобразуем fieldsets в список для изменения
            fieldsets_list = list(fieldsets)
            # Обновляем первое полеset, добавляя ID в начало
            if fieldsets_list:
                main_info = dict(fieldsets_list[0][1])
                main_info['fields'] = ('id',) + main_info['fields']
                fieldsets_list[0] = (fieldsets_list[0][0], main_info)
            return tuple(fieldsets_list)
        return fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем форму чтобы ID не требовался для новых объектов"""
        form = super().get_form(request, obj, **kwargs)
        
        # Для новых объектов делаем поле id необязательным (если оно есть в форме)
        if obj is None and 'id' in form.base_fields:
            form.base_fields['id'].required = False
            form.base_fields['id'].widget.attrs['style'] = 'display:none;'
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение модели для правильной генерации ID"""
        logger.info(f"[TaskCategoryAdmin] save_model called, change={change}, obj.pk={obj.pk if obj else None}, obj.id={getattr(obj, 'id', None)}")
        from django.db import connection
        from django.utils import timezone
        
        # Если это новый объект и ID не задан, получаем следующий ID из БД
        if not change and not obj.id:
            logger.info(f"[TaskCategoryAdmin] Generating new ID for category")
            with connection.cursor() as cursor:
                # Получаем максимальный ID и увеличиваем на 1
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM task_categories")
                next_id = cursor.fetchone()[0]
                obj.id = next_id
                logger.info(f"[TaskCategoryAdmin] Generated ID: {obj.id}")
        
        # Устанавливаем created_at для новых объектов (так как managed=False, auto_now_add не работает)
        if not change and not obj.created_at:
            obj.created_at = timezone.now()
            logger.info(f"[TaskCategoryAdmin] Set created_at={obj.created_at}")
        
        # Сохраняем объект
        logger.info(f"[TaskCategoryAdmin] Saving category with id={obj.id}, slug={obj.slug}")
        obj.save()
        logger.info(f"[TaskCategoryAdmin] Category saved successfully with id={obj.id}")
    
    def response_add(self, request, obj, post_url_continue=None):
        """Переопределяем response_add чтобы сохранить переводы после создания категории"""
        response = super().response_add(request, obj, post_url_continue)
        # Переводы уже сохранены через save_formset, просто возвращаем ответ
        return response
    
    def save_related(self, request, form, formsets, change):
        """Переопределяем сохранение связанных объектов"""
        logger.info(f"[TaskCategoryAdmin] save_related called, change={change}, form.instance.pk={form.instance.pk if form.instance else None}")
        
        # Сначала сохраняем основную модель если она еще не сохранена
        if form.instance and not form.instance.pk:
            logger.warning(f"[TaskCategoryAdmin] Main category not saved yet, saving first...")
            # Генерируем ID и сохраняем объект
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM task_categories")
                next_id = cursor.fetchone()[0]
                form.instance.id = next_id
            form.instance.save()
            logger.info(f"[TaskCategoryAdmin] Main category saved with id={form.instance.id}")
        
        # Затем сохраняем все формсеты используя наш метод save_formset
        for formset in formsets:
            logger.info(f"[TaskCategoryAdmin] Calling save_formset for {formset.model.__name__}")
            self.save_formset(request, form, formset, change)
    
    def save_formset(self, request, form, formset, change):
        """Переопределяем сохранение формсета для правильной обработки связанных объектов"""
        logger.info(f"[TaskCategoryAdmin] save_formset called for {formset.model.__name__}, change={change}, form.instance.pk={form.instance.pk if form.instance else None}")
        
        # Убеждаемся что основной объект сохранен (на случай если save_related не был вызван)
        if form.instance and not form.instance.pk:
            logger.warning(f"[TaskCategoryAdmin] Main category not saved yet, saving now...")
            # Генерируем ID и сохраняем объект
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM task_categories")
                next_id = cursor.fetchone()[0]
                form.instance.id = next_id
            form.instance.save()
            logger.info(f"[TaskCategoryAdmin] Main category saved with id={form.instance.id}")
        
        instances = formset.save(commit=False)
        logger.info(f"[TaskCategoryAdmin] Got {len(instances)} instances from formset for {formset.model.__name__}")
        
        # Удаляем объекты помеченные для удаления
        for obj in formset.deleted_objects:
            logger.info(f"[TaskCategoryAdmin] Deleting object: {obj}")
            obj.delete()
        
        # Сохраняем новые и измененные объекты
        for idx, instance in enumerate(instances):
            # Пропускаем пустые формы
            if not instance:
                logger.warning(f"[TaskCategoryAdmin] Skipping empty instance #{idx} in {formset.model.__name__}")
                continue
            
            # Для CategoryTranslation проверяем обязательные поля
            if formset.model == CategoryTranslation:
                logger.info(f"[TaskCategoryAdmin] Processing CategoryTranslation instance #{idx}: {instance.name}")
                if not hasattr(instance, 'language_id') or not instance.language_id:
                    logger.warning(f"[TaskCategoryAdmin] Missing language_id for translation #{idx}, skipping")
                    continue
                if not hasattr(instance, 'name') or not instance.name or not instance.name.strip():
                    logger.warning(f"[TaskCategoryAdmin] Missing name for translation #{idx}, skipping")
                    continue
                
                # Убеждаемся что category установлен (для новых объектов)
                if not instance.category_id and form.instance.pk:
                    instance.category_id = form.instance.pk
                    logger.info(f"[TaskCategoryAdmin] Setting category_id={instance.category_id} for new translation #{idx}")
                
                # Проверяем что есть обязательные поля перед сохранением
                if instance.category_id and instance.language_id and instance.name:
                    try:
                        logger.info(f"[TaskCategoryAdmin] Saving CategoryTranslation #{idx}: {instance.name} for category {instance.category_id}")
                        instance.save()
                        logger.info(f"[TaskCategoryAdmin] CategoryTranslation #{idx} saved successfully with id={instance.id}")
                    except Exception as e:
                        logger.error(f"[TaskCategoryAdmin] Error saving category translation #{idx}: {e}", exc_info=True)
                        continue
                else:
                    logger.warning(f"[TaskCategoryAdmin] Missing required fields for CategoryTranslation #{idx}, skipping save. category_id={instance.category_id}, language_id={instance.language_id}, name={instance.name}")
        
        # Сохраняем изменения в формсете (many-to-many поля)
        # Для CategoryTranslation нет many-to-many полей, поэтому проверяем наличие метода
        if hasattr(formset, 'save_m2m'):
            try:
                formset.save_m2m()
                logger.info(f"[TaskCategoryAdmin] save_m2m called for {formset.model.__name__}")
            except AttributeError:
                # Если save_m2m не определен или не нужен, просто пропускаем
                logger.debug(f"[TaskCategoryAdmin] save_m2m not needed for {formset.model.__name__}")
                pass
    
    def get_name(self, obj):
        """Получаем название из перевода (русский)"""
        try:
            translation = obj.translations.filter(language__code='ru').first()
            if translation:
                return translation.name
        except:
            pass
        return obj.slug
    get_name.short_description = 'Название'
    
    def activate_categories(self, request, queryset):
        queryset.update(is_active=True)
    activate_categories.short_description = 'Активировать выбранные категории'
    
    def deactivate_categories(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_categories.short_description = 'Деактивировать выбранные категории'


# ============================================================================
# CategoryTranslation Admin
# ============================================================================

@admin.register(CategoryTranslation)
class CategoryTranslationAdmin(admin.ModelAdmin):
    verbose_name = 'Перевод категории'
    verbose_name_plural = 'Переводы категорий'
    list_display = ['category', 'language', 'name']
    list_filter = ['language', 'category']
    search_fields = ['name', 'category__slug']
    readonly_fields = ['id']


# ============================================================================
# TaskTranslation Inline
# ============================================================================

class TaskTranslationInline(admin.TabularInline):
    model = TaskTranslation
    extra = 1
    fields = ['language', 'title', 'description']
    verbose_name = 'Перевод'
    verbose_name_plural = 'Переводы'
    readonly_fields = []  # Убираем readonly для новых объектов
    
    def get_readonly_fields(self, request, obj=None):
        # Для новых объектов не делаем поля readonly
        if obj is None:
            return []
        return ['id'] if hasattr(obj, 'id') else []
    
    def get_formset(self, request, obj=None, **kwargs):
        """Переопределяем формсет для валидации"""
        formset = super().get_formset(request, obj, **kwargs)
        
        class CustomFormset(formset):
            def clean(self):
                """Валидация формсета"""
                if any(self.errors):
                    return
                
                # Проверяем что есть хотя бы один перевод
                translations = []
                languages_seen = set()
                
                for form in self.forms:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        language = form.cleaned_data.get('language')
                        title = form.cleaned_data.get('title', '').strip()
                        description = form.cleaned_data.get('description', '').strip()
                        
                        # Если заполнены все обязательные поля
                        if language and title and description:
                            # Проверяем на дубликаты языков
                            if language.id in languages_seen:
                                from django.core.exceptions import ValidationError
                                raise ValidationError(f'Перевод на язык "{language.name}" уже добавлен. Каждый язык может быть указан только один раз.')
                            languages_seen.add(language.id)
                            translations.append(form.cleaned_data)
                        # Если заполнена только часть полей - это ошибка
                        elif language or title or description:
                            from django.core.exceptions import ValidationError
                            raise ValidationError('Для перевода необходимо заполнить все поля: язык, заголовок и описание.')
                
                if not translations:
                    from django.core.exceptions import ValidationError
                    raise ValidationError('Необходимо добавить хотя бы один перевод (язык, заголовок и описание).')
        
        return CustomFormset


# ============================================================================
# TaskGenderTarget Inline
# ============================================================================

class TaskGenderTargetInline(admin.TabularInline):
    model = TaskGenderTarget
    extra = 1
    fields = ['gender']
    verbose_name = 'Целевая аудитория'
    verbose_name_plural = 'Целевые аудитории'
    readonly_fields = []  # Убираем readonly для новых объектов
    
    def get_readonly_fields(self, request, obj=None):
        # Для новых объектов не делаем поля readonly
        if obj is None:
            return []
        return ['id'] if hasattr(obj, 'id') else []


# ============================================================================
# Task Admin
# ============================================================================

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    verbose_name = 'Задание'
    verbose_name_plural = 'Задания'
    list_display = ['id', 'get_title', 'category', 'get_gender_targets', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['id']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('category', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
    inlines = [TaskTranslationInline, TaskGenderTargetInline]
    actions = ['activate_tasks', 'deactivate_tasks']
    
    def get_readonly_fields(self, request, obj=None):
        """ID должен быть readonly только для существующих объектов"""
        readonly = ['created_at']
        if obj and obj.pk:
            readonly.append('id')
        return readonly
    
    def get_fieldsets(self, request, obj=None):
        """Динамически добавляем поле ID только для существующих объектов"""
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.pk:  # Если объект существует, добавляем ID
            # Преобразуем fieldsets в список для изменения
            fieldsets_list = list(fieldsets)
            # Обновляем первое полеset, добавляя ID в начало
            if fieldsets_list:
                main_info = dict(fieldsets_list[0][1])
                main_info['fields'] = ('id',) + main_info['fields']
                fieldsets_list[0] = (fieldsets_list[0][0], main_info)
            return tuple(fieldsets_list)
        return fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем форму чтобы ID не требовался для новых объектов"""
        form = super().get_form(request, obj, **kwargs)
        
        # Для новых объектов делаем поле id необязательным (если оно есть в форме)
        if obj is None and 'id' in form.base_fields:
            form.base_fields['id'].required = False
            form.base_fields['id'].widget.attrs['style'] = 'display:none;'
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение модели для правильной генерации ID"""
        from django.db import connection
        from django.utils import timezone
        
        # Если это новый объект и ID не задан, получаем следующий ID из БД
        if not change and not obj.id:
            with connection.cursor() as cursor:
                # Получаем максимальный ID и увеличиваем на 1
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM tasks")
                next_id = cursor.fetchone()[0]
                obj.id = next_id
        
        # Устанавливаем created_at для новых объектов (так как managed=False, auto_now_add не работает)
        if not change and not obj.created_at:
            obj.created_at = timezone.now()
        
        # Сохраняем объект
        obj.save()
        
        # После сохранения пытаемся автоматически перевести задание
        # Используем транзакцию Django для гарантии что данные сохранены
        from django.db import transaction
        transaction.on_commit(lambda: self._auto_translate_task(obj))
    
    def save_formset(self, request, form, formset, change):
        """Переопределяем сохранение формсета для правильной обработки связанных объектов"""
        # Убеждаемся что основной объект сохранен
        if form.instance and not form.instance.pk:
            form.instance.save()
        
        instances = formset.save(commit=False)
        
        # Удаляем объекты помеченные для удаления
        for obj in formset.deleted_objects:
            obj.delete()
        
        # Сохраняем новые и измененные объекты
        for instance in instances:
            # Пропускаем пустые формы
            if not instance:
                continue
            
            # Для TaskTranslation проверяем обязательные поля
            if formset.model == TaskTranslation:
                if not hasattr(instance, 'language_id') or not instance.language_id:
                    continue
                if not hasattr(instance, 'title') or not instance.title or not instance.title.strip():
                    continue
                if not hasattr(instance, 'description') or not instance.description or not instance.description.strip():
                    continue
                
                # Убеждаемся что task установлен (для новых объектов)
                if not instance.task_id and form.instance.pk:
                    instance.task_id = form.instance.pk
                
                # Проверяем что есть обязательные поля перед сохранением
                if instance.task_id and instance.language_id and instance.title:
                    try:
                        instance.save()
                    except Exception as e:
                        print(f"[Admin] Error saving translation: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            # Для TaskGenderTarget проверяем обязательные поля
            elif formset.model == TaskGenderTarget:
                if not hasattr(instance, 'gender') or not instance.gender:
                    continue
                
                # Убеждаемся что task установлен (для новых объектов)
                if not instance.task_id and form.instance.pk:
                    instance.task_id = form.instance.pk
                
                # Сохраняем если есть обязательные поля
                if instance.task_id and instance.gender:
                    try:
                        instance.save()
                    except Exception as e:
                        print(f"[Admin] Error saving gender target: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            # Для других моделей просто сохраняем
            else:
                if not instance.task_id and form.instance.pk:
                    instance.task_id = form.instance.pk
                if instance.task_id:
                    try:
                        instance.save()
                    except Exception as e:
                        print(f"[Admin] Error saving {formset.model.__name__}: {e}")
                        continue
        
        # Сохраняем изменения в формсете
        formset.save_m2m()
        
        # После сохранения переводов пытаемся автоматически перевести задание
        # если это был формсет с переводами
        if formset.model == TaskTranslation and form.instance.pk:
            # Выполняем перевод сразу после сохранения формсета
            # Используем транзакцию Django для гарантии что данные сохранены
            from django.db import transaction
            # Сохраняем ссылку на объект чтобы избежать проблем с замыканием
            task_id = form.instance.id
            def translate_after_commit():
                try:
                    # Получаем свежий объект из БД
                    from .models import Task
                    task = Task.objects.get(pk=task_id)
                    self._auto_translate_task(task)
                except Exception as e:
                    print(f"[Admin] Ошибка при получении задания для перевода: {e}")
            transaction.on_commit(translate_after_commit)
    
    def get_title(self, obj):
        """Получаем заголовок из перевода (русский)"""
        try:
            translation = obj.translations.filter(language__code='ru').first()
            if translation:
                return translation.title
        except:
            pass
        return f"Task #{obj.id}"
    get_title.short_description = 'Заголовок'
    
    def get_gender_targets(self, obj):
        targets = obj.gender_targets.all()
        if targets:
            return ', '.join([t.get_gender_display() for t in targets])
        return 'Не указано'
    get_gender_targets.short_description = 'Для кого'
    
    def activate_tasks(self, request, queryset):
        queryset.update(is_active=True)
    activate_tasks.short_description = 'Активировать выбранные задания'
    
    def deactivate_tasks(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_tasks.short_description = 'Деактивировать выбранные задания'
    
    def _auto_translate_task(self, task):
        """Автоматический перевод задания на другие языки"""
        try:
            # Импортируем сервис перевода из бэкенда
            import sys
            import os
            import time
            backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'backend')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from app.services.translation_service import TranslationService
            from app.core.database import SessionLocal
            
            # Обновляем объект из БД чтобы убедиться что он сохранен
            task.refresh_from_db()
            
            # Получаем русский перевод через Django ORM
            ru_translation = task.translations.filter(language__code='ru').first()
            if not ru_translation:
                print(f"[Admin] Нет русского перевода для задания #{task.id}")
                return  # Нет русского перевода - не переводим
            
            # Проверяем есть ли уже переводы на другие языки
            en_translation = task.translations.filter(language__code='en').first()
            es_translation = task.translations.filter(language__code='es').first()
            
            # Если есть все переводы - не переводим
            if en_translation and es_translation:
                print(f"[Admin] Все переводы уже существуют для задания #{task.id}")
                return
            
            # Небольшая задержка чтобы убедиться что данные сохранены в БД
            time.sleep(0.2)
            
            # Используем сервис перевода из бэкенда
            db = SessionLocal()
            try:
                # Проверяем что задание существует в БД бэкенда
                from app.models.task import Task as BackendTask
                from app.core.config import settings as backend_settings
                print(f"[Admin] Проверяю задание #{task.id} в БД бэкенда (путь: {backend_settings.DATABASE_PATH})")
                
                backend_task = db.query(BackendTask).filter(BackendTask.id == task.id).first()
                if not backend_task:
                    print(f"[Admin] Задание #{task.id} не найдено в БД бэкенда")
                    # Пробуем найти все задания для диагностики
                    all_tasks = db.query(BackendTask).limit(5).all()
                    print(f"[Admin] Найдено заданий в БД бэкенда: {[t.id for t in all_tasks]}")
                    return
                
                print(f"[Admin] Задание #{task.id} найдено в БД бэкенда, начинаю перевод...")
                translation_service = TranslationService()
                translation_service.translate_task(db, task.id, source_lang='ru')
                print(f"[Admin] Автоматически переведено задание #{task.id}")
                
                # Обновляем объект Django чтобы увидеть новые переводы
                task.refresh_from_db()
            except Exception as e:
                print(f"[Admin] Ошибка автоматического перевода задания {task.id}: {e}")
                import traceback
                traceback.print_exc()
                # Не критично - можно добавить переводы вручную
            finally:
                db.close()
        except ImportError as e:
            # Если не удалось импортировать модули бэкенда - это нормально
            # Пользователь может добавить переводы вручную
            print(f"[Admin] Не удалось импортировать модули бэкенда: {e}")
        except Exception as e:
            # Другие ошибки - логируем но не прерываем работу
            print(f"[Admin] Не удалось выполнить автоматический перевод: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# TaskTranslation Admin
# ============================================================================

@admin.register(TaskTranslation)
class TaskTranslationAdmin(admin.ModelAdmin):
    verbose_name = 'Перевод задания'
    verbose_name_plural = 'Переводы заданий'
    list_display = ['task', 'language', 'title']
    list_filter = ['language', 'task__category']
    search_fields = ['title', 'description', 'task__id']
    readonly_fields = ['id']


# ============================================================================
# TaskGenderTarget Admin
# ============================================================================

@admin.register(TaskGenderTarget)
class TaskGenderTargetAdmin(admin.ModelAdmin):
    verbose_name = 'Целевая аудитория задания'
    verbose_name_plural = 'Целевые аудитории заданий'
    list_display = ['task', 'gender']
    list_filter = ['gender']
    search_fields = ['task__id']


# ============================================================================
# CompletedTask Admin
# ============================================================================

@admin.register(CompletedTask)
class CompletedTaskAdmin(admin.ModelAdmin):
    verbose_name = 'Выполненное задание'
    verbose_name_plural = 'Выполненные задания'
    list_display = ['user', 'task', 'completed_at']
    list_filter = ['completed_at', 'task__category']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'task__id']
    readonly_fields = ['id', 'completed_at']
    date_hierarchy = 'completed_at'


# ============================================================================
# DailyFreeTask Admin
# ============================================================================

@admin.register(DailyFreeTask)
class DailyFreeTaskAdmin(admin.ModelAdmin):
    verbose_name = 'Ежедневное бесплатное задание'
    verbose_name_plural = 'Ежедневные бесплатные задания'
    list_display = ['user', 'date', 'count', 'last_reset']
    list_filter = ['date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'last_reset']
    date_hierarchy = 'date'
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'date', 'count')
        }),
        ('Даты', {
            'fields': ('last_reset',)
        }),
    )


# ============================================================================
# DailyBonus Admin
# ============================================================================

@admin.register(DailyBonus)
class DailyBonusAdmin(admin.ModelAdmin):
    verbose_name = 'Ежедневный бонус'
    verbose_name_plural = 'Ежедневные бонусы'
    list_display = ['user', 'day_number', 'bonus_amount', 'date', 'claimed_at']
    list_filter = ['day_number', 'date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'claimed_at']
    date_hierarchy = 'date'
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'day_number', 'bonus_amount', 'date')
        }),
        ('Даты', {
            'fields': ('claimed_at',)
        }),
    )


# ============================================================================
# Transaction Admin
# ============================================================================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    verbose_name = 'Транзакция'
    verbose_name_plural = 'Транзакции'
    list_display = ['user', 'amount', 'transaction_type', 'status', 'payment_method', 'get_ton_info', 'created_at']
    list_filter = ['transaction_type', 'status', 'payment_method', 'created_at']
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'yookassa_payment_id', 'ton_transaction_hash', 'description'
    ]
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'amount', 'transaction_type', 'status')
        }),
        ('Оплата', {
            'fields': ('payment_method', 'yookassa_payment_id')
        }),
        ('TON платеж', {
            'fields': ('ton_transaction_hash', 'ton_from_address', 'ton_to_address', 'ton_amount'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('description', 'created_at')
        }),
    )
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_refunded']
    
    def get_ton_info(self, obj):
        """Показываем информацию о TON платеже"""
        if obj.ton_transaction_hash:
            return f"TON: {obj.ton_transaction_hash[:16]}..."
        return '-'
    get_ton_info.short_description = 'TON платеж'
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = 'Отметить как завершенные'
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
    mark_as_failed.short_description = 'Отметить как неудачные'
    
    def mark_as_refunded(self, request, queryset):
        queryset.update(status='refunded')
    mark_as_refunded.short_description = 'Отметить как возвращенные'


# ============================================================================
# UserCategory Admin
# ============================================================================

@admin.register(UserCategory)
class UserCategoryAdmin(admin.ModelAdmin):
    verbose_name = 'Интерес пользователя'
    verbose_name_plural = 'Интересы пользователей'
    list_display = ['user', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'category__slug']
    readonly_fields = ['id', 'created_at']
