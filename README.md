<div align="center">

# ⚡ Sparks

**Telegram Mini App для пар: короткие ежедневные задания, «искры» за прогресс и оплата в TON**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Django Admin](https://img.shields.io/badge/Django-Admin-092E20?style=for-the-badge&logo=django&logoColor=white)
![TON](https://img.shields.io/badge/TON-0098EA?style=for-the-badge&logo=ton&logoColor=white)

</div>

---

## 📖 О проекте

Sparks — Telegram Mini App про отношения: приложение выдаёт парам короткие задания (карточки), помогает регулярно проявлять заботу и внимание, показывает прогресс и баланс «искр». Бесплатных заданий в день ограниченное количество, дополнительные можно докупить за TON. Проект состоит из React-фронтенда, FastAPI-бэкенда, Django-админки и Telegram-бота.

<!-- TODO: скриншот -->

## ✨ Возможности

- 🃏 **Карточки заданий** — карусель с листанием вперёд/назад; после просмотра всех доступных заданий показывается offer-карточка покупки
- 🎯 **Онбординг** — выбор формата аккаунта и интересов (категорий), задания подбираются по аудитории (male / female / couple / all)
- 📆 **Дневной лимит** бесплатных заданий (сброс в 00:00 МСК) + купленные дополнительные
- 🎁 **Ежедневный бонус** — отдельная модалка со статусом и получением бонуса
- 💎 **Баланс «искр»** на сервере и покупка пакетов за TON, мониторинг незавершённых платежей раз в минуту
- 👛 **TON Connect + TON Proof** — привязка кошелька к уже существующему профилю (пользователь идентифицируется по Telegram ID; отвязка — `PATCH /auth/wallet/disconnect`)
- 🌍 **Локализация** ru / en / es, автоперевод заданий через MyMemory API
- 🛠 **Django Admin** — управление пользователями, балансом, заданиями, категориями, переводами
- 🤖 **Telegram-бот** — `/start` и кнопка «Начать», открывающая Mini App

## 🧱 Стек

| Слой | Технологии |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, react-i18next, @react-spring/web, TON Connect UI |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic Settings, APScheduler |
| Бот | python-telegram-bot 20.7 (запускается вместе с бэкендом) |
| БД | SQLite (путь задаётся `DATABASE_PATH`) |
| Админка | Django 4.2 (Django Admin) |
| Инфраструктура | Docker, Docker Compose, nginx (раздача фронтенда) |

## 🗂 Структура проекта

```text
.
├── backend/               # FastAPI-приложение
│   ├── app/
│   │   ├── api/v1/        # роутеры: auth, tasks, profile, categories, languages, payments, daily_bonus, admin
│   │   ├── models/        # SQLAlchemy-модели
│   │   ├── services/      # бизнес-логика: задания, TON-платежи, перевод, ежедневные бонусы
│   │   ├── bot.py         # Telegram-бот
│   │   └── main.py        # точка входа, планировщик задач
│   ├── alembic/           # миграции
│   └── scripts/           # seed_data, create_admin, reset_database и др.
├── frontend/              # React + Vite + Tailwind (src/components, hooks, locales: ru/en/es)
├── admin/                 # Django Admin (apps/admin_app, config)
├── docker-compose.yml     # прод-режим
├── docker-compose.dev.yml # dev-режим
└── run_server.py          # запуск backend из корня проекта
```

## 🚀 Быстрый старт

```bash
git clone https://github.com/Edvvard0/sparks.git
cd sparks
cp .env.example .env     # заполните значения (см. «Конфигурация»)

docker compose up -d --build
docker compose ps
```

Dev-режим (hot reload):

```bash
docker compose -f docker-compose.dev.yml up --build
```

| Сервис | Порт |
|---|---|
| Backend (Swagger: `/docs`) | `8000` |
| Frontend | `5173` |
| Django Admin (`/admin/`) | `8001` |

Логи: `docker compose logs -f backend` (аналогично `frontend`, `admin`).

<details>
<summary>Запуск без Docker (backend)</summary>

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_data.py                        # опционально: языки, категории, примеры заданий
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

## ⚙️ Конфигурация

Шаблоны: `.env.example`, `env.production.example`.

| Переменная | Назначение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather |
| `APP_URL` | URL Mini App для кнопки в боте |
| `ENABLE_TELEGRAM_BOT` | Включить/выключить автозапуск бота |
| `TON_WALLET_ADDRESS` | Кошелёк для приёма платежей |
| `TON_API_URL`, `TON_API_KEY` | TON API и ключ |
| `TON_NETWORK` | `mainnet` / `testnet` |
| `TON_SIMULATE_PAYMENTS` | Симуляция платежей (только для тестов) |
| `TON_MIN_AMOUNT_NANOTONS` | Минимальная сумма перевода |
| `MYMEMORY_API_KEY` | Ключ MyMemory (необязателен) |
| `DATABASE_PATH` | Путь к файлу SQLite |
| `TIMEZONE`, `API_V1_PREFIX` | Часовой пояс (`Europe/Moscow`) и префикс API (`/api/v1`) |
| `VITE_API_URL` | URL бэкенда для фронтенда |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` | Секрет и режим отладки Django-админки |

## 🔌 API

Префикс `/api/v1`. Пользователь определяется заголовком `X-Telegram-User-ID` (или `tg_id` в query), кошелёк — `X-Wallet-Address`.

<details>
<summary>Основные эндпоинты</summary>

| Группа | Эндпоинты |
|---|---|
| `/auth` | `POST /register`, `GET /me`, `GET /verify`, `POST /ton/connect`, `POST /ton-proof/generate`, `POST /ton-proof/check`, `PATCH /wallet/disconnect` |
| `/tasks` | `GET /`, `GET /daily-free-count`, `GET /{task_id}`, `POST /{task_id}/complete`, `POST /purchase-extra` |
| `/profile` | `GET /`, `PUT /`, `PUT /interests`, `PUT /language`, `GET /history` |
| `/payments` | `GET /balance`, `GET /packages`, `POST /ton/create`, `GET /ton/check/{transaction_id}` |
| `/daily-bonus` | `GET /status`, `POST /claim` |
| `/categories`, `/languages` | `GET /` |
| `/admin` | `POST /login` |
| — | `GET /health` |

</details>

Команда бота: `/start`.

## 👤 Автор

**Эдвард Осипчук** · GitHub: [@Edvvard0](https://github.com/Edvvard0) · Telegram: [@Edward0076](https://t.me/Edward0076)
