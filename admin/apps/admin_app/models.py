from django.db import models
import logging

# Настраиваем logger для отладки
logger = logging.getLogger(__name__)


# ============================================================================
# Language - Языки
# ============================================================================

class Language(models.Model):
    """Модель языка"""
    id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=10, unique=True, db_index=True, verbose_name='Код языка')
    name = models.CharField(max_length=100, verbose_name='Название')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'languages'
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'
        managed = False  # Не управляем миграциями через Django
    
    def __str__(self):
        return f"{self.name} ({self.code})"


# ============================================================================
# User - Пользователи
# ============================================================================

class User(models.Model):
    """Модель пользователя Telegram"""
    GENDER_CHOICES = [
        ('male', 'Мужчина'),
        ('female', 'Женщина'),
        ('couple', 'Пара'),
    ]
    
    tg_id = models.BigIntegerField(primary_key=True, db_index=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=255, null=True, blank=True, db_index=True, verbose_name='Username')
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Фамилия')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='Тип аккаунта')
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        db_column='language_id',
        related_name='users',
        verbose_name='Язык'
    )
    password = models.CharField(max_length=255, null=True, blank=True, verbose_name='Пароль (хеш)')
    is_admin = models.BooleanField(default=False, verbose_name='Администратор')
    balance = models.IntegerField(default=0, verbose_name='Баланс')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    wallet_address = models.CharField(
        max_length=48,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        verbose_name='TON адрес кошелька'
    )
    has_lifetime_subscription = models.BooleanField(
        default=False,
        verbose_name='Lifetime подписка'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
        managed = False
    
    def save(self, *args, **kwargs):
        """Переопределяем save для сохранения через прямой SQL (так как managed=False)"""
        from django.db import connection
        from django.utils import timezone
        
        if not self.tg_id:
            raise ValueError("Cannot save User: tg_id is not set")
        
        # Убеждаемся, что language_id установлен из ForeignKey поля language
        if self.language and not self.language_id:
            self.language_id = self.language.id
        elif not self.language_id:
            raise ValueError("Cannot save User: language_id is not set")
        
        # Устанавливаем created_at и updated_at
        now = timezone.now()
        if not self.pk and not self.created_at:
            self.created_at = now
        self.updated_at = now
        
        # Сохраняем через прямой SQL
        with connection.cursor() as cursor:
            # Проверяем, существует ли запись с таким tg_id
            cursor.execute("SELECT COUNT(*) FROM users WHERE tg_id = %s", [self.tg_id])
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # UPDATE
                cursor.execute("""
                    UPDATE users 
                    SET username = %s, first_name = %s, last_name = %s, gender = %s,
                        language_id = %s, password = %s, is_admin = %s, balance = %s,
                        is_active = %s, wallet_address = %s, has_lifetime_subscription = %s,
                        created_at = %s, updated_at = %s
                    WHERE tg_id = %s
                """, [
                    self.username, self.first_name, self.last_name, self.gender,
                    self.language_id, self.password, 1 if self.is_admin else 0, self.balance,
                    1 if self.is_active else 0, self.wallet_address, 1 if self.has_lifetime_subscription else 0,
                    self.created_at, self.updated_at, self.tg_id
                ])
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO users (tg_id, username, first_name, last_name, gender, language_id,
                                     password, is_admin, balance, is_active, wallet_address,
                                     has_lifetime_subscription, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    self.tg_id, self.username, self.first_name, self.last_name, self.gender, self.language_id,
                    self.password, 1 if self.is_admin else 0, self.balance, 1 if self.is_active else 0,
                    self.wallet_address, 1 if self.has_lifetime_subscription else 0,
                    self.created_at, self.updated_at
                ])
                self.pk = self.tg_id
    
    def refresh_from_db(self, using=None, fields=None):
        """Переопределяем refresh_from_db для моделей с managed=False"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tg_id, username, first_name, last_name, gender, language_id, password,
                       is_admin, balance, is_active, wallet_address, has_lifetime_subscription,
                       created_at, updated_at
                FROM users WHERE tg_id = %s
            """, [self.tg_id])
            row = cursor.fetchone()
            if row:
                self.tg_id = row[0]
                self.username = row[1]
                self.first_name = row[2]
                self.last_name = row[3]
                self.gender = row[4]
                self.language_id = row[5]
                self.password = row[6]
                self.is_admin = bool(row[7])
                self.balance = row[8]
                self.is_active = bool(row[9])
                self.wallet_address = row[10]
                self.has_lifetime_subscription = bool(row[11])
                self.created_at = row[12]
                self.updated_at = row[13]
                self.pk = self.tg_id
    
    def __str__(self):
        name = f"{self.first_name} {self.last_name or ''}".strip()
        return f"{name} (@{self.username or 'без username'})"


