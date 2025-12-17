from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import pytz
from app.core.database import get_db
from app.core.dependencies import get_current_user_required as get_current_user
from app.core.config import settings
from app.schemas.daily_bonus import DailyBonusStatusResponse, DailyBonusClaimResponse
from app.models.user import User
from app.models.daily import DailyBonus
from app.models.transaction import Transaction, TransactionType, PaymentMethod

router = APIRouter()

# Бонусы по дням (1-7 день)
BONUS_AMOUNTS = {
    1: 10,
    2: 15,
    3: 20,
    4: 25,
    5: 30,
    6: 35,
    7: 40
}


def get_moscow_date() -> date:
    """Получить текущую дату по МСК"""
    moscow_tz = pytz.timezone(settings.TIMEZONE)
    moscow_time = datetime.now(moscow_tz)
    return moscow_time.date()


def get_next_reset_time() -> datetime:
    """Получить время следующего сброса (00:00 МСК следующего дня)"""
    moscow_tz = pytz.timezone(settings.TIMEZONE)
    moscow_time = datetime.now(moscow_tz)
    tomorrow = moscow_time.date() + timedelta(days=1)
    reset_time = moscow_tz.localize(datetime.combine(tomorrow, datetime.min.time()))
    return reset_time


def calculate_day_number(db: Session, user: User) -> int:
    """Вычислить номер дня для пользователя (1-7)"""
    today = get_moscow_date()
    
    # Получаем последний бонус пользователя
    last_bonus = db.query(DailyBonus).filter(
        DailyBonus.user_id == user.tg_id
    ).order_by(DailyBonus.date.desc()).first()
    
    if not last_bonus:
        # Первый бонус - день 1
        return 1
    
    # Проверяем, был ли бонус получен вчера
    yesterday = today - timedelta(days=1)
    
    if last_bonus.date == yesterday:
        # Бонус был получен вчера - увеличиваем день
        next_day = last_bonus.day_number + 1
        if next_day > 7:
            # После 7-го дня начинаем заново
            return 1
        return next_day
    elif last_bonus.date == today:
        # Бонус уже получен сегодня - возвращаем текущий день
        return last_bonus.day_number
    else:
        # Пропущен день - начинаем заново с дня 1
        return 1


@router.get("/status", response_model=DailyBonusStatusResponse)
async def get_daily_bonus_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статуса ежедневного бонуса"""
    today = get_moscow_date()
    
    # Проверяем, был ли бонус получен сегодня
    today_bonus = db.query(DailyBonus).filter(
        DailyBonus.user_id == user.tg_id,
        DailyBonus.date == today
    ).first()
    
    day_number = calculate_day_number(db, user)
    bonus_amount = BONUS_AMOUNTS.get(day_number, 10)
    is_claimed = today_bonus is not None
    can_claim = not is_claimed
    
    # Получаем список всех полученных дней для отображения галочек
    # Нужно получить все бонусы, которые были получены последовательно (без пропусков)
    all_bonuses = db.query(DailyBonus).filter(
        DailyBonus.user_id == user.tg_id
    ).order_by(DailyBonus.date.desc()).all()
    
    claimed_days = []
    if all_bonuses:
        yesterday = today - timedelta(days=1)
        last_bonus = all_bonuses[0]  # Самый последний бонус
        
        if last_bonus.date == yesterday:
            # Бонус был получен вчера - все дни до текущего пройдены
            # Получаем все последовательные дни до текущего
            claimed_days = list(range(1, day_number))
        elif last_bonus.date == today:
            # Бонус получен сегодня - все дни до текущего включительно пройдены
            claimed_days = list(range(1, day_number + 1))
        else:
            # Пропущен день - начинаем заново, пройденных дней нет
            claimed_days = []
    else:
        # Нет бонусов - пройденных дней нет
        claimed_days = []
    
    return DailyBonusStatusResponse(
        day_number=day_number,
        bonus_amount=bonus_amount,
        is_claimed=is_claimed,
        can_claim=can_claim,
        next_reset_at=get_next_reset_time(),
        claimed_days=claimed_days
    )


@router.post("/claim", response_model=DailyBonusClaimResponse)
async def claim_daily_bonus(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение ежедневного бонуса"""
    today = get_moscow_date()
    
    # Проверяем, был ли бонус уже получен сегодня
    today_bonus = db.query(DailyBonus).filter(
        DailyBonus.user_id == user.tg_id,
        DailyBonus.date == today
    ).first()
    
    if today_bonus:
        raise HTTPException(status_code=400, detail="Бонус уже получен сегодня")
    
    # Вычисляем номер дня
    day_number = calculate_day_number(db, user)
    bonus_amount = BONUS_AMOUNTS.get(day_number, 10)
    
    # Создаем запись о бонусе
    bonus = DailyBonus(
        user_id=user.tg_id,
        day_number=day_number,
        bonus_amount=bonus_amount,
        date=today
    )
    db.add(bonus)
    
    # Обновляем баланс пользователя
    user.balance += bonus_amount
    
    # Создаем транзакцию
    transaction = Transaction(
        user_id=user.tg_id,
        amount=bonus_amount,
        transaction_type=TransactionType.BONUS,
        payment_method=PaymentMethod.DAILY_BONUS
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(user)
    
    return DailyBonusClaimResponse(
        success=True,
        bonus_amount=bonus_amount,
        new_balance=user.balance,
        day_number=day_number
    )

