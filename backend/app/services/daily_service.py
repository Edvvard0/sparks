from sqlalchemy.orm import Session
from datetime import date, datetime
import pytz
from app.models.daily import DailyFreeTask
from app.core.database import SessionLocal
from app.core.config import settings


def reset_daily_free_tasks():
    """
    Сброс счетчика бесплатных заданий для всех пользователей
    Запускается в 00:00 по МСК
    """
    db = SessionLocal()
    try:
        # Получаем текущую дату по МСК
        moscow_tz = pytz.timezone(settings.TIMEZONE)
        moscow_time = datetime.now(moscow_tz)
        today = moscow_time.date()
        
        # Сбрасываем счетчики для всех пользователей
        # Обновляем записи за сегодня или создаем новые
        daily_tasks = db.query(DailyFreeTask).filter(
            DailyFreeTask.date == today
        ).all()
        
        for daily_task in daily_tasks:
            daily_task.count = 0
            daily_task.last_reset = moscow_time
        
        # Для пользователей без записи на сегодня создаем новые
        # (это должно происходить при первом обращении, но на всякий случай)
        
        db.commit()
        print(f"Daily free tasks reset at {moscow_time} for {len(daily_tasks)} users")
    except Exception as e:
        db.rollback()
        print(f"Error resetting daily free tasks: {e}")
    finally:
        db.close()

