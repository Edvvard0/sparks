// Telegram WebApp types
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready: () => void;
        expand: () => void;
        initDataUnsafe?: {
          user?: {
            id: number;
            first_name?: string;
            last_name?: string;
            username?: string;
            language_code?: string;
            photo_url?: string;
          };
        };
        setHeaderColor: (color: string) => void;
        setBackgroundColor: (color: string) => void;
        BackButton: {
          show: () => void;
          hide: () => void;
          onClick: (callback: () => void) => void;
          offClick: (callback: () => void) => void;
        };
      };
    };
  }
}

// Инициализация Telegram WebApp
export const initTelegram = () => {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    
    // Разворачиваем приложение на полный экран
    try {
      if ('expand' in tg && typeof tg.expand === 'function') {
        tg.expand();
        console.log('[Telegram] App expanded to fullscreen');
      }
    } catch (e) {
      console.warn('[Telegram] Error expanding app:', e);
    }
    
    // Проверяем версию WebApp (версия 6.0 не поддерживает некоторые методы)
    const version = (tg as any).version || '6.0';
    const versionNumber = parseFloat(version);
    
    // Настройка цветов темы (только для версий >= 6.1)
    if (versionNumber >= 6.1) {
      try {
        if ('setHeaderColor' in tg && typeof tg.setHeaderColor === 'function') {
          tg.setHeaderColor('#171717');
        }
      } catch (e) {
        // Игнорируем ошибки
      }
      
      try {
        if ('setBackgroundColor' in tg && typeof tg.setBackgroundColor === 'function') {
          tg.setBackgroundColor('#171717');
        }
      } catch (e) {
        // Игнорируем ошибки
      }
    }
    
    return tg;
  }
  
  // Заглушка для локального тестирования
  // ВАЖНО: Проверяем только в development, в продакшене всегда используем реальный Telegram WebApp
  if (import.meta.env.DEV && !window.Telegram?.WebApp) {
    // Создаем заглушку для window.Telegram.WebApp только в development
    if (!window.Telegram) {
      window.Telegram = {
        WebApp: {
          ready: () => {},
          expand: () => {},
          initDataUnsafe: {
            user: {
              id: 5254325840,
              first_name: 'Test',
              last_name: 'User',
              username: 'test_user',
              language_code: 'ru',
            },
          },
          setHeaderColor: () => {},
          setBackgroundColor: () => {},
          BackButton: {
            show: () => {},
            hide: () => {},
            onClick: () => {},
            offClick: () => {},
          },
        },
      };
    }
    return window.Telegram.WebApp;
  }
  
  // В продакшене: если нет Telegram WebApp, возвращаем null
  // Это означает что приложение запущено не в Telegram Mini App
  if (!window.Telegram?.WebApp) {
    return null;
  }
  
  return null;
};

// Получение tg_id из Telegram WebApp
export const getTelegramUserId = (): number | null => {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    const user = window.Telegram.WebApp.initDataUnsafe?.user;
    if (user?.id) {
      return user.id;
    }
  }
  
  // Заглушка для локального тестирования (только в development)
  if (import.meta.env.DEV) {
    const DEV_TG_ID = 5254325840;
    return DEV_TG_ID;
  }
  
  // В продакшене: если нет Telegram WebApp, возвращаем null
  // Авторизация будет происходить только через wallet_address
  return null;
};

// Получение данных пользователя из Telegram
export const getTelegramUserData = () => {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    const user = window.Telegram.WebApp.initDataUnsafe?.user;
    if (user) {
      return {
        id: user.id,
        first_name: user.first_name || '',
        last_name: user.last_name || null,
        username: user.username || null,
        language_code: user.language_code || 'en',
        photo_url: user.photo_url || null,
      };
    }
  }
  
  // Заглушка для локального тестирования (только в development)
  if (import.meta.env.DEV && !window.Telegram?.WebApp) {
    return {
      id: 5254325840,
      first_name: 'Test',
      last_name: 'User',
      username: 'test_user',
      language_code: 'ru',
      photo_url: null,
    };
  }
  
  return null;
};

// Настройка кнопки "Назад"
export const setupBackButton = (onClick: () => void) => {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    
    // Проверяем версию WebApp (версия 6.0 не поддерживает BackButton)
    const version = (tg as any).version || '6.0';
    const versionNumber = parseFloat(version);
    
    // BackButton доступен только с версии 6.1+
    if (versionNumber >= 6.1) {
      try {
        if (tg.BackButton && 'show' in tg.BackButton && typeof tg.BackButton.show === 'function') {
          tg.BackButton.show();
          if ('onClick' in tg.BackButton && typeof tg.BackButton.onClick === 'function') {
            tg.BackButton.onClick(onClick);
          }
          return () => {
            try {
              if (tg.BackButton && 'hide' in tg.BackButton && typeof tg.BackButton.hide === 'function') {
                tg.BackButton.hide();
              }
              if (tg.BackButton && 'offClick' in tg.BackButton && typeof tg.BackButton.offClick === 'function') {
                tg.BackButton.offClick(onClick);
              }
            } catch (e) {
              // Игнорируем ошибки
            }
          };
        }
      } catch (e) {
        // Игнорируем ошибки
      }
    }
  }
  return () => {};
};

// Скрытие кнопки "Назад"
export const hideBackButton = () => {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    try {
      const tg = window.Telegram.WebApp;
      
      // Проверяем версию WebApp (версия 6.0 не поддерживает BackButton)
      const version = (tg as any).version || '6.0';
      const versionNumber = parseFloat(version);
      
      // BackButton доступен только с версии 6.1+
      if (versionNumber >= 6.1 && tg.BackButton && 'hide' in tg.BackButton && typeof tg.BackButton.hide === 'function') {
        tg.BackButton.hide();
      }
    } catch (e) {
      // Игнорируем ошибки
    }
  }
};
