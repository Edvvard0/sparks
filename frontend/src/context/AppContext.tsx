import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getTelegramUserId, getTelegramUserData, initTelegram } from '../lib/telegram';
import apiClient from '../lib/api';

// Хук для получения photo_url из Telegram данных
export const useTelegramPhotoUrl = (): string | null => {
  const tgUserData = getTelegramUserData();
  return tgUserData?.photo_url || null;
};

export interface User {
  tg_id: number;
  username: string | null;
  first_name: string;
  last_name: string | null;
  gender: 'male' | 'female' | 'couple';
  balance: number;
  language: {
    code: string;
    name: string;
  };
  interests: Array<{
    id: number;
    slug: string;
    name: string;
    color: string;
  }>;
  is_admin: boolean;
  wallet_address: string | null;
  has_lifetime_subscription: boolean;
  created_at: string;
}

interface Task {
  id: number;
  title: string;
  description: string;
  category: {
    id: number;
    name: string;
    color: string;
  };
  is_free: boolean;
  is_completed: boolean;
}

interface AppContextType {
  tg_id: number | null;
  wallet_address: string | null;
  user: User | null;
  balance: number;
  language: string;
  tasks: Task[];
  setUser: (user: User | null) => void;
  setWalletAddress: (wallet_address: string | null) => void;
  setBalance: (balance: number) => void;
  setLanguage: (language: string) => void;
  setTasks: (tasks: Task[]) => void;
  updateUser: () => Promise<void>;
  loading: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [tg_id, setTgId] = useState<number | null>(null);
  const [wallet_address, setWalletAddress] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [balance, setBalance] = useState<number>(0);
  const [language, setLanguage] = useState<string>('ru');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  
  // Загрузка wallet_address из localStorage при инициализации
  useEffect(() => {
    const storedWalletAddress = localStorage.getItem('wallet_address');
    if (storedWalletAddress) {
      setWalletAddress(storedWalletAddress);
    }
  }, []);

  // Инициализация Telegram и получение tg_id
  // ВАЖНО: tg_id всегда берется из Telegram Mini App, но сохраняется в localStorage для быстрого доступа
  useEffect(() => {
    initTelegram();
    
    // Проверяем localStorage сначала (быстрее)
    const storedTgId = localStorage.getItem('tg_id');
    if (storedTgId) {
      try {
        const parsedTgId = parseInt(storedTgId, 10);
        if (!isNaN(parsedTgId)) {
          setTgId(parsedTgId);
          // Продолжаем проверку из Telegram для обновления если изменился
        }
      } catch (e) {
        // Игнорируем ошибку парсинга
      }
    }
    
    // Небольшая задержка чтобы Telegram WebApp успел инициализироваться
    setTimeout(() => {
      // Получаем tg_id ТОЛЬКО из Telegram WebApp
      const userId = getTelegramUserId();
      
      if (userId) {
        setTgId(userId);
        // Сохраняем в localStorage для быстрого доступа при следующей загрузке
        localStorage.setItem('tg_id', userId.toString());
      } else {
        // Если нет tg_id из Telegram, устанавливаем заглушку только для разработки
        if (import.meta.env.DEV) {
          const DEV_TG_ID = 5254325840;
          setTgId(DEV_TG_ID);
          localStorage.setItem('tg_id', DEV_TG_ID.toString());
        }
        // В продакшене: если нет tg_id из Telegram, значит приложение запущено не в Telegram
        // В этом случае авторизация будет происходить только через wallet_address
      }
    }, 100);
  }, []);

  // Восстановление TON Connect соединения при загрузке
  // ВАЖНО: Этот useEffect выполняется только один раз при монтировании
  // wallet_address будет установлен из TON Connect UI автоматически через useTonAuth
  useEffect(() => {
    // TON Connect UI автоматически восстанавливает соединение через TonConnectUIProvider
    // Синхронизируем wallet_address из localStorage с состоянием ТОЛЬКО один раз при монтировании
    const storedWalletAddress = localStorage.getItem('wallet_address')
    if (storedWalletAddress && !wallet_address) {
      // Устанавливаем wallet_address только если его еще нет в контексте
      // Это вызовет useEffect для updateUser, но только один раз
      setWalletAddress(storedWalletAddress)
    }
  }, []) // Пустой массив зависимостей - выполняется только при монтировании

  // Загрузка данных пользователя
  // ВАЖНО: Используем useRef для хранения функции, чтобы она не менялась при каждом рендере
  const updateUserRef = React.useRef<(() => Promise<void>) | null>(null);
  
