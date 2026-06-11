import { Link } from 'react-router-dom'
import { Database, ArrowRight } from 'lucide-react'

interface WorkspaceInsufficientDataStateProps {
  missingRequirements?: string[]
  nextActions?: string[]
}

export default function WorkspaceInsufficientDataState({
  missingRequirements = ['Profit & Loss Statement (P&L)', 'Balance Sheet', 'Cash Flow Statement', 'Debt Amortization Schedule'],
  nextActions = ['Upload core financial statements in the Data Room', 'Build active financial snapshot'],
}: WorkspaceInsufficientDataStateProps) {
  return (
    <div className="softform-panel relative overflow-hidden rounded-[32px] p-8 sm:p-10 shadow-floating-panel bg-[linear-gradient(145deg,rgba(255,255,255,0.76),rgba(231,240,244,0.66))] border border-white">
      {/* Ambient glow backgrounds */}
      <div className="absolute -top-12 -left-12 w-48 h-48 bg-softform-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-softform-amber-300/10 rounded-full blur-3xl pointer-events-none" />

      <div className="mx-auto flex max-w-lg flex-col items-center text-center relative z-10">
        {/* Icon container */}
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-[20px] bg-softform-mist-100/80 text-softform-amber-500 ring-4 ring-softform-aqua-300/10 shadow-soft-inner">
          <Database size={28} strokeWidth={1.5} />
        </div>

        {/* Title */}
        <h2 className="mb-2 text-lg font-bold text-softform-navy-950">
          Insufficient Workspace Data
        </h2>
        
        {/* Description */}
        <p className="mb-6 text-sm leading-relaxed text-softform-text-secondary">
          To display financial outcomes and run advisory modules, this workspace requires core statements to be uploaded and compiled.
        </p>

        {/* Missing requirements checklist */}
        <div className="w-full text-left bg-white/40 border border-white/60 rounded-2xl p-5 mb-6 backdrop-blur-sm space-y-4">
          <div className="space-y-1">
            <span className="block text-[10px] font-bold uppercase tracking-wider text-softform-navy-900/40">
              Required Documents
            </span>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1.5">
              {missingRequirements.map((req, idx) => (
                <li key={idx} className="flex items-center gap-2 text-xs text-softform-text-secondary">
                  <div className="h-1.5 w-1.5 rounded-full bg-softform-amber-500/80 shrink-0" />
                  <span className="truncate">{req}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="h-[1px] bg-softform-navy-950/5" />

          <div className="space-y-1">
            <span className="block text-[10px] font-bold uppercase tracking-wider text-softform-navy-900/40">
              Next Actions
            </span>
            <ul className="space-y-1.5 pt-1.5">
              {nextActions.map((action, idx) => (
                <li key={idx} className="flex items-center gap-2 text-xs text-softform-text-secondary">
                  <div className="flex h-4 w-4 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep shrink-0">
                    <span className="text-[10px] font-bold">{idx + 1}</span>
                  </div>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Action Button */}
        <Link
          to="/platform/data-room"
          className="inline-flex items-center gap-1.5 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-softform-navy-800 transition"
        >
          Go to Data Room
          <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  )
}
