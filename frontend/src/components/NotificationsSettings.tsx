import { useState } from 'react'
import closeIcon from '../assets/icons/settings/close-icon.svg'

interface NotificationsSettingsProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  onClose?: () => void
  onOpenSettings?: () => void
}

const NotificationsSettings = ({ onNavigate, onClose, onOpenSettings }: NotificationsSettingsProps) => {
  const [notifications, setNotifications] = useState({
    all: false,
    games: true,
  })

  return (
    <div className="fixed inset-0 z-[300] flex items-end justify-center">
      {/* Backdrop - полностью перекрывает весь экран включая BottomNavigation */}
      <div 
        className="fixed inset-0 bg-black/50 z-[300]"
        onClick={onClose || (() => onNavigate?.('profile'))}
      />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-[393px] bg-[#1E1E1E] rounded-t-3xl overflow-hidden max-h-[85vh] flex flex-col z-[301]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 flex-shrink-0">
          <h1 className="text-white text-2xl font-semibold">Уведомления</h1>
          <button 
            onClick={onClose || (() => onNavigate?.('profile'))}
            className="w-10 h-10 flex items-center justify-center"
          >
            <img src={closeIcon} alt="Close" width={24} height={24} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 overflow-y-auto flex-1 min-h-0">
          {/* Settings List */}
          <div className="space-y-0 mb-6">
            {/* Все уведомления */}
            <div className="border-b border-[#2E2E2E]">
              <div className="flex items-center justify-between py-4">
                <div className="flex-1">
                  <span className="text-white text-base font-semibold leading-[1.375] block mb-1">Все уведомления</span>
                  <span className="text-[#7D7D7D] text-base leading-[1.193]">Отключите, если уведомления мешают</span>
                </div>
                <button
                  onClick={() => setNotifications({ ...notifications, all: !notifications.all })}
                  className={`w-14 h-6 rounded-full transition-colors flex items-center ${
                    notifications.all ? 'bg-[#2FD15A] justify-end' : 'bg-[#404042] justify-start'
                  } px-0.5`}
                >
                  <div className="w-5 h-5 rounded-full bg-white" />
                </button>
              </div>
            </div>

            {/* Только игры */}
            <div className="border-b border-[#2E2E2E]">
              <div className="flex items-center justify-between py-4">
                <div className="flex-1">
                  <span className="text-white text-base font-semibold leading-[1.375] block mb-1">Только игры</span>
                  <span className="text-[#7D7D7D] text-base leading-[1.193]">Мы будем присылать сообщения только про новые игры, ничего лишнего</span>
                </div>
                <button
                  onClick={() => setNotifications({ ...notifications, games: !notifications.games })}
                  className={`w-14 h-6 rounded-full transition-colors flex items-center ${
                    notifications.games ? 'bg-[#2FD15A] justify-end' : 'bg-[#404042] justify-start'
                  } px-0.5`}
                >
                  <div className="w-5 h-5 rounded-full bg-white" />
                </button>
              </div>
            </div>
          </div>

        </div>

        {/* Back Button */}
        <div className="px-6 pb-8 flex-shrink-0">
          <button 
            onClick={() => {
              if (onOpenSettings) {
                onOpenSettings()
              } else {
                onClose?.()
              }
            }}
            className="w-full h-16 rounded-full bg-[#000000] flex items-center justify-center transition-opacity hover:opacity-90"
          >
            <span className="text-white text-xl font-semibold">Назад</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotificationsSettings
