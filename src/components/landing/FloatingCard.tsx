import { motion } from 'framer-motion'
import { ReactNode } from 'react'

interface FloatingCardProps {
  children: ReactNode
  delay?: number
  className?: string
  position?: {
    top?: string
    left?: string
    right?: string
    bottom?: string
  }
}

export default function FloatingCard({ 
  children, 
  delay = 0, 
  className = '',
  position = {}
}: FloatingCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ 
        opacity: 1, 
        y: 0, 
        scale: 1,
      }}
      transition={{ 
        duration: 0.8, 
        delay,
        ease: [0.16, 1, 0.3, 1]
      }}
      className={`absolute backdrop-blur-xl bg-white/80 rounded-2xl shadow-2xl border border-white/40 ${className}`}
      style={position}
    >
      {children}
    </motion.div>
  )
}
