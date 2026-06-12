import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  CheckCircle2, 
  Circle, 
  ArrowRight, 
  FileText, 
  Database, 
  Activity, 
  Compass, 
  FileCheck, 
  Bot, 
  Printer, 
  TrendingUp, 
  Building,
  RefreshCw
} from 'lucide-react'
import { fetchAllRunStatuses } from '../../lib/workspaceRunHelpers'
import { API_BASE_URL } from '../../lib/apiBase'

interface ReleaseOnboardingChecklistProps {
  compact?: boolean
}

interface ChecklistItem {
  id: number
  title: string
  description: string
  to: string
  isCompleted: boolean
  isActive: boolean
  icon: React.ComponentType<{ size?: string | number; className?: string }>
}

export default function ReleaseOnboardingChecklist({ compact = false }: ReleaseOnboardingChecklistProps) {
  const [workspaceId, setWorkspaceId] = useState<string | null>(localStorage.getItem('active_workspace_id'))
  const [hasSnapshot, setHasSnapshot] = useState<boolean>(false)
  const [runStatuses, setRunStatuses] = useState<Record<string, { status?: string } | null>>({})
  const [loading, setLoading] = useState(true)

  const loadOnboardingState = async () => {
    const activeId = localStorage.getItem('active_workspace_id')
    setWorkspaceId(activeId)
    
    if (!activeId) {
      setHasSnapshot(false)
      setRunStatuses({})
      setLoading(false)
      return
    }

    try {
      // Check for active snapshot
      const snapshotRes = await fetch(`${API_BASE_URL}/api/workspaces/${activeId}/snapshot/active`, {
        headers: { 'x-workspace-id': activeId }
      })
      setHasSnapshot(snapshotRes.ok)

      // Fetch run statuses
      const statuses = await fetchAllRunStatuses(activeId)
      setRunStatuses(statuses)
    } catch (e) {
      console.warn('Failed to load onboarding checklist states:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOnboardingState()

    const handleWorkspaceChanged = () => {
      loadOnboardingState()
    }

    window.addEventListener('workspaceChanged', handleWorkspaceChanged)
    return () => window.removeEventListener('workspaceChanged', handleWorkspaceChanged)
  }, [])

  const steps: ChecklistItem[] = [
    {
      id: 1,
      title: 'Create/select workspace',
      description: 'Establish or pick a corporate workspace boundary for data segregation.',
      to: '/platform/data-room',
      isCompleted: !!workspaceId,
      isActive: !workspaceId,
      icon: Building,
    },
    {
      id: 2,
      title: 'Initialize sample workspace',
      description: 'Kickstart with sample or actual structure for system validation.',
      to: '/platform/data-room',
      isCompleted: !!workspaceId,
      isActive: !!workspaceId && !hasSnapshot,
      icon: Database,
    },
    {
      id: 3,
      title: 'Upload records in Data Room',
      description: 'Provide general ledgers, trial balances, or bank statements.',
      to: '/platform/data-room',
      isCompleted: hasSnapshot,
      isActive: hasSnapshot ? false : !!workspaceId,
      icon: FileText,
    },
    {
      id: 4,
      title: 'Build active snapshot',
      description: 'Trigger the parser ingestion pipeline to build a normalized balance sheet.',
      to: '/platform/data-room',
      isCompleted: hasSnapshot,
      isActive: hasSnapshot ? false : !!workspaceId,
      icon: FileCheck,
    },
    {
      id: 5,
      title: 'Review Financial Health',
      description: 'Evaluate ratio profiles, integrity metrics, and cash flow forecasts.',
      to: '/platform/financial-health',
      isCompleted: hasSnapshot && runStatuses['financial_health']?.status === 'completed',
      isActive: hasSnapshot && runStatuses['financial_health']?.status !== 'completed',
      icon: Activity,
    },
    {
      id: 6,
      title: 'Review Market Watch',
      description: 'Inspect HIBOR, macro flags, and candidate credit channels.',
      to: '/platform/market-watch',
      isCompleted: hasSnapshot && runStatuses['funding_strategy']?.status === 'completed',
      isActive: hasSnapshot && runStatuses['financial_health']?.status === 'completed' && runStatuses['funding_strategy']?.status !== 'completed',
      icon: TrendingUp,
    },
    {
      id: 7,
      title: 'Review Credit Readiness / Funding Strategy',
      description: 'Analyze mock scores, gaps, and prioritized facility structures.',
      to: '/platform/credit-readiness',
      isCompleted: hasSnapshot && runStatuses['credit_score']?.status === 'completed',
      isActive: hasSnapshot && runStatuses['funding_strategy']?.status === 'completed' && runStatuses['credit_score']?.status !== 'completed',
      icon: Compass,
    },
    {
      id: 8,
      title: 'Generate Advisory Blueprint',
      description: 'Draft the planning-support brief with parameterized stress testing.',
      to: '/platform/advisory-blueprint',
      isCompleted: hasSnapshot && runStatuses['advisory_blueprint']?.status === 'completed',
      isActive: hasSnapshot && runStatuses['credit_score']?.status === 'completed' && runStatuses['advisory_blueprint']?.status !== 'completed',
      icon: FileText,
    },
    {
      id: 9,
      title: 'Ask AI CFO',
      description: 'Converse with the planning agent for document Q&A and scenario context.',
      to: '/platform/ai-cfo',
      isCompleted: hasSnapshot && runStatuses['workflow_run']?.status === 'completed',
      isActive: hasSnapshot && runStatuses['advisory_blueprint']?.status === 'completed' && runStatuses['workflow_run']?.status !== 'completed',
      icon: Bot,
    },
    {
      id: 10,
      title: 'Export advisor-ready Report',
      description: 'Compile reports as planning support, subject to relationship manager review.',
      to: '/platform/reports',
      isCompleted: hasSnapshot && runStatuses['workflow_run']?.status === 'completed',
      isActive: hasSnapshot && runStatuses['workflow_run']?.status === 'completed',
      icon: Printer,
    },
  ]

  const totalSteps = steps.length
  const completedSteps = steps.filter(s => s.isCompleted).length
  const progressPct = Math.round((completedSteps / totalSteps) * 100)

  if (compact) {
    return (
      <div className="bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-2xl p-4 backdrop-blur-md shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-softform-navy-950 uppercase tracking-wider">
            Release Onboarding
          </h4>
          <span className="text-xs font-semibold text-softform-teal-deep">
            {completedSteps}/{totalSteps} Steps ({progressPct}%)
          </span>
        </div>
        
        {/* Simplified progress bar */}
        <div className="w-full bg-slate-200/50 dark:bg-slate-850/30 h-1.5 rounded-full overflow-hidden">
          <div 
            className="bg-softform-teal-500 h-full rounded-full transition-all duration-500" 
            style={{ width: `${progressPct}%` }}
          />
        </div>

        <div className="grid grid-cols-5 gap-1 pt-1">
          {steps.map((step) => {
            const Icon = step.icon
            return (
              <Link 
                key={step.id} 
                to={step.to}
                title={`${step.id}. ${step.title}`}
                className={`flex flex-col items-center justify-center p-2 rounded-lg border text-center transition-all ${
                  step.isCompleted
                    ? 'bg-emerald-50/30 border-emerald-100/50 text-emerald-600 dark:text-emerald-400'
                    : step.isActive
                    ? 'bg-softform-teal-500/10 border-softform-teal-500/30 text-softform-teal-deep dark:text-softform-aqua-300 ring-1 ring-softform-teal-500/20'
                    : 'bg-slate-50/20 border-slate-100/30 text-slate-400'
                }`}
              >
                <Icon size={14} className={step.isActive ? 'animate-pulse' : ''} />
                <span className="text-[10px] font-bold mt-1">{step.id}</span>
              </Link>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-[32px] p-6 sm:p-8 backdrop-blur-md shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-softform-navy-950/5 pb-4">
        <div>
          <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
            <span>Release Onboarding Checklist</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-softform-teal-500/10 text-softform-teal-deep border border-softform-teal-500/20">
              Interactive Guide
            </span>
          </h2>
          <p className="text-xs text-softform-text-muted mt-1">
            Follow these 10 structured steps to ingest data, run diagnostic analyses, and export advisor-ready planning materials.
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted">Onboarding Progress</p>
            <p className="text-sm font-bold text-softform-navy-950 tabular-nums">
              {completedSteps} / {totalSteps} Completed ({progressPct}%)
            </p>
          </div>
          <button 
            onClick={loadOnboardingState}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-400 hover:text-slate-600 transition-colors"
            title="Refresh status"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Main progress bar */}
      <div className="w-full bg-slate-200/50 dark:bg-slate-850/30 h-2.5 rounded-full overflow-hidden">
        <div 
          className="bg-gradient-to-r from-softform-teal-500 to-emerald-500 h-full rounded-full transition-all duration-500" 
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Grid of Steps */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {steps.map((step) => {
          const Icon = step.icon
          return (
            <Link
              key={step.id}
              to={step.to}
              className={`flex flex-col justify-between p-4 rounded-2xl border transition-all hover:scale-[1.01] hover:shadow-sm ${
                step.isCompleted
                  ? 'bg-emerald-50/20 dark:bg-emerald-950/5 border-emerald-100/50 dark:border-emerald-900/15'
                  : step.isActive
                  ? 'bg-white border-softform-teal-500/60 dark:bg-slate-900 ring-2 ring-softform-teal-500/10'
                  : 'bg-white/40 dark:bg-slate-900/40 border-slate-100/50 dark:border-slate-800/40 opacity-75 hover:opacity-100'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className={`p-2 rounded-xl ${
                    step.isCompleted
                      ? 'bg-emerald-100/50 text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400'
                      : step.isActive
                      ? 'bg-softform-teal-500/10 text-softform-teal-deep dark:bg-softform-teal-950/20 dark:text-softform-aqua-300'
                      : 'bg-slate-100/50 text-slate-400 dark:bg-slate-850/50 dark:text-slate-500'
                  }`}>
                    <Icon size={18} className={step.isActive ? 'animate-pulse' : ''} />
                  </div>
                  
                  {step.isCompleted ? (
                    <CheckCircle2 size={16} className="text-emerald-500 fill-emerald-500/10" />
                  ) : step.isActive ? (
                    <span className="text-[9px] font-bold uppercase tracking-wider text-softform-teal-deep dark:text-softform-aqua-300 bg-softform-teal-500/10 px-1.5 py-0.5 rounded">
                      Next
                    </span>
                  ) : (
                    <Circle size={16} className="text-slate-300 dark:text-slate-650" />
                  )}
                </div>

                <h3 className="text-xs font-bold text-softform-navy-950 leading-snug">
                  {step.id}. {step.title}
                </h3>
                <p className="text-[10px] text-softform-text-muted mt-1 leading-relaxed line-clamp-3">
                  {step.description}
                </p>
              </div>

              <div className="mt-4 flex items-center justify-end text-[10px] font-bold text-softform-teal-deep dark:text-softform-aqua-300 group">
                <span className="mr-1 group-hover:underline">Proceed</span>
                <ArrowRight size={10} className="transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
