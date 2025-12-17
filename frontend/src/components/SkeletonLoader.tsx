interface SkeletonLoaderProps {
  className?: string
  width?: string
  height?: string
}

export const TaskCardSkeleton = ({ className = '' }: SkeletonLoaderProps) => (
  <div className={`w-full h-[480px] rounded-[16px] bg-[#2E2E2E] animate-pulse ${className}`} />
)

export const CategorySkeleton = ({ className = '' }: SkeletonLoaderProps) => (
  <div className={`h-10 rounded-[123px] bg-[#2E2E2E] animate-pulse ${className}`} style={{ width: '120px' }} />
)

export const TextSkeleton = ({ width = '100%', height = '20px', className = '' }: SkeletonLoaderProps) => (
  <div 
    className={`rounded bg-[#2E2E2E] animate-pulse ${className}`}
    style={{ width, height }}
  />
)

export default TaskCardSkeleton

