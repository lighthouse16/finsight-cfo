import { type ReactNode } from 'react'
import InfoTooltip from '../ui/InfoTooltip'
import { motion } from 'framer-motion'

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
  const activeTitleAddon = titleAddon || (subtitle ? (
    <InfoTooltip label={`About ${title}`} content={subtitle} />
  ) : null)

  return (
    <motion.header 
      className="mb-8"
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between pb-5 border-b border-softform-text-muted/10">
        <div className="max-w-[680px] space-y-2.5">
          {chip && <div>{chip}</div>}
          <div className="flex items-center gap-1.5">
            <h1 className="text-2xl font-bold leading-tight text-softform-navy-950 sm:text-3xl">
              {title}
            </h1>
            {activeTitleAddon}
          </div>
        </div>
        {actions && (
          <div className="flex shrink-0 flex-wrap items-center gap-3 lg:justify-end">
            {actions}
          </div>
        )}
      </div>
    </motion.header>
  )
}
