import { type ReactNode } from 'react'
import clsx from 'clsx'

type StatusChipVariant = 'neutral' | 'signal' | 'caution' | 'navy'

type StatusChipProps = {
  children: ReactNode
  variant?: StatusChipVariant
  className?: string
}

const variantStyles: Record<StatusChipVariant, string> = {
  neutral:
    'bg-white/50 text-softform-text-secondary border-white/60',
  signal:
    'bg-softform-mist-100/60 text-softform-teal-deep border-softform-aqua-300/30',
  caution:
    'bg-softform-cream/50 text-softform-amber-500 border-softform-amber-200/40',
  navy:
    'bg-softform-navy-900/90 text-white/90 border-white/10',
}

export default function StatusChip({
  children,
  variant = 'neutral',
  className,
}: StatusChipProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.14em] whitespace-nowrap transition-colors duration-200',
        'backdrop-blur-sm',
        variantStyles[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}
