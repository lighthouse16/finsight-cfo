import { Link } from 'react-router-dom'
import StatusChip from './StatusChip'
import {
  FolderOpen,
  FileText,
  TrendingUp,
  ScrollText,
  Compass,
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
  return (
    <section className="mb-8 rounded-[22px] border border-softform-aqua-300/20 bg-softform-mist-100/40 p-5 shadow-soft-inner">
      <div className="mb-3 flex items-center gap-2">
        <Compass size={14} className="text-softform-teal-deep" />
        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-teal-deep">
          Demo Flow
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {FLOW_STEPS.map((step) => {
          const Icon = iconMap[step.id]
          return (
            <Link
              key={step.id}
              to={step.href}
              className="group flex items-start gap-3 rounded-2xl border border-white/70 bg-white/60 p-4 transition-all duration-200 hover:bg-white hover:shadow-floating-panel hover:-translate-y-0.5"
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
    </section>
  )
}
