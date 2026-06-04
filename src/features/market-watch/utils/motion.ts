import { Variants } from 'framer-motion'

// Shared motion tokens
export const EASE_ENTER = [0.22, 1, 0.36, 1] // cubic-bezier(0.22, 1, 0.36, 1)
export const EASE_EXIT = [0.4, 0, 0.2, 1] // cubic-bezier(0.4, 0, 0.2, 1)

export const DUR_HOVER = 0.14 // 140ms
export const DUR_ENTER = 0.24 // 240ms
export const DUR_TAB = 0.3 // 300ms

// Common Framer Motion variants
export const fadeInVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { duration: DUR_ENTER, ease: EASE_ENTER }
  },
  exit: { 
    opacity: 0,
    transition: { duration: DUR_HOVER, ease: EASE_EXIT }
  }
}

export const slideUpVariants: Variants = {
  hidden: { opacity: 0, y: 8 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: DUR_ENTER, ease: EASE_ENTER }
  },
  exit: { 
    opacity: 0, 
    y: -8,
    transition: { duration: DUR_HOVER, ease: EASE_EXIT }
  }
}

export const staggerContainerVariants = (staggerChildren = 0.05): Variants => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren,
      delayChildren: 0.02
    }
  }
})

// Tooltip / small popover animation
export const tooltipVariants: Variants = {
  hidden: { opacity: 0, y: 4, scale: 0.95 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { duration: 0.15, ease: EASE_ENTER }
  },
  exit: { 
    opacity: 0, 
    y: 4, 
    scale: 0.95,
    transition: { duration: 0.1, ease: EASE_EXIT }
  }
}
