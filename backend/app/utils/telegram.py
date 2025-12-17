import hmac
import hashlib
import urllib.parse
from typing import Dict, Optional
from app.core.config import settings


def verify_telegram_data(init_data: str) -> Optional[Dict]:
    """
    Верификация данных от Telegram WebApp
    
    Args:
        init_data: Строка с данными от Telegram (query string)
        
    Returns:
        Dict с данными пользователя или None если верификация не прошла
    """
    try:
        # Парсим query string
        parsed_data = urllib.parse.parse_qs(init_data)
        
        # Извлекаем hash для проверки
        if 'hash' not in parsed_data:
            return None
            
        received_hash = parsed_data['hash'][0]
        
        # Создаем строку для проверки (без hash)
        data_check_string = []
        for key in sorted(parsed_data.keys()):
            if key != 'hash':
                data_check_string.append(f"{key}={parsed_data[key][0]}")
        
        data_check_string = '\n'.join(data_check_string)
        
        # Создаем секретный ключ из bot token
        secret_key = hmac.new(
            "WebAppData".encode(),
            settings.TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем hash
        if calculated_hash != received_hash:
            return None
        
        # Извлекаем данные пользователя
        result = {}
        if 'user' in parsed_data:
            import json
            user_data = json.loads(parsed_data['user'][0])
            result['tg_id'] = user_data.get('id')
            result['username'] = user_data.get('username')
            result['first_name'] = user_data.get('first_name')
            result['last_name'] = user_data.get('last_name')
            result['language_code'] = user_data.get('language_code', 'en')
        
        return result
        
    except Exception as e:
        print(f"Error verifying Telegram data: {e}")
        return None

