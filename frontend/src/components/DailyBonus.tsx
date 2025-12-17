import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useApp } from '../context/AppContext'
import apiClient from '../lib/api'
import { showError, showSuccess } from '../lib/toast'
import closeIcon from '../assets/icons/settings/close-icon.svg'
import lightningIcon from '../assets/icons/lightning-icon.svg'
import Icon from './Icon'

interface DailyBonusProps {
  onClose: () => void
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
}

interface DailyBonusStatus {
  day_number: number
  bonus_amount: number
  is_claimed: boolean
  can_claim: boolean
  next_reset_at: string
  claimed_days?: number[] // Массив номеров дней, которые уже получены
}

const DailyBonus = ({ onClose }: DailyBonusProps) => {
  const { t } = useTranslation()
  const { setBalance, updateUser } = useApp()
  const [status, setStatus] = useState<DailyBonusStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [claiming, setClaiming] = useState(false)

  // Загрузка статуса бонуса
  useEffect(() => {
    const loadStatus = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get<DailyBonusStatus>('/daily-bonus/status')
        setStatus(response.data)
      } catch (error: any) {
        console.error('Error loading daily bonus status:', error)
        showError(error.message || t('dailyBonus.errorLoadingStatus'))
      } finally {
        setLoading(false)
      }
    }

    loadStatus()
  }, [])

  // Получение бонуса
  const handleClaim = async () => {
    if (!status || !status.can_claim || claiming) return

    try {
      setClaiming(true)
      const response = await apiClient.post<{ success: boolean; bonus_amount: number; new_balance: number; day_number: number }>(
        '/daily-bonus/claim'
      )

      setBalance(response.data.new_balance)
      await updateUser()
      showSuccess(t('dailyBonus.bonusReceived', { amount: response.data.bonus_amount }))
      
      // Обновляем статус
      const statusResponse = await apiClient.get<DailyBonusStatus>('/daily-bonus/status')
      setStatus(statusResponse.data)
      
      // Закрываем модальное окно через небольшую задержку
      setTimeout(() => {
        onClose()
      }, 1000)
    } catch (error: any) {
      console.error('Error claiming daily bonus:', error)
      showError(error.message || t('dailyBonus.errorClaiming'))
    } finally {
      setClaiming(false)
    }
  }

  // Бонусы для всех 7 дней
  const bonuses = [10, 15, 20, 25, 30, 35, 40]

  if (loading) {
    return (
      <div className="fixed inset-0 z-[300] flex items-end justify-center bg-black/50">
        <div className="bg-[#1C1B1A] rounded-t-[24px] p-6 max-w-[393px] w-full">
          <div className="text-center text-[#808080] py-8">{t('dailyBonus.loading')}</div>
        </div>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="fixed inset-0 z-[300] flex items-end justify-center bg-black/50">
        <div className="bg-[#1C1B1A] rounded-t-[24px] p-6 max-w-[393px] w-full">
          <div className="text-center text-[#808080] py-8">{t('dailyBonus.errorLoading')}</div>
        </div>
      </div>
    )
  }

  return (
    <div 
      className="fixed inset-0 z-[500] flex items-end justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={onClose}
    >
      <div 
        className="bg-[#1C1B1A] rounded-t-[24px] p-6 max-w-[393px] w-full relative max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        style={{ zIndex: 501 }}
      >
        {/* Close Button - справа вверху */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-8 h-8 flex items-center justify-center z-10"
        >
          <img src={closeIcon} alt="Close" width={24} height={24} />
        </button>

        {/* Header - слева вверху */}
        <div className="mb-6 pr-8">
          <h1 className="text-white text-2xl font-semibold mb-2">
            {t('dailyBonus.todayBonus', { amount: status.bonus_amount })}
          </h1>
          <p className="text-[#7D7D7D] text-sm leading-[1.375]">
            {t('dailyBonus.returnEveryDay')}
          </p>
        </div>

        {/* Today Subtitle - по центру */}
        <div className="mb-4 text-center">
          <h2 className="text-white text-sm font-medium">{t('dailyBonus.today')}</h2>
        </div>

        {/* Bonus Cards - горизонтальная прокрутка */}
        <div className="mb-8 relative">
          {/* Пунктирная линия соединяющая карточки */}
          <div className="absolute top-[50px] left-0 right-0 h-px border-t border-dashed border-[#333333] opacity-30"></div>
          
          {/* Контейнер с прокруткой */}
          <div className="overflow-x-auto pb-4 -mx-6 px-6 scrollbar-hide" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
            <style>{`
              .scrollbar-hide::-webkit-scrollbar {
                display: none;
              }
            `}</style>
            <div className="flex gap-4 min-w-max">
              {bonuses.map((bonus, index) => {
                const dayNumber = index + 1
                const isActive = status.day_number === dayNumber
                // День пройден, если он в списке claimed_days или меньше текущего дня (и текущий день уже получен)
                const isPast = (status.claimed_days && status.claimed_days.includes(dayNumber)) || 
                              (dayNumber < status.day_number && status.is_claimed)
                
                return (
                  <div key={dayNumber} className="flex flex-col items-center relative flex-shrink-0">
                    {/* Пунктирная линия между карточками */}
                    {index < bonuses.length - 1 && (
                      <div className="absolute top-[50px] left-full w-4 h-px border-t border-dashed border-[#333333] opacity-30"></div>
                    )}
                    
                    <div
                      className={`w-[100px] h-[120px] rounded-2xl border-2 flex flex-col items-center justify-center gap-1.5 relative ${
                        isActive
                          ? 'bg-[#F7931A] border-[#F7931A]'
                          : isPast
                          ? 'bg-transparent border-[#333333] opacity-50'
                          : 'bg-transparent border-[#333333]'
                      }`}
                    >
                      {/* Галочка в правом верхнем углу для активной или пройденной карточки */}
                      {(isActive || isPast) && (
                        <div className="absolute top-2 right-2 w-5 h-5 bg-white rounded-full flex items-center justify-center z-10">
                          <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                            <path d="M2 6L5 9L10 3" stroke={isActive ? "#F7931A" : "#333333"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                      )}
                      
                      <Icon
                        src={lightningIcon}
                        alt="Lightning"
                        width={24}
                        height={24}
                        color={isActive ? '#FFFFFF' : '#808080'}
                      />
                      <span className={`text-base font-semibold leading-[1.375] ${
                        isActive ? 'text-white' : 'text-white'
                      }`}>
                        {bonus}
                      </span>
                      <span className={`text-xs mt-1 ${
                        isActive ? 'text-white' : 'text-[#808080]'
                      }`}>
                        {t('dailyBonus.dayNumber', { number: dayNumber })}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Claim Button */}
        <button
          onClick={handleClaim}
          disabled={!status.can_claim || claiming}
          className={`w-full h-14 rounded-full flex items-center justify-center transition-opacity ${
            status.can_claim && !claiming
              ? 'bg-[#1E1E1E] hover:opacity-90'
              : 'bg-[#333333] opacity-50 cursor-not-allowed'
          }`}
        >
          <span className="text-white text-lg font-semibold">
            {claiming ? t('dailyBonus.claiming') : status.is_claimed ? t('dailyBonus.alreadyClaimed') : t('dailyBonus.claim')}
          </span>
        </button>
      </div>
    </div>
  )
}

export default DailyBonus
