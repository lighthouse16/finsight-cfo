import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import {
  FileText,
  ArrowRight,
  Database,
  Compass,
  TrendingUp,
  CheckSquare,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SourceInfoTooltip from '../market-watch/components/SourceInfoTooltip'
import { fetchDataRoomReadiness } from './api/dataRoomApi'
import type { DataRoomResponse } from './types'

export default function DataRoomPage() {
  const [activeNotification, setActiveNotification] = useState<string | null>(null)
  const [readinessData, setReadinessData] = useState<DataRoomResponse | null>(null)
  const [isLoadingReadiness, setIsLoadingReadiness] = useState(true)

  useEffect(() => {
    let isMounted = true

    fetchDataRoomReadiness().then((data) => {
      if (!isMounted) return
      setReadinessData(data)
      setIsLoadingReadiness(false)
    })

    return () => {
      isMounted = false
    }
  }, [])

  const handleActionClick = (recordName: string, action: string) => {
    setActiveNotification(
      `Integration trigger simulated: "${action}" for ${recordName}. Records integration is currently set to demo context. Connection to company servers requires production connectors.`
    )
    setTimeout(() => {
      setActiveNotification(null)
    }, 6000)
  }

  const records = readinessData?.records ?? []
  const dependencies = readinessData?.dependencies ?? []
  const totalRequired = readinessData?.summary.totalRequired ?? 0
  const connectedRequired = readinessData?.summary.connectedRequired ?? 0
  const missingRequired = readinessData?.summary.missingRequired ?? 0
  const readinessPercentage = readinessData?.summary.readinessPercentage ?? 0

  // Status mapping to calm colors/chips
  const getStatusChipVariant = (status: string) => {
    switch (status) {
      case 'demo_available':
      case 'connected':
        return 'signal'
      case 'missing':
        return 'caution'
      case 'optional':
      case 'coming_soon':
      default:
        return 'neutral'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'demo_available':
        return 'Demo available'
      case 'connected':
        return 'Connected'
      case 'missing':
        return 'Missing'
      case 'optional':
        return 'Optional'
      case 'coming_soon':
        return 'Coming soon'
      default:
        return status
    }
  }

  return (
    <div className="space-y-8 pb-12">
      {/* 1. Page Header */}
      <PageHeader
        title="Data Room"
        subtitle="Company records required for production financial analysis and advisory context."
        titleAddon={
          <SourceInfoTooltip
            title="Data Room Provenance"
            sources={[
              { label: 'Company Financial Records', mode: 'workspace-derived' },
              { label: 'Integration Status Tracker', mode: 'workspace-derived' },
            ]}
            ariaLabel="Data room source information"
          />
        }
        chip={
          <StatusChip variant={readinessPercentage === 100 ? 'signal' : 'caution'}>
            {readinessPercentage}% Connected
          </StatusChip>
        }
      />

      {/* State Notification Toast */}
      <AnimatePresence>
        {activeNotification && (
          <div className="fixed bottom-6 right-6 z-50 max-w-md rounded-2xl border border-white/60 bg-white/95 p-4 shadow-floating-panel backdrop-blur-xl transition-all duration-300">
            <div className="flex gap-3">
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep">
                <Database size={12} />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold text-softform-navy-950">System Notification</p>
                <p className="text-xs text-softform-text-secondary leading-relaxed">
                  {activeNotification}
                </p>
              </div>
            </div>
          </div>
        )}
      </AnimatePresence>

      {/* 2. Data Readiness Overview */}
      <section className="grid gap-4 sm:grid-cols-4">
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Required Records
          </p>
          <p className="text-2xl font-black text-softform-navy-950 tabular-finance">{totalRequired}</p>
          <p className="text-xs text-softform-text-secondary">Specified in advisory parameters</p>
        </div>
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Connected Records
          </p>
          <p className="text-2xl font-black text-softform-teal-deep tabular-finance">{connectedRequired}</p>
          <p className="text-xs text-softform-text-secondary">Currently active in demo mode</p>
        </div>
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Missing Records
          </p>
          <p className="text-2xl font-black text-softform-amber-500 tabular-finance">{missingRequired}</p>
          <p className="text-xs text-softform-text-secondary">Required for full calibration</p>
        </div>
        <div className="softform-card rounded-[22px] p-5 space-y-2 hover-lift">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-softform-text-muted/90">
            Production Readiness
          </p>
          <p className="text-2xl font-black text-softform-navy-950 tabular-finance">{readinessPercentage}%</p>
          <p className="text-xs text-softform-text-secondary">Demo to Production threshold</p>
        </div>
      </section>

      {/* 3. Required Records Checklist */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-bold text-softform-navy-950">Integration Status</h2>
          <span className="text-xs font-medium text-softform-text-muted">
            {isLoadingReadiness ? 'Loading readiness contract' : 'Required records checklist'}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-softform-navy-950/10 text-[10px] font-bold uppercase tracking-[0.16em] text-softform-text-muted/80">
                <th className="pb-4 pl-3 w-8"></th>
                <th className="pb-4">Record Name</th>
                <th className="pb-4 hidden md:table-cell">Category</th>
                <th className="pb-4">Dependency Fits</th>
                <th className="pb-4 text-center">Status</th>
                <th className="pb-4 text-right pr-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-softform-navy-950/5">
              {records.map((rec) => (
                <tr key={rec.id} className="group hover:bg-white/20 transition-all duration-200">
                  <td className="py-4 pl-3">
                    {/* Checkbox indicator */}
                    {(rec.status === 'connected' || rec.status === 'demo_available') ? (
                      <div className="flex h-5 w-5 items-center justify-center rounded bg-softform-teal-deep/10 text-softform-teal-deep border border-softform-teal-deep/20 shadow-sm" title="Connected for Analysis">
                        <CheckSquare size={11} strokeWidth={2.5} />
                      </div>
                    ) : rec.status === 'missing' ? (
                      <div className="flex h-5 w-5 items-center justify-center rounded border border-softform-amber-500/30 text-softform-amber-500/80 bg-softform-cream/40 shadow-inner" title="Required Document Missing">
                        <div className="h-1.5 w-1.5 rounded-full bg-softform-amber-500" />
                      </div>
                    ) : (
                      <div className="flex h-5 w-5 items-center justify-center rounded border border-softform-text-muted/20 text-softform-text-muted/40 bg-white/20" title="Optional Document">
                        <div className="h-1 w-1 rounded-full bg-softform-text-muted/40" />
                      </div>
                    )}
                  </td>
                  <td className="py-4 space-y-1">
                    <div className="font-bold text-softform-navy-950 text-sm flex items-center gap-2">
                      <FileText size={14} className="text-softform-text-muted/70 shrink-0" />
                      {rec.name}
                    </div>
                    <p className="text-xs text-softform-text-secondary max-w-[320px] leading-relaxed">
                      {rec.purpose}
                    </p>
                  </td>
                  <td className="py-4 hidden md:table-cell">
                    <span className="text-xs font-medium text-softform-text-secondary">{rec.category}</span>
                  </td>
                  <td className="py-4">
                    <div className="flex flex-wrap gap-1">
                      {rec.requiredFor.map((rf) => (
                        <span
                          key={rf}
                          className="inline-block rounded bg-softform-mist-100/60 px-2 py-0.5 text-[10px] text-softform-teal-deep font-bold border border-softform-aqua-300/20 uppercase tracking-[0.08em]"
                        >
                          {rf}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-4 text-center">
                    <StatusChip variant={getStatusChipVariant(rec.status)}>
                      {getStatusLabel(rec.status)}
                    </StatusChip>
                  </td>
                  <td className="py-4 text-right pr-3">
                    <button
                      type="button"
                      onClick={() => handleActionClick(rec.name, rec.actionLabel)}
                      className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold transition border shadow-sm ${
                        rec.actionLabel === 'Review'
                          ? 'bg-white/80 border-white/60 text-softform-navy-950 hover:bg-white hover:-translate-y-0.5'
                          : rec.actionLabel === 'Upload'
                          ? 'bg-softform-navy-900 border-softform-navy-950/10 text-white hover:bg-softform-navy-800 hover:-translate-y-0.5'
                          : 'bg-white/40 border-white/30 text-softform-text-muted cursor-not-allowed'
                      }`}
                      disabled={rec.actionLabel === 'Coming soon'}
                    >
                      {rec.actionLabel}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 4. Analysis Dependency Map */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-bold text-softform-navy-950">Analysis Dependency Mapping</h2>
          <p className="text-xs text-softform-text-muted mt-1">
            Understanding how integrated documents feed the advisory models
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {dependencies.map((feed) => (
            <div
              key={feed.recordGroup}
              className="p-5 rounded-[22px] bg-white/40 border border-white/60 shadow-sm space-y-4 hover-lift"
            >
              <h3 className="font-bold text-softform-navy-950 text-sm leading-snug">
                {feed.recordGroup}
              </h3>
              <div className="h-[1px] bg-softform-navy-950/5" />
              <div className="space-y-2">
                <span className="text-[9px] font-bold text-softform-text-muted/90 uppercase tracking-[0.14em]">
                  Feeds Engine Outcomes
                </span>
                <ul className="space-y-2 pt-1">
                  {feed.outputs.map((out, oIdx) => (
                    <li key={oIdx} className="text-xs text-softform-text-secondary flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-softform-teal-deep/70 shrink-0" />
                      <span className="font-medium text-softform-navy-900/90">{out}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Demo vs Production State */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-5">
        <h2 className="text-base font-bold text-softform-navy-950">Active Workspace Environment</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-bold text-softform-navy-950 block">Analysis Context</span>
            <span className="text-softform-teal-deep font-semibold">Demo financial analysis active</span>
          </div>
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-bold text-softform-navy-950 block">Market Indicators</span>
            <span className="text-softform-teal-deep font-semibold">Provider-backed market data active</span>
          </div>
          <div className="p-5 rounded-[22px] bg-white/40 border border-white/60 text-xs space-y-2 hover-lift">
            <span className="font-bold text-softform-navy-950 block">Requirement Level</span>
            <span className="text-softform-amber-500 font-semibold">Company records required for production mode</span>
          </div>
        </div>
      </section>

      {/* 6. Link to Advisory Blueprint & Market Watch */}
      <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
        <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
          <h3 className="font-bold text-softform-navy-950 text-base">Explore Workspace Modules</h3>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            The Data Room is the primary source of company records. Connect records to transition from demo context to production-ready analysis in other modules.
          </p>
        </div>
        <div className="flex gap-3.5 shrink-0 w-full sm:w-auto justify-center sm:justify-end">
          <Link
            to="/platform/market-watch"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-white/80 bg-white/60 px-4 py-2.5 text-xs font-bold text-softform-navy-950 hover:bg-white transition shadow-sm"
          >
            <TrendingUp size={14} className="text-softform-teal-deep" />
            Review Market Watch
          </Link>
          <Link
            to="/platform/advisory-blueprint"
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-softform-navy-800 transition shadow-sm"
          >
            <Compass size={14} className="text-softform-teal-deep" />
            View Advisory Blueprint
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>

      {/* Footer Info */}
      <footer className="pt-6 border-t border-softform-navy-950/5 text-center space-y-2">
        <p className="text-xs text-softform-text-muted">
          Demo analysis is currently active. Connect company records to transition to production-ready analysis.
        </p>
        <p className="text-xs text-softform-text-muted">
          FinSight CFO Workspace • Powered by softform design token system.
        </p>
      </footer>
    </div>
  )
}
