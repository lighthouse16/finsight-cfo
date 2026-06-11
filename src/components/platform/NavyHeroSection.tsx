import { ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface NavyHeroSectionProps {
  eyebrow: string
  title: string | ReactNode
  description: string | ReactNode
  aside?: ReactNode
  badges?: ReactNode
  className?: string
  layoutClassName?: string
}

export default function NavyHeroSection({
  eyebrow,
  title,
  description,
  aside,
  badges,
  className,
  layoutClassName = "relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-center",
}: NavyHeroSectionProps) {
  return (
    <section className={cn("softform-navy-card rounded-[32px] p-8 space-y-6 relative overflow-hidden", className)}>
      <div className="absolute top-0 right-0 w-72 h-72 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
      <div className={layoutClassName}>
        <div className="space-y-4">
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-softform-aqua-300 animate-pulse block">
            {eyebrow}
          </span>
          {typeof title === 'string' ? (
            <h2 className="text-3xl font-semibold text-white tracking-tight">
              {title}
            </h2>
          ) : (
            title
          )}
          {typeof description === 'string' ? (
            <p className="text-sm leading-relaxed text-white/80 max-w-3xl">
              {description}
            </p>
          ) : (
            description
          )}
          {badges}
        </div>

        {aside}
      </div>
    </section>
  )
}