# ============================================================================
# TaskCategory - Категории заданий
# ============================================================================

class TaskCategory(models.Model):
    """Модель категории заданий (интересы)"""
    id = models.IntegerField(primary_key=True)
    slug = models.CharField(max_length=100, unique=True, db_index=True, verbose_name='URL-слаг')
    color = models.CharField(max_length=7, verbose_name='Цвет (HEX)')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'task_categories'
        verbose_name = 'Категория заданий'
        verbose_name_plural = 'Категории заданий'
        ordering = ['slug']
        managed = False
    
    def save(self, *args, **kwargs):
        """Переопределяем save для сохранения через прямой SQL (так как managed=False)"""
        from django.db import connection
        from django.utils import timezone
        
        # Генерируем ID если его нет
        if not self.pk and not self.id:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM task_categories")
                next_id = cursor.fetchone()[0]
                self.id = next_id
        
        # Устанавливаем created_at для новых объектов
        if not self.pk and not self.created_at:
            self.created_at = timezone.now()
        
        # Сохраняем через прямой SQL
        if not self.id:
            raise ValueError("Cannot save TaskCategory: id is not set")
        
        with connection.cursor() as cursor:
            # Проверяем, существует ли запись с таким ID
            cursor.execute("SELECT COUNT(*) FROM task_categories WHERE id = %s", [self.id])
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # UPDATE
                cursor.execute("""
                    UPDATE task_categories 
                    SET slug = %s, color = %s, is_active = %s, created_at = %s
                    WHERE id = %s
                """, [self.slug, self.color, 1 if self.is_active else 0, self.created_at, self.id])
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO task_categories (id, slug, color, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, [self.id, self.slug, self.color, 1 if self.is_active else 0, self.created_at])
                self.pk = self.id
    
    def refresh_from_db(self, using=None, fields=None):
        """Переопределяем refresh_from_db для моделей с managed=False"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, slug, color, is_active, created_at FROM task_categories WHERE id = %s", [self.id])
            row = cursor.fetchone()
            if row:
                self.id = row[0]
                self.slug = row[1]
                self.color = row[2]
                self.is_active = bool(row[3])
                self.created_at = row[4]
                self.pk = self.id
    
    def __str__(self):
        # Получаем перевод для отображения (если есть)
        try:
            translation = self.translations.filter(language__code='ru').first()
            if translation:
                return translation.name
        except:
            pass
        return self.slug


# ============================================================================
# CategoryTranslation - Переводы категорий
# ============================================================================

class CategoryTranslation(models.Model):
    """Модель перевода категории"""
    id = models.IntegerField(primary_key=True)
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.CASCADE,
        db_column='category_id',
        related_name='translations',
        verbose_name='Категория'
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        db_column='language_id',
        related_name='category_translations',
        verbose_name='Язык'
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    
    class Meta:
        db_table = 'category_translations'
        verbose_name = 'Перевод категории'
        verbose_name_plural = 'Переводы категорий'
        unique_together = [['category', 'language']]
        managed = False
    
    def save(self, *args, **kwargs):
        """Переопределяем save чтобы обработать случай когда category еще не сохранена"""
        logger.info(f"[CategoryTranslation Model] save called for {self.name}, category_id={getattr(self, 'category_id', None)}, pk={self.pk}")
        from django.db import connection
        
        # Если category_id не установлен, но есть category объект - используем его ID
        if not self.category_id and self.category and self.category.pk:
            self.category_id = self.category.pk
            logger.info(f"[CategoryTranslation Model] Set category_id from category.pk: {self.category_id}")
        
        # Если category_id все еще не установлен - это ошибка, но не падаем
        # Django admin должен установить его через save_formset
        if not self.category_id:
            logger.warning(f"[CategoryTranslation Model] WARNING: category_id not set, skipping save for {self.name}")
            # Не сохраняем, если category_id не установлен
            # Django admin должен установить его позже
            return
        
        # Генерируем ID если его нет
        if not self.pk and not self.id:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM category_translations")
                next_id = cursor.fetchone()[0]
                self.id = next_id
            logger.info(f"[CategoryTranslation Model] Generated new ID: {self.id}")
        
        # Сохраняем через прямой SQL (так как managed=False)
        with connection.cursor() as cursor:
            # Проверяем, существует ли запись с таким ID
            cursor.execute("SELECT COUNT(*) FROM category_translations WHERE id = %s", [self.id])
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # UPDATE
                cursor.execute("""
                    UPDATE category_translations 
                    SET category_id = %s, language_id = %s, name = %s
                    WHERE id = %s
                """, [self.category_id, self.language_id, self.name, self.id])
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO category_translations (id, category_id, language_id, name)
                    VALUES (%s, %s, %s, %s)
                """, [self.id, self.category_id, self.language_id, self.name])
                self.pk = self.id
        
        logger.info(f"[CategoryTranslation Model] Successfully saved {self.name} with id={self.id}")
    
    def __str__(self):
        return f"{self.category.slug} ({self.language.code}): {self.name}"


