import { useState } from 'react'
import closeIcon from '../assets/icons/settings/close-icon.svg'

interface FAQProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  onClose?: () => void
  onOpenSettings?: () => void
}

const FAQ = ({ onNavigate, onClose, onOpenSettings }: FAQProps) => {
  const [openQuestion, setOpenQuestion] = useState<number | null>(null)

  const questions = [
    {
      id: 1,
      question: 'Что такое Sparks?',
      answer: 'Sparks — это приложение для пар, которое помогает разнообразить отношения через интересные задания и челленджи.',
    },
    {
      id: 2,
      question: 'Как заработать искры?',
      answer: 'Искры можно заработать, выполняя ежедневные задания, получая ежедневные бонусы или приобретая их в магазине.',
    },
    {
      id: 3,
      question: 'Как работают задания?',
      answer: 'Каждый день вам доступны бесплатные задания. После их выполнения вы получаете новые задания на следующий день.',
    },
    {
      id: 4,
      question: 'Можно ли использовать приложение бесплатно?',
      answer: 'Да, приложение можно использовать бесплатно. Ежедневно доступны бесплатные задания. Для большего количества заданий можно приобрести искры.',
    },
  ]

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
          <h1 className="text-white text-2xl font-semibold">Вопросы и ответы</h1>
          <button 
            onClick={onClose || (() => onNavigate?.('profile'))}
            className="w-10 h-10 flex items-center justify-center"
          >
            <img src={closeIcon} alt="Close" width={24} height={24} />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 overflow-y-auto flex-1 min-h-0">
          {/* FAQ List */}
          <div className="space-y-0 mb-6">
            {questions.map((item) => (
              <div key={item.id} className="border-b border-[#2E2E2E]">
                <button
                  onClick={() => setOpenQuestion(openQuestion === item.id ? null : item.id)}
                  className="w-full flex items-center justify-between py-4"
                >
                  <span className="text-white text-base font-medium text-left pr-4">{item.question}</span>
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 20 20"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className={`transition-transform ${openQuestion === item.id ? 'rotate-180' : ''}`}
                  >
                    <path
                      d="M5 7.5L10 12.5L15 7.5"
                      stroke="#808080"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
                {openQuestion === item.id && (
                  <div className="pb-4">
                    <p className="text-[#808080] text-sm leading-relaxed">{item.answer}</p>
                  </div>
                )}
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

export default FAQ
