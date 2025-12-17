import { useTranslation } from 'react-i18next'
import { useApp } from '../context/AppContext'
import notificationIcon from '../assets/icons/settings/notification-icon.svg'
import languageIcon from '../assets/icons/settings/language-icon.svg'
import questionIcon from '../assets/icons/settings/question-icon.svg'
import supportIcon from '../assets/icons/settings/support-icon.svg'
import newsIcon from '../assets/icons/settings/news-icon.svg'
import chevronIcon from '../assets/icons/settings/chevron-icon.svg'
import closeIcon from '../assets/icons/settings/close-icon.svg'

interface SettingsProps {
  onClose: () => void
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  onOpenModal?: (modal: 'notificationsSettings' | 'languageSettings' | 'faq') => void
}

const Settings = ({ onClose, onOpenModal }: SettingsProps) => {
  const { t } = useTranslation()
  const { user } = useApp()
  return (
    <div className="fixed inset-0 z-[300] flex items-end justify-center">
      {/* Backdrop - полностью перекрывает весь экран включая BottomNavigation */}
      <div 
        className="fixed inset-0 bg-black/50 z-[300]"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-[393px] bg-[#1E1E1E] rounded-t-3xl overflow-hidden max-h-[90vh] flex flex-col z-[301]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 flex-shrink-0">
          <h1 className="text-white text-2xl font-semibold">{t('settings.title')}</h1>
          <button 
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center hover:opacity-70 transition-opacity"
          >
            <img src={closeIcon} alt="Close" width={24} height={24} />
          </button>
        </div>

        {/* Settings List */}
        <div className="px-6 overflow-y-auto flex-1 min-h-0">
          {/* Settings Section */}
          <div className="mb-6">
            {/* Уведомления */}
            <button 
              onClick={() => {
                onClose()
                onOpenModal?.('notificationsSettings')
              }}
              className="w-full flex items-center gap-4 py-4 border-b border-[#2E2E2E]"
            >
              <div className="w-9 h-9 flex items-center justify-center flex-shrink-0">
                <img src={notificationIcon} alt="Notifications" width={36} height={36} />
              </div>
              <div className="flex-1 text-left">
                <span className="text-white text-base font-medium">{t('settings.notifications')}</span>
              </div>
              <img src={chevronIcon} alt="Chevron" width={8} height={14} />
            </button>

            {/* Язык */}
            <button 
              onClick={() => {
                onClose()
                onOpenModal?.('languageSettings')
              }}
              className="w-full flex items-center gap-4 py-4 border-b border-[#2E2E2E]"
            >
              <div className="w-9 h-9 flex items-center justify-center flex-shrink-0">
                <img src={languageIcon} alt="Language" width={36} height={36} />
              </div>
              <div className="flex-1 text-left">
                <div className="flex items-center justify-between">
                  <span className="text-white text-base font-medium">{t('settings.language')}</span>
                  <span className="text-[#7D7D7D] text-base mr-2">{user?.language?.name || t('settings.language')}</span>
                </div>
              </div>
              <img src={chevronIcon} alt="Chevron" width={8} height={14} />
            </button>
          </div>

          {/* Subtitle */}
          <div className="mb-4">
            <h2 className="text-[#7D7D7D] text-sm font-medium">{t('settings.accountAndSupport')}</h2>
          </div>

          {/* Account and Support Section */}
          <div className="mb-6">
            {/* Вопросы и ответы */}
            <button 
              onClick={() => {
                onClose()
                onOpenModal?.('faq')
              }}
              className="w-full flex items-center gap-4 py-4 border-b border-[#2E2E2E]"
            >
              <div className="w-9 h-9 flex items-center justify-center flex-shrink-0">
                <img src={questionIcon} alt="FAQ" width={36} height={36} />
              </div>
              <div className="flex-1 text-left">
                <span className="text-white text-base font-medium">{t('settings.faq')}</span>
              </div>
              <img src={chevronIcon} alt="Chevron" width={8} height={14} />
            </button>

            {/* Поддержка - прямая ссылка на Telegram */}
            <a
              href="https://t.me/kondrova_e"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center gap-4 py-4 border-b border-[#2E2E2E]"
            >
              <div className="w-9 h-9 flex items-center justify-center flex-shrink-0">
                <img src={supportIcon} alt="Support" width={36} height={36} />
              </div>
              <div className="flex-1 text-left">
                <span className="text-white text-base font-medium">{t('settings.support')}</span>
              </div>
              <img src={chevronIcon} alt="Chevron" width={8} height={14} />
            </a>

            {/* Новости Sparks - прямая ссылка на Telegram */}
            <a
              href="https://t.me/sparks_app"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center gap-4 py-4 border-b border-[#2E2E2E]"
            >
              <div className="w-9 h-9 flex items-center justify-center flex-shrink-0">
                <img src={newsIcon} alt="News" width={36} height={36} />
              </div>
              <div className="flex-1 text-left">
                <span className="text-white text-base font-medium">{t('settings.news')}</span>
              </div>
              <img src={chevronIcon} alt="Chevron" width={8} height={14} />
            </a>
          </div>
        </div>

        {/* Back Button */}
        <div className="px-6 pb-8 flex-shrink-0">
          <button 
            onClick={onClose}
            className="w-full h-16 rounded-full bg-[#000000] flex items-center justify-center transition-opacity hover:opacity-90"
          >
            <span className="text-white text-xl font-semibold">{t('settings.back')}</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Settings
