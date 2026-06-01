import { useEffect, useRef, ReactNode } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

// Register ScrollTrigger plugin
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

interface ScrollAnimationWrapperProps {
  children: ReactNode
  animation?: 'fadeIn' | 'slideUp' | 'slideLeft' | 'slideRight' | 'scale' | 'reveal'
  delay?: number
  duration?: number
  start?: string
  end?: string
  scrub?: boolean | number
  markers?: boolean
  className?: string
}

export default function ScrollAnimationWrapper({
  children,
  animation = 'fadeIn',
  delay = 0,
  duration = 1,
  start = 'top 80%',
  end = 'bottom 20%',
  scrub = false,
  markers = false,
  className = ''
}: ScrollAnimationWrapperProps) {
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (prefersReducedMotion) {
      // Skip animations if user prefers reduced motion
      gsap.set(element, { opacity: 1, x: 0, y: 0, scale: 1 })
      return
    }

    // Define animation variants
    const animations = {
      fadeIn: {
        from: { opacity: 0 },
        to: { opacity: 1 }
      },
      slideUp: {
        from: { opacity: 0, y: 60 },
        to: { opacity: 1, y: 0 }
      },
      slideLeft: {
        from: { opacity: 0, x: 60 },
        to: { opacity: 1, x: 0 }
      },
      slideRight: {
        from: { opacity: 0, x: -60 },
        to: { opacity: 1, x: 0 }
      },
      scale: {
        from: { opacity: 0, scale: 0.8 },
        to: { opacity: 1, scale: 1 }
      },
      reveal: {
        from: { opacity: 0, clipPath: 'inset(0 100% 0 0)' },
        to: { opacity: 1, clipPath: 'inset(0 0% 0 0)' }
      }
    }

    const selectedAnimation = animations[animation]

    // Set initial state
    gsap.set(element, selectedAnimation.from)

    // Create ScrollTrigger animation
    const scrollTrigger = ScrollTrigger.create({
      trigger: element,
      start,
      end,
      scrub,
      markers,
      onEnter: () => {
        gsap.to(element, {
          ...selectedAnimation.to,
          duration,
          delay,
          ease: 'power3.out'
        })
      }
    })

    // Cleanup
    return () => {
      scrollTrigger.kill()
    }
  }, [animation, delay, duration, start, end, scrub, markers])

  return (
    <div ref={elementRef} className={className}>
      {children}
    </div>
  )
}
