import { type ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  subtitle?: string
  actions?: ReactNode
  chip?: ReactNode
  titleAddon?: ReactNode
}

export default function PageHeader({
  title,
  subtitle,
  actions,
  chip,
  titleAddon,
}: PageHeaderProps) {
  return (
    <header className="mb-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-[680px] space-y-2.5">
          {chip && <div>{chip}</div>}
          <div className="flex items-start gap-1.5">
            <h1 className="text-3xl font-bold leading-tight text-softform-navy-950 sm:text-4xl">
              {title}
            </h1>
            {titleAddon}
          </div>
          {subtitle && (
            <p className="text-base leading-relaxed text-softform-text-secondary sm:text-lg">
              {subtitle}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex shrink-0 flex-wrap items-center gap-3 lg:justify-end">
            {actions}
          </div>
        )}
      </div>
    </header>
  )
}
