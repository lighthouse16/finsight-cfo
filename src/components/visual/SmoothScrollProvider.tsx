import { ReactNode } from 'react'

interface SmoothScrollProviderProps {
  children: ReactNode
}

export default function SmoothScrollProvider({ children }: SmoothScrollProviderProps) {
  // Disabled smooth scroll - using normal browser scrolling
  return <>{children}</>
}
