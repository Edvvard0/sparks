import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useApp } from '../context/AppContext'
import apiClient from '../lib/api'
import { showError } from '../lib/toast'
import TONPayment from './TONPayment'
import { formatTonAmount } from '../lib/ton-payment'
import coinIcon from '../assets/icons/coin-icon.svg'
import closeIcon from '../assets/icons/settings/close-icon.svg'

interface Package {
  id: number
  amount: number | string
  price: number
  min_ton_amount?: string | null
  discount?: number | null
  original_price?: number | null
  title?: string | null
  description?: string | null
}

interface SparksPurchaseProps {
  onClose: () => void
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
}

const SparksPurchase = ({ onClose, onNavigate }: SparksPurchaseProps) => {
  const { t } = useTranslation()
  const { balance, updateUser, wallet_address } = useApp()
  const [packages, setPackages] = useState<Package[]>([])
  const [selectedPackageId, setSelectedPackageId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [processingPayment, setProcessingPayment] = useState(false)
  const [showHowToEarn, setShowHowToEarn] = useState(false)
  const [showTonPayment, setShowTonPayment] = useState(false)
  const [showWalletRequired, setShowWalletRequired] = useState(false)
  const [tonPaymentData, setTonPaymentData] = useState<{
    transactionId: number
    tonAmount: string
    tonAddress: string
    comment?: string
  } | null>(null)

  // Загрузка пакетов
  useEffect(() => {
    const loadPackages = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get<{ packages: Package[] }>('/payments/packages')
        // Фильтруем пакеты - убираем разовый платеж (пакеты с title)
        const filteredPackages = response.data.packages.filter(pkg => !pkg.title || pkg.title.trim() === '')
        setPackages(filteredPackages)
        // Выбираем второй пакет по умолчанию (если есть)
        if (filteredPackages.length > 1) {
          setSelectedPackageId(filteredPackages[1].id)
        } else if (filteredPackages.length > 0) {
          setSelectedPackageId(filteredPackages[0].id)
        }
      } catch (error) {
        console.error('Error loading packages:', error)
      } finally {
        setLoading(false)
      }
    }

    loadPackages()
  }, [])


  const handlePayment = async () => {
    if (!selectedPackageId) return

    // Проверяем подключен ли TON кошелек
    if (!wallet_address) {
      setShowWalletRequired(true)
      return
    }

    try {
      setProcessingPayment(true)
      const response = await apiClient.post<{ 
        transaction_id: number
        ton_amount: string
        ton_address: string
        comment?: string
      }>('/payments/ton/create', {
        package_id: selectedPackageId
      })

      // Показываем модальное окно TON платежа
      setTonPaymentData({
        transactionId: response.data.transaction_id,
        tonAmount: response.data.ton_amount,
        tonAddress: response.data.ton_address,
        comment: response.data.comment
      })
      setShowTonPayment(true)
    } catch (error: any) {
      console.error('Error creating payment:', error)
      showError(error.message || t('sparksPurchase.errorPayment'))
    } finally {
      setProcessingPayment(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[300] flex items-end justify-center">
      {/* Backdrop - полностью перекрывает весь экран включая BottomNavigation */}
      <div 
        className="fixed inset-0 bg-black/50 z-[300]"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-[393px] bg-[#171717] rounded-t-3xl overflow-hidden max-h-[90vh] flex flex-col z-[301]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 flex-shrink-0">
          <h1 className="text-white text-2xl font-semibold">{t('sparksPurchase.needMoreSparks')}</h1>
          <button 
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center hover:opacity-70 transition-opacity"
          >
            <img src={closeIcon} alt="Close" width={24} height={24} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 overflow-y-auto flex-1 min-h-0">
          {/* Balance at top - золотая монета с молнией и число */}
          <div className="flex justify-center items-center gap-2.5 pb-4">
            <img 
              src={coinIcon} 
              alt="Coin" 
              width={38} 
              height={38} 
            />
            <span className="text-white text-[40px] font-semibold leading-[0.55]">{balance}</span>
          </div>

          {/* How to earn question - справа вверху */}
          <div className="text-right mb-6">
            <button
              onClick={() => setShowHowToEarn(true)}
              className="text-[#7D7D7D] text-base leading-[1.375] hover:text-white transition-colors"
            >
              {t('sparksPurchase.howToEarn')}
            </button>
          </div>

          {/* Divider */}
          <div className="h-px bg-[#333333] mb-6"></div>

          {/* Description */}
          <p className="text-[#7D7D7D] text-base mb-1 leading-[1.375]">{t('sparksPurchase.moreSparksDescription1')}</p>
          <p className="text-[#7D7D7D] text-base mb-6 leading-[1.375]">{t('sparksPurchase.moreSparksDescription2')}</p>

        {/* Packages */}
        {loading ? (
          <div className="text-center text-[#808080] py-8">{t('sparksPurchase.loadingPackages')}</div>
        ) : (
          <div className="space-y-3 mb-8">
            {packages.map((pkg) => {
              const isSelected = selectedPackageId === pkg.id
              const hasTitle = pkg.title && pkg.title.trim() !== ''
              
              return (
                <div
                  key={pkg.id}
                  onClick={() => setSelectedPackageId(pkg.id)}
                  className={`rounded-[18px] p-4 flex items-center justify-between border-2 cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#6456F0] border-[#6456F0]'
                      : 'bg-transparent border-[#333333] hover:border-[#444444]'
                  }`}
                >
                  <div className="flex items-center gap-2 flex-1">
                    {hasTitle ? (
                      // Пакет с title и description (четвертый пакет)
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-white text-base font-semibold">{pkg.title}</h3>
                          {pkg.discount && (
                            <span className="bg-[#EB454E] text-white text-xs font-semibold px-2 py-0.5 rounded">
                              -{pkg.discount}%
                            </span>
                          )}
                        </div>
                        {pkg.description && (
                          <p className="text-[#808080] text-xs">{pkg.description}</p>
                        )}
                      </div>
                    ) : (
                      // Обычный пакет с количеством искр
                      <>
                        <span className="text-white text-lg font-semibold">
                          {pkg.amount}
                        </span>
                        {/* Иконка молнии (желтая) */}
                        <svg width="16" height="16" viewBox="0 0 17 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M1.05436 11.2505L8.50962 1.20117C9.09382 0.415624 10.1851 0.904107 10.1851 1.95068V9.72911C10.1851 10.3568 10.614 10.8639 11.1422 10.8639H14.7692C15.5932 10.8639 16.032 12.0162 15.4876 12.7507L8.03233 22.7988C7.44814 23.5844 6.35682 23.0959 6.35682 22.0493V14.2709C6.35682 13.6432 5.928 13.1361 5.39974 13.1361H1.77154C0.947463 13.1361 0.509941 11.9838 1.05436 11.2505Z" fill="#FFC700" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                        {/* Бейдж скидки */}
                        {pkg.discount && (
                          <span className="bg-[#EB454E] text-white text-xs font-semibold px-2 py-0.5 rounded">
                            -{pkg.discount}%
                          </span>
                        )}
                      </>
                    )}
                  </div>
                  <div className="text-right flex-shrink-0 ml-4">
                    {/* Цена */}
                    <div className="text-white text-lg font-semibold">
                      {pkg.price.toLocaleString()} {t('sparksPurchase.currency')}
                    </div>
                    {/* Минимальная сумма в TON */}
                    {pkg.min_ton_amount && (
                      <div className="text-[#808080] text-xs">
                        {formatTonAmount(pkg.min_ton_amount)} TON
                      </div>
                    )}
                    {/* Зачеркнутая старая цена */}
                    {pkg.original_price && (
                      <div className="text-[#808080] text-xs line-through">
                        {pkg.original_price.toLocaleString()} {t('sparksPurchase.currency')}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Payment Button */}
        <button
          onClick={handlePayment}
          className="w-full h-16 rounded-full bg-[#1E1E1E] flex items-center justify-center transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={!selectedPackageId || loading || processingPayment}
        >
          <span className="text-white text-xl font-semibold">
            {processingPayment ? t('sparksPurchase.processing') : t('sparksPurchase.proceedToPayment')}
          </span>
        </button>
        </div>
      </div>

      {/* Modal: How to earn sparks */}
      {showHowToEarn && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setShowHowToEarn(false)}
        >
          <div
            className="bg-[#1F1F1F] rounded-[24px] p-6 max-w-[320px] mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-white text-xl font-semibold mb-4">{t('sparksPurchase.howToEarnTitle')}</h2>
            <div className="space-y-3 text-[#808080] text-sm mb-6">
              <p>{t('sparksPurchase.howToEarn1')}</p>
              <p>{t('sparksPurchase.howToEarn2')}</p>
              <p>{t('sparksPurchase.howToEarn3')}</p>
              <p>{t('sparksPurchase.howToEarn4')}</p>
            </div>
            <button
              onClick={() => setShowHowToEarn(false)}
              className="w-full h-12 rounded-full bg-[#6456F0] text-white font-semibold"
            >
              {t('sparksPurchase.understood')}
            </button>
          </div>
        </div>
      )}

      {/* Modal: Wallet Required */}
      {showWalletRequired && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setShowWalletRequired(false)}
        >
          <div
            className="bg-[#1F1F1F] rounded-[24px] p-6 max-w-[320px] mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-white text-xl font-semibold mb-4">{t('sparksPurchase.walletRequiredTitle')}</h2>
            <div className="space-y-3 text-[#808080] text-sm mb-6">
              <p>{t('sparksPurchase.walletRequiredMessage')}</p>
            </div>
            <div className="space-y-3">
              <button
                onClick={() => {
                  setShowWalletRequired(false)
                  onNavigate?.('profile')
                }}
                className="w-full h-12 rounded-full bg-[#6456F0] text-white font-semibold hover:bg-[#5548E0] transition-colors"
              >
                {t('sparksPurchase.goToProfile')}
              </button>
              <button
                onClick={() => setShowWalletRequired(false)}
                className="w-full h-12 rounded-full bg-transparent border border-[#333333] text-white font-semibold hover:border-[#444444] transition-colors"
              >
                {t('sparksPurchase.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TON Payment Modal */}
      {showTonPayment && tonPaymentData && (
        <TONPayment
          transactionId={tonPaymentData.transactionId}
          tonAmount={tonPaymentData.tonAmount}
          tonAddress={tonPaymentData.tonAddress}
          comment={tonPaymentData.comment}
          onSuccess={() => {
            setShowTonPayment(false)
            setTonPaymentData(null)
            updateUser().then(() => {
              onNavigate?.('home')
            })
          }}
          onClose={() => {
            setShowTonPayment(false)
            setTonPaymentData(null)
          }}
        />
      )}
    </div>
  )
}

export default SparksPurchase
