import axios, { AxiosInstance, AxiosError } from 'axios';
import { showError } from './toast';

// Определяем базовый URL API
// В dev режиме всегда используем относительный путь через Vite proxy
// В production используем относительный путь через nginx proxy
const getApiBaseUrl = (): string => {
  // В dev режиме всегда используем относительный путь через Vite proxy
  // Vite проксирует /api на http://localhost:8000
  if (import.meta.env.DEV) {
    return '/api/v1';
  }
  
  // В production используем относительный путь через nginx proxy
  // nginx проксирует /api/v1/ на backend:8000/api/v1/
  // Если указан явно в env - используем его (только для production)
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

// Логируем базовый URL для отладки (только в dev режиме)
if (import.meta.env.DEV) {
  console.log('[API] Base URL:', API_BASE_URL);
}

// Создаем экземпляр axios
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // Увеличиваем таймаут по умолчанию до 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления tg_id, username, photo_url или wallet_address в заголовки
apiClient.interceptors.request.use(
  (config) => {
    const DEFAULT_TG_ID = '5254325840';
    const tgId = localStorage.getItem('tg_id');
    const walletAddress = localStorage.getItem('wallet_address');

    // Получаем данные из Telegram WebApp (если доступны)
    let tgUserId: number | null = null;
    let tgUsername: string | null = null;
    
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      const user = window.Telegram.WebApp.initDataUnsafe?.user;
      if (user?.id) {
        tgUserId = user.id;
      }
      if (user?.username) {
        tgUsername = user.username;
      }
    }

    // Используем tg_id из Telegram WebApp в первую очередь
    if (tgUserId) {
      config.headers['X-Telegram-User-ID'] = String(tgUserId);
      localStorage.setItem('tg_id', String(tgUserId));
    } else if (tgId) {
      // Fallback на сохраненный tg_id
      const tgIdNumber = parseInt(tgId, 10);
      if (!isNaN(tgIdNumber) && tgIdNumber > 0) {
        config.headers['X-Telegram-User-ID'] = String(tgIdNumber);
      } else {
        localStorage.removeItem('tg_id');
      }
    } else if (import.meta.env.DEV) {
      // Заглушка только в dev режиме
      localStorage.setItem('tg_id', DEFAULT_TG_ID);
      config.headers['X-Telegram-User-ID'] = DEFAULT_TG_ID;
    }

    // Добавляем username из Telegram WebApp
    if (tgUsername) {
      config.headers['X-Telegram-Username'] = tgUsername;
    }

    // Если есть wallet_address, используем его
    if (walletAddress && walletAddress.trim()) {
      config.headers['X-Wallet-Address'] = walletAddress.trim();
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as any;

      // 401 - не авторизован
      if (status === 401) {
        // Очищаем данные, но НЕ делаем редирект автоматически
        // Редирект должен обрабатываться компонентами
        localStorage.removeItem('tg_id');
        localStorage.removeItem('wallet_address');
        localStorage.removeItem('user');
        // Не показываем ошибку и не делаем редирект - пусть компоненты обрабатывают
        // showError('Сессия истекла. Пожалуйста, войдите снова.');
        // window.location.href = '/';
      }

      // 404 - пользователь не найден (не редиректим, это нормально для нового пользователя)
      // Редирект убран, чтобы избежать бесконечного цикла перезагрузок

      // Показываем toast для других ошибок
      if (status !== 401 && status !== 404) {
        let errorMessage = 'Произошла ошибка';
        
        // Обработка разных форматов ошибок
        if (data?.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            // Массив ошибок валидации
            errorMessage = data.detail.map((err: any) => {
              if (typeof err === 'string') return err;
              if (err?.msg) return err.msg;
              return JSON.stringify(err);
            }).join(', ');
          } else if (typeof data.detail === 'object') {
            errorMessage = data.detail.msg || data.detail.message || JSON.stringify(data.detail);
          }
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        showError(errorMessage);
      }

      // Формируем сообщение об ошибке для reject
      let errorMessage = 'Произошла ошибка';
      if (data?.detail) {
        if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorMessage = data.detail.map((err: any) => {
            if (typeof err === 'string') return err;
            if (err?.msg) return err.msg;
            return JSON.stringify(err);
          }).join(', ');
        } else if (typeof data.detail === 'object') {
          errorMessage = data.detail.msg || data.detail.message || JSON.stringify(data.detail);
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      return Promise.reject({
        status,
        message: errorMessage,
        data,
      });
    }

    const errorMessage = error.message || 'Ошибка сети. Проверьте подключение к интернету.';
    // Не показываем toast для сетевых ошибок - это может быть нормально, если бэкенд недоступен
    // showError(errorMessage);
    return Promise.reject({
      status: 0,
      message: errorMessage,
    });
  }
);

export default apiClient;
