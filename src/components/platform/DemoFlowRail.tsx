import { Link, useLocation } from 'react-router-dom'
import StatusChip from './StatusChip'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FolderOpen,
  FileText,
  TrendingUp,
  ScrollText,
  Compass,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

type DemoFlowStep = {
  id: string
  label: string
  description: string
  href: string
  chipLabel: 'Preview-only' | 'Source-aware' | 'Context-only'
}

const FLOW_STEPS: DemoFlowStep[] = [
  {
    id: 'data-room',
    label: 'Data Room',
    description: 'Upload and preview structured financial records.',
    href: '/platform/data-room',
    chipLabel: 'Preview-only',
  },
  {
    id: 'financial-preview',
    label: 'Financial Preview',
    description: 'Review ratios, integrity, and summary bands from preview records.',
    href: '/platform/data-room',
    chipLabel: 'Preview-only',
  },
  {
    id: 'market-watch',
    label: 'Market Watch',
    description: 'Context-only signals using provider-backed and workspace-derived sources.',
    href: '/platform/market-watch',
    chipLabel: 'Source-aware',
  },
  {
    id: 'advisory-blueprint',
    label: 'Advisory Blueprint',
    description: 'Financing readiness brief based on demo analysis.',
    href: '/platform/advisory-blueprint',
    chipLabel: 'Context-only',
  },
]

const chipVariantMap: Record<string, 'neutral' | 'signal' | 'caution' | 'navy'> = {
  'Preview-only': 'neutral',
  'Source-aware': 'signal',
  'Context-only': 'caution',
}

const iconMap: Record<string, typeof FolderOpen> = {
  'data-room': FolderOpen,
  'financial-preview': FileText,
  'market-watch': TrendingUp,
  'advisory-blueprint': ScrollText,
}

export default function DemoFlowRail() {
  const location = useLocation()
  const isOverview = location.pathname === '/platform/overview'
  const [isOpen, setIsOpen] = useState(isOverview)

  return (
    <section className="mb-8 rounded-[22px] border border-softform-aqua-300/20 bg-softform-mist-100/40 p-5 shadow-soft-inner transition-all">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 text-left focus-visible:outline-none"
        >
          <Compass size={14} className="text-softform-teal-deep animate-spin" style={{ animationDuration: '10s' }} />
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-teal-deep flex items-center gap-1">
            Workspace Flow
            {!isOverview && (
              <span className="normal-case font-medium text-softform-text-muted/80 ml-1">
                ({isOpen ? 'click to collapse' : 'click to expand'})
              </span>
            )}
          </p>
        </button>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-softform-text-muted hover:text-softform-navy-950 transition-colors p-0.5 rounded-lg hover:bg-white/40"
          aria-label={isOpen ? 'Collapse workspace flow' : 'Expand workspace flow'}
        >
          {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0, marginTop: 0 }}
            animate={{ height: 'auto', opacity: 1, marginTop: 12 }}
            exit={{ height: 0, opacity: 0, marginTop: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {FLOW_STEPS.map((step) => {
                const Icon = iconMap[step.id]
                const isCurrent = location.pathname === step.href
                return (
                  <Link
                    key={step.id}
                    to={step.href}
                    className={`group flex items-start gap-3 rounded-2xl border p-4 transition-all duration-200 hover:bg-white hover:shadow-floating-panel hover:-translate-y-0.5 ${
                      isCurrent
                        ? 'border-softform-teal-500 bg-white shadow-sm ring-1 ring-softform-teal-500/20'
                        : 'border-white/70 bg-white/60'
                    }`}
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-softform-mist-100/80 text-softform-teal-deep border border-white/60 shadow-sm transition-colors group-hover:bg-softform-mist-100">
                      <Icon size={15} />
                    </div>
                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-softform-navy-950 leading-tight">
                          {step.label}
                        </span>
                        <StatusChip
                          variant={chipVariantMap[step.chipLabel] ?? 'neutral'}
                          className="text-[8px] px-1.5 py-0.5 shrink-0"
                        >
                          {step.chipLabel}
                        </StatusChip>
                      </div>
                      <p className="text-[11px] leading-relaxed text-softform-text-secondary">
                        {step.description}
                      </p>
                    </div>
                  </Link>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}
