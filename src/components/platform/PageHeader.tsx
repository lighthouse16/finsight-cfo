import { type ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  subtitle?: string
  actions?: ReactNode
  chip?: ReactNode
}

export default function PageHeader({
  title,
  subtitle,
  actions,
  chip,
}: PageHeaderProps) {
  return (
    <header className="mb-8 space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3">
          {chip && <div>{chip}</div>}
          <h1 className="text-3xl font-bold leading-tight text-softform-navy-950 sm:text-4xl">
            {title}
          </h1>
          {subtitle && (
            <p className="max-w-2xl text-base leading-relaxed text-softform-text-secondary sm:text-lg">
              {subtitle}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex shrink-0 items-center gap-3">{actions}</div>
        )}
      </div>
    </header>
  )
}
