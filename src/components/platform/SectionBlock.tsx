import { type ReactNode } from 'react'

interface SectionBlockProps {
  title?: string
  icon?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
  containerType?: 'card' | 'panel' | 'none'
}

export default function SectionBlock({
  title,
  icon,
  action,
  children,
  className = '',
  containerType = 'none',
}: SectionBlockProps) {
  const getContainerClass = () => {
    switch (containerType) {
      case 'card':
        return 'softform-card rounded-[24px] p-6 md:p-8'
      case 'panel':
        return 'softform-panel rounded-[32px] p-6 md:p-8 shadow-floating-panel'
      default:
        return ''
    }
  }

  return (
    <section className={`space-y-4 ${getContainerClass()} ${className}`}>
      {title && (
        <div className="flex flex-wrap items-center justify-between gap-4 pb-2">
          <div className="flex items-center gap-2">
            {icon && <span className="text-softform-text-secondary">{icon}</span>}
            <h2 className="softform-section-header text-lg font-semibold text-softform-navy-950">
              {title}
            </h2>
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      <div>{children}</div>
    </section>
  )
}
