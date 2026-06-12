import { Activity, ShieldAlert, Cpu, Calendar, CheckCircle, HelpCircle } from 'lucide-react'

export interface RunMetadata {
  id: string
  runId: string
  snapshotId: string
  status: string
  runType: string
  createdAt: string
  logicVersion: string
  warningsCount?: number
}

interface RunMetadataBadgeProps {
  metadata?: RunMetadata
}

function formatRunType(type: string): string {
  if (!type) return ''
  return type
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function truncateId(id: string): string {
  if (!id) return ''
  if (id.length <= 12) return id
  return `${id.slice(0, 8)}...${id.slice(-4)}`
}

function formatDate(isoString: string): string {
  try {
    const date = new Date(isoString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
  } catch {
    return isoString
  }
}

export default function RunMetadataBadge({ metadata }: RunMetadataBadgeProps) {
  if (!metadata) {
    return (
      <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700/60 rounded-full text-xs font-semibold backdrop-blur-sm shadow-sm">
        <HelpCircle size={13} className="text-slate-400" />
        <span>Local/Fallback Mode (Non-Persisted)</span>
      </div>
    )
  }

  const { runId, snapshotId, status, runType, createdAt, logicVersion, warningsCount = 0 } = metadata

  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-xl text-xs text-slate-600 dark:text-slate-300 backdrop-blur-md shadow-sm">
      {/* Run Type */}
      <div className="flex items-center gap-1.5">
        <Activity size={14} className="text-softform-teal-deep dark:text-softform-aqua-300" />
        <span className="font-semibold text-slate-800 dark:text-slate-100">{formatRunType(runType)}</span>
      </div>

      <span className="hidden sm:inline text-slate-300 dark:text-slate-700">|</span>

      {/* Run ID */}
      <div className="flex items-center gap-1">
        <span className="text-slate-400">Run:</span>
        <code className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800/60 rounded text-[11px] font-mono select-all" title={runId}>
          {truncateId(runId)}
        </code>
      </div>

      {/* Snapshot ID */}
      <div className="flex items-center gap-1">
        <span className="text-slate-400">Snapshot:</span>
        <code className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800/60 rounded text-[11px] font-mono select-all" title={snapshotId}>
          {truncateId(snapshotId)}
        </code>
      </div>

      <span className="hidden sm:inline text-slate-300 dark:text-slate-700">|</span>

      {/* Status */}
      <div className="flex items-center gap-1.5">
        {isCompleted ? (
          <CheckCircle size={13} className="text-emerald-500" />
        ) : isFailed ? (
          <ShieldAlert size={13} className="text-rose-500" />
        ) : (
          <span className="w-2 h-2 rounded-full bg-amber-400" />
        )}
        <span className="capitalize font-medium">{status}</span>
      </div>

      {/* Logic Version */}
      <div className="flex items-center gap-1">
        <Cpu size={13} className="text-slate-400" />
        <span className="text-slate-400">Engine:</span>
        <span className="font-mono text-[11px]">{logicVersion}</span>
      </div>

      {/* Timestamp */}
      <div className="flex items-center gap-1.5">
        <Calendar size={13} className="text-slate-400" />
        <span>{formatDate(createdAt)}</span>
      </div>

      {/* Warnings count if any */}
      {warningsCount > 0 && (
        <div className="flex items-center gap-1 px-2 py-0.5 bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 border border-amber-200/50 dark:border-amber-900/30 rounded-full font-medium">
          <ShieldAlert size={12} />
          <span>{warningsCount} {warningsCount === 1 ? 'Warning' : 'Warnings'}</span>
        </div>
      )}
    </div>
  )
}
