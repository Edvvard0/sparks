import lightningIcon from '../assets/icons/lightning-icon_welcome.svg'
import gamesIcon from '../assets/icons/games-icon_welcome.svg'
import logoBg from '../assets/icons/Logo.svg'

interface WelcomeProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
}

const Welcome = ({ onNavigate }: WelcomeProps) => {
  const handleButtonClick = () => {
    // При клике на любую кнопку переходим на онбординг
    if (onNavigate) {
      onNavigate('onboarding')
    }
  }

  return (
    <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-black overflow-hidden flex flex-col">
      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center relative px-4 pb-32">
        {/* Logo Background - позиционируем по центру экрана */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] z-0 pointer-events-none opacity-100">
          <img src={logoBg} alt="Logo Background" className="w-full h-full object-contain" />
        </div>

        {/* Buttons Container - вертикальное расположение кнопок, опущены ниже */}
        <div className="absolute bottom-[140px] left-1/2 -translate-x-1/2 z-10 w-full flex flex-col items-center gap-2.5 px-6">
          {/* Button 1 - ДЛЯ НЕЁ */}
          <button
            onClick={handleButtonClick}
            className="w-full max-w-[240px] h-[55px] rounded-[28px] overflow-hidden group hover:opacity-80 transition-opacity active:scale-[0.98]"
            style={{
              background: 'rgba(0, 0, 0, 0.05)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              transform: 'rotate(-3deg)',
            }}
          >
            <div className="relative h-full flex items-center justify-center">
              <span className="text-white text-sm font-semibold">ДЛЯ НЕЁ</span>
            </div>
          </button>

          {/* Button 2 - ЗАДАНИЯ ДЛЯ ПАР */}
          <button
            onClick={handleButtonClick}
            className="w-full max-w-[260px] h-[60px] rounded-[30px] overflow-hidden group hover:opacity-80 transition-opacity active:scale-[0.98]"
            style={{
              background: 'rgba(0, 0, 0, 0.05)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              transform: 'rotate(2deg)',
            }}
          >
            <div className="relative h-full flex items-center justify-center gap-2">
              <img src={lightningIcon} alt="Lightning" width={16} height={16} className="flex-shrink-0" />
              <span className="text-white text-sm font-semibold">ЗАДАНИЯ ДЛЯ ПАР</span>
            </div>
          </button>

          {/* Button 3 - ДЛЯ НЕГО */}
          <button
            onClick={handleButtonClick}
            className="w-full max-w-[240px] h-[55px] rounded-[28px] overflow-hidden group hover:opacity-80 transition-opacity active:scale-[0.98]"
            style={{
              background: 'rgba(0, 0, 0, 0.05)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              transform: 'rotate(-2deg)',
            }}
          >
            <div className="relative h-full flex items-center justify-center">
              <span className="text-white text-sm font-semibold">ДЛЯ НЕГО</span>
            </div>
          </button>

          {/* Button 4 - Минигры */}
          <button
            onClick={handleButtonClick}
            className="w-full max-w-[240px] h-[55px] rounded-[28px] overflow-hidden group hover:opacity-80 transition-opacity active:scale-[0.98]"
            style={{
              background: 'rgba(0, 0, 0, 0.05)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              transform: 'rotate(3deg)',
            }}
          >
            <div className="relative h-full flex items-center justify-center gap-2">
              <img src={gamesIcon} alt="Games" width={16} height={16} className="flex-shrink-0" />
              <span className="text-white text-sm font-semibold">Минигры</span>
            </div>
          </button>
        </div>

        {/* Bottom Button - Поехали (в самом низу) */}
        <button
          onClick={handleButtonClick}
          className="absolute bottom-5 left-1/2 -translate-x-1/2 w-[320px] h-[56px] rounded-[123px] bg-[#141414] flex items-center justify-center z-10 hover:bg-[#1a1a1a] transition-colors active:scale-[0.98]"
        >
          <span className="text-[#E7E7E7] text-lg font-semibold">Поехали</span>
        </button>
      </div>
    </div>
  )
}

export default Welcome
