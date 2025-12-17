import { useState, useEffect, useRef } from 'react'
import { Toaster } from 'react-hot-toast'
import { useTonWallet } from '@tonconnect/ui-react'
import { useIsConnectionRestored } from '@tonconnect/ui-react'
import Onboarding from './components/Onboarding'
import Welcome from './components/Welcome'
import Home from './components/Home'
import Profile from './components/Profile'
import DailyBonus from './components/DailyBonus'
import SparksPurchase from './components/SparksPurchase'
import AllInterests from './components/AllInterests'
import NotificationsSettings from './components/NotificationsSettings'
import LanguageSettings from './components/LanguageSettings'
import FAQ from './components/FAQ'
import { useApp } from './context/AppContext'
import { useTonAuth } from './hooks/useTonAuth'
import { initTelegram, hideBackButton, setupBackButton } from './lib/telegram'

function App() {
  const { wallet_address, user, loading } = useApp()
  const wallet = useTonWallet()
  const isConnectionRestored = useIsConnectionRestored()
  const [currentPage, setCurrentPage] = useState<'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news'>('welcome')
  const [showDailyBonus, setShowDailyBonus] = useState(false)
  const [showNotificationsSettings, setShowNotificationsSettings] = useState(false)
  const [showLanguageSettings, setShowLanguageSettings] = useState(false)
  const [showFAQ, setShowFAQ] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showSparksPurchase, setShowSparksPurchase] = useState(false)
  
  // Определяем, открыта ли любая модалка
  const isAnyModalOpen = showDailyBonus || showNotificationsSettings || showLanguageSettings || showFAQ || showSettings || showSparksPurchase
  
  // Ref для отслеживания начальной инициализации
  const hasInitializedRef = useRef(false)

  // Используем хук для авторизации через TON Connect (только для обновления wallet_address)
  // Регистрация происходит через tg_id после онбординга
  useTonAuth()

  useEffect(() => {
    // Инициализация Telegram WebApp
    initTelegram()
  }, [])

  // Определение текущей страницы на основе состояния пользователя
  // ВАЖНО: Зарегистрированный пользователь (с интересами) всегда попадает на Home
  useEffect(() => {
    // Ждем завершения загрузки и восстановления соединения
    if (loading || !isConnectionRestored) {
      return
    }

    // Если пользователь зарегистрирован (есть интересы) - всегда показываем Home
    if (user && user.interests && user.interests.length > 0) {
      // Если пользователь уже на welcome или onboarding, переводим на Home
      if (currentPage === 'welcome' || currentPage === 'onboarding') {
        console.log('[App] Registered user found with interests, redirecting to home')
        setCurrentPage('home')
        hasInitializedRef.current = true
        return
      }
      // Если уже на Home или другой странице (не welcome/onboarding) - не меняем
      // Используем явную проверку типов для обхода сужения типов TypeScript
      const pageValue: string = currentPage
      if (pageValue !== 'welcome' && pageValue !== 'onboarding') {
        hasInitializedRef.current = true
        return
      }
    }

    // Инициализация только один раз при первой загрузке
    if (!hasInitializedRef.current) {
      hasInitializedRef.current = true
      
      // Если пользователь найден и есть интересы - показываем Home
      if (user && user.interests && user.interests.length > 0) {
        console.log('[App] User found with interests, redirecting to home')
        setCurrentPage('home')
        return
      }
      
      // Если пользователь не найден или нет интересов - показываем Welcome
      // Пользователь сам решит когда перейти на onboarding через клик на кнопку
      console.log('[App] Initial load - showing welcome page')
      setCurrentPage('welcome')
      return
    }
  }, [loading, isConnectionRestored, user, currentPage]) // Добавили currentPage для отслеживания изменений

  // Настройка кнопки "Назад" в Telegram
  useEffect(() => {
    if (currentPage === 'welcome' || currentPage === 'onboarding') {
      hideBackButton()
      return
    }
    
    // Создаем обработчик клика с текущим значением currentPage
    const handleBackClick = () => {
      // Логика возврата назад
      if (currentPage === 'home') {
        // В Telegram нельзя закрыть главный экран
        return
      } else if (currentPage === 'profile') {
        // Возврат на главный экран
        setCurrentPage('home')
      } else if (currentPage === 'allInterests') {
        // Возврат на профиль
        setCurrentPage('profile')
      }
      // Для других страниц можно добавить логику навигации назад
    }
    
    const cleanup = setupBackButton(handleBackClick)
    
    // Cleanup при размонтировании или изменении страницы
    return cleanup
  }, [currentPage])

  // Показываем загрузку пока определяем состояние
  if (loading || !isConnectionRestored) {
    return (
      <div className="min-h-screen bg-sparks-bg flex items-center justify-center">
        <div className="text-sparks-text">Загрузка...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-sparks-bg">
      <Toaster />
      {currentPage === 'welcome' ? (
        <Welcome onNavigate={(page) => setCurrentPage(page)} />
      ) : currentPage === 'onboarding' ? (
        <Onboarding onComplete={() => setCurrentPage('home')} />
      ) : currentPage === 'profile' ? (
        <Profile 
          onNavigate={(page) => {
            if (page === 'dailyBonus') {
              setShowDailyBonus(true)
            } else if (page === 'sparksPurchase') {
              setShowSparksPurchase(true)
            } else {
              setCurrentPage(page)
            }
          }}
          onOpenModal={(modal) => {
            if (modal === 'notificationsSettings') {
              setShowNotificationsSettings(true)
            } else if (modal === 'languageSettings') {
              setShowLanguageSettings(true)
            } else if (modal === 'faq') {
              setShowFAQ(true)
            }
            // Support и News теперь прямые ссылки, не модалки
          }}
          onOpenSettings={() => setShowSettings(true)}
          hideBottomNavigation={isAnyModalOpen}
        />
      ) : currentPage === 'allInterests' ? (
        <AllInterests onNavigate={(page) => {
          if (page === 'dailyBonus') {
            setShowDailyBonus(true)
          } else {
            setCurrentPage(page)
          }
        }} onClose={() => setCurrentPage('profile')} />
      ) : currentPage === 'home' ? (
        user ? (
          <Home 
            onNavigate={(page) => {
              if (page === 'dailyBonus') {
                setShowDailyBonus(true)
              } else if (page === 'sparksPurchase') {
                setShowSparksPurchase(true)
              } else {
                setCurrentPage(page)
              }
            }}
            hideBottomNavigation={isAnyModalOpen}
          />
        ) : (
          <Welcome onNavigate={(page) => setCurrentPage(page)} />
        )
      ) : (
        <Welcome onNavigate={(page) => setCurrentPage(page)} />
      )}
      
      {/* DailyBonus как модальное окно */}
      {showDailyBonus && (
        <DailyBonus 
          onClose={() => setShowDailyBonus(false)} 
          onNavigate={(page) => {
            setShowDailyBonus(false)
            if (page !== 'dailyBonus') {
              setCurrentPage(page)
            }
          }} 
        />
      )}

      {/* SparksPurchase как модальное окно */}
      {showSparksPurchase && (
        <SparksPurchase 
          onClose={() => setShowSparksPurchase(false)} 
          onNavigate={(page) => {
            setShowSparksPurchase(false)
            if (page === 'dailyBonus') {
              setShowDailyBonus(true)
            } else if (page !== 'sparksPurchase') {
              setCurrentPage(page)
            }
          }} 
        />
      )}

      {/* Settings модальные окна поверх Profile */}
      {showNotificationsSettings && (
        <NotificationsSettings 
          onClose={() => setShowNotificationsSettings(false)} 
          onNavigate={(page) => {
            setShowNotificationsSettings(false)
            if (page === 'dailyBonus') {
              setShowDailyBonus(true)
            } else if (page !== 'notificationsSettings') {
              setCurrentPage(page)
            }
          }}
          onOpenSettings={() => {
            setShowNotificationsSettings(false)
            // Открываем Settings через функцию из Profile
            if ((window as any).openSettingsFromProfile) {
              (window as any).openSettingsFromProfile()
            }
          }}
        />
      )}

      {showLanguageSettings && (
        <LanguageSettings 
          onClose={() => setShowLanguageSettings(false)} 
          onNavigate={(page) => {
            setShowLanguageSettings(false)
            if (page === 'dailyBonus') {
              setShowDailyBonus(true)
            } else if (page !== 'languageSettings') {
              setCurrentPage(page)
            }
          }}
          onOpenSettings={() => {
            setShowLanguageSettings(false)
            // Открываем Settings через функцию из Profile
            if ((window as any).openSettingsFromProfile) {
              (window as any).openSettingsFromProfile()
            }
          }}
        />
      )}

      {showFAQ && (
        <FAQ 
          onClose={() => setShowFAQ(false)} 
          onNavigate={(page) => {
            setShowFAQ(false)
            if (page === 'dailyBonus') {
              setShowDailyBonus(true)
            } else if (page !== 'faq') {
              setCurrentPage(page)
            }
          }}
          onOpenSettings={() => {
            setShowFAQ(false)
            // Открываем Settings через функцию из Profile
            if ((window as any).openSettingsFromProfile) {
              (window as any).openSettingsFromProfile()
            }
          }}
        />
      )}


    </div>
  )
}

export default App