# ============================================================================
# Task - Задания
# ============================================================================

class Task(models.Model):
    """Модель задания"""
    id = models.IntegerField(primary_key=True)
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.CASCADE,
        db_column='category_id',
        related_name='tasks',
        verbose_name='Категория'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['-created_at']
        managed = False
    
    def save(self, *args, **kwargs):
        """Переопределяем save для сохранения через прямой SQL (так как managed=False)"""
        from django.db import connection
        from django.utils import timezone
        
        # Генерируем ID если его нет
        if not self.pk and not self.id:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM tasks")
                next_id = cursor.fetchone()[0]
                self.id = next_id
        
        # Устанавливаем created_at для новых объектов
        if not self.pk and not self.created_at:
            self.created_at = timezone.now()
        
        # Сохраняем через прямой SQL
        if not self.id:
            raise ValueError("Cannot save Task: id is not set")
        
        if not self.category_id:
            raise ValueError("Cannot save Task: category_id is not set")
        
        with connection.cursor() as cursor:
            # Проверяем, существует ли запись с таким ID
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE id = %s", [self.id])
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # UPDATE
                cursor.execute("""
                    UPDATE tasks 
                    SET category_id = %s, is_active = %s, created_at = %s
                    WHERE id = %s
                """, [self.category_id, 1 if self.is_active else 0, self.created_at, self.id])
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO tasks (id, category_id, is_active, created_at)
                    VALUES (%s, %s, %s, %s)
                """, [self.id, self.category_id, 1 if self.is_active else 0, self.created_at])
                self.pk = self.id
    
    def __str__(self):
        # Получаем перевод для отображения (если есть)
        try:
            translation = self.translations.filter(language__code='ru').first()
            if translation:
                return translation.title
        except:
            pass
        return f"Task #{self.id}"


# ============================================================================
# TaskTranslation - Переводы заданий
# ============================================================================

class TaskTranslation(models.Model):
    """Модель перевода задания"""
    id = models.IntegerField(primary_key=True)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        db_column='task_id',
        related_name='translations',
        verbose_name='Задание'
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        db_column='language_id',
        related_name='task_translations',
        verbose_name='Язык'
    )
    title = models.CharField(max_length=500, verbose_name='Заголовок', blank=False)
    description = models.CharField(max_length=2000, verbose_name='Описание', blank=False)
    
    class Meta:
        db_table = 'task_translations'
        verbose_name = 'Перевод задания'
        verbose_name_plural = 'Переводы заданий'
        unique_together = [['task', 'language']]
        managed = False
    
    def save(self, *args, **kwargs):
        """Переопределяем save для правильной генерации ID"""
        from django.db import connection
        
        # Если это новый объект и ID не задан, получаем следующий ID из БД
        if not self.pk:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM task_translations")
                next_id = cursor.fetchone()[0]
                self.id = next_id
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.task.id} ({self.language.code}): {self.title}"


# ============================================================================
# TaskGenderTarget - Целевая аудитория заданий
# ============================================================================

class TaskGenderTarget(models.Model):
    """Промежуточная модель для связи Task с gender_target"""
    GENDER_TARGET_CHOICES = [
        ('male', 'Мужчина'),
        ('female', 'Женщина'),
        ('couple', 'Пара'),
        ('all', 'Все'),
    ]
    
    id = models.IntegerField(primary_key=True)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        db_column='task_id',
        related_name='gender_targets',
        verbose_name='Задание'
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_TARGET_CHOICES,
        db_column='gender',
        verbose_name='Для кого'
    )
    
    class Meta:
        db_table = 'task_gender_targets'
        verbose_name = 'Целевая аудитория задания'
        verbose_name_plural = 'Целевые аудитории заданий'
        unique_together = [['task', 'gender']]
        managed = False
    
    def save(self, *args, **kwargs):
        """Переопределяем save для правильной генерации ID"""
        from django.db import connection
        
        # Если это новый объект и ID не задан, получаем следующий ID из БД
        if not self.pk:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM task_gender_targets")
                next_id = cursor.fetchone()[0]
                self.id = next_id
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        try:
            task_title = self.task.translations.filter(language__code='ru').first()
            if task_title:
                return f"{task_title.title} - {self.get_gender_display()}"
        except:
            pass
        return f"Task #{self.task.id} - {self.get_gender_display()}"


# ============================================================================
# CompletedTask - Выполненные задания
# ============================================================================

class CompletedTask(models.Model):
    """Модель выполненного задания"""
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='tg_id',
        related_name='completed_tasks',
        verbose_name='Пользователь'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        db_column='task_id',
        related_name='completed_by',
        verbose_name='Задание'
    )
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата выполнения')
    
    class Meta:
        db_table = 'completed_tasks'
        verbose_name = 'Выполненное задание'
        verbose_name_plural = 'Выполненные задания'
        ordering = ['-completed_at']
        unique_together = [['user', 'task']]
        managed = False
    
    def __str__(self):
        try:
            task_title = self.task.translations.filter(language__code='ru').first()
            if task_title:
                return f"{self.user.first_name} - {task_title.title}"
        except:
            pass
        return f"{self.user.first_name} - Task #{self.task.id}"


# ============================================================================
# DailyFreeTask - Ежедневные бесплатные задания
# ============================================================================

class DailyFreeTask(models.Model):
    """Модель ежедневного бесплатного задания (счетчик)"""
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='tg_id',
        related_name='daily_free_tasks',
        verbose_name='Пользователь'
    )
    date = models.DateField(verbose_name='Дата')
    count = models.IntegerField(default=0, verbose_name='Количество (макс 3)')
    paid_available = models.IntegerField(default=0, verbose_name='Купленные задания на день')
    last_reset = models.DateTimeField(auto_now=True, verbose_name='Последний сброс')
    
    class Meta:
        db_table = 'daily_free_tasks'
        verbose_name = 'Ежедневное бесплатное задание'
        verbose_name_plural = 'Ежедневные бесплатные задания'
        unique_together = [['user', 'date']]
        managed = False
    
    def __str__(self):
        return f"{self.user.first_name} - {self.date} ({self.count}/3)"


# ============================================================================
# DailyBonus - Ежедневные бонусы
# ============================================================================

class DailyBonus(models.Model):
    """Модель ежедневного бонуса"""
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='tg_id',
        related_name='daily_bonuses',
        verbose_name='Пользователь'
    )
    day_number = models.IntegerField(verbose_name='День (1-7)')
    bonus_amount = models.IntegerField(verbose_name='Сумма бонуса')
    claimed_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата получения')
    date = models.DateField(verbose_name='Дата')
    
    class Meta:
        db_table = 'daily_bonuses'
        verbose_name = 'Ежедневный бонус'
        verbose_name_plural = 'Ежедневные бонусы'
        unique_together = [['user', 'date']]
        managed = False
    
    def __str__(self):
        return f"{self.user.first_name} - День {self.day_number} ({self.date})"


# ============================================================================
# Transaction - Транзакции
# ============================================================================

class Transaction(models.Model):
    """Модель транзакции"""
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Покупка'),
        ('task_payment', 'Оплата задания'),
        ('bonus', 'Бонус'),
        ('refund', 'Возврат'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('ton', 'TON'),
        ('daily_bonus', 'Ежедневный бонус'),
        ('system', 'Система'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('completed', 'Завершена'),
        ('failed', 'Неудачна'),
        ('refunded', 'Возвращена'),
    ]
    
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='tg_id',
        related_name='transactions',
        verbose_name='Пользователь'
    )
    amount = models.IntegerField(verbose_name='Сумма')
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Тип транзакции'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True,
        verbose_name='Способ оплаты'
    )
    yookassa_payment_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='ID платежа ЮKassa'
    )
    ton_transaction_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Хеш транзакции TON'
    )
    ton_from_address = models.CharField(
        max_length=48,
        null=True,
        blank=True,
        verbose_name='TON адрес отправителя'
    )
    ton_to_address = models.CharField(
        max_length=48,
        null=True,
        blank=True,
        verbose_name='TON адрес получателя'
    )
    ton_amount = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='TON сумма (nanotons)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    description = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Описание'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-created_at']
        managed = False
    
    def __str__(self):
        return f"{self.user.first_name} - {self.get_transaction_type_display()} ({self.amount})"


# ============================================================================
# UserCategory - Интересы пользователей
# ============================================================================

class UserCategory(models.Model):
    """Модель связи пользователя с категорией (интересы)"""
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        to_field='tg_id',
        related_name='interests',
        verbose_name='Пользователь'
    )
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.CASCADE,
        db_column='category_id',
        related_name='users',
        verbose_name='Категория'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        db_table = 'user_categories'
        verbose_name = 'Интерес пользователя'
        verbose_name_plural = 'Интересы пользователей'
        unique_together = [['user', 'category']]
        managed = False
    
    def save(self, *args, **kwargs):
        """Переопределяем save для сохранения через прямой SQL (так как managed=False)"""
        from django.db import connection
        from django.utils import timezone
        
        # Убеждаемся, что user_id установлен из ForeignKey
        if self.user and not self.user_id:
            self.user_id = self.user.tg_id if hasattr(self.user, 'tg_id') else self.user
        
        # Убеждаемся, что category_id установлен из ForeignKey
        if self.category and not self.category_id:
            self.category_id = self.category.id if hasattr(self.category, 'id') else self.category
        
        if not self.user_id:
            raise ValueError("Cannot save UserCategory: user_id is not set")
        if not self.category_id:
            raise ValueError("Cannot save UserCategory: category_id is not set")
        
        # Устанавливаем created_at для новых объектов
        if not self.pk and not self.created_at:
            self.created_at = timezone.now()
        
        # Генерируем ID если его нет
        if not self.pk and not self.id:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM user_categories")
                next_id = cursor.fetchone()[0]
                self.id = next_id
        
        # Сохраняем через прямой SQL
        with connection.cursor() as cursor:
            # Проверяем, существует ли запись с таким ID
            cursor.execute("SELECT COUNT(*) FROM user_categories WHERE id = %s", [self.id])
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # UPDATE
                cursor.execute("""
                    UPDATE user_categories 
                    SET user_id = %s, category_id = %s, created_at = %s
                    WHERE id = %s
                """, [self.user_id, self.category_id, self.created_at, self.id])
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO user_categories (id, user_id, category_id, created_at)
                    VALUES (%s, %s, %s, %s)
                """, [self.id, self.user_id, self.category_id, self.created_at])
                self.pk = self.id
    
    def __str__(self):
        try:
            translation = self.category.translations.filter(language__code='ru').first()
            if translation:
                return f"{self.user.first_name} - {translation.name}"
        except:
            pass
        return f"{self.user.first_name} - {self.category.slug}"
