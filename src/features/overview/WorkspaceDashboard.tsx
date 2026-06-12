/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FolderOpen,
  Database,
  HeartPulse,
  BarChart3,
  ShieldCheck,
  Landmark,
  ScrollText,
  BotMessageSquare,
  FileText,
  ArrowRight,
  CheckCircle2,
  Lock,
  Loader2,
  AlertTriangle,
} from 'lucide-react'
import { useWorkspace } from '../../context/workspaceContext'
import { fetchWorkspaceFiles, fetchActiveWorkspaceSnapshot } from '../data-room/api/dataRoomApi'
import { fetchAllRunStatuses } from '../../lib/workspaceRunHelpers'

type StepStatus = 'not_started' | 'ready' | 'completed' | 'blocked'

interface JourneyStep {
  id: string
  label: string
  description: string
  route: string
  icon: typeof FolderOpen
  status: StepStatus
  blockedReason?: string
  ctaLabel: string
}

export default function WorkspaceDashboard() {
  const { activeWorkspace } = useWorkspace()

  const [hasFiles, setHasFiles] = useState<boolean | null>(null)
  const [hasSnapshot, setHasSnapshot] = useState<boolean | null>(null)
  const [runStatuses, setRunStatuses] = useState<Record<string, any | null>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!activeWorkspace) return

    const loadState = async () => {
      setLoading(true)
      try {
        // Check files
        const files = await fetchWorkspaceFiles(activeWorkspace.id).catch(() => [])
        setHasFiles(files.length > 0)

        // Check snapshot
        try {
          await fetchActiveWorkspaceSnapshot(activeWorkspace.id)
          setHasSnapshot(true)
        } catch {
          setHasSnapshot(false)
        }

        // Check run statuses
        const statuses = await fetchAllRunStatuses(activeWorkspace.id)
        setRunStatuses(statuses)
      } catch (err) {
        console.warn('WorkspaceDashboard: failed to load state', err)
      } finally {
        setLoading(false)
      }
    }

    loadState()
  }, [activeWorkspace])

  if (!activeWorkspace) return null

  const hasRun = (key: string) => {
    const run = runStatuses[key]
    return run && (run.status === 'completed' || run.status === 'success')
  }

  const steps: JourneyStep[] = [
    {
      id: 'upload',
      label: 'Upload financial documents',
      description: 'Upload P&L, balance sheet, cash flow, debt schedule, and receivables aging.',
      route: '/platform/data-room',
      icon: FolderOpen,
      status: hasFiles ? 'completed' : 'not_started',
      ctaLabel: hasFiles ? 'View Data Room' : 'Go to Data Room',
    },
    {
      id: 'snapshot',
      label: 'Build financial snapshot',
      description: 'Parse uploaded records into a structured financial snapshot for analysis.',
      route: '/platform/data-room',
      icon: Database,
      status: hasSnapshot
        ? 'completed'
        : hasFiles
          ? 'ready'
          : 'blocked',
      blockedReason: !hasFiles ? 'Upload financial documents first.' : undefined,
      ctaLabel: hasSnapshot ? 'Review Snapshot' : 'Build Snapshot',
    },
    {
      id: 'financial_health',
      label: 'Review financial health',
      description: 'Analyze liquidity, leverage, coverage, receivables, and cashflow quality.',
      route: '/platform/financial-health',
      icon: HeartPulse,
      status: hasRun('financial_health')
        ? 'completed'
        : hasSnapshot
          ? 'ready'
          : 'blocked',
      blockedReason: !hasSnapshot ? 'Build a financial snapshot first.' : undefined,
      ctaLabel: hasRun('financial_health') ? 'View Health' : 'Run Analysis',
    },
    {
      id: 'valuation',
      label: 'Run valuation',
      description: 'Build indicative WACC, DCF, and enterprise value from financial forecasts.',
      route: '/platform/valuation',
      icon: BarChart3,
      status: hasRun('valuation')
        ? 'completed'
        : hasSnapshot
          ? 'ready'
          : 'blocked',
      blockedReason: !hasSnapshot ? 'Build a financial snapshot first.' : undefined,
      ctaLabel: hasRun('valuation') ? 'View Valuation' : 'Run Valuation',
    },
    {
      id: 'credit_readiness',
      label: 'Credit readiness check',
      description: 'See how your financial profile may appear before lender conversations.',
      route: '/platform/credit-readiness',
      icon: ShieldCheck,
      status: hasRun('credit_score')
        ? 'completed'
        : hasSnapshot
          ? 'ready'
          : 'blocked',
      blockedReason: !hasSnapshot ? 'Build a financial snapshot first.' : undefined,
      ctaLabel: hasRun('credit_score') ? 'View Readiness' : 'Check Readiness',
    },
    {
      id: 'funding_strategy',
      label: 'Funding strategy',
      description: 'Compare timing, channels, approval fit, loan structure, and stress scenarios.',
      route: '/platform/funding-strategy',
      icon: Landmark,
      status: hasRun('funding_strategy')
        ? 'completed'
        : hasSnapshot
          ? 'ready'
          : 'blocked',
      blockedReason: !hasSnapshot ? 'Build a financial snapshot first.' : undefined,
      ctaLabel: hasRun('funding_strategy') ? 'View Strategy' : 'Explore Funding',
    },
    {
      id: 'advisory_blueprint',
      label: 'Generate advisory blueprint',
      description: 'Consolidate all analyses into an advisor-ready financing readiness brief.',
      route: '/platform/advisory-blueprint',
      icon: ScrollText,
      status: hasRun('advisory_blueprint')
        ? 'completed'
        : hasSnapshot
          ? 'ready'
          : 'blocked',
      blockedReason: !hasSnapshot ? 'Build a financial snapshot first.' : undefined,
      ctaLabel: hasRun('advisory_blueprint') ? 'View Blueprint' : 'Generate Blueprint',
    },
    {
      id: 'ai_cfo',
      label: 'Ask AI CFO',
      description: 'Ask questions across your financial records, market context, and funding strategy.',
      route: '/platform/ai-cfo',
      icon: BotMessageSquare,
      status: hasSnapshot ? 'ready' : 'blocked',
      blockedReason: !hasSnapshot
        ? 'Build a financial snapshot first.'
        : undefined,
      ctaLabel: 'Open AI CFO',
    },
    {
      id: 'reports',
      label: 'Export advisor report',
      description: 'Generate CFO snapshots, funding-readiness summaries, and lender-facing documents.',
      route: '/platform/reports',
      icon: FileText,
      status: hasSnapshot ? 'ready' : 'blocked',
      blockedReason: !hasSnapshot ? 'Build a financial snapshot first.' : undefined,
      ctaLabel: 'Generate Report',
    },
  ]

  const completedCount = steps.filter((s) => s.status === 'completed').length

  if (loading) {
    return (
      <section className="rounded-[32px] border border-white/60 bg-white/40 p-6 backdrop-blur-md shadow-sm sm:p-8">
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 size={20} className="animate-spin text-softform-teal-deep" />
          <span className="text-sm text-softform-text-muted">
            Loading workspace progress…
          </span>
        </div>
      </section>
    )
  }

  return (
    <section className="rounded-[32px] border border-white/60 bg-white/40 p-6 backdrop-blur-md shadow-sm sm:p-8">
      {/* Header */}
      <div className="flex flex-col gap-3 border-b border-softform-navy-950/5 pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-softform-navy-950">
            Workspace Journey
          </h2>
          <p className="mt-1 text-xs text-softform-text-muted">
            Follow these steps to move from uploaded records to a complete advisory output.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 flex-1 min-w-[80px] rounded-full bg-softform-navy-950/5 sm:w-32 sm:flex-none">
            <div
              className="h-full rounded-full bg-softform-teal-deep transition-all duration-500"
              style={{ width: `${(completedCount / steps.length) * 100}%` }}
            />
          </div>
          <span className="text-xs font-semibold text-softform-text-muted tabular-finance">
            {completedCount}/{steps.length}
          </span>
        </div>
      </div>

      {/* Step List */}
      <div className="mt-5 space-y-2">
        {steps.map((step, index) => {
          const Icon = step.icon

          return (
            <div
              key={step.id}
              className={`group flex items-start gap-4 rounded-2xl border px-5 py-4 transition-all duration-200 ${
                step.status === 'completed'
                  ? 'border-softform-teal-deep/15 bg-softform-mist-100/30'
                  : step.status === 'blocked'
                    ? 'border-softform-navy-950/5 bg-white/20 opacity-60'
                    : 'border-white/70 bg-white/50 hover:bg-white/70 hover:shadow-sm'
              }`}
            >
              {/* Step number + status icon */}
              <div className="flex flex-col items-center gap-1.5 pt-0.5">
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
                    step.status === 'completed'
                      ? 'bg-softform-teal-deep/10 text-softform-teal-deep'
                      : step.status === 'blocked'
                        ? 'bg-softform-navy-950/5 text-softform-text-muted'
                        : 'bg-softform-mist-100 text-softform-navy-950'
                  }`}
                >
                  {step.status === 'completed' ? (
                    <CheckCircle2 size={16} />
                  ) : step.status === 'blocked' ? (
                    <Lock size={14} />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Icon
                        size={14}
                        className={
                          step.status === 'completed'
                            ? 'text-softform-teal-deep'
                            : 'text-softform-text-muted'
                        }
                      />
                      <span
                        className={`text-sm font-semibold ${
                          step.status === 'completed'
                            ? 'text-softform-teal-deep'
                            : 'text-softform-navy-950'
                        }`}
                      >
                        {step.label}
                      </span>
                      {step.status === 'completed' && (
                        <span className="rounded-full bg-softform-teal-deep/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-softform-teal-deep">
                          Done
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-softform-text-secondary">
                      {step.description}
                    </p>
                    {step.status === 'blocked' && step.blockedReason && (
                      <p className="mt-1.5 flex items-center gap-1 text-[11px] font-medium text-softform-amber-500">
                        <AlertTriangle size={11} />
                        {step.blockedReason}
                      </p>
                    )}
                  </div>

                  {/* CTA */}
                  {step.status !== 'blocked' && (
                    <Link
                      to={step.route}
                      className={`shrink-0 inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all ${
                        step.status === 'completed'
                          ? 'border border-softform-teal-deep/20 bg-white/60 text-softform-teal-deep hover:bg-white'
                          : 'bg-softform-navy-900 text-white hover:bg-softform-navy-800 shadow-sm'
                      }`}
                    >
                      {step.ctaLabel}
                      <ArrowRight size={12} />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
