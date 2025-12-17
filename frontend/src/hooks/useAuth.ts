import { useState, useCallback } from 'react';
import apiClient from '../lib/api';
import { useApp } from '../context/AppContext';
import { getTelegramUserData } from '../lib/telegram';

interface RegisterData {
  wallet_address?: string;
  tg_id?: number;
  username?: string;
  first_name: string;
  last_name: string | null;
  gender: 'male' | 'female' | 'couple';
  category_ids: number[];
  language_code?: string;
}

export const useAuth = () => {
  const { wallet_address, tg_id, setUser, updateUser } = useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Регистрация пользователя по tg_id (wallet_address опционален)
  const register = useCallback(
    async (data: Omit<RegisterData, 'first_name' | 'last_name' | 'language_code'>) => {
      // ВАЖНО: Регистрация требует tg_id из Telegram
      if (!tg_id) {
        throw new Error('Telegram ID required for registration');
      }

      setLoading(true);
      setError(null);

      try {
        // Получаем данные пользователя из Telegram
        const tgUserData = getTelegramUserData();
        
        const registerData: RegisterData = {
          tg_id: tg_id, // Обязательно - основной идентификатор
          wallet_address: data.wallet_address || wallet_address || undefined, // Опционально
          username: tgUserData?.username || undefined,
          first_name: tgUserData?.first_name || 'User',
          last_name: tgUserData?.last_name || null,
          gender: data.gender,
          category_ids: data.category_ids,
          language_code: tgUserData?.language_code || 'ru',
        };

        console.log('[Onboarding] Registering user with tg_id:', tg_id)

        const response = await apiClient.post('/auth/register', registerData);
        const userData = response.data;

        console.log('[Onboarding] User registered successfully:', userData)

        // Очищаем localStorage перед установкой новых данных
        localStorage.removeItem('user');
        
        // Сохраняем tg_id в localStorage
        if (userData.tg_id) {
          localStorage.setItem('tg_id', userData.tg_id.toString());
        }
        
        // Сохраняем wallet_address в localStorage если есть
        if (userData.wallet_address) {
          localStorage.setItem('wallet_address', userData.wallet_address);
        }
        
        setUser(userData);
        await updateUser();

        return userData;
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || error.message || 'Registration failed';
        setError(errorMessage);
        console.error('[Onboarding] Registration error:', error)
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [tg_id, wallet_address, setUser, updateUser]
  );

  return {
    register,
    loading,
    error,
  };
};
