import { motion, useReducedMotion, Variants } from 'framer-motion'
import { ReactNode } from 'react'

type MotionStaggerProps = {
  children: ReactNode
  className?: string
  staggerDelay?: number
}

export default function MotionStagger({ children, className, staggerDelay = 0.04 }: MotionStaggerProps) {
  const shouldReduceMotion = useReducedMotion()

  const variants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : staggerDelay,
        delayChildren: 0.02
      }
    }
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={variants}
      className={className}
    >
      {children}
    </motion.div>
  )
}
