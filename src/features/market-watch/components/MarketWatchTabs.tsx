import { type ElementType } from 'react'
import clsx from 'clsx'
import { motion } from 'framer-motion'

export type TabId =
  | 'pulse'
  | 'rates'
  | 'fx'
  | 'sectors'
  | 'commodities'
  | 'stress'

type TabOption = {
  id: TabId
  label: string
  icon: ElementType
}

type MarketWatchTabsProps = {
  tabs: TabOption[]
  activeTab: TabId
  onChange: (tabId: TabId) => void
}

export default function MarketWatchTabs({
  tabs,
  activeTab,
  onChange,
}: MarketWatchTabsProps) {
  return (
    <div className="relative mb-8 w-full border-b border-softform-text-muted/20 pb-4">
      <div className="flex w-full items-center gap-2 overflow-x-auto pb-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:pb-0">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={clsx(
                'group relative flex shrink-0 items-center gap-2 rounded-full px-5 py-2.5 transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-softform-teal-500/40',
                isActive
                  ? 'text-softform-navy-950 font-semibold'
                  : 'text-softform-navy-950/70 font-medium hover:text-softform-navy-950',
              )}
              aria-selected={isActive}
              role="tab"
            >
              {isActive && (
                <motion.div
                  layoutId="activeTabPill"
                  className="absolute inset-0 rounded-full bg-white/80 border border-white/90 shadow-[inset_0_2px_4px_rgba(8,17,31,0.08),_0_1px_2px_rgba(255,255,255,0.8)] backdrop-blur-md -z-10"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              <tab.icon
                size={16}
                strokeWidth={isActive ? 2.5 : 1.5}
                className={clsx(
                  'shrink-0 transition-colors',
                  isActive
                    ? 'text-softform-teal-deep'
                    : 'text-softform-text-muted group-hover:text-softform-text-secondary',
                )}
              />
              <span className="text-[14px]">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
