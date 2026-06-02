import { Building2, CheckCircle2, Circle, FileText } from 'lucide-react'
import { CompanyProfile } from '../types'

type CompanyStripProps = {
  profile: CompanyProfile
  dataMode: string
}

export default function CompanyStrip({ profile, dataMode }: CompanyStripProps) {
  const connectedCount = profile.connectedRecords.filter(r => r.status === 'connected').length
  const totalCount = profile.connectedRecords.length
  
  return (
    <div className="softform-panel rounded-[28px] p-5 mb-6">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-softform-teal-500/10">
            <Building2 size={20} className="text-softform-teal-deep" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-softform-navy-950">
              {profile.companyName}
            </h3>
            <p className="text-xs text-softform-text-muted">
              {profile.sector}
            </p>
          </div>
        </div>

        <div className="h-8 w-px bg-softform-navy-900/10" />

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted mb-0.5">
            Geography
          </p>
          <p className="text-xs font-semibold text-softform-navy-900">
            {profile.geography}
          </p>
        </div>

        <div className="h-8 w-px bg-softform-navy-900/10" />

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted mb-0.5">
            Connected Records
          </p>
          <div className="flex items-center gap-2">
            <FileText size={14} className="text-softform-teal-deep" />
            <span className="text-xs font-semibold text-softform-navy-900">
              {connectedCount}/{totalCount} datasets
            </span>
          </div>
        </div>

        <div className="h-8 w-px bg-softform-navy-900/10" />

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            {profile.connectedRecords.slice(0, 4).map((record) => (
              <div
                key={record.id}
                className="relative group"
                title={record.label}
              >
                {record.status === 'connected' ? (
                  <CheckCircle2 size={16} className="text-softform-teal-500" />
                ) : (
                  <Circle size={16} className="text-softform-text-muted/40" />
                )}
              </div>
            ))}
            {profile.connectedRecords.length > 4 && (
              <span className="text-xs text-softform-text-muted">
                +{profile.connectedRecords.length - 4}
              </span>
            )}
          </div>
        </div>

        <div className="ml-auto">
          <div className="inline-flex items-center gap-2 rounded-full bg-softform-teal-500/10 px-3 py-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-softform-teal-500" />
            <span className="text-xs font-semibold text-softform-teal-deep">
              {dataMode === 'demo_workspace' ? 'Demo Workspace' : dataMode}
            </span>
          </div>
        </div>
      </div>

      {/* Expandable records detail - optional */}
      <details className="mt-4 group">
        <summary className="cursor-pointer text-xs font-semibold text-softform-teal-deep hover:text-softform-teal-500 transition-colors list-none">
          <span className="inline-flex items-center gap-1">
            View connected records
            <svg className="h-3 w-3 transition-transform group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        </summary>
        <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
          {profile.connectedRecords.map((record) => (
            <div
              key={record.id}
              className="flex items-center gap-2 rounded-lg bg-white/40 px-3 py-2 text-xs"
            >
              {record.status === 'connected' ? (
                <CheckCircle2 size={14} className="text-softform-teal-500 shrink-0" />
              ) : record.status === 'partial' ? (
                <Circle size={14} className="text-softform-amber-500 shrink-0" />
              ) : (
                <Circle size={14} className="text-softform-text-muted/40 shrink-0" />
              )}
              <span className="font-medium text-softform-navy-900">{record.label}</span>
            </div>
          ))}
        </div>
      </details>
    </div>
  )
}
