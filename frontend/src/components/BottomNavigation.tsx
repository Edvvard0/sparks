import homeIcon from '../assets/icons/home-icon.svg'
import gamesIcon from '../assets/icons/games-icon.svg'
import lightningIcon from '../assets/icons/lightning-icon.svg'
import profileIcon from '../assets/icons/profile-icon.svg'

interface BottomNavigationProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  currentPage?: string
  hide?: boolean
}

const BottomNavigation = ({ onNavigate, currentPage = 'home', hide = false }: BottomNavigationProps) => {
  if (hide) {
    return null
  }
  const getIconStyle = (page: string) => {
    const isActive = currentPage === page
    return {
      opacity: isActive ? 1 : 0.5,
      filter: isActive ? 'brightness(0) saturate(100%) invert(100%)' : 'brightness(0) saturate(100%) invert(50%)'
    }
  }
  
  return (
    <div className="fixed bottom-0 left-0 right-0 w-full max-w-[393px] mx-auto z-[200] pointer-events-auto">
      <div className="relative h-[80px] bg-[#171717] rounded-t-[24px] shadow-[0_-2px_16px_rgba(0,0,0,0.4)] overflow-hidden" style={{ borderTopLeftRadius: '24px', borderTopRightRadius: '24px' }}>
        <div className="relative flex justify-center items-center h-full pt-6 pb-4 z-10 pointer-events-auto">
          <button onClick={() => onNavigate?.('home')} className="cursor-pointer flex-1 flex justify-center items-center">
            <img src={homeIcon} alt="Home" width={22} height={26} style={getIconStyle('home')} />
          </button>

          <button 
            onClick={() => {
              // Вызываем callback для открытия DailyBonus как модального окна
              onNavigate?.('dailyBonus')
            }} 
            className="cursor-pointer flex-1 flex justify-center items-center"
          >
            <img src={gamesIcon} alt="Games" width={25} height={23} style={getIconStyle('dailyBonus')} />
          </button>

          <button 
            onClick={() => {
              // Вызываем callback для открытия SparksPurchase как модального окна
              onNavigate?.('sparksPurchase')
            }} 
            className="cursor-pointer flex-1 flex justify-center items-center"
          >
            <img src={lightningIcon} alt="Lightning" width={17} height={24} style={getIconStyle('sparksPurchase')} />
          </button>

          <button onClick={() => onNavigate?.('profile')} className="cursor-pointer flex-1 flex justify-center items-center">
            <img src={profileIcon} alt="Profile" width={24} height={24} style={getIconStyle('profile')} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default BottomNavigation

