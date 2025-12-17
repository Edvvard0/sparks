import { useState } from 'react'
import { useSpring, animated } from '@react-spring/web'
import { useDrag } from '@use-gesture/react'
import coinIcon from '../assets/icons/coin-icon.svg'

interface Task {
  id: number
  title: string
  description: string
  category: {
    id: number
    slug: string
    name: string
    color: string
  }
  sparks_reward: number
  is_completed: boolean
  is_free: boolean
}

interface TaskCardProps {
  task: Task
  index: number
  onComplete: () => void
  onSkip: () => void
  isCompleting: boolean
}

const TaskCard = ({ task, index, onComplete, onSkip, isCompleting }: TaskCardProps) => {
  const [isRemoved, setIsRemoved] = useState(false)

  const [{ x, y, rotate, scale }, api] = useSpring(() => ({
    x: 0,
    y: 0,
    rotate: 0,
    scale: 1,
    config: { tension: 300, friction: 30 }
  }))

  const bind = useDrag(
    ({ down, movement: [mx, my], velocity: [vx], direction: [dx] }) => {
      // Свайп влево для выполнения
      const trigger = Math.abs(mx) > 100
      const shouldComplete = !down && trigger && dx < 0

      if (shouldComplete) {
        // Анимация свайпа влево
        api.start({
          x: -500,
          rotate: -20,
          scale: 0.8,
          config: { tension: 200, friction: 20 }
        })
        setTimeout(() => {
          setIsRemoved(true)
          onComplete()
        }, 300)
      } else if (!down && Math.abs(mx) > 20) {
        // Возвращаем карточку на место если свайп не завершен
        api.start({ x: 0, y: 0, rotate: 0, scale: 1 })
      } else if (down) {
        // Двигаем карточку вместе с пальцем
        api.start({
          x: mx,
          y: my,
          rotate: mx / 10,
          scale: 1,
          immediate: true
        })
      }
    },
    { axis: 'x' }
  )

  if (isRemoved) {
    return null
  }

  // Z-index и масштаб для эффекта стека
  const zIndex = 10 - index
  const scaleValue = 1 - index * 0.05
  const yOffset = index * 10

  return (
    <animated.div
      {...bind()}
      style={{
        x,
        y,
        rotate,
        scale: index === 0 ? scale : scaleValue,
        zIndex,
        touchAction: 'none',
        transform: index > 0 ? `translateY(${yOffset}px) scale(${scaleValue})` : undefined
      }}
      className={`absolute inset-0 ${index === 0 ? 'cursor-grab active:cursor-grabbing' : 'pointer-events-none'}`}
    >
      <div
        className="w-full h-full rounded-[24px] p-6 flex flex-col justify-between shadow-2xl"
        style={{
          background: task.category.color || '#6456F0',
          opacity: 1 - index * 0.2
        }}
      >
        {/* Category Badge */}
        <div className="flex justify-between items-start">
          <div
            className="px-4 py-2 rounded-full text-sm font-medium"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              backdropFilter: 'blur(10px)'
            }}
          >
            <span className="text-white">{task.category.name}</span>
          </div>
          
          {/* Reward */}
          <div className="flex items-center gap-1 px-3 py-2 rounded-full bg-black bg-opacity-20 backdrop-blur-sm">
            <img src={coinIcon} alt="Coin" width={20} height={20} />
            <span className="text-white text-sm font-semibold">+{task.sparks_reward}</span>
          </div>
        </div>

        {/* Task Content */}
        <div className="flex-1 flex flex-col justify-center py-8">
          <h2 className="text-white text-2xl font-bold mb-4 text-center leading-tight">
            {task.title}
          </h2>
          <p className="text-white text-base text-center opacity-90 leading-relaxed">
            {task.description}
          </p>
        </div>

        {/* Action Hint */}
        <div className="text-center">
          <p className="text-white text-sm opacity-60">
            Свайп влево для выполнения →
          </p>
        </div>

        {/* Loading overlay */}
        {isCompleting && (
          <div className="absolute inset-0 bg-black bg-opacity-50 rounded-[24px] flex items-center justify-center">
            <div className="w-10 h-10 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>
    </animated.div>
  )
}

export default TaskCard

