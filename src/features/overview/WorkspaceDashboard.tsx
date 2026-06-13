/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Database,
  HeartPulse,
  BarChart3,
  BotMessageSquare,
  FileText,
  ArrowRight,
  Loader2,
} from 'lucide-react'
import { useWorkspace } from '../../context/workspaceContext'
import { fetchWorkspaceFiles, fetchActiveWorkspaceSnapshot } from '../data-room/api/dataRoomApi'
import { fetchAllRunStatuses, ANALYSIS_RUN_TYPES } from '../../lib/workspaceRunHelpers'
import StatusChip from '../../components/platform/StatusChip'

export default function WorkspaceDashboard() {
  const { activeWorkspace } = useWorkspace()

  const [filesCount, setFilesCount] = useState<number | null>(null)
  const [hasSnapshot, setHasSnapshot] = useState<boolean | null>(null)
  const [runStatuses, setRunStatuses] = useState<Record<string, any | null>>({})
  const [latestAnalysis, setLatestAnalysis] = useState<{ name: string; date: string } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!activeWorkspace) return

    const loadState = async () => {
      setLoading(true)
      try {
        // Check files
        const files = await fetchWorkspaceFiles(activeWorkspace.id).catch(() => [])
        setFilesCount(files.length)

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

        // Find latest run
        const runsList = Object.values(statuses).filter(Boolean) as any[]
        if (runsList.length > 0) {
          runsList.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
          const latest = runsList[0]
          const matchingType = ANALYSIS_RUN_TYPES.find(t => t.key === latest.runType)
          setLatestAnalysis({
            name: matchingType ? matchingType.label : latest.runType,
            date: new Date(latest.createdAt).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }) + ' ' + new Date(latest.createdAt).toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
              hour12: true,
            })
          })
        } else {
          setLatestAnalysis(null)
        }
      } catch (err) {
        console.warn('WorkspaceDashboard: failed to load state', err)
      } finally {
        setLoading(false)
      }
    }

    loadState()
  }, [activeWorkspace])

  if (!activeWorkspace) return null

  if (loading) {
    return (
      <section className="rounded-[32px] border border-white/60 bg-white/40 p-6 backdrop-blur-md shadow-sm sm:p-8">
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 size={20} className="animate-spin text-softform-teal-deep" />
          <span className="text-sm text-softform-text-secondary font-medium">
            Loading workspace dashboard context…
          </span>
        </div>
      </section>
    )
  }

  const coreRunTypes = ANALYSIS_RUN_TYPES.filter((t) => t.isCore)
  const completedCoreCount = coreRunTypes.filter((t) => {
    const run = runStatuses[t.key]
    return run && (run.status === 'completed' || run.status === 'success')
  }).length

  const isValuationReady = runStatuses['valuation']?.status === 'completed' || runStatuses['valuation']?.status === 'success'

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-2 border-b border-softform-navy-950/5 pb-4">
        <h2 className="text-lg font-semibold text-softform-navy-950 dark:text-slate-100">
          Workspace Dashboard
        </h2>
        <p className="text-xs text-softform-text-secondary">
          Track the ingestion pipelines, diagnostic analyses, and AI readiness markers of your active workspace.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* 1. Uploaded Files */}
        <Link 
          to="/platform/data-room" 
          className="softform-card hover-lift p-5 rounded-[22px] flex flex-col justify-between border border-white/60 dark:border-slate-800/60 min-h-[180px]"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-xl bg-slate-100/60 text-slate-650 dark:bg-slate-800/60 dark:text-slate-400">
                <FileText size={20} />
              </div>
              <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
                Records
              </span>
            </div>
            <h3 className="text-[10px] font-bold text-softform-text-secondary uppercase tracking-wider">
              Uploaded Records
            </h3>
            <p className="text-lg font-bold text-softform-navy-950 dark:text-slate-100 mt-1">
              {filesCount !== null ? `${filesCount} Files` : '0 Files'}
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-semibold text-softform-text-secondary dark:text-slate-400">
            <span className="truncate max-w-[130px]">P&L, balance sheets, TBs</span>
            <ArrowRight size={10} />
          </div>
        </Link>

        {/* 2. Snapshot Status */}
        <Link 
          to="/platform/data-room" 
          className="softform-card hover-lift p-5 rounded-[22px] flex flex-col justify-between border border-white/60 dark:border-slate-800/60 min-h-[180px]"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-xl bg-slate-100/60 text-slate-650 dark:bg-slate-800/60 dark:text-slate-400">
                <Database size={20} />
              </div>
              <StatusChip variant={hasSnapshot ? 'signal' : 'caution'}>
                {hasSnapshot ? 'Active' : 'Missing'}
              </StatusChip>
            </div>
            <h3 className="text-[10px] font-bold text-softform-text-secondary uppercase tracking-wider">
              Financial Snapshot
            </h3>
            <p className="text-lg font-bold text-softform-navy-950 dark:text-slate-100 mt-1">
              {hasSnapshot ? 'Ingested' : 'Not Ingested'}
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-semibold text-softform-text-secondary dark:text-slate-400">
            <span className="truncate max-w-[130px]">
              {hasSnapshot ? 'Active balance sheet ready' : 'Needs ingestion run'}
            </span>
            <ArrowRight size={10} />
          </div>
        </Link>

        {/* 3. Valuation Status */}
        <Link 
          to="/platform/valuation" 
          className="softform-card hover-lift p-5 rounded-[22px] flex flex-col justify-between border border-white/60 dark:border-slate-800/60 min-h-[180px]"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-xl bg-slate-100/60 text-slate-650 dark:bg-slate-800/60 dark:text-slate-400">
                <BarChart3 size={20} />
              </div>
              <StatusChip variant={isValuationReady ? 'signal' : 'neutral'}>
                {isValuationReady ? 'Ready' : 'Pending'}
              </StatusChip>
            </div>
            <h3 className="text-[10px] font-bold text-softform-text-secondary uppercase tracking-wider">
              Indicative Valuation
            </h3>
            <p className="text-lg font-bold text-softform-navy-950 dark:text-slate-100 mt-1">
              {isValuationReady ? 'Calculated' : 'Pending'}
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-semibold text-softform-text-secondary dark:text-slate-400">
            <span className="truncate max-w-[130px]">
              {isValuationReady ? 'WACC & DCF ready' : 'Requires calculation run'}
            </span>
            <ArrowRight size={10} />
          </div>
        </Link>

        {/* 4. Latest Analysis */}
        <Link 
          to="/platform/financial-health" 
          className="softform-card hover-lift p-5 rounded-[22px] flex flex-col justify-between border border-white/60 dark:border-slate-800/60 min-h-[180px]"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-xl bg-slate-100/60 text-slate-650 dark:bg-slate-800/60 dark:text-slate-400">
                <HeartPulse size={20} />
              </div>
              <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
                Diagnostic
              </span>
            </div>
            <h3 className="text-[10px] font-bold text-softform-text-secondary uppercase tracking-wider">
              Latest Diagnostic
            </h3>
            <p className="text-lg font-bold text-softform-navy-950 dark:text-slate-100 mt-1 truncate">
              {latestAnalysis ? latestAnalysis.name : 'None'}
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-semibold text-softform-text-secondary dark:text-slate-400">
            <span className="truncate max-w-[130px]">
              {latestAnalysis ? latestAnalysis.date : 'No runs compiled'}
            </span>
            <ArrowRight size={10} />
          </div>
        </Link>

        {/* 5. AI CFO Readiness (Active Dark Card) */}
        <Link 
          to="/platform/ai-cfo" 
          className="softform-navy-card hover-lift p-5 rounded-[22px] flex flex-col justify-between min-h-[180px] text-white"
        >
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-xl bg-white/10 text-white">
                <BotMessageSquare size={20} />
              </div>
              <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.12em] bg-softform-teal-500/20 text-softform-aqua-300 border-softform-teal-500/40 animate-pulse">
                {completedCoreCount === coreRunTypes.length ? 'Ready' : 'Pending'}
              </span>
            </div>
            <h3 className="text-[10px] font-bold text-slate-200 uppercase tracking-wider">
              AI CFO Context
            </h3>
            <p className="text-lg font-bold text-white mt-1">
              {completedCoreCount === coreRunTypes.length ? 'Fully Prepared' : `${completedCoreCount}/${coreRunTypes.length} Core Runs`}
            </p>
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-semibold text-slate-200">
            <span className="truncate max-w-[130px]">
              {completedCoreCount === coreRunTypes.length ? 'Context is fully ready' : 'Execute core runs first'}
            </span>
            <ArrowRight size={10} className="text-slate-200" />
          </div>
        </Link>
      </div>
    </section>
  )
}
