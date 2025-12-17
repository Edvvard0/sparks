from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    DATABASE_PATH: str = "sparks.db"  # Путь к SQLite файлу
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    APP_URL: str = ""  # URL приложения для бота (например, https://your-app.com)
    ENABLE_TELEGRAM_BOT: bool = True  # Включить/выключить автозапуск бота (для локальной разработки можно установить False)
    
    # TON
    TON_WALLET_ADDRESS: str = ""  # Адрес кошелька для приема платежей
    TON_API_URL: str = "https://tonapi.io/v2"  # URL TON API
    TON_API_KEY: Optional[str] = None  # API ключ (если нужен)
    TON_NETWORK: str = "mainnet"  # mainnet или testnet
    TON_MIN_AMOUNT_NANOTONS: int = 100000000  # Минимальная сумма перевода в nanotons (0.1 TON)
    TON_SIMULATE_PAYMENTS: bool = False  # Симуляция платежей (для тестирования без реальных транзакций)
    
    # MyMemory Translation API
    MYMEMORY_API_KEY: Optional[str] = None
    
    # Timezone
    TIMEZONE: str = "Europe/Moscow"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    @field_validator('TON_SIMULATE_PAYMENTS', 'ENABLE_TELEGRAM_BOT', mode='before')
    @classmethod
    def parse_bool(cls, v):
        """Парсинг boolean значений из переменных окружения"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            # Убираем пробелы и приводим к нижнему регистру
            v_lower = v.strip().lower()
            # Проверяем только точное совпадение с true/false/1/0
            if v_lower in ('true', '1', 'yes', 'on'):
                return True
            elif v_lower in ('false', '0', 'no', 'off', ''):
                return False
            # Если значение не распознано - возвращаем False по умолчанию
            # Это предотвратит ошибку при неправильных значениях типа 'trueimage.png'
            return False
        return bool(v) if v else False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Игнорировать лишние поля из .env


settings = Settings()

