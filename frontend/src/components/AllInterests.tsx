import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useApp } from '../context/AppContext'
import apiClient from '../lib/api'
import { CategorySkeleton } from './SkeletonLoader'
import closeIcon from '../assets/icons/settings/close-icon.svg'

interface Category {
  id: number
  slug: string
  name: string
  color: string
  is_active: boolean
}

interface AllInterestsProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  onClose?: () => void
}

const AllInterests = ({ onNavigate, onClose }: AllInterestsProps) => {
  const { t } = useTranslation()
  const { user, setUser, language, updateUser } = useApp()
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
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
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadCategories()
  }, [language])

  // Установка выбранных категорий из профиля пользователя
  useEffect(() => {
    if (user && user.interests) {
      const selectedIds = new Set(user.interests.map(i => i.id))
      setSelectedCategoryIds(selectedIds)
    }
  }, [user])

  const toggleCategory = (categoryId: number) => {
    const newSet = new Set(selectedCategoryIds)
    
    if (newSet.has(categoryId)) {
      newSet.delete(categoryId)
    } else if (newSet.size < 3) {
      newSet.add(categoryId)
    }
    
    setSelectedCategoryIds(newSet)
  }

  const handleSave = async () => {
    if (selectedCategoryIds.size < 1 || selectedCategoryIds.size > 3) {
      setError(t('allInterests.errorCategories'))
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const categoryIdsArray = Array.from(selectedCategoryIds)
      const response = await apiClient.put('/profile/interests', {
        category_ids: categoryIdsArray
      })
      
      setUser(response.data)
      // Обновляем пользователя в контексте
      await updateUser()
      onClose?.()
    } catch (err: any) {
      setError(err.message || t('allInterests.error'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden">
        <div className="px-6 pt-6 pb-32">
          <div className="flex flex-wrap gap-3 mb-6">
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
    <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden">
      {/* Balance at top */}
      <div className="flex justify-center items-center gap-2 pt-6 pb-4">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#FFC700] to-[#FFA500]"></div>
        <span className="text-sparks-text text-base font-semibold">{user?.balance || 0}</span>
      </div>

      {/* Content */}
      <div className="px-6 pt-6 pb-32">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-white text-2xl font-semibold">{t('allInterests.title')}</h1>
          {onClose && (
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center"
            >
              <img src={closeIcon} alt="Close" width={24} height={24} />
            </button>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 px-4 py-2 bg-red-500/20 border border-red-500 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Interests List */}
        <div className="flex flex-wrap gap-3 mb-6">
          {categories.map((category) => {
            const isSelected = selectedCategoryIds.has(category.id)
            const bgColor = isSelected ? category.color : '#2E2E2E'

            return (
              <button
                key={category.id}
                onClick={() => toggleCategory(category.id)}
                disabled={!isSelected && selectedCategoryIds.size >= 3}
                className="px-4 py-2.5 rounded-[123px] text-xl font-medium leading-[1.19] transition-all flex items-center gap-2 text-white cursor-pointer hover:opacity-80 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: bgColor }}
              >
                {category.name}
              </button>
            )
          })}
        </div>

        {/* Save Button */}
        <div className="flex justify-center mt-8">
          <button
            onClick={handleSave}
            disabled={saving || selectedCategoryIds.size < 1}
            className="w-full max-w-[344px] h-16 bg-sparks-button-active rounded-[123px] flex items-center justify-center px-2.5 py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-white text-xl font-semibold leading-[1.1] font-sf-pro-display">
              {saving ? t('allInterests.saving') : t('allInterests.save')}
            </span>
          </button>
        </div>
      </div>

      {/* FOOT - Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 w-full max-w-[393px] mx-auto">
        <div className="relative h-[80px] overflow-hidden bg-[#171717]">
          {/* Navigation Menu - 4 icons */}
          <div className="relative flex justify-center items-center gap-16 pt-6 pb-4 z-10">
            <button onClick={() => onNavigate?.('home')} className="cursor-pointer">
              <svg width="22" height="26" viewBox="0 0 22 26" fill="none">
                <path d="M6.51321 0.569177C7.31867 0.0478392 8.21651 -0.0587738 9.24673 0.0261852C10.2535 0.109292 11.5025 0.387387 13.0613 0.731293L15.2978 1.2235L16.4091 1.47058C17.4624 1.70896 18.3428 1.92817 19.0548 2.18936C20.0264 2.54587 20.7959 3.01941 21.3117 3.82908C21.8269 4.63824 21.9331 5.53903 21.8498 6.57529C21.7682 7.5889 21.4945 8.8463 21.1545 10.4182L18.9385 21.4656C18.9329 21.4939 18.9255 21.5216 18.9171 21.5486C18.9167 21.5524 18.9174 21.5565 18.9171 21.5603C18.8207 22.6157 18.5499 23.4988 17.874 24.2176L17.875 24.2186C17.2028 24.9346 16.3294 25.2721 15.2655 25.4618C14.2218 25.6479 12.8794 25.7099 11.1941 25.789L8.77894 25.9023C7.0937 25.9814 5.75132 26.0454 4.69478 25.9579C3.61762 25.8687 2.71621 25.6138 1.97982 24.9638V24.9647C1.23931 24.3123 0.888456 23.4568 0.693633 22.4148C0.503631 21.3982 0.443964 20.0919 0.367447 18.4615L0.0930215 12.6117C0.0164902 10.9811 -0.0468875 9.67475 0.0471211 8.64471C0.143525 7.58891 0.412747 6.7044 1.08916 5.98542C1.76131 5.26974 2.63498 4.93188 3.69864 4.7422C3.83507 4.71789 3.97673 4.69518 4.12347 4.67482C4.34687 3.83162 4.66502 3.01395 5.04343 2.32023C5.43062 1.61051 5.92406 0.950649 6.51321 0.569177ZM14.1385 5.84088C13.21 5.76395 11.9897 5.82028 10.2604 5.90143L7.8453 6.01472C6.11595 6.09587 4.89619 6.15391 3.97893 6.31747C3.0822 6.47739 2.59488 6.71939 2.25522 7.08117V7.08215C1.91851 7.44003 1.71923 7.92232 1.63996 8.79023C1.55843 9.68394 1.61204 10.8596 1.69075 12.5365L1.96517 18.3863C2.04389 20.0636 2.10103 21.2396 2.26596 22.1218C2.40614 22.8713 2.60905 23.319 2.90466 23.6366L3.03846 23.7645C3.41047 24.0929 3.91805 24.2879 4.82564 24.3632C5.75419 24.4401 6.97438 24.3847 8.70374 24.3036L11.1189 24.1903C12.8482 24.1091 14.068 24.0501 14.9853 23.8866C15.8819 23.7266 16.3683 23.4847 16.708 23.1229H16.709C17.0457 22.7649 17.244 22.2828 17.3232 21.4148C17.4048 20.5209 17.3522 19.345 17.2734 17.6676L16.999 11.8187C16.9203 10.1413 16.8622 8.96542 16.6972 8.08317C16.5371 7.22678 16.2953 6.76526 15.9267 6.44052L15.9247 6.43954C15.5528 6.1115 15.0457 5.91611 14.1385 5.84088ZM9.6569 13.3373C9.9957 13.0873 10.5709 12.9144 11.2546 13.2465C12.1519 13.6829 12.4235 15.2475 10.4685 16.6695L10.4665 16.6704C10.0946 16.9407 9.90879 17.0756 9.57584 17.0914C9.32581 17.1031 9.15182 17.0399 8.91371 16.9087L8.64807 16.7544C6.56769 15.5217 6.69093 13.9383 7.54353 13.4203C8.19332 13.0256 8.78252 13.1444 9.14321 13.3617C9.29069 13.4504 9.36492 13.4945 9.40689 13.4926C9.44892 13.4903 9.51868 13.4392 9.6569 13.3373ZM9.11586 1.62098C8.26619 1.55086 7.77433 1.65901 7.38337 1.91201C7.12129 2.08156 6.78376 2.47005 6.44778 3.08588C6.21887 3.5055 6.01019 3.995 5.83838 4.51759C6.42489 4.48057 7.06765 4.44898 7.7701 4.41602L10.1852 4.30273C11.8704 4.22366 13.2129 4.15863 14.2694 4.24609C15.346 4.33529 16.2472 4.59001 16.9834 5.2393C17.7242 5.89174 18.0757 6.74711 18.2705 7.78921C18.4607 8.80597 18.5202 10.1127 18.5967 11.7435L18.7217 14.4116L19.588 10.092L19.5909 10.0803C19.9404 8.46435 20.183 7.32889 20.254 6.44638C20.3231 5.58705 20.2163 5.08642 19.963 4.68849C19.71 4.29134 19.3052 3.98541 18.504 3.69138C17.68 3.38905 16.5562 3.14074 14.953 2.78704L12.7166 2.29288C11.1133 1.93916 9.98938 1.69312 9.11586 1.62098Z" fill="#808080"/>
              </svg>
            </button>

            <button onClick={() => onNavigate?.('dailyBonus')} className="cursor-pointer">
              <svg width="25" height="23" viewBox="0 0 25 23" fill="none">
                <path d="M24.1993 11.3301H24.1888M19.5301 11.3301H19.5196M10.7592 6.06538H10.7475M0.80076 11.3301C0.80076 17.1446 5.4138 21.8594 11.1032 21.8594C13.9894 21.8594 16.5983 20.6462 18.469 18.6924C19.2178 17.9086 19.5922 17.5178 19.5079 16.8779C19.4225 16.2379 18.8797 15.9173 17.794 15.2762L16.9072 14.7533C14.3298 13.2324 13.0406 12.4719 13.0406 11.3301C13.0406 10.1882 14.3298 9.42658 16.9072 7.90685L17.794 7.38272C18.8797 6.74277 19.4225 6.42338 19.5079 5.78226C19.5933 5.1423 19.2189 4.75038 18.469 3.9677C16.5983 2.01392 13.9894 0.800699 11.1032 0.800699C5.4138 0.800699 0.80076 5.51551 0.80076 11.3301Z" stroke="#808080" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            <button onClick={() => onNavigate?.('sparksPurchase')} className="cursor-pointer">
              <svg width="17" height="24" viewBox="0 0 17 24" fill="none">
                <path d="M1.05436 11.2505L8.50962 1.20117C9.09382 0.415624 10.1851 0.904107 10.1851 1.95068V9.72911C10.1851 10.3568 10.614 10.8639 11.1422 10.8639H14.7692C15.5932 10.8639 16.032 12.0162 15.4876 12.7507L8.03233 22.7988C7.44814 23.5844 6.35682 23.0959 6.35682 22.0493V14.2709C6.35682 13.6432 5.928 13.1361 5.39974 13.1361H1.77154C0.947463 13.1361 0.509941 11.9838 1.05436 11.2505Z" stroke="#808080" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            <button onClick={() => onNavigate?.('profile')} className="cursor-pointer">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 23.1863C18.1781 23.1863 23.1864 18.178 23.1864 11.9999C23.1864 5.82186 18.1781 0.813544 12 0.813544C5.82192 0.813544 0.813606 5.82186 0.813606 11.9999C0.813606 18.178 5.82192 23.1863 12 23.1863Z" stroke="#808080" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M6.96617 17.5931C9.57484 14.8614 14.3973 14.7327 17.0339 17.5931M14.7911 9.20328C14.7911 10.747 13.5382 11.9999 11.9911 11.9999C11.6235 12.0005 11.2593 11.9286 10.9195 11.7883C10.5797 11.648 10.2709 11.4421 10.0107 11.1824C9.75055 10.9226 9.54415 10.6141 9.40333 10.2745C9.26251 9.93493 9.19003 9.57091 9.19003 9.20328C9.19003 7.65956 10.4429 6.40668 11.9911 6.40668C12.3586 6.40624 12.7227 6.47825 13.0623 6.61859C13.402 6.75894 13.7107 6.96487 13.9708 7.2246C14.2308 7.48433 14.4371 7.79277 14.5779 8.13229C14.7186 8.47181 14.7911 8.83574 14.7911 9.20328Z" stroke="#808080" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AllInterests
