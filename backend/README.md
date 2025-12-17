# Sparks Backend API


FastAPI бэкенд для Telegram Mini App Sparks.

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example` и заполните настройки:
```bash
cp .env.example .env
```

4. Настройте PostgreSQL и создайте базу данных:
```sql
CREATE DATABASE sparks;
```

5. Настройте Alembic для миграций:
```bash
cd backend
alembic init alembic
```
Затем скопируйте содержимое из `alembic_env_template.py` в `alembic/env.py` и настройте `alembic.ini` (см. `ALEMBIC_SETUP.md`)

6. Создайте первую миграцию:
```bash
alembic revision --autogenerate -m "Initial migration"
```

7. Примените миграции:
```bash
alembic upgrade head
```

8. Заполните базу тестовыми данными (опционально):
```bash
python scripts/seed_data.py
```

## Запуск

### Вариант 1: Из директории backend/
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Вариант 2: Через скрипт из backend/
```bash
cd backend
python run.py
```

### Вариант 3: Из корневой директории проекта
```bash
python run_server.py
```

### Вариант 4: Через Python модуль (из backend/)
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Документация

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура проекта

```
backend/
├── app/
│   ├── api/
│   │   └── v1/          # API эндпоинты
│   ├── core/             # Конфигурация и зависимости
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Бизнес-логика
│   ├── utils/            # Утилиты
│   └── main.py           # Точка входа
├── alembic/              # Миграции БД
└── requirements.txt      # Зависимости
```

## Особенности

- Автоматический перевод заданий через MyMemory API
- Сброс бесплатных заданий в 00:00 МСК через APScheduler
- Аутентификация по tg_id (Telegram User ID)
- Интеграция с YooKassa для платежей

## Аутентификация

API использует простую аутентификацию по `tg_id`. Передавайте `tg_id` через заголовок `X-Telegram-User-ID` или query параметр `tg_id`.

Подробнее см. [API_AUTH.md](API_AUTH.md)

