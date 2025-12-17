import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useApp } from '../context/AppContext'
import { useAuth } from '../hooks/useAuth'
import apiClient from '../lib/api'
import { CategorySkeleton } from './SkeletonLoader'
import { getTelegramUserData } from '../lib/telegram'
import maleIcon from '../assets/icons/male-icon.svg'
import femaleIcon from '../assets/icons/female-icon.svg'
import coupleIcon from '../assets/icons/couple-icon.svg'

type Gender = 'male' | 'female' | 'couple' | null

interface Category {
  id: number
  slug: string
  name: string
  color: string
  is_active: boolean
}

interface OnboardingProps {
  onComplete: () => void
}

const Onboarding = ({ onComplete }: OnboardingProps) => {
  const { t } = useTranslation()
  const { tg_id, wallet_address, language, setUser, setLanguage, updateUser } = useApp()
  const { register, loading: authLoading } = useAuth()
  const [selectedGender, setSelectedGender] = useState<Gender>(null)
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<Set<number>>(new Set())
  const [selectedCategoriesOrder, setSelectedCategoriesOrder] = useState<number[]>([])
  const [showMoreCategories, setShowMoreCategories] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Загрузка категорий
  useEffect(() => {
    const loadCategories = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get<{ categories: Category[] }>(
          '/categories/',
          {
            params: { language_code: language || 'ru' }
          }
        )
        setCategories(response.data.categories)
      } catch (err: any) {
        setError(err.message || t('onboarding.error'))
      } finally {
        setLoading(false)
      }
    }

    loadCategories()
  }, [language])

  // Получаем имя пользователя из Telegram
  const tgUserData = getTelegramUserData()
  const userName = tgUserData?.first_name || t('onboarding.defaultUserName')

  const toggleCategory = (categoryId: number) => {
    const newSet = new Set(selectedCategoryIds)
    const newOrder = [...selectedCategoriesOrder]
    
    if (newSet.has(categoryId)) {
      newSet.delete(categoryId)
      setSelectedCategoriesOrder(newOrder.filter(id => id !== categoryId))
    } else if (newSet.size < 3) {
      newSet.add(categoryId)
      newOrder.push(categoryId)
      setSelectedCategoriesOrder(newOrder)
    }
    setSelectedCategoryIds(newSet)
  }

  // Get color based on selection order (yellow, purple, red)
  const getCategoryColor = (categoryId: number) => {
    const index = selectedCategoriesOrder.indexOf(categoryId)
    if (index === -1) return null
    
    const colors = ['#FFC700', '#6049EC', '#EB454E'] // yellow, purple, red
    return colors[index % 3]
  }

  const handleContinue = async () => {
    if (!selectedGender || selectedCategoryIds.size < 1 || selectedCategoryIds.size > 3) {
      setError(t('onboarding.errorGenderCategories'))
      return
    }

    // Проверяем наличие tg_id из Telegram
    if (!tg_id) {
      setError(t('onboarding.errorTgId'))
      return
    }

    try {
      setError(null)
      const categoryIdsArray = Array.from(selectedCategoryIds)
      
      // Получаем wallet_address из localStorage если он есть (подключен через TON Connect)
      const storedWalletAddress = localStorage.getItem('wallet_address')
      const walletAddressToUse = wallet_address || storedWalletAddress || undefined
      
      // Регистрация по tg_id (wallet_address опционален)
      const userData = await register({
        wallet_address: walletAddressToUse, // Опционально - используется если был подключен TON кошелек
        gender: selectedGender,
        category_ids: categoryIdsArray,
      })

      // Очищаем все кэшированные данные перед установкой нового пользователя
      localStorage.removeItem('user')
      
      setUser(userData)
      setLanguage(userData.language?.code || 'ru')
      await updateUser()
      
      // Небольшая задержка для гарантии обновления данных
      await new Promise(resolve => setTimeout(resolve, 100))
      
      onComplete()
    } catch (err: any) {
      setError(err.message || t('onboarding.errorRegistration'))
    }
  }

  const mainCategories = categories.slice(0, 8)
  const additionalCategories = categories.slice(8)

  const allCategories = showMoreCategories 
    ? [...mainCategories, ...additionalCategories]
    : mainCategories

  if (loading) {
    return (
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-sparks-bg pb-32">
        <div className="px-[31px] pt-8">
          <div className="mb-8">
            <CategorySkeleton className="mb-4" />
            <CategorySkeleton className="mb-4" />
            <CategorySkeleton className="mb-4" />
          </div>
          <div className="flex flex-wrap gap-3">
            <CategorySkeleton />
            <CategorySkeleton />
            <CategorySkeleton />
            <CategorySkeleton />
            <CategorySkeleton />
            <CategorySkeleton />
            <CategorySkeleton />
            <CategorySkeleton />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-sparks-bg pb-32 flex flex-col">
      {/* Main Content */}
      <div className="px-[31px] pt-8 flex-1 flex flex-col">
        {/* Greeting */}
        <div className="text-center mb-8">
          <h1 className="text-white text-xl font-bold mb-2">
            {t('onboarding.greeting', { name: userName })}
          </h1>
          <p className="text-sparks-text text-base mb-6">
            {t('onboarding.setup')}
          </p>
        </div>

        {/* Gender Selection */}
        <div className="mb-8">
          <h2 className="text-sparks-text text-base font-semibold leading-[1.375] mb-4 text-center">
            {t('onboarding.whoAreYou')}
          </h2>
          
          <div className="flex gap-4 justify-center items-start">
            {/* Male */}
            <button
              onClick={() => setSelectedGender(selectedGender === 'male' ? null : 'male')}
              className={`relative w-[104px] h-[120px] rounded-[18px] border-2 transition-all overflow-hidden ${
                selectedGender === 'male'
                  ? 'border-sparks-primary bg-sparks-primary'
                  : 'border-[#333333] bg-sparks-card-bg'
              }`}
            >
              {selectedGender === 'male' && (
                <div className="absolute top-1 right-1 w-5 h-5 bg-sparks-primary rounded-full flex items-center justify-center z-20">
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6L5 9L10 3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
              <div className="absolute inset-0 flex items-center justify-center pb-8">
                <img 
                  src={maleIcon} 
                  alt="Male" 
                  width={42} 
                  height={42}
                  style={{ 
                    filter: selectedGender === 'male' 
                      ? 'brightness(0) saturate(100%) invert(100%)' 
                      : 'brightness(0) saturate(100%) invert(50%)' 
                  }}
                />
              </div>
              <span className={`absolute bottom-2 left-1/2 -translate-x-1/2 text-sm font-medium whitespace-nowrap ${
                selectedGender === 'male' ? 'text-white' : 'text-sparks-text'
              }`}>
                {t('onboarding.male')}
              </span>
            </button>

            {/* Female */}
            <button
              onClick={() => setSelectedGender(selectedGender === 'female' ? null : 'female')}
              className={`relative w-[104px] h-[120px] rounded-[18px] border-2 transition-all overflow-hidden ${
                selectedGender === 'female'
                  ? 'border-sparks-primary bg-sparks-primary'
                  : 'border-[#333333] bg-sparks-card-bg'
              }`}
            >
              {selectedGender === 'female' && (
                <div className="absolute top-1 right-1 w-5 h-5 bg-sparks-primary rounded-full flex items-center justify-center z-20">
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6L5 9L10 3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
              <div className="absolute inset-0 flex items-center justify-center pb-8">
                <img 
                  src={coupleIcon} 
                  alt="Female" 
                  width={37} 
                  height={39}
                  style={{ 
                    filter: selectedGender === 'female' 
                      ? 'brightness(0) saturate(100%) invert(100%)' 
                      : 'brightness(0) saturate(100%) invert(50%)' 
                  }}
                />
              </div>
              <span className={`absolute bottom-2 left-1/2 -translate-x-1/2 text-sm font-medium whitespace-nowrap ${
                selectedGender === 'female' ? 'text-white' : 'text-sparks-text'
              }`}>
                {t('onboarding.female')}
              </span>
            </button>

            {/* Couple */}
            <button
              onClick={() => setSelectedGender(selectedGender === 'couple' ? null : 'couple')}
              className={`relative w-[104px] h-[120px] rounded-[18px] border-2 transition-all overflow-hidden ${
                selectedGender === 'couple'
                  ? 'border-sparks-primary bg-sparks-primary'
                  : 'border-[#333333] bg-sparks-card-bg'
              }`}
            >
              {selectedGender === 'couple' && (
                <div className="absolute top-1 right-1 w-5 h-5 bg-sparks-primary rounded-full flex items-center justify-center z-20">
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6L5 9L10 3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
              )}
              <div className="absolute inset-0 flex items-center justify-center pb-8">
                <img 
                  src={femaleIcon} 
                  alt="Couple" 
                  width={31} 
                  height={45}
                  style={{ 
                    filter: selectedGender === 'couple' 
                      ? 'brightness(0) saturate(100%) invert(100%)' 
                      : 'brightness(0) saturate(100%) invert(50%)' 
                  }}
                />
              </div>
              <span className={`absolute bottom-2 left-1/2 -translate-x-1/2 text-sm font-medium whitespace-nowrap ${
                selectedGender === 'couple' ? 'text-white' : 'text-sparks-text'
              }`}>
                {t('onboarding.couple')}
              </span>
            </button>
          </div>
        </div>

        {/* Categories Selection */}
        <div className="mb-8">
          <h2 className="text-sparks-text text-base font-semibold leading-[1.375] mb-4 text-center">
            {selectedCategoryIds.size < 1 
              ? String(t('onboarding.selectDirections1to3'))
              : String(t('onboarding.selectDirections', { count: selectedCategoryIds.size } as any))
            }
          </h2>

          <div className="flex flex-wrap gap-3 justify-center">
            {allCategories.map((category) => {
              const isSelected = selectedCategoryIds.has(category.id)
              const bgColor = isSelected 
                ? ''
                : 'bg-sparks-card-bg'
              const textColor = 'text-white'

              // Get background color based on selection order
              const selectedColor = getCategoryColor(category.id)

              return (
                <button
                  key={category.id}
                  onClick={() => toggleCategory(category.id)}
                  disabled={!isSelected && selectedCategoryIds.size >= 5}
                  className={`relative px-4 py-2.5 rounded-[123px] text-xl font-medium leading-[1.19] transition-all flex items-center gap-2 ${
                    !isSelected ? bgColor : ''
                  } ${textColor} ${
                    !isSelected && selectedCategoryIds.size >= 5
                      ? 'opacity-50 cursor-not-allowed'
                      : 'cursor-pointer hover:opacity-80'
                  }`}
                  style={selectedColor ? { backgroundColor: selectedColor } : {}}
                >
                  {category.name}
                </button>
              )
            })}
            
            {/* More categories button */}
            {!showMoreCategories && additionalCategories.length > 0 && (
              <button
                onClick={() => setShowMoreCategories(true)}
                className="px-4 py-2.5 rounded-[123px] text-xl font-medium leading-[1.19] bg-sparks-card-bg text-white cursor-pointer hover:opacity-80 transition-all"
              >
                •••
              </button>
            )}
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 px-4 py-2 bg-red-500/20 border border-red-500 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Continue Button */}
        <div className="flex justify-center mt-8 mb-8 px-[25px]">
          <button 
            onClick={handleContinue}
            disabled={authLoading || !selectedGender || selectedCategoryIds.size < 1}
            className="w-full max-w-[344px] h-16 bg-sparks-button-active rounded-[123px] flex items-center justify-center px-2.5 py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-white text-xl font-semibold leading-[1.1] font-sf-pro-display">
              {authLoading ? t('onboarding.loading') : t('onboarding.continue')}
            </span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding
