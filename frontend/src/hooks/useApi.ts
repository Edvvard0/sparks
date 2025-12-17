import { useState, useCallback } from 'react';
import apiClient from '../lib/api';
import { useApp } from '../context/AppContext';

export const useApi = () => {
  const { tg_id } = useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(
    async <T = any>(
      method: 'get' | 'post' | 'put' | 'delete',
      url: string,
      data?: any,
      config?: any
    ): Promise<T> => {
      if (!tg_id) {
        throw new Error('User not authenticated');
      }

      setLoading(true);
      setError(null);

      try {
        const response = await apiClient[method](url, data, config);
        return response.data;
      } catch (error: any) {
        const errorMessage = error.message || 'Request failed';
        setError(errorMessage);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [tg_id]
  );

  return {
    request,
    loading,
    error,
  };
};
