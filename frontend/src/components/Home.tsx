import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { animated, useSprings } from '@react-spring/web'
import { useApp } from '../context/AppContext'
import apiClient from '../lib/api'
import { TaskCardSkeleton } from './SkeletonLoader'
import paginationLockIcon from '../assets/icons/pagination-lock.svg'
import lightningLargeIcon from '../assets/icons/lightning-large.svg'
import coinIcon from '../assets/icons/coin-icon.svg'
import logoTaskIcon from '../assets/icons/Logo_task.svg'
import arrowLeftIcon from '../assets/icons/arrow-left.svg'
import arrowRightIcon from '../assets/icons/arrow-right.svg'
import BottomNavigation from './BottomNavigation'

interface Task {
  id: number
  title: string
  description: string
  category: {
    id: number
    name: string
    color: string
  }
  is_free: boolean
  is_completed: boolean
}

interface HomeProps {
  onNavigate?: (page: 'welcome' | 'onboarding' | 'home' | 'profile' | 'dailyBonus' | 'sparksPurchase' | 'allInterests' | 'notificationsSettings' | 'languageSettings' | 'faq' | 'support' | 'news') => void
  hideBottomNavigation?: boolean
}

const Home = ({ onNavigate, hideBottomNavigation = false }: HomeProps) => {
  const { t } = useTranslation()
  const { user, balance, setBalance, setUser } = useApp()
  const [tasks, setTasks] = useState<Task[]>([])
  const [currentCardIndex, setCurrentCardIndex] = useState(0)
  const [freeRemaining, setFreeRemaining] = useState(3)
  const [paidAvailable, setPaidAvailable] = useState(0)
  const [resetAt, setResetAt] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [buying, setBuying] = useState(false)
  
  // Максимальное количество доступных карточек (бесплатные + купленные)
  const maxAvailableCards = freeRemaining + paidAvailable
  // Доступные карточки для показа - показываем ВСЕ задания для навигации назад
  const availableTasks = tasks
  // Проверка, нужно ли показывать страницу offer (когда есть задания и достигнут лимит доступных карточек)
  // Offer показывается только если есть задания и пользователь может пролистать все доступные
  const shouldShowOffer = maxAvailableCards > 0 && availableTasks.length > 0
  // Общее количество карточек в карусели (задания + offer если нужно)
  const totalCards = availableTasks.length + (shouldShowOffer ? 1 : 0)

  // Вычисление времени до следующего 00:00 МСК
  const calculateTimeUntilReset = (): Date => {
    const now = new Date()
    const moscowTimeStr = now.toLocaleString('sv-SE', { timeZone: 'Europe/Moscow' })
    const [datePart] = moscowTimeStr.split(' ')
    const [year, month, day] = datePart.split('-').map(Number)

    // Целевое время: 00:00 следующего дня по МСК
    const resetUTC = Date.UTC(year, month - 1, day + 1, 0, 0, 0) // следующая дата 00:00 по календарю
    const moscowOffset = 3 * 60 * 60 * 1000 // UTC+3

    // Переводим 00:00 МСК в UTC и создаем локальный Date
    const resetTime = new Date(resetUTC - moscowOffset)
    return resetTime
  }

  // Функция загрузки заданий
  const loadTasks = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get<{ tasks: Task[]; total: number; free_remaining: number; paid_available?: number }>(
        '/tasks/',
        {
          params: { limit: 20, offset: 0 }
        }
      )
      // Фильтруем выполненные задания и нормализуем id в число
      const filteredTasks = response.data.tasks
        .filter((task: Task) => !task.is_completed)
        .map((task: Task) => {
          const idNumber = Number(task.id)
          return {
            ...task,
            id: Number.isFinite(idNumber) ? idNumber : task.id,
          }
        })
        .filter((task: Task) => Number.isInteger(task.id))

      console.log('Loaded tasks:', {
        total: response.data.tasks.length,
        filtered: filteredTasks.length,
        free_remaining: response.data.free_remaining,
        user_tg_id: user?.tg_id,
        all_tasks: response.data.tasks.map(t => ({ id: t.id, title: t.title, is_completed: t.is_completed }))
      })

      setTasks(filteredTasks)
      setFreeRemaining(response.data.free_remaining)
      setPaidAvailable(response.data.paid_available || 0)
      
      // Если текущий индекс больше чем доступных карточек, корректируем его
      const newMaxAvailable = (response.data.free_remaining || 0) + (response.data.paid_available || 0)
      if (currentCardIndex >= newMaxAvailable && newMaxAvailable > 0) {
        // Переходим на страницу offer (последняя карточка)
        setCurrentCardIndex(newMaxAvailable)
      } else if (currentCardIndex >= filteredTasks.length && filteredTasks.length > 0) {
        // Если индекс больше чем заданий, но есть задания - переходим на последнее задание
        setCurrentCardIndex(Math.min(newMaxAvailable - 1, filteredTasks.length - 1))
      } else if (filteredTasks.length === 0) {
        // Если нет заданий, сбрасываем индекс
        setCurrentCardIndex(0)
      }

      // Вычисляем время сброса до следующего 00:00 МСК
      const resetTime = calculateTimeUntilReset()
      setResetAt(resetTime)
    } catch (error) {
      console.error('Error loading tasks:', error)
      // При ошибке сбрасываем индекс
      if (tasks.length === 0) {
        setCurrentCardIndex(0)
      }
    } finally {
      setLoading(false)
    }
  }

  // Загрузка заданий при монтировании или изменении user
  useEffect(() => {
    if (user) {
      // Сбрасываем состояние перед загрузкой новых заданий
      setTasks([])
      setCurrentCardIndex(0)
      setFreeRemaining(3) // Сбрасываем на начальное значение
      loadTasks()
    } else if (!user) {
      // Если пользователя нет, сбрасываем все состояние
      setTasks([])
      setCurrentCardIndex(0)
      setFreeRemaining(3)
    }
  }, [user])

  // Автоматическая загрузка заданий при изменении баланса (после пополнения)
  // Убрано, чтобы избежать бесконечной перезагрузки
  // Задания загружаются только при монтировании или изменении user

  const [completingTask, setCompletingTask] = useState(false)
  const [lastClickTime, setLastClickTime] = useState(0)

  // Упрощенная анимация карточек (включая offer страницу) с плавным переходом
  const [springs] = useSprings(
    totalCards,
    (index: number) => ({
      opacity: index === currentCardIndex ? 1 : index === currentCardIndex + 1 ? 0.7 : index === currentCardIndex - 1 ? 0.7 : 0.5,
      scale: index === currentCardIndex ? 1 : index === currentCardIndex + 1 ? 0.98 : index === currentCardIndex - 1 ? 0.98 : 0.96,
      config: { tension: 200, friction: 40 }, // Более плавная анимация: меньше tension, больше friction
    }),
    [totalCards, currentCardIndex]
  )

  // Обработчик двойного клика
  const handleDoubleClick = async () => {
    if (completingTask || currentCardIndex >= tasks.length) {
      return
    }

    const currentTask = tasks[currentCardIndex]
    const taskIdNumber = Number(currentTask?.id)
    if (!currentTask || !Number.isInteger(taskIdNumber) || taskIdNumber <= 0) {
      console.warn('Некорректный id задания, пропускаем выполнение', currentTask?.id)
      return
    }

    setCompletingTask(true)

    try {
      // Выполнение задания через API
      const response = await apiClient.post<{ success: boolean; message: string; balance: number }>(
        `/tasks/${taskIdNumber}/complete`
      )

      // Обновление баланса
      if (response.data.balance !== undefined) {
        setBalance(response.data.balance)
        if (user) {
          setUser({ ...user, balance: response.data.balance })
        }
        // Не вызываем updateUser здесь, чтобы избежать лишних запросов и ошибок 404
        // Баланс уже обновлен из ответа API
      }

      // Обновление количества бесплатных заданий - получаем актуальное значение с сервера
      let newFreeRemaining = freeRemaining
      try {
        const freeCountResponse = await apiClient.get<{ remaining: number; reset_at: string; paid_available?: number }>(
          '/tasks/daily-free-count'
        )
        newFreeRemaining = freeCountResponse.data.remaining
        setFreeRemaining(newFreeRemaining)
        setPaidAvailable(freeCountResponse.data.paid_available || 0)
        // Вычисляем время сброса до следующего 00:00 МСК
        const resetTime = calculateTimeUntilReset()
        setResetAt(resetTime)
      } catch (freeCountError: any) {
        // Если ошибка при получении количества бесплатных заданий, уменьшаем локально
        console.warn('Error loading daily free count:', freeCountError)
        // Уменьшаем счетчик локально только если задание было бесплатным
        // Проверяем, было ли задание бесплатным (если freeRemaining > 0, то скорее всего было бесплатным)
        if (freeRemaining > 0) {
          newFreeRemaining = Math.max(0, freeRemaining - 1)
          setFreeRemaining(newFreeRemaining)
        }
        // Вычисляем время сброса до следующего 00:00 МСК
        const resetTime = calculateTimeUntilReset()
        setResetAt(resetTime)
      }

      // Удаление выполненного задания из списка
      const remainingTasks = tasks.filter(t => t.id !== currentTask.id)

      // Обновление индекса после выполнения задания
      setTasks(remainingTasks) // Обновляем список заданий
      
      const newMaxAvailable = newFreeRemaining + paidAvailable
      if (remainingTasks.length === 0) {
        // Нет заданий - переходим на начало или на offer если нет доступных попыток
        if (newMaxAvailable <= 0) {
          setCurrentCardIndex(0) // Будет показана страница offer (если она есть)
        } else {
          setCurrentCardIndex(0)
        }
      } else {
        // Есть задания - остаемся на текущей позиции или корректируем если нужно
        if (currentCardIndex >= remainingTasks.length) {
          // Если индекс больше чем заданий, переходим на последнее доступное задание или offer
          const newTotalCards = remainingTasks.length + (newMaxAvailable > 0 ? 1 : 0)
          setCurrentCardIndex(Math.min(newMaxAvailable, newTotalCards - 1))
        }
        // Иначе остаемся на текущей позиции
      }
    } catch (error: any) {
      console.error('Error completing task:', error)

      // Извлекаем сообщение об ошибке
      let errorMessage = 'Ошибка выполнения задания';
      if (error?.message) {
        if (typeof error.message === 'string') {
          errorMessage = error.message;
        } else if (Array.isArray(error.message)) {
          errorMessage = error.message.map((err: any) => {
            if (typeof err === 'string') return err;
            if (err?.msg) return err.msg;
            return JSON.stringify(err);
          }).join(', ');
        }
      } else if (error?.data?.detail) {
        if (typeof error.data.detail === 'string') {
          errorMessage = error.data.detail;
        } else if (Array.isArray(error.data.detail)) {
          errorMessage = error.data.detail.map((err: any) => {
            if (typeof err === 'string') return err;
            if (err?.msg) return err.msg;
            return JSON.stringify(err);
          }).join(', ');
        }
      }

      // Показываем ошибку только если это не ошибка валидации (422)
      if (error?.status !== 422) {
        const { showError } = await import('../lib/toast');
        showError(errorMessage);
      }

    } finally {
      setCompletingTask(false)
    }
  }

  // Обработчик клика для определения двойного клика
  const handleCardClick = () => {
    const now = Date.now()
    const timeSinceLastClick = now - lastClickTime

    if (timeSinceLastClick < 300) {
      // Двойной клик
      handleDoubleClick()
      setLastClickTime(0)
    } else {
      setLastClickTime(now)
    }
  }

  // Корректировка индекса при изменении доступных карточек
  useEffect(() => {
    if (!loading && !completingTask) {
      const newMaxAvailable = freeRemaining + paidAvailable
      const newTotalCards = availableTasks.length + (newMaxAvailable > 0 && availableTasks.length > 0 ? 1 : 0)
      
      // Если текущий индекс больше чем доступных карточек и есть offer страница, переходим на offer
      if (currentCardIndex >= newMaxAvailable && newMaxAvailable > 0 && newTotalCards > availableTasks.length) {
        // Переходим на страницу offer (последняя карточка)
        setCurrentCardIndex(availableTasks.length)
      } else if (currentCardIndex >= newTotalCards && newTotalCards > 0) {
        // Если индекс больше чем общее количество карточек, переходим на последнюю
        setCurrentCardIndex(newTotalCards - 1)
      }
    }
  }, [freeRemaining, paidAvailable, availableTasks.length, loading, completingTask, currentCardIndex])

  // Таймер обратного отсчета
  const [timeRemaining, setTimeRemaining] = useState<string>('')
  // Проверка, находимся ли мы на странице offer
  const isOnOfferPage = shouldShowOffer && currentCardIndex === availableTasks.length

  useEffect(() => {
    if (!resetAt || !isOnOfferPage) return

    const updateTimer = () => {
      const now = new Date()
      const diff = resetAt.getTime() - now.getTime()

      if (diff <= 0) {
        setTimeRemaining('0 ч 0 мин 0 сек')
        return
      }

      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      const seconds = Math.floor((diff % (1000 * 60)) / 1000)

      setTimeRemaining(t('home.timeFormat', { hours, minutes, seconds }))
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)

    return () => clearInterval(interval)
  }, [resetAt, isOnOfferPage])

  // Обработчик навигации стрелками с плавной анимацией
  const handlePreviousCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(prev => prev - 1)
    }
  }

  const handleNextCard = () => {
    // Если мы на последнем доступном задании (maxAvailableCards - 1) и есть offer страница, переходим на offer
    if (currentCardIndex === maxAvailableCards - 1 && shouldShowOffer) {
      setCurrentCardIndex(availableTasks.length) // Переходим на offer страницу
    } else if (currentCardIndex < availableTasks.length - 1) {
      // Переходим к следующему заданию, если оно есть
      setCurrentCardIndex(prev => prev + 1)
    } else if (currentCardIndex < totalCards - 1 && currentCardIndex >= maxAvailableCards) {
      // Если мы уже на offer странице или после неё, можем листать дальше
      setCurrentCardIndex(prev => prev + 1)
    }
  }

  // Если показываем Offer страницу
  const handlePurchase = async () => {
    if (buying || balance < 10) return
    try {
      setBuying(true)
      const response = await apiClient.post<{ success: boolean; balance: number; free_remaining: number; paid_available: number }>(
        '/tasks/purchase-extra'
      )
      if (response.data.success) {
        setBalance(response.data.balance)
        if (user) {
          setUser({ ...user, balance: response.data.balance })
        }
        setFreeRemaining(response.data.free_remaining)
        setPaidAvailable(response.data.paid_available)
        // Перезагружаем задания, чтобы получить новое задание
        await loadTasks()
        // После покупки новое задание добавляется перед страницей offer
        // Если мы были на странице offer, переходим на новое задание
        const newMaxAvailable = response.data.free_remaining + response.data.paid_available
        if (currentCardIndex >= maxAvailableCards) {
          // Мы были на странице offer - переходим на новое задание
          setCurrentCardIndex(newMaxAvailable - 1)
        }
      } else {
        const { showError } = await import('../lib/toast')
        showError(t('home.topUp'))
      }
    } catch (error: any) {
      console.error('Error purchasing task:', error)
      const { showError } = await import('../lib/toast')
      showError(error?.message || t('home.topUp'))
    } finally {
      setBuying(false)
    }
  }

  if ((availableTasks.length === 0 || maxAvailableCards === 0) && !shouldShowOffer) {
    // Показываем обычную страницу покупки, если нет карточек
    return (
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden flex flex-col">
        {/* Balance at top */}
        <div className="flex justify-center items-center gap-2 pt-6 pb-4">
          <img src={coinIcon} alt="Coin" width={24} height={24} />
          <span className="text-sparks-text text-base font-semibold">{balance}</span>
        </div>

        {/* Offer Content */}
        <div className="flex-1 flex flex-col items-center justify-center px-8 pb-32">
          {/* Large Lightning Icon */}
          <div className="mb-8">
            <img src={lightningLargeIcon} alt="Lightning" className="w-[63px] h-[104px]" />
          </div>

          {/* Title */}
          <h1 className="text-white text-xl font-semibold text-center mb-4 leading-tight">
            {t('home.freeTasksEnded')}
          </h1>

          {/* Description */}
          <p className="text-[#808080] text-sm text-center mb-8 leading-relaxed px-4">
            {t('home.comeTomorrow')}
          </p>

          {/* Button */}
          {balance >= 10 ? (
            <button
              className="w-full max-w-[280px] h-14 rounded-full bg-[#EB454E] flex items-center justify-center mb-6 transition-opacity hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed"
              disabled={buying}
              onClick={handlePurchase}
            >
              <span className="text-white text-base font-semibold">{t('home.openFor10')}</span>
            </button>
          ) : (
            <button
              className="w-full max-w-[280px] h-14 rounded-full bg-[#EB454E] flex items-center justify-center mb-6 transition-opacity hover:opacity-90"
              onClick={() => {
                onNavigate?.('sparksPurchase')
              }}
            >
              <span className="text-white text-base font-semibold">{t('home.topUp')}</span>
            </button>
          )}

          {/* Timer */}
          <p className="text-white text-sm text-center">
            {t('home.newSparksIn')} {timeRemaining}
          </p>
        </div>

        {/* Pagination */}
        <div className="flex justify-center items-center gap-2 mb-8">
          {[0, 1, 2].map((index) => (
            <div
              key={index}
              className="w-2 h-2 rounded-full bg-[#333333] transition-all duration-300"
            ></div>
          ))}
          <div className="flex items-center justify-center w-[57px] h-[11px]">
            <img src={paginationLockIcon} alt="Lock" className="w-[57px] h-[11px]" />
          </div>
        </div>

        {/* Bottom Navigation */}
        <BottomNavigation onNavigate={onNavigate} currentPage="home" hide={hideBottomNavigation} />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden">
        {/* Balance at top */}
        <div className="flex justify-center items-center gap-2 pt-6 pb-4">
          <img src={coinIcon} alt="Coin" width={24} height={24} />
          <span className="text-sparks-text text-base font-semibold">{balance}</span>
        </div>

        {/* Skeleton loader */}
        <div className="relative px-[38px] pt-4 pb-32">
          <div className="relative flex justify-center" style={{ height: '488.53px' }}>
            <TaskCardSkeleton />
          </div>
        </div>

        {/* Bottom Navigation */}
        <BottomNavigation onNavigate={onNavigate} hide={hideBottomNavigation} />
      </div>
    )
  }

  if (tasks.length === 0) {
    return (
      <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] flex flex-col">
        {/* Balance at top */}
        <div className="flex justify-center items-center gap-2 pt-6 pb-4">
          <img src={coinIcon} alt="Coin" width={24} height={24} />
          <span className="text-sparks-text text-base font-semibold">{balance}</span>
        </div>

        {/* Content */}
        <div className="flex-1 flex items-center justify-center pb-32">
          <div className="text-sparks-text text-center">
            <p className="mb-4">{t('home.noTasks')}</p>
            <button
              onClick={() => onNavigate?.('sparksPurchase')}
              className="px-6 py-3 bg-sparks-primary rounded-full text-white"
            >
              {t('home.topUpBalance')}
            </button>
          </div>
        </div>

        {/* Bottom Navigation */}
        <BottomNavigation onNavigate={onNavigate} currentPage="home" hide={hideBottomNavigation} />
      </div>
    )
  }

  return (
    <div className="relative w-full max-w-[393px] mx-auto min-h-screen bg-[#171717] overflow-hidden flex flex-col">
      {/* Balance at top */}
      <div className="flex justify-center items-center gap-2 pt-6 pb-4">
        <img src={coinIcon} alt="Coin" width={24} height={24} />
        <span className="text-sparks-text text-base font-semibold">{balance}</span>
      </div>

      {/* Cards Section with Animation */}
      <div className="relative px-[38px] flex-1 flex items-center justify-center pb-32">
        {/* Left Arrow - показываем если не на первой карточке и модалка не открыта */}
        {currentCardIndex > 0 && !hideBottomNavigation && (
          <button
            onClick={handlePreviousCard}
            className="absolute left-[10px] z-[500] w-10 h-10 rounded-full bg-[#2E2E2E] flex items-center justify-center hover:bg-[#3E3E3E] transition-colors"
          >
            <img src={arrowLeftIcon} alt="Previous" width={24} height={24} />
          </button>
        )}

        {/* Right Arrow - показываем если не на последней карточке и модалка не открыта */}
        {currentCardIndex < totalCards - 1 && !hideBottomNavigation && (
          <button
            onClick={handleNextCard}
            className="absolute right-[10px] z-[500] w-10 h-10 rounded-full bg-[#2E2E2E] flex items-center justify-center hover:bg-[#3E3E3E] transition-colors"
          >
            <img src={arrowRightIcon} alt="Next" width={24} height={24} />
          </button>
        )}

        <div className="relative flex justify-center items-center" style={{ height: '488.53px', width: '100%' }}>
          {/* Card Stack Effect with react-spring - рендерим задания */}
          {availableTasks.map((task, index) => {
            const isActive = index === currentCardIndex
            const offset = index - currentCardIndex
            const zIndex = totalCards - Math.abs(offset)

            // Calculate position based on offset
            let top = 0
            let left = 0
            let scale = 1
            let opacity = 1
            let translateX = 0 // Для анимации сдвига предыдущей карточки

            if (offset === 0) {
              // Active card
              top = 0
              left = 0
              scale = 1
              opacity = 1
              translateX = 0
            } else if (offset === 1) {
              // Next card (behind)
              top = 4.74
              left = 11.17
              scale = 0.98
              opacity = 0.7
              translateX = 0
            } else if (offset === -1) {
              // Previous card (behind) - быстро скрываем и сдвигаем влево
              top = 4.74
              left = -11.17
              scale = 0.98
              opacity = 0 // Полностью скрываем предыдущую карточку
              translateX = -50 // Сдвигаем влево для плавного исчезновения
            } else if (offset === 2) {
              // Second next card
              top = 30
              left = 17.54
              scale = 0.96
              opacity = 0.5
              translateX = 0
            } else if (offset === -2) {
              // Second previous card - полностью скрываем
              top = 30
              left = -17.54
              scale = 0.96
              opacity = 0
              translateX = -100
            } else {
              // Cards far away - hide
              opacity = 0
              translateX = 0
            }

            // Анимация свайпа (Scale & Rotate вариант) с плавным переходом
            const spring = springs[index] || {
              x: { get: () => 0 },
              y: { get: () => 0 },
              rotate: { get: () => 0 },
              opacity: { get: () => opacity },
              scale: { get: () => scale }
            }

            return (
              <animated.div
                key={task.id}
                className="absolute transition-all ease-in-out"
                style={{
                  top: `${top}px`,
                  left: `calc(50% - 153.5px + ${left}px)`, // 153.5px = половина ширины карточки (307px / 2)
                  width: '307px',
                  height: '480px',
                  scale: isActive ? spring.scale : scale,
                  opacity: isActive ? spring.opacity : (offset === -1 ? 0 : opacity), // Быстро скрываем предыдущую карточку
                  zIndex: zIndex + 200, // Очень высокий z-index карточек для визуального отображения
                  transformOrigin: 'center center',
                  pointerEvents: isActive ? 'auto' : 'none', // Разрешаем клики только на активной карточке
                  transition: offset === -1 
                    ? 'all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94)' // Плавное исчезновение предыдущей карточки
                    : 'all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)', // Плавное появление новой карточки
                  transform: `translateX(${offset === -1 ? translateX : 0}px)` // Сдвигаем предыдущую карточку влево
                } as any}
                onClick={isActive ? handleCardClick : undefined}
              >
                <div
                  className="w-full h-full rounded-[16px] overflow-hidden"
                  style={{
                    background: 'linear-gradient(149deg, rgba(44, 44, 44, 1) 24%, rgba(30, 30, 30, 1) 90%)'
                  }}
                >
                  {/* Border */}
                  <div
                    className="absolute inset-[8px] border border-[#333333] rounded-[12px] pointer-events-none"
                    style={{ borderWidth: '1.6px' }}
                  ></div>

                  {/* Content */}
                  <div className="relative h-full flex flex-col items-center justify-center px-[44.84px] pb-20">
                    {/* Текст задания - крупный, без заголовка */}
                    <p className="text-[#F5F7FA] text-2xl font-semibold leading-[1.3] text-center whitespace-pre-line flex-1 flex items-center justify-center">
                      {task.description || task.title}
                    </p>

                    {/* Logo at bottom */}
                    <div className="absolute bottom-[50px] left-1/2 -translate-x-1/2 flex items-center justify-center">
                      <img src={logoTaskIcon} alt="Logo" className="w-auto h-auto max-w-[60px] max-h-[60px]" />
                    </div>
                  </div>
                </div>
              </animated.div>
            )
          })}
          
          {/* Offer страница как последняя карточка в карусели */}
          {shouldShowOffer && (
            (() => {
              const offerIndex = availableTasks.length
              const isActive = offerIndex === currentCardIndex
              const offset = offerIndex - currentCardIndex
              const zIndex = totalCards - Math.abs(offset)

              // Страница оплаты показывается только когда пользователь достиг лимита
              // Если currentCardIndex < maxAvailableCards, страница оплаты полностью скрыта
              const isBeforeLimit = currentCardIndex < maxAvailableCards

              let top = 0
              let left = 0
              let scale = 1
              let opacity = 0 // По умолчанию скрыта
              let translateX = 0

              if (!isBeforeLimit) {
                if (offset === 0) {
                  top = 0
                  left = 0
                  scale = 1
                  opacity = 1
                  translateX = 0
                } else if (offset === 1) {
                  top = 4.74
                  left = 11.17
                  scale = 0.98
                  opacity = 0.7
                  translateX = 0
                } else if (offset === -1) {
                  // Предыдущая карточка (задание перед offer) - быстро скрываем
                  top = 4.74
                  left = -11.17
                  scale = 0.98
                  opacity = 0
                  translateX = -50
                } else if (offset === 2) {
                  top = 30
                  left = 17.54
                  scale = 0.96
                  opacity = 0.5
                  translateX = 0
                } else if (offset === -2) {
                  top = 30
                  left = -17.54
                  scale = 0.96
                  opacity = 0
                  translateX = -100
                } else {
                  opacity = 0
                  translateX = 0
                }
              }

              const spring = springs[offerIndex] || {
                opacity: { get: () => opacity },
                scale: { get: () => scale }
              }

              return (
                <animated.div
                  key="offer-card"
                  className="absolute transition-all ease-in-out"
                  style={{
                    top: `${top}px`,
                    left: `calc(50% - 153.5px + ${left}px)`,
                    width: '307px',
                    height: '480px',
                    scale: isActive ? spring.scale : scale,
                    opacity: isBeforeLimit ? 0 : (isActive ? spring.opacity : (offset === -1 ? 0 : opacity)), // Полностью скрыта до достижения лимита и при переключении назад
                    zIndex: isBeforeLimit ? -1 : (zIndex + 200), // Низкий z-index до достижения лимита
                    transformOrigin: 'center center',
                    pointerEvents: isActive && !isBeforeLimit ? 'auto' : 'none', // Клики только когда видна
                    transition: offset === -1 
                      ? 'all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94)' // Плавное исчезновение при переключении назад
                      : 'all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)', // Плавное появление
                    visibility: isBeforeLimit ? 'hidden' : 'visible', // Скрыта до достижения лимита
                    transform: `translateX(${offset === -1 ? translateX : 0}px)` // Сдвигаем при переключении назад
                  } as any}
                >
                  <div
                    className="w-full h-full rounded-[16px] overflow-hidden flex flex-col items-center justify-center px-8"
                    style={{
                      background: 'linear-gradient(149deg, rgba(44, 44, 44, 1) 24%, rgba(30, 30, 30, 1) 90%)'
                    }}
                  >
                    {/* Border */}
                    <div
                      className="absolute inset-[8px] border border-[#333333] rounded-[12px] pointer-events-none"
                      style={{ borderWidth: '1.6px' }}
                    ></div>

                    {/* Offer Content */}
                    <div className="relative h-full flex flex-col items-center justify-center">
                      {/* Large Lightning Icon */}
                      <div className="mb-8">
                        <img src={lightningLargeIcon} alt="Lightning" className="w-[63px] h-[104px]" />
                      </div>

                      {/* Title */}
                      <h1 className="text-white text-xl font-semibold text-center mb-4 leading-tight">
                        {t('home.freeTasksEnded')}
                      </h1>

                      {/* Description */}
                      <p className="text-[#808080] text-sm text-center mb-8 leading-relaxed px-4">
                        {t('home.comeTomorrow')}
                      </p>

                      {/* Button */}
                      {balance >= 10 ? (
                        <button
                          className="w-full max-w-[280px] h-14 rounded-full bg-[#EB454E] flex items-center justify-center mb-6 transition-opacity hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed"
                          disabled={buying}
                          onClick={handlePurchase}
                        >
                          <span className="text-white text-base font-semibold">{t('home.openFor10')}</span>
                        </button>
                      ) : (
                        <button
                          className="w-full max-w-[280px] h-14 rounded-full bg-[#EB454E] flex items-center justify-center mb-6 transition-opacity hover:opacity-90"
                          onClick={() => {
                            onNavigate?.('sparksPurchase')
                          }}
                        >
                          <span className="text-white text-base font-semibold">{t('home.topUp')}</span>
                        </button>
                      )}

                      {/* Timer */}
                      <p className="text-white text-sm text-center">
                        {t('home.newSparksIn')} {timeRemaining}
                      </p>
                    </div>
                  </div>
                </animated.div>
              )
            })()
          )}
        </div>

      </div>

      {/* Pagination */}
      <div className="flex justify-center items-center gap-2 mb-8">
        {Array.from({ length: totalCards }).map((_, index) => {
          const isOfferCard = index === availableTasks.length && shouldShowOffer
          const isActive = index === currentCardIndex

          if (isOfferCard) {
            return (
              <div key={index} className="flex items-center justify-center w-[57px] h-[11px]">
                <img src={paginationLockIcon} alt="Lock" className="w-[57px] h-[11px]" />
              </div>
            )
          }

          return (
            <div
              key={index}
              className={`transition-all duration-300 ${
                isActive
                  ? 'w-2 h-[11px] rounded-full bg-white'
                  : 'w-2 h-2 rounded-full bg-[#333333]'
              }`}
            ></div>
          )
        })}
      </div>

      {/* Bottom Navigation */}
      <BottomNavigation onNavigate={onNavigate} currentPage="home" />
    </div>
  )
}


export default Home
