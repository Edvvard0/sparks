# Настройка переменных окружения

Создайте файл `.env` в директории `backend/` на основе `.env.example` и заполните следующие переменные:

## Обязательные переменные

### База данных PostgreSQL
```env
POSTGRES_DB=sparks              # Название базы данных
POSTGRES_USER=postgres          # Пользователь PostgreSQL
POSTGRES_PASSWORD=postgres       # Пароль пользователя
POSTGRES_HOST=localhost          # Хост БД (localhost для локальной разработки)
POSTGRES_PORT=5432               # Порт PostgreSQL (по умолчанию 5432)
```

### Telegram Bot Token
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```
Получить токен можно у [@BotFather](https://t.me/BotFather) в Telegram.

## Опциональные переменные

### YooKassa (для платежей)
```env
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here
```
Эти данные можно получить в личном кабинете YooKassa после регистрации.

### MyMemory Translation API
```env
MYMEMORY_API_KEY=your_mymemory_api_key_here
```
API ключ можно получить на сайте [MyMemory](https://mymemory.translated.net/).

**Примечание:** MyMemory API может работать и без ключа, но с ограничениями (лимит символов в день).

### Часовой пояс
```env
TIMEZONE=Europe/Moscow
```
Используется для сброса бесплатных заданий в 00:00 МСК.

## Пример заполненного .env файла

```env
POSTGRES_DB=sparks
POSTGRES_USER=postgres
POSTGRES_PASSWORD=my_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

MYMEMORY_API_KEY=your_api_key_here

TIMEZONE=Europe/Moscow
```

## Важно

- **НЕ коммитьте файл `.env` в git!** Он должен быть в `.gitignore`
- Используйте разные значения для разработки и продакшена
- Храните секретные ключи в безопасности

