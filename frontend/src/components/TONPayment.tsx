import { useState, useEffect, useCallback, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useApp } from '../context/AppContext'
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react'
import { SendTransactionRequest } from '@tonconnect/ui-react'
import { checkPaymentStatus, formatTonAmount } from '../lib/ton-payment'
import { showError, showSuccess } from '../lib/toast'
import closeIcon from '../assets/icons/settings/close-icon.svg'

interface TONPaymentProps {
  transactionId: number
  tonAmount: string
  tonAddress: string
  comment?: string
  onSuccess: () => void
  onClose: () => void
}

const TONPayment = ({ transactionId, tonAmount, tonAddress, onSuccess, onClose }: TONPaymentProps) => {
  const { t } = useTranslation()
  const { updateUser } = useApp()
  const wallet = useTonWallet()
  const [tonConnectUI] = useTonConnectUI()
  const [status, setStatus] = useState<'waiting' | 'processing' | 'success' | 'failed'>('waiting')
  const [checking, setChecking] = useState(false)
  const [txSent, setTxSent] = useState(false)
  const isMountedRef = useRef(true) // Флаг для отслеживания монтирования компонента
  const checkStatusTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null) // Ref для хранения timeout
  const checkStatusIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null) // Ref для хранения interval

  // Проверка статуса платежа
  const handleCheckStatus = useCallback(async () => {
    // Проверяем что компонент еще смонтирован
    if (!isMountedRef.current) {
      console.log('[Payment] Component unmounted, stopping status check')
      return
    }
    
    try {
      setChecking(true)
      setStatus('processing')
      
      console.log(`[Payment] Checking status for transaction ${transactionId}`)
      
      const result = await checkPaymentStatus(transactionId, (newStatus) => {
        if (!isMountedRef.current) return // Не обновляем состояние если компонент размонтирован
        console.log(`[Payment] Status changed: ${newStatus}`)
        setStatus(newStatus === 'completed' ? 'success' : newStatus === 'failed' ? 'failed' : 'processing')
      })
      
      // Проверяем что компонент еще смонтирован перед обновлением состояния
      if (!isMountedRef.current) {
        console.log('[Payment] Component unmounted during status check, stopping')
        return
      }
      
      console.log(`[Payment] Status check result:`, result)
      
      if (result.status === 'completed') {
        console.log(`[Payment] Transaction completed successfully!`)
        setStatus('success')
        showSuccess(t('tonPayment.success'))
        await updateUser()
        // Очищаем все таймауты перед вызовом onSuccess
        if (checkStatusTimeoutRef.current) {
          clearTimeout(checkStatusTimeoutRef.current)
          checkStatusTimeoutRef.current = null
        }
        setTimeout(() => {
          if (isMountedRef.current) {
            onSuccess()
          }
        }, 1500)
      } else if (result.status === 'failed') {
        console.log(`[Payment] Transaction failed`)
        setStatus('failed')
        showError(t('tonPayment.failed'))
        // Модалка закроется автоматически через useEffect
      } else if (result.status === 'not_found') {
        console.log(`[Payment] Transaction not found`)
        setStatus('failed')
        showError('Транзакция не найдена')
        // Модалка закроется автоматически через useEffect
      } else if (result.status === 'pending') {
        // Если платеж еще pending, продолжаем проверку
        console.log(`[Payment] Still pending, will check again in 5 seconds`)
        checkStatusTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            handleCheckStatus()
          }
        }, 5000)
      } else {
        // Для других статусов тоже продолжаем проверку
        console.log(`[Payment] Status: ${result.status}, will check again in 5 seconds`)
        checkStatusTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            handleCheckStatus()
          }
        }, 5000)
      }
    } catch (error: any) {
      console.error('[Payment] Error checking payment status:', error)
      console.error('[Payment] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      })
      
      // Проверяем что компонент еще смонтирован
      if (!isMountedRef.current) {
        console.log('[Payment] Component unmounted during error handling, stopping')
        return
      }
      
      // Если ошибка 404 или not_found, прекращаем проверку
      if (error.response?.status === 404 || error.message?.includes('not found')) {
        setStatus('failed')
        showError('Транзакция не найдена')
        // Модалка закроется автоматически через useEffect
        return
      }
      
      // Для других ошибок продолжаем проверку (особенно важно для режима симуляции)
      console.log('[Payment] Will retry status check in 5 seconds')
      checkStatusTimeoutRef.current = setTimeout(() => {
        if (isMountedRef.current) {
          handleCheckStatus()
        }
      }, 5000)
    } finally {
      if (isMountedRef.current) {
        setChecking(false)
      }
    }
  }, [transactionId, updateUser, onSuccess, t])

  // Создаем транзакцию для отправки через TON Connect
  const createTransaction = useCallback((): SendTransactionRequest => {
    // Простая транзакция без комментария
    // Комментарий требует специального кодирования в BOC формате и не обязателен для платежей
    return {
      validUntil: Math.floor(Date.now() / 1000) + 600, // 10 минут
      messages: [
        {
          address: tonAddress,
          amount: tonAmount, // Уже в nanotons как строка
        }
      ]
    }
  }, [tonAddress, tonAmount])

  // Отправка транзакции через TON Connect UI
  const sendTransaction = useCallback(async () => {
    if (!wallet) {
      showError(t('tonPayment.walletNotConnected'))
      return
    }

    try {
      setStatus('processing')
      const tx = createTransaction()
      
      // Отправляем транзакцию через TON Connect UI
      const result = await tonConnectUI.sendTransaction(tx)
      
      if (result.boc) {
        // Транзакция отправлена успешно
        setTxSent(true)
        console.log('Transaction sent successfully, BOC:', result.boc.substring(0, 50) + '...')
        // Начинаем проверку статуса платежа
        handleCheckStatus()
      } else {
        throw new Error('Транзакция не была отправлена')
      }
    } catch (error: any) {
      console.error('[Payment] Error sending transaction:', error)
      const errorMessage = error.message || error.toString() || JSON.stringify(error)
      
      // Логируем все детали ошибки
      console.log('[Payment] Error details:', {
        message: errorMessage,
        error: error,
        transactionId,
        errorType: error.constructor?.name
      })
      
      // Определяем тип ошибки для пользователя
      if (errorMessage.includes('User rejected') || errorMessage.includes('rejected') || errorMessage.includes('отклонен')) {
        console.log('[Payment] Transaction rejected by user')
        showError(t('tonPayment.rejected'))
        setStatus('failed')
        // Модалка закроется автоматически через useEffect
        return
      } else if (
        errorMessage.includes('insufficient') || 
        errorMessage.includes('not enough') || 
        errorMessage.includes('Недостаточно') ||
        errorMessage.includes('insufficient funds') ||
        errorMessage.toLowerCase().includes('недостаточно средств')
      ) {
        console.log('[Payment] Insufficient funds detected')
        showError(t('tonPayment.insufficientFunds'))
        setStatus('failed')
        // Модалка закроется автоматически через useEffect
        return
      } else if (
        errorMessage.includes('TON_CONNECT_SDK_ERROR') ||
        errorMessage.includes('BadRequestError') ||
        errorMessage.includes('Bad Request') ||
        errorMessage.includes('Request failed')
      ) {
        console.log('[Payment] TON Connect SDK error detected')
        showError(t('tonPayment.sdkError'))
        setStatus('failed')
        // Модалка закроется автоматически через useEffect
        return
      } else {
        // Для других ошибок показываем общее сообщение и закрываем модалку
        console.log('[Payment] Unknown error occurred')
        showError(t('tonPayment.unknownError'))
        setStatus('failed')
        // Модалка закроется автоматически через useEffect
        return
      }
    }
  }, [wallet, tonConnectUI, createTransaction, handleCheckStatus])

  // Автоматически отправляем транзакцию при монтировании, если кошелек подключен
  useEffect(() => {
    if (wallet && !txSent && status === 'waiting') {
      sendTransaction()
    }
  }, [wallet, txSent, status, sendTransaction])

  // Cleanup при размонтировании компонента
  useEffect(() => {
    isMountedRef.current = true
    
    return () => {
      console.log('[Payment] Component unmounting, cleaning up timeouts')
      isMountedRef.current = false
      
      // Очищаем все таймауты
      if (checkStatusTimeoutRef.current) {
        clearTimeout(checkStatusTimeoutRef.current)
        checkStatusTimeoutRef.current = null
      }
      if (checkStatusIntervalRef.current) {
        clearInterval(checkStatusIntervalRef.current)
        checkStatusIntervalRef.current = null
      }
    }
  }, [])

  // Автоматическое закрытие при ошибке
  useEffect(() => {
    if (status === 'failed') {
      const timer = setTimeout(() => {
        if (isMountedRef.current) {
          onClose()
        }
      }, 3000) // Закрываем через 3 секунды после ошибки
      
      return () => clearTimeout(timer)
    }
  }, [status, onClose])

  return (
    <div className="fixed inset-0 z-[500] flex items-end justify-center bg-black/50">
      <div className="relative bg-[#1E1E1E] rounded-t-[24px] p-6 max-w-[393px] w-full max-h-[90vh] overflow-y-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-10 h-10 flex items-center justify-center z-10 hover:opacity-70 transition-opacity"
        >
          <img src={closeIcon} alt="Close" width={24} height={24} />
        </button>

        {/* Header */}
        <div className="mb-6 pr-12">
          <h2 className="text-white text-xl font-semibold mb-2">
            {t('tonPayment.payWithTon')}
          </h2>
          <p className="text-[#808080] text-sm">
            {t('tonPayment.instructions')}
          </p>
        </div>

        {/* Payment Details */}
        <div className="mb-6 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-[#808080] text-sm">{t('tonPayment.amountInTon')}</span>
            <span className="text-white text-base font-semibold">{formatTonAmount(tonAmount)} TON</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[#808080] text-sm">{t('tonPayment.minAmount')}</span>
            <span className="text-white text-sm">{formatTonAmount(tonAmount)} TON</span>
          </div>
        </div>

        {/* Status */}
        {status === 'waiting' && (
          <div className="mb-6 text-center">
            <p className="text-[#808080] text-sm mb-4">
              {wallet ? 'Подготовка транзакции...' : 'Пожалуйста, подключите кошелек для оплаты'}
            </p>
            {wallet ? (
              <button
                onClick={sendTransaction}
                disabled={checking}
                className="w-full h-12 rounded-full bg-[#6456F0] text-white font-semibold disabled:opacity-50"
              >
                Отправить транзакцию
              </button>
            ) : (
              <button
                onClick={() => tonConnectUI.openModal()}
                className="w-full h-12 rounded-full bg-[#6456F0] text-white font-semibold"
              >
                Подключить кошелек
              </button>
            )}
          </div>
        )}

        {status === 'processing' && (
          <div className="mb-6 text-center">
            <p className="text-white text-sm mb-4">{t('tonPayment.processing')}</p>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto"></div>
          </div>
        )}

        {status === 'success' && (
          <div className="mb-6 text-center">
            <p className="text-green-400 text-sm mb-4">{t('tonPayment.success')}</p>
          </div>
        )}

        {status === 'failed' && (
          <div className="mb-6 text-center">
            <p className="text-red-400 text-sm mb-4">{t('tonPayment.failed')}</p>
            <button
              onClick={handleCheckStatus}
              className="w-full h-12 rounded-full bg-[#6456F0] text-white font-semibold"
            >
              Проверить снова
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default TONPayment

