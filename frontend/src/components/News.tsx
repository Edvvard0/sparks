import closeIcon from '../assets/icons/settings/close-icon.svg'
import newsIcon from '../assets/icons/settings/news-icon.svg'

interface NewsProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  onClose?: () => void
  onOpenSettings?: () => void
}

const News = ({ onNavigate, onClose, onOpenSettings }: NewsProps) => {
  const telegramLink = 'https://t.me/Edward0076'

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
          <h1 className="text-white text-2xl font-semibold">Новости Sparks</h1>
          <button 
            onClick={onClose || (() => onNavigate?.('profile'))}
            className="w-10 h-10 flex items-center justify-center"
          >
            <img src={closeIcon} alt="Close" width={24} height={24} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 overflow-y-auto flex-1 min-h-0">
          {/* News Content */}
          <div className="flex flex-col items-center justify-center min-h-[400px] mb-6">
            {/* Icon */}
            <div className="w-20 h-20 rounded-full bg-[#BC001F]/20 flex items-center justify-center mb-6">
              <img src={newsIcon} alt="News" width={40} height={40} />
            </div>

            {/* Text */}
            <h2 className="text-white text-xl font-semibold mb-2 text-center">Подписывайтесь на новости</h2>
            <p className="text-[#808080] text-sm text-center mb-8">
              Будьте в курсе всех обновлений и новостей Sparks
            </p>

            {/* Telegram Button */}
            <a
              href={telegramLink}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full max-w-[280px] h-14 rounded-full bg-[#EB454E] flex items-center justify-center gap-3 transition-opacity hover:opacity-90"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="white"/>
                <path d="M16.64 8.8C16.49 10.38 15.84 14.22 15.51 15.99C15.37 16.74 15.09 16.99 14.83 17.02C14.25 17.07 13.81 16.64 13.25 16.27C12.37 15.69 11.87 15.33 11.02 14.77C10.03 14.12 10.67 13.76 11.24 13.18C11.39 13.03 14.95 9.7 15.02 9.37C15.03 9.3 15.03 9.11 14.91 9.01C14.79 8.91 14.63 8.94 14.5 8.96C14.33 8.99 12.25 10.12 8.38 12.35C7.8 12.66 7.27 12.81 6.8 12.79C6.28 12.77 5.3 12.52 4.55 12.3C3.65 12.04 2.94 11.9 3 11.37C3.03 11.11 3.33 10.87 3.9 10.64C7.14 9.11 9.95 7.91 12.33 7.04C15.7 5.87 16.69 5.5 17.12 5.5C17.22 5.5 17.41 5.52 17.52 5.61C17.61 5.69 17.64 5.78 17.65 5.87C17.66 5.96 17.68 6.14 17.67 6.25C17.65 6.44 16.64 8.8 16.64 8.8Z" fill="#171717"/>
              </svg>
              <span className="text-white text-base font-semibold">Подписаться в Telegram</span>
            </a>
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

export default News
