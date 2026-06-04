import { motion, useReducedMotion, Variants } from 'framer-motion'
import { ReactNode } from 'react'
import { EASE_ENTER, DUR_ENTER } from '../utils/motion'

type MotionRevealProps = {
  children: ReactNode
  className?: string
  yOffset?: number
  delay?: number
}

export default function MotionReveal({ children, className, yOffset = 8, delay = 0 }: MotionRevealProps) {
  const shouldReduceMotion = useReducedMotion()

  const variants: Variants = {
    hidden: { 
      opacity: 0, 
      y: shouldReduceMotion ? 0 : yOffset 
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: DUR_ENTER, 
        ease: EASE_ENTER,
        delay: shouldReduceMotion ? 0 : delay
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
