from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class DailyBonusStatusResponse(BaseModel):
    day_number: int  # 1-7
    bonus_amount: int  # Сумма бонуса
    is_claimed: bool  # Забран ли бонус сегодня
    can_claim: bool  # Можно ли забрать сейчас
    next_reset_at: datetime  # Время следующего сброса
    claimed_days: list[int] = []  # Список номеров дней, которые уже получены (для отображения галочек)


class DailyBonusClaimResponse(BaseModel):
    success: bool
    bonus_amount: int
    new_balance: int
    day_number: int

