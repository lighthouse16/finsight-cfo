import { useEffect, useRef, ReactNode } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

interface ParallaxSectionProps {
  children: ReactNode
  speed?: number
  direction?: 'up' | 'down' | 'left' | 'right'
  className?: string
}

export default function ParallaxSection({
  children,
  speed = 0.5,
  direction = 'up',
  className = ''
}: ParallaxSectionProps) {
  const sectionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const section = sectionRef.current
    if (!section) return

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (prefersReducedMotion) {
      return
    }

    // Calculate movement based on direction
    const getMovement = () => {
      const distance = 100 * speed
      switch (direction) {
        case 'up':
          return { y: -distance }
        case 'down':
          return { y: distance }
        case 'left':
          return { x: -distance }
        case 'right':
          return { x: distance }
        default:
          return { y: -distance }
      }
    }

    const movement = getMovement()

    // Create parallax effect
    gsap.to(section, {
      ...movement,
      ease: 'none',
      scrollTrigger: {
        trigger: section,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true,
      }
    })

    // Cleanup
    return () => {
      ScrollTrigger.getAll().forEach(trigger => {
        if (trigger.trigger === section) {
          trigger.kill()
        }
      })
    }
  }, [speed, direction])

  return (
    <div ref={sectionRef} className={className}>
      {children}
    </div>
  )
}
