import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useApp } from '../context/AppContext'
import apiClient from '../lib/api'
import i18n from '../lib/i18n'
import closeIcon from '../assets/icons/settings/close-icon.svg'

interface Language {
  code: string
  name: string
  is_active: boolean
}

interface LanguageSettingsProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  onClose?: () => void
  onOpenSettings?: () => void
}

const LanguageSettings = ({ onNavigate, onClose, onOpenSettings }: LanguageSettingsProps) => {
  const { t } = useTranslation()
  const { user, setUser, setLanguage, updateUser } = useApp()
  const [languages, setLanguages] = useState<Language[]>([])
  const [selectedLanguageCode, setSelectedLanguageCode] = useState<string>('ru')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Загрузка языков
  useEffect(() => {
    const loadLanguages = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get<{ languages: Language[] }>('/languages/')
        setLanguages(response.data.languages)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadLanguages()
  }, [])

  // Установка текущего языка пользователя
  useEffect(() => {
    if (user && user.language) {
      setSelectedLanguageCode(user.language.code)
    }
  }, [user])

  const handleLanguageChange = async (languageCode: string) => {
    if (languageCode === selectedLanguageCode) {
      return
    }

    try {
      setSaving(true)
      setError(null)
      
      const response = await apiClient.put('/profile/language', {
        language_code: languageCode
      })
      
      setUser(response.data)
      setLanguage(languageCode)
      i18n.changeLanguage(languageCode)
      await updateUser()
      
      // Закрываем страницу после сохранения
      if (onClose) {
        onClose()
      } else {
        sessionStorage.setItem('openSettings', 'true')
        onNavigate?.('profile')
      }
    } catch (err: any) {
      setError(err.message || t('languageSettings.error'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 z-[300] flex items-end justify-center">
        <div className="fixed inset-0 bg-black/50 z-[300]" />
        <div className="relative w-full max-w-[393px] bg-[#1E1E1E] rounded-t-3xl overflow-hidden p-6 z-[301]">
          <div className="text-center text-[#808080] py-8">{t('common.loading')}</div>
        </div>
      </div>
    )
  }

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
          <h1 className="text-white text-2xl font-semibold">{t('languageSettings.title')}</h1>
          <button 
            onClick={onClose || (() => onNavigate?.('profile'))}
            className="w-10 h-10 flex items-center justify-center"
          >
            <img src={closeIcon} alt="Close" width={24} height={24} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 overflow-y-auto flex-1 min-h-0">
          {/* Error message */}
          {error && (
            <div className="mb-4 px-4 py-2 bg-red-500/20 border border-red-500 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Languages List */}
          <div className="space-y-0 mb-6">
            {languages.map((lang) => (
              <div key={lang.code} className="border-b border-[#2E2E2E]">
                <button
                  onClick={() => handleLanguageChange(lang.code)}
                  disabled={saving}
                  className="w-full flex items-center justify-between py-4 px-0 hover:bg-[#1F1F1F] transition-colors disabled:opacity-50"
                >
                  <span className="text-white text-base font-medium">{lang.name}</span>
                  {selectedLanguageCode === lang.code && (
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <path
                        d="M16.6667 5L7.50004 14.1667L3.33337 10"
                        stroke="#6049EC"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </button>
              </div>
            ))}
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

export default LanguageSettings
