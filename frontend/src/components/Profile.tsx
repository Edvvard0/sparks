import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react'
import { useApp } from '../context/AppContext'
import apiClient from '../lib/api'
import Settings from './Settings'
import { TextSkeleton } from './SkeletonLoader'
import { getTelegramUserData } from '../lib/telegram'
import heartIcon from '../assets/icons/heart-icon.svg'
import coinIcon from '../assets/icons/coin-icon.svg'
import lightningIcon from '../assets/icons/lightning-icon.svg'
import BottomNavigation from './BottomNavigation'


interface ProfileProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  onOpenModal?: (modal: 'notificationsSettings' | 'languageSettings' | 'faq') => void
  onOpenSettings?: () => void
  hideBottomNavigation?: boolean
}

const Profile = ({ onNavigate, onOpenModal, onOpenSettings, hideBottomNavigation = false }: ProfileProps) => {
  const { t } = useTranslation()
  const { user, updateUser, wallet_address, setWalletAddress } = useApp()
  const wallet = useTonWallet()
  const [tonConnectUI] = useTonConnectUI()
  const [showSettings, setShowSettings] = useState(false)
  const [loading, setLoading] = useState(true)

  // Обработчик подключения TON кошелька
  const handleConnectWallet = () => {
    if (tonConnectUI) {
      try {
        // Открываем модалку TON Connect
        // useTonAuth автоматически обработает подключение и обновит данные пользователя
        tonConnectUI.openModal()
      } catch (error) {
        console.error('Error opening TON Connect modal:', error)
      }
    }
  }

  // Обработчик отключения TON кошелька
  const handleDisconnectWallet = async () => {
    if (tonConnectUI) {
      try {
        // Отключаем кошелек через TON Connect UI
        await tonConnectUI.disconnect()
        
        // Очищаем wallet_address из контекста и localStorage
        setWalletAddress(null)
        localStorage.removeItem('wallet_address')
        
        // Обновляем wallet_address на бэкенде (устанавливаем в null)
        try {
          const tgId = localStorage.getItem('tg_id')
          if (tgId) {
            await apiClient.patch('/auth/wallet/disconnect', {}, {
              headers: {
                'X-Telegram-User-ID': tgId
              }
            })
            console.log('Wallet address cleared on backend')
          }
        } catch (error) {
          console.error('Error updating wallet address on backend:', error)
          // Продолжаем выполнение даже если обновление на бэкенде не удалось
        }
        
        // Обновляем данные пользователя после отключения
        await updateUser()
        
        console.log('Wallet disconnected successfully')
      } catch (error) {
        console.error('Error disconnecting wallet:', error)
      }
    }
  }
  
  // Слушаем изменения состояния кошелька для обновления данных
  useEffect(() => {
    if (!tonConnectUI) return
    
    const unsubscribe = tonConnectUI.onStatusChange(async (walletInfo) => {
      if (walletInfo) {
        // Кошелек подключен - useTonAuth обработает proof и обновит данные
        // Дополнительно обновляем данные пользователя через небольшую задержку
        console.log('Wallet status changed - connected:', walletInfo)
        setTimeout(async () => {
          await updateUser()
        }, 2000) // Даем время useTonAuth обработать proof
      } else {
        // Кошелек отключен - обновляем данные пользователя
        console.log('Wallet status changed - disconnected')
        await updateUser()
      }
    })
    
    return () => {
      unsubscribe()
    }
  }, [tonConnectUI, updateUser])
  
  // Загрузка данных профиля и истории
  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true)
        
        // Загрузка профиля (если не загружен)
        if (!user) {
          await updateUser()
        }
      } catch (error) {
        console.error('Error loading profile:', error)
      } finally {
        setLoading(false)
      }
    }

    loadProfile()
  }, []) // Загружаем только один раз при монтировании
  
  
  // Открываем Settings при возврате из дочерних страниц настроек
  const handleSettingsNavigation = (page: string) => {
    if (['notificationsSettings', 'languageSettings', 'faq'].includes(page)) {
      setShowSettings(false)
      onOpenModal?.(page as 'notificationsSettings' | 'languageSettings' | 'faq')
    } else {
      onNavigate?.(page as any)
    }
  }

  // Функция для открытия Settings из модалок настроек
  const handleOpenSettings = () => {
    setShowSettings(true)
  }
  
  // Передаем функцию открытия Settings в App через onOpenSettings
  useEffect(() => {
    if (onOpenSettings) {
      // Сохраняем функцию открытия Settings для использования в модалках
      (window as any).openSettingsFromProfile = handleOpenSettings
    }
    return () => {
      if ((window as any).openSettingsFromProfile === handleOpenSettings) {
        delete (window as any).openSettingsFromProfile
      }
    }
  }, [onOpenSettings])
  
  // Проверяем, нужно ли открыть Settings при монтировании (если вернулись из дочерней страницы)
  useEffect(() => {
    const shouldOpenSettings = sessionStorage.getItem('openSettings')
    if (shouldOpenSettings === 'true') {
      setShowSettings(true)
      sessionStorage.removeItem('openSettings')
    }
  }, [])

  // Показываем skeleton только при первой загрузке
  if (loading) {
    return (
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden">
        <div className="px-6 pt-12 pb-32">
          <div className="flex flex-col items-center mb-8">
            <div className="w-24 h-24 rounded-full bg-[#333333] mb-4 animate-pulse"></div>
            <TextSkeleton width="150px" height="24px" className="mb-1" />
            <TextSkeleton width="100px" height="16px" />
          </div>
          <div className="mb-8">
            <TextSkeleton width="120px" height="20px" className="mb-4" />
            <div className="flex flex-wrap gap-2">
              <TextSkeleton width="80px" height="32px" className="rounded-full" />
              <TextSkeleton width="100px" height="32px" className="rounded-full" />
              <TextSkeleton width="90px" height="32px" className="rounded-full" />
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Если user не загружен после загрузки, показываем сообщение с возможностью обновить
  if (!user) {
    return (
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden flex flex-col">
        {/* Balance at top */}
        <div className="flex justify-center items-center gap-2 pt-6 pb-4">
          <img src={coinIcon} alt="Coin" width={24} height={24} />
          <span className="text-sparks-text text-base font-semibold">0</span>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center px-6">
            <p className="text-white text-base mb-4">{t('profile.errorLoading')}</p>
            <button 
              onClick={async () => {
                setLoading(true)
                await updateUser()
                setLoading(false)
              }}
              className="px-6 py-3 bg-sparks-primary rounded-full text-white"
            >
              {t('profile.reload')}
            </button>
          </div>
        </div>
        {/* Bottom Navigation */}
        <BottomNavigation onNavigate={onNavigate} currentPage="profile" hide={hideBottomNavigation || showSettings} />
      </div>
    )
  }

  // Получаем данные из Telegram для имени и фото
  const tgUserData = getTelegramUserData()
  const displayName = tgUserData?.first_name 
    ? (tgUserData.last_name ? `${tgUserData.first_name} ${tgUserData.last_name}` : tgUserData.first_name)
    : (user.last_name ? `${user.first_name} ${user.last_name}` : user.first_name)

  const username = tgUserData?.username 
    ? `@${tgUserData.username}` 
    : (user.username ? `@${user.username}` : t('profile.username'))
  
  const photoUrl = tgUserData?.photo_url || null

  // Форматирование даты регистрации
  const createdDate = new Date(user.created_at)
  const monthNames = [
    t('profile.months.january'),
    t('profile.months.february'),
    t('profile.months.march'),
    t('profile.months.april'),
    t('profile.months.may'),
    t('profile.months.june'),
    t('profile.months.july'),
    t('profile.months.august'),
    t('profile.months.september'),
    t('profile.months.october'),
    t('profile.months.november'),
    t('profile.months.december')
  ]
  const formattedDate = `${monthNames[createdDate.getMonth()]} ${createdDate.getFullYear()}`

  return (
    <>
      {showSettings && (
        <Settings 
          onClose={() => setShowSettings(false)} 
          onNavigate={handleSettingsNavigation} 
          onOpenModal={onOpenModal}
        />
      )}
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden flex flex-col">
      {/* Balance at top */}
      <div className="flex justify-center items-center gap-2 pt-6 pb-4">
        <img src={coinIcon} alt="Coin" width={24} height={24} />
        <span className="text-sparks-text text-base font-semibold">{user?.balance || 0}</span>
      </div>
      {/* Content */}
      <div className="px-6 pt-4 pb-32 flex-1 overflow-y-auto">
        {/* Profile Header */}
        <div className="flex flex-col items-center mb-8 px-4 py-6 rounded-2xl bg-[#1E1E1E]">
          {/* Avatar */}
          <div className="w-24 h-24 rounded-full bg-[#333333] mb-4 overflow-hidden">
            {photoUrl ? (
              <img 
                src={photoUrl} 
                alt={displayName}
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback на placeholder при ошибке загрузки
                  const target = e.target as HTMLImageElement
                  target.style.display = 'none'
                  const parent = target.parentElement
                  if (parent) {
                    parent.innerHTML = `
                      <div class="w-full h-full bg-gradient-to-br from-[#555555] to-[#333333] flex items-center justify-center">
                        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                          <circle cx="24" cy="24" r="24" fill="#808080"/>
                          <path d="M24 16C26.2091 16 28 17.7909 28 20C28 22.2091 26.2091 24 24 24C21.7909 24 20 22.2091 20 20C20 17.7909 21.7909 16 24 16Z" fill="#E7E7E7"/>
                          <path d="M16 32C16 28 20 26 24 26C28 26 32 28 32 32" stroke="#E7E7E7" strokeWidth="2" strokeLinecap="round"/>
                        </svg>
                      </div>
                    `
                  }
                }}
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-[#555555] to-[#333333] flex items-center justify-center">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <circle cx="24" cy="24" r="24" fill="#808080"/>
                  <path d="M24 16C26.2091 16 28 17.7909 28 20C28 22.2091 26.2091 24 24 24C21.7909 24 20 22.2091 20 20C20 17.7909 21.7909 16 24 16Z" fill="#E7E7E7"/>
                  <path d="M16 32C16 28 20 26 24 26C28 26 32 28 32 32" stroke="#E7E7E7" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
            )}
          </div>

          {/* Name with Lifetime Badge */}
          <div className="flex items-center gap-2 justify-center mb-1">
            <h1 className="text-white text-xl font-semibold">{displayName}</h1>
            {user.has_lifetime_subscription && (
              <div className="px-2 py-0.5 rounded-full bg-[#FFC700]">
                <span className="text-black text-xs font-semibold">{t('profile.lifetimeBadge')}</span>
              </div>
            )}
          </div>

          {/* Username */}
          <p className="text-[#808080] text-sm">{username}</p>
          {user.has_lifetime_subscription && (
            <p className="text-[#FFC700] text-xs mt-1">{t('profile.lifetimeSubscriber')}</p>
          )}
        </div>

        {/* My Interests Section */}
        <div className="mb-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h2 className="text-white text-lg font-semibold">{t('profile.interests')}</h2>
              <div className="px-2.5 py-1 rounded-lg bg-[#2E2E2E] min-w-[28px] flex items-center justify-center">
                <span className="text-white text-xs font-semibold">{user.interests.length}</span>
              </div>
            </div>
            <button 
              onClick={() => onNavigate?.('allInterests')}
              className="text-[#808080] text-sm font-medium hover:text-white transition-colors"
            >
              {t('profile.viewAll')}
            </button>
          </div>

          {/* Interests Buttons */}
          <div className="flex flex-wrap gap-2">
            {user.interests.slice(0, 3).map((interest) => (
              <button
                key={interest.id}
                className="px-4 py-2 rounded-full whitespace-nowrap flex-shrink-0"
                style={{ backgroundColor: interest.color }}
              >
                <span className="text-white text-sm font-medium">{interest.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* TON Wallet Section */}
        <div className="mb-8">
          <h2 className="text-white text-lg font-semibold mb-4">{t('profile.wallet') || 'TON Кошелек'}</h2>
          {wallet_address || wallet?.account?.address ? (
            <div className="p-4 rounded-lg bg-[#1F1F1F] border border-[#333333]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[#808080] text-sm">{t('profile.walletConnected') || 'Кошелек подключен'}</span>
                <button
                  onClick={handleDisconnectWallet}
                  className="text-[#EB454E] text-sm font-medium hover:underline transition-colors"
                >
                  {t('profile.disconnect') || 'Отключить'}
                </button>
              </div>
              <p className="text-white text-xs font-mono break-all">
                {(wallet_address || wallet?.account?.address)?.slice(0, 6)}...{(wallet_address || wallet?.account?.address)?.slice(-4)}
              </p>
            </div>
          ) : (
            <button
              onClick={handleConnectWallet}
              className="w-full p-4 rounded-lg bg-[#1F1F1F] border border-[#333333] hover:bg-[#2A2A2A] transition-colors text-left"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#2E2E2E] flex items-center justify-center flex-shrink-0">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-white text-sm font-medium">{t('profile.connectWallet') || 'Подключить TON кошелек'}</span>
                    <span className="text-[#808080] text-xs mt-0.5">{t('profile.connectWalletDescription') || 'Для пополнения баланса'}</span>
                  </div>
                </div>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" className="flex-shrink-0">
                  <path d="M6 12L10 8L6 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </button>
          )}
        </div>

        {/* Settings Section */}
        <div className="mb-8">
          <button 
            onClick={() => setShowSettings(true)}
            className="w-full text-left"
          >
          <h2 className="text-white text-lg font-semibold mb-4">{t('profile.settings')}</h2>
          </button>
        </div>

        {/* Info Text */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <img src={heartIcon} alt="Heart" width={16} height={16} className="opacity-50" />
          <p className="text-[#808080] text-xs">{t('profile.togetherWithSparks', { date: formattedDate })}</p>
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNavigation onNavigate={onNavigate} currentPage="profile" />
    </div>
    </>
  )
}

export default Profile