  // Создаем функцию updateUser один раз и сохраняем в ref
  React.useEffect(() => {
    updateUserRef.current = async () => {
      // Если уже идет обновление, не запускаем новое
      if (isUpdatingRef.current) {
        return;
      }
      
      // Проверяем wallet_address из localStorage на случай если он еще не в контексте
      const storedWalletAddress = localStorage.getItem('wallet_address');
      
      // tg_id всегда берется из Telegram WebApp (из контекста, который установлен при инициализации)
      // wallet_address берем из контекста или localStorage
      const currentTgId = tg_id;
      const currentWalletAddress = wallet_address || storedWalletAddress;
      
      // Если нет ни tg_id ни wallet_address, не загружаем пользователя
      if (!currentTgId && !currentWalletAddress) {
        setUser(null);
        setLoading(false);
        return;
      }

      // Устанавливаем флаг обновления
      isUpdatingRef.current = true;

      // Определяем headers вне try блока для использования в catch
      const headers: Record<string, string> = {};

      try {
        // Используем tg_id из Telegram WebApp в первую очередь (быстрее поиск в БД)
        if (currentTgId) {
          headers['X-Telegram-User-ID'] = currentTgId.toString();
          console.log('[AppContext] Loading user with tg_id:', currentTgId);
        }

        // Используем wallet_address как fallback или дополнительный идентификатор
        if (currentWalletAddress) {
          headers['X-Wallet-Address'] = currentWalletAddress;
          console.log('[AppContext] Loading user with wallet_address:', `${currentWalletAddress.substring(0, 10)}...`);
        }

        if (!currentTgId && !currentWalletAddress) {
          console.log('[AppContext] No tg_id or wallet_address, cannot load user');
          setUser(null);
          setLoading(false);
          isUpdatingRef.current = false;
          return;
        }

        const response = await apiClient.get('/auth/me', {
          timeout: 10000,
          headers
        });

        console.log('[AppContext] User loaded successfully:', {
          tg_id: response.data?.tg_id,
          has_interests: response.data?.interests?.length > 0,
          interests_count: response.data?.interests?.length || 0
        });

        const userData = response.data;

        // Сохраняем tg_id в localStorage после успешной загрузки
        if (userData.tg_id) {
          localStorage.setItem('tg_id', userData.tg_id.toString());
        }

        setUser(userData);
        setBalance(userData.balance || 0);
        setLanguage(userData.language?.code || 'ru');

        // НЕ обновляем wallet_address здесь - это вызовет бесконечный цикл
        // wallet_address обновляется только из TON Connect через useTonAuth
        // Просто сохраняем в localStorage если отличается
        if (userData.wallet_address && userData.wallet_address !== wallet_address && userData.wallet_address !== storedWalletAddress) {
          localStorage.setItem('wallet_address', userData.wallet_address);
        }
      } catch (error: any) {
        // Если ошибка 401 (не авторизован), 404 (не найден) или сетевые ошибки - пользователь не найден
        // Это нормально для нового пользователя - он должен пройти онбординг и зарегистрироваться через /register
        // 404 означает что пользователь еще не зарегистрирован - показываем Welcome страницу
        if (error.status === 401 || error.status === 404 || error.status === 0 || !error.response) {
          console.log('[AppContext] User not found, status:', error.status);
          console.log('[AppContext] Request details:', {
            tg_id: currentTgId,
            wallet_address: currentWalletAddress ? `${currentWalletAddress.substring(0, 10)}...` : null,
            headers: Object.keys(headers)
          });
          console.log('[AppContext] Error details:', {
            message: error?.message,
            response: error?.response?.data,
            status: error?.status
          });
          setUser(null);
        } else {
          // Другие ошибки логируем
          console.error('[AppContext] Failed to load user:', error);
          console.error('[AppContext] Request details:', {
            tg_id: currentTgId,
            wallet_address: currentWalletAddress ? `${currentWalletAddress.substring(0, 10)}...` : null,
            headers: Object.keys(headers)
          });
        }
      } finally {
        setLoading(false);
        isUpdatingRef.current = false;
      }
    };
  }, [tg_id, wallet_address]); // Обновляем функцию только когда меняются tg_id или wallet_address
  
  // Обертка для вызова функции из ref
  const updateUser = React.useCallback(async () => {
    if (updateUserRef.current) {
      await updateUserRef.current();
    }
  }, []); // Пустой массив зависимостей - функция не меняется

  // Загружаем пользователя при наличии tg_id или wallet_address (только один раз при монтировании)
  const hasCheckedUserRef = React.useRef(false);
  const lastTgIdRef = React.useRef<number | null>(null);
  const lastWalletAddressRef = React.useRef<string | null>(null);
  const isUpdatingRef = React.useRef(false); // Флаг для предотвращения множественных запросов
  
  // Загружаем пользователя ОДИН РАЗ при монтировании или изменении tg_id/wallet_address
  useEffect(() => {
    // Если уже идет обновление, не запускаем новое
    if (isUpdatingRef.current) {
      return;
    }
    
    // Проверяем, изменились ли tg_id или wallet_address
    const tgIdChanged = tg_id !== lastTgIdRef.current;
    const walletChanged = wallet_address !== lastWalletAddressRef.current;
    
    // Если значения не изменились и уже проверяли - не вызываем updateUser
    if (!tgIdChanged && !walletChanged && hasCheckedUserRef.current) {
      return;
    }
    
    // Если нет ни tg_id ни wallet_address, не загружаем пользователя
    if (!tg_id && !wallet_address) {
      setLoading(false);
      setUser(null);
      lastTgIdRef.current = tg_id;
      lastWalletAddressRef.current = wallet_address;
      return;
    }
    
    // Обновляем refs ПЕРЕД вызовом updateUser
    lastTgIdRef.current = tg_id;
    lastWalletAddressRef.current = wallet_address;
    hasCheckedUserRef.current = true;
    
    // Вызываем updateUser (он сам проверит isUpdatingRef)
    // Используем функцию из ref чтобы избежать бесконечного цикла
    if (updateUserRef.current) {
      updateUserRef.current();
    }
  }, [tg_id, wallet_address]); // Убрали updateUser из зависимостей

  const value: AppContextType = {
    tg_id,
    wallet_address,
    user,
    balance,
    language,
    tasks,
    setUser,
    setWalletAddress,
    setBalance,
    setLanguage,
    setTasks,
    updateUser,
    loading,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Экспортируем функцию отдельно для совместимости с Fast Refresh
function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

export { useApp };
