import { Building2 } from 'lucide-react'
import { CompanyProfile } from '../types'
import clsx from 'clsx'

type CompanyStripProps = {
  profile: CompanyProfile
  dataMode: string
}

export default function CompanyStrip({ profile, dataMode }: CompanyStripProps) {
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

        <div className="flex-1 min-w-[200px]">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted mb-1">
            Connected Records
          </p>
          <div className="flex flex-wrap items-center gap-y-1 text-xs text-softform-text-secondary font-medium">
            {profile.connectedRecords.map((record, index) => (
              <span key={record.id} className="flex items-center">
                {index > 0 && <span className="mx-1.5 text-softform-text-muted opacity-40">·</span>}
                <span className={clsx(
                  record.status === 'connected' ? 'text-softform-teal-deep font-semibold' : 'text-softform-text-muted/60'
                )}>
                  {record.label}
                </span>
              </span>
            ))}
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
    </div>
  )
}
