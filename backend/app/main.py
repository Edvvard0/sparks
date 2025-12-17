from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1 import auth, tasks, profile, categories, languages, payments, admin, daily_bonus
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz
from app.services.daily_service import reset_daily_free_tasks
from app.services.ton_service import TONService
from app.core.database import SessionLocal

app = FastAPI(
    title="Sparks API",
    description="API для Telegram Mini App Sparks",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix=settings.API_V1_PREFIX + "/auth", tags=["auth"])
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX + "/tasks", tags=["tasks"])
app.include_router(profile.router, prefix=settings.API_V1_PREFIX + "/profile", tags=["profile"])
app.include_router(categories.router, prefix=settings.API_V1_PREFIX + "/categories", tags=["categories"])
app.include_router(languages.router, prefix=settings.API_V1_PREFIX + "/languages", tags=["languages"])
app.include_router(payments.router, prefix=settings.API_V1_PREFIX + "/payments", tags=["payments"])
app.include_router(daily_bonus.router, prefix=settings.API_V1_PREFIX + "/daily-bonus", tags=["daily-bonus"])
app.include_router(admin.router, prefix=settings.API_V1_PREFIX + "/admin", tags=["admin"])


# Обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Настройка scheduled task для сброса бесплатных заданий
scheduler = AsyncIOScheduler()
moscow_tz = pytz.timezone(settings.TIMEZONE)

# Задача на 00:00 МСК каждый день
scheduler.add_job(
    reset_daily_free_tasks,
    trigger=CronTrigger(hour=0, minute=0, timezone=moscow_tz),
    id="reset_daily_free_tasks",
    name="Reset daily free tasks at 00:00 MSK",
    replace_existing=True
)

# Задача для периодической проверки pending TON платежей (каждые 60 секунд)
async def monitor_ton_payments():
    """Периодическая проверка pending TON платежей"""
    db = SessionLocal()
    try:
        await TONService.monitor_pending_payments(db)
    except Exception as e:
        print(f"Error monitoring TON payments: {e}")
    finally:
        db.close()

scheduler.add_job(
    monitor_ton_payments,
    trigger=IntervalTrigger(seconds=60),  # Проверка каждые 60 секунд
    id="monitor_ton_payments",
    name="Monitor pending TON payments",
    replace_existing=True
)


# Глобальная переменная для хранения экземпляра бота
bot_app_instance = None

@app.on_event("startup")
async def startup_event():
    """Запуск scheduled tasks при старте приложения"""
    global bot_app_instance
    
    scheduler.start()
    print("Scheduler started")
    
    # Логируем настройки TON для отладки
    print(f"[Config] TON_SIMULATE_PAYMENTS = {settings.TON_SIMULATE_PAYMENTS}")
    print(f"[Config] TON_NETWORK = {settings.TON_NETWORK}")
    if settings.TON_SIMULATE_PAYMENTS:
        print("[Config] ⚠️ PAYMENT SIMULATION MODE IS ENABLED - Transactions will be auto-confirmed!")
    
    # Запуск Telegram бота (если токен установлен и бот включен)
    if settings.TELEGRAM_BOT_TOKEN and settings.ENABLE_TELEGRAM_BOT:
        try:
            from app.bot import setup_bot
            bot_app_instance = setup_bot()
            if bot_app_instance:
                # Инициализируем и запускаем бота
                await bot_app_instance.initialize()
                await bot_app_instance.start()
                await bot_app_instance.updater.start_polling(drop_pending_updates=True)
                print("🤖 Telegram bot started")
        except Exception as e:
            print(f"⚠️ Failed to start Telegram bot: {e}")
            bot_app_instance = None
    elif settings.TELEGRAM_BOT_TOKEN and not settings.ENABLE_TELEGRAM_BOT:
        print("⚠️ Telegram bot disabled (ENABLE_TELEGRAM_BOT=False)")
    elif not settings.TELEGRAM_BOT_TOKEN:
        print("⚠️ Telegram bot token not set")


@app.on_event("shutdown")
async def shutdown_event():
    """Остановка scheduled tasks и бота при остановке приложения"""
    global bot_app_instance
    
    scheduler.shutdown()
    print("Scheduler stopped")
    
    # Остановка Telegram бота
    if bot_app_instance:
        try:
            await bot_app_instance.updater.stop()
            await bot_app_instance.stop()
            await bot_app_instance.shutdown()
            print("🤖 Telegram bot stopped")
        except Exception as e:
            print(f"⚠️ Error stopping Telegram bot: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

