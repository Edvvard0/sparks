import React from 'react'

interface IconProps {
  src: string
  alt?: string
  className?: string
  width?: number | string
  height?: number | string
  color?: string
}

const Icon: React.FC<IconProps> = ({ 
  src, 
  alt = '', 
  className = '', 
  width, 
  height,
  color 
}) => {
  return (
    <img 
      src={src} 
      alt={alt} 
      className={className}
      width={width}
      height={height}
      style={color ? { filter: `brightness(0) saturate(100%) invert(${color === '#E7E7E7' || color === '#FFFFFF' ? '100%' : color === '#808080' ? '50%' : '0%'})` } : undefined}
    />
  )
}

export default Icon

