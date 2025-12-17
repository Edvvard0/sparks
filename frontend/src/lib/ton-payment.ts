/**
 * Утилиты для работы с TON платежами
 */

/**
 * Генерация deep link для перевода TON
 */
export const generateTonDeepLink = (
  toAddress: string,
  amountNanotons: string,
  comment?: string
): string => {
  let deepLink = `ton://transfer/${toAddress}?amount=${amountNanotons}`;
  
  if (comment) {
    const encodedComment = encodeURIComponent(comment);
    deepLink += `&text=${encodedComment}`;
  }
  
  return deepLink;
};

/**
 * Открытие кошелька через deep link
 */
export const openTonWallet = (deepLink: string): void => {
  // Пробуем открыть deep link
  window.location.href = deepLink;
  
  // Fallback для мобильных устройств
  setTimeout(() => {
    // Если не открылось, показываем инструкции
    const userAgent = navigator.userAgent.toLowerCase();
    const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
    
    if (isMobile) {
      // На мобильных устройствах deep link должен работать автоматически
      console.log('Opening TON wallet...');
    } else {
      // На десктопе показываем QR код или инструкции
      console.log('Please open TON wallet manually');
    }
  }, 1000);
};

/**
 * Проверка статуса платежа
 */
export const checkPaymentStatus = async (
  transactionId: number,
  onStatusChange?: (status: string) => void
): Promise<{ status: string; confirmed: boolean }> => {
  // Импортируем apiClient динамически чтобы избежать циклических зависимостей
  const { default: apiClient } = await import('./api');
  
  // Делаем только ОДИН запрос, не рекурсивную проверку
  // Рекурсивная проверка должна быть в компоненте, чтобы можно было остановить при размонтировании
  try {
    console.log(`[Payment API] Checking status for transaction ${transactionId}`);
    
    const response = await apiClient.get(`/payments/ton/check/${transactionId}`);
    const data = response.data;
    
    console.log(`[Payment API] Response received:`, data);
    
    if (onStatusChange) {
      onStatusChange(data.status);
    }
    
    return { status: data.status, confirmed: data.confirmed || false };
    
  } catch (error: any) {
    console.error('[Payment API] Error checking payment status:', error);
    console.error('[Payment API] Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    });
    
    // Возвращаем ошибку вместо рекурсивной проверки
    throw error;
  }
};

/**
 * Форматирование суммы в TON для отображения
 */
export const formatTonAmount = (nanotons: string): string => {
  const nanotonsNum = BigInt(nanotons);
  const tons = Number(nanotonsNum) / 1_000_000_000;
  return tons.toFixed(2);
};

