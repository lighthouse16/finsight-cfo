import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText,
  ArrowRight,
  Database,
  Compass,
  TrendingUp,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import { dataRoomRecords, dependencyFeeds } from './data/dataRoomSeed'

export default function DataRoomPage() {
  const [activeNotification, setActiveNotification] = useState<string | null>(null)

  const handleActionClick = (recordName: string, action: string) => {
    setActiveNotification(
      `Integration trigger simulated: "${action}" for ${recordName}. Records integration is currently set to demo context. Connection to company servers requires production connectors.`
    )
    setTimeout(() => {
      setActiveNotification(null)
    }, 6000)
  }

  // Calculate quick stats
  const totalRequired = dataRoomRecords.filter((r) => r.status !== 'optional').length
  const connectedRequired = dataRoomRecords.filter(
    (r) => r.status === 'demo_available'
  ).length
  const missingRequired = dataRoomRecords.filter(
    (r) => r.status === 'missing'
  ).length
  const readinessPercentage = Math.round((connectedRequired / totalRequired) * 100)

  // Status mapping to calm colors/chips
  const getStatusChipVariant = (status: string) => {
    switch (status) {
      case 'demo_available':
        return 'signal'
      case 'connected':
        return 'signal'
      case 'missing':
        return 'caution'
      case 'optional':
      default:
        return 'neutral'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'demo_available':
        return 'Demo Available'
      case 'connected':
        return 'Connected'
      case 'missing':
        return 'Missing'
      case 'optional':
        return 'Optional'
      default:
        return status
    }
  }

  return (
    <div className="space-y-8">
      {/* 1. Page Header */}
      <PageHeader
        title="Data Room"
        subtitle="Company records required for production financial analysis and advisory context."
        chip={
          <StatusChip variant={readinessPercentage === 100 ? 'signal' : 'caution'}>
            {readinessPercentage}% Connected
          </StatusChip>
        }
      />

      <div className="rounded-2xl border border-white/50 bg-white/20 p-4 backdrop-blur-sm">
        <p className="text-xs leading-relaxed text-softform-text-muted">
          <strong>Quiet Disclaimer:</strong> Demo analysis is currently used until company records are connected.
        </p>
      </div>

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
        <div className="softform-card rounded-2xl p-5 space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted">
            Required Records
          </p>
          <p className="text-2xl font-black text-softform-navy-950">{totalRequired}</p>
          <p className="text-xs text-softform-text-secondary">Specified in advisory parameters</p>
        </div>
        <div className="softform-card rounded-2xl p-5 space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted">
            Connected Records
          </p>
          <p className="text-2xl font-black text-softform-teal-deep">{connectedRequired}</p>
          <p className="text-xs text-softform-text-secondary">Currently active in demo mode</p>
        </div>
        <div className="softform-card rounded-2xl p-5 space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted">
            Missing Records
          </p>
          <p className="text-2xl font-black text-softform-amber-500">{missingRequired}</p>
          <p className="text-xs text-softform-text-secondary">Required for full calibration</p>
        </div>
        <div className="softform-card rounded-2xl p-5 space-y-2">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted">
            Production Readiness
          </p>
          <p className="text-2xl font-black text-softform-navy-950">{readinessPercentage}%</p>
          <p className="text-xs text-softform-text-secondary">Demo to Production threshold</p>
        </div>
      </section>

      {/* 3. Required Records Checklist */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-bold text-softform-navy-950">Integration Status</h2>
          <span className="text-xs text-softform-text-muted">Required records checklist</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-softform-navy-950/5 text-[10px] font-semibold uppercase tracking-wider text-softform-text-muted">
                <th className="pb-3 pl-2">Record Name</th>
                <th className="pb-3 hidden md:table-cell">Category</th>
                <th className="pb-3">Dependency Fits</th>
                <th className="pb-3 text-center">Status</th>
                <th className="pb-3 text-right pr-2">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-softform-navy-950/5">
              {dataRoomRecords.map((rec) => (
                <tr key={rec.id} className="group hover:bg-white/10 transition-colors">
                  <td className="py-4 pl-2 space-y-1">
                    <div className="font-bold text-softform-navy-950 text-sm flex items-center gap-2">
                      <FileText size={14} className="text-softform-text-muted shrink-0" />
                      {rec.name}
                    </div>
                    <p className="text-xs text-softform-text-secondary max-w-[280px] leading-relaxed">
                      {rec.purpose}
                    </p>
                  </td>
                  <td className="py-4 hidden md:table-cell">
                    <span className="text-xs text-softform-text-secondary">{rec.category}</span>
                  </td>
                  <td className="py-4">
                    <div className="flex flex-wrap gap-1">
                      {rec.requiredFor.map((rf) => (
                        <span
                          key={rf}
                          className="inline-block rounded bg-softform-mist-100/40 px-1.5 py-0.5 text-[10px] text-softform-teal-deep font-semibold"
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
                  <td className="py-4 text-right pr-2">
                    <button
                      type="button"
                      onClick={() => handleActionClick(rec.name, rec.actionLabel)}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition border ${
                        rec.actionLabel === 'Review'
                          ? 'bg-white/80 border-white/60 text-softform-navy-950 hover:bg-white'
                          : rec.actionLabel === 'Upload'
                          ? 'bg-softform-navy-900 border-softform-navy-950/10 text-white hover:bg-softform-navy-800'
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

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {dependencyFeeds.map((feed, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-white/45 border border-white/60 shadow-sm space-y-3"
            >
              <h3 className="font-bold text-softform-navy-950 text-sm leading-snug">
                {feed.recordGroup}
              </h3>
              <div className="h-0.5 bg-softform-navy-950/5" />
              <div className="space-y-2">
                <span className="text-[9px] font-semibold text-softform-text-muted uppercase tracking-wider">
                  Feeds Engine Outcomes
                </span>
                <ul className="space-y-1">
                  {feed.outputs.map((out, oIdx) => (
                    <li key={oIdx} className="text-xs text-softform-text-secondary flex items-center gap-1.5">
                      <div className="h-1.5 w-1.5 rounded-full bg-softform-teal-deep shrink-0" />
                      <span>{out}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Demo vs Production State */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-4">
        <h2 className="text-base font-bold text-softform-navy-950">Active Workspace Environment</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="p-4 rounded-xl bg-white/45 border border-white/60 text-xs space-y-1">
            <span className="font-semibold text-softform-navy-950 block">Analysis Context</span>
            <span className="text-softform-teal-deep font-semibold">Demo financial analysis active</span>
          </div>
          <div className="p-4 rounded-xl bg-white/45 border border-white/60 text-xs space-y-1">
            <span className="font-semibold text-softform-navy-950 block">Market Indicators</span>
            <span className="text-softform-teal-deep font-semibold">Provider-backed market data active</span>
          </div>
          <div className="p-4 rounded-xl bg-white/45 border border-white/60 text-xs space-y-1">
            <span className="font-semibold text-softform-navy-950 block">Requirement Level</span>
            <span className="text-softform-amber-500 font-semibold">Company records required for production mode</span>
          </div>
        </div>
      </section>

      {/* 6. Link to Advisory Blueprint & Market Watch */}
      <section className="flex flex-col sm:flex-row gap-4 items-center justify-between p-6 rounded-3xl border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md">
        <div className="space-y-1 text-center sm:text-left">
          <h3 className="font-bold text-softform-navy-950 text-sm">Explore Workspace Modules</h3>
          <p className="text-xs text-softform-text-secondary">
            Navigate to active intelligence and planning outputs
          </p>
        </div>
        <div className="flex gap-3 shrink-0">
          <Link
            to="/platform/market-watch"
            className="inline-flex items-center gap-1.5 rounded-xl border border-white/80 bg-white/60 px-4 py-2 text-xs font-semibold text-softform-navy-950 hover:bg-white transition"
          >
            <TrendingUp size={14} className="text-softform-teal-deep" />
            Review Market Watch
          </Link>
          <Link
            to="/platform/advisory-blueprint"
            className="inline-flex items-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2 text-xs font-semibold text-white hover:bg-softform-navy-800 transition"
          >
            <Compass size={14} className="text-softform-teal-deep" />
            View Advisory Blueprint
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>
    </div>
  )
}

// Simple AnimatePresence fallback just for safe compilation in case framer-motion imports differ.
// Typically standard framer-motion is used, but we import it directly so it is standard.
import { AnimatePresence } from 'framer-motion'
