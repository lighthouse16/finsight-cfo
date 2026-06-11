/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react'
import { Play, RefreshCw, CheckCircle2, AlertTriangle, HelpCircle, Loader2 } from 'lucide-react'
import {
  triggerAnalysisRun,
  fetchAllRunStatuses,
  ANALYSIS_RUN_TYPES,
  getRunStatusLabel,
  isRunMissing,
} from '../../lib/workspaceRunHelpers'

interface WorkspaceRunReadinessProps {
  workspaceId: string
  onStatusChange?: () => void
}

export default function WorkspaceRunReadiness({ workspaceId, onStatusChange }: WorkspaceRunReadinessProps) {
  const [statuses, setStatuses] = useState<Record<string, any | null>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Track which runs are currently executing
  const [executingTypes, setExecutingTypes] = useState<Record<string, boolean>>({})
  const [runningAll, setRunningAll] = useState(false)
  const [runningAllProgress, setRunningAllProgress] = useState('')

  const loadStatuses = async () => {
    try {
      setLoading(true)
      const data = await fetchAllRunStatuses(workspaceId)
      setStatuses(data)
      setError(null)
    } catch (err: any) {
      console.error('Error loading run statuses:', err)
      setError('Failed to fetch analysis run statuses.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (workspaceId) {
      loadStatuses()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId])

  const handleRunSingle = async (runType: string) => {
    setExecutingTypes((prev) => ({ ...prev, [runType]: true }))
    try {
      await triggerAnalysisRun(workspaceId, runType)
      await loadStatuses()
      if (onStatusChange) {
        onStatusChange()
      }
    } catch (err: any) {
      console.error(`Error running analysis for ${runType}:`, err)
      alert(`Failed to run ${runType}: ${err.message || err}`)
    } finally {
      setExecutingTypes((prev) => ({ ...prev, [runType]: false }))
    }
  }

  const handleRunAllMissing = async () => {
    const missingCoreTypes = ANALYSIS_RUN_TYPES.filter(
      (typeInfo) => typeInfo.isCore && isRunMissing(statuses[typeInfo.key])
    )

    if (missingCoreTypes.length === 0) {
      return
    }

    setRunningAll(true)
    try {
      for (let i = 0; i < missingCoreTypes.length; i++) {
        const typeInfo = missingCoreTypes[i]
        setRunningAllProgress(`Running ${typeInfo.label} (${i + 1}/${missingCoreTypes.length})...`)
        
        // Update local execution state for spinner
        setExecutingTypes((prev) => ({ ...prev, [typeInfo.key]: true }))
        try {
          await triggerAnalysisRun(workspaceId, typeInfo.key)
        } catch (err: any) {
          console.error(`Sequential run failed for ${typeInfo.key}:`, err)
          // We can report warning but continue
        } finally {
          setExecutingTypes((prev) => ({ ...prev, [typeInfo.key]: false }))
        }
      }
      setRunningAllProgress('Refreshing statuses...')
      await loadStatuses()
      if (onStatusChange) {
        onStatusChange()
      }
    } catch (err: any) {
      console.error('Error during Run All operation:', err)
    } finally {
      setRunningAll(false)
      setRunningAllProgress('')
    }
  }

  const formatDate = (isoString?: string) => {
    if (!isoString) return ''
    try {
      return new Date(isoString).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      })
    } catch {
      return isoString
    }
  }

  if (loading && Object.keys(statuses).length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 px-4 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm">
        <Loader2 className="w-8 h-8 text-softform-teal-deep dark:text-softform-aqua-300 animate-spin mb-2" />
        <span className="text-sm text-slate-500 dark:text-slate-400">Loading analysis run statuses...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-6 bg-rose-50/50 dark:bg-rose-950/10 border border-rose-200/50 dark:border-rose-900/20 rounded-3xl backdrop-blur-md shadow-sm">
        <AlertTriangle className="w-8 h-8 text-rose-500 mb-2" />
        <span className="text-sm text-slate-800 dark:text-slate-200 font-semibold mb-1">{error}</span>
        <button
          onClick={loadStatuses}
          className="text-xs font-semibold text-softform-teal-deep dark:text-softform-aqua-300 hover:underline flex items-center gap-1 mt-2"
        >
          <RefreshCw size={12} /> Try Again
        </button>
      </div>
    )
  }

  const coreRunTypes = ANALYSIS_RUN_TYPES.filter((t) => t.isCore)
  const completedCoreCount = coreRunTypes.filter((t) => getRunStatusLabel(statuses[t.key]) === 'completed').length
  const missingCoreCount = coreRunTypes.length - completedCoreCount

  return (
    <div className="bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm p-6 max-w-4xl w-full">
      {/* Header and Core Stats */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5 mb-5">
        <div>
          <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">Analysis Run Readiness</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {completedCoreCount} of {coreRunTypes.length} core analyses completed.
          </p>
        </div>
        
        {missingCoreCount > 0 && (
          <div className="flex items-center gap-3">
            {runningAll && (
              <span className="text-xs text-slate-500 dark:text-slate-400 italic animate-pulse">
                {runningAllProgress}
              </span>
            )}
            <button
              onClick={handleRunAllMissing}
              disabled={runningAll || Object.values(executingTypes).some(Boolean)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 dark:bg-slate-100 hover:bg-slate-850 dark:hover:bg-white text-white dark:text-slate-900 text-xs font-semibold rounded-full shadow-sm disabled:opacity-50 transition-colors"
            >
              {runningAll ? (
                <Loader2 size={13} className="animate-spin" />
              ) : (
                <Play size={13} fill="currentColor" />
              )}
              <span>Run All Missing Core Runs</span>
            </button>
          </div>
        )}
      </div>

      {/* Grid of Analyses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ANALYSIS_RUN_TYPES.map((typeInfo) => {
          const run = statuses[typeInfo.key]
          const status = getRunStatusLabel(run)
          const isCore = typeInfo.isCore
          const isExecuting = !!executingTypes[typeInfo.key]
          
          return (
            <div
              key={typeInfo.key}
              className={`flex items-center justify-between p-3.5 rounded-2xl border ${
                status === 'completed'
                  ? 'bg-emerald-50/20 dark:bg-emerald-950/5 border-emerald-100/50 dark:border-emerald-900/10'
                  : status === 'failed'
                  ? 'bg-rose-50/20 dark:bg-rose-950/5 border-rose-100/50 dark:border-rose-900/10'
                  : 'bg-slate-50/40 dark:bg-slate-800/10 border-slate-100/60 dark:border-slate-800/30'
              }`}
            >
              {/* Type and Meta */}
              <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
                    {typeInfo.label}
                  </span>
                  {isCore && (
                    <span className="text-[10px] uppercase font-bold tracking-wide text-slate-400 dark:text-slate-500">
                      Core
                    </span>
                  )}
                </div>
                
                {run?.createdAt ? (
                  <span className="text-[11px] text-slate-400 dark:text-slate-500">
                    Run: {formatDate(run.createdAt)}
                  </span>
                ) : (
                  <span className="text-[11px] text-slate-400 dark:text-slate-500 italic">
                    Not run yet
                  </span>
                )}
              </div>

              {/* Status and Action */}
              <div className="flex items-center gap-3">
                {/* Status indicator */}
                <div className="flex items-center">
                  {status === 'completed' ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 text-[11px] font-semibold rounded-full border border-emerald-100 dark:border-emerald-900/30">
                      <CheckCircle2 size={11} /> Ready
                    </span>
                  ) : status === 'failed' ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-rose-50 dark:bg-rose-950/30 text-rose-600 dark:text-rose-400 text-[11px] font-semibold rounded-full border border-rose-100 dark:border-rose-900/30">
                      <AlertTriangle size={11} /> Failed
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-100 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 text-[11px] font-medium rounded-full border border-slate-200/50 dark:border-slate-700/30">
                      <HelpCircle size={11} /> Pending
                    </span>
                  )}
                </div>

                {/* Run / Rerun Button */}
                <button
                  onClick={() => handleRunSingle(typeInfo.key)}
                  disabled={isExecuting || runningAll}
                  className="flex items-center justify-center w-7 h-7 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-250 dark:border-slate-700 rounded-full shadow-sm hover:shadow transition-shadow disabled:opacity-55"
                  title={status === 'completed' ? 'Rerun Analysis' : 'Run Analysis'}
                >
                  {isExecuting ? (
                    <Loader2 size={12} className="animate-spin text-softform-teal-deep dark:text-softform-aqua-300" />
                  ) : status === 'completed' ? (
                    <RefreshCw size={11} />
                  ) : (
                    <Play size={11} fill="currentColor" className="ml-0.5" />
                  )}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
