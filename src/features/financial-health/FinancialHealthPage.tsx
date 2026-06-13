/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, ShieldCheck, Coins, TrendingUp, AlertTriangle, Loader2, RefreshCw, Play } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import ScoreRing from '../../components/platform/ScoreRing'
import ServiceErrorState from '../../components/platform/ServiceErrorState'
import NavyHeroSection from '../../components/platform/NavyHeroSection'
import PageLoadingSkeleton from '../../components/platform/PageLoadingSkeleton'
import WorkflowFooter from '../../components/platform/WorkflowFooter'
import type { FinancialSignal, IntegrityCheckResult, RatioMetric } from '../market-watch/types'
import { getFinancialHealthAnalysis } from './financialHealthApi'
import { motion } from 'framer-motion'
import { formatNumber, formatHKD, formatBand, bandVariant } from '../../lib/formatters'
import { fetchLatestRunSafe, triggerAnalysisRun } from '../../lib/workspaceRunHelpers'

import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'

type MetricCard = {
  key: string
  label: string
  metric?: RatioMetric | null
  suffix?: string
  hint: string
}

const staggerContainer = {
  show: { transition: { staggerChildren: 0.04 } }
}

const staggerItem = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 }
}

export default function FinancialHealthPage() {
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasSnapshotButNoRun, setHasSnapshotButNoRun] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const loadAnalysis = async () => {
    setLoading(true)
    setError(null)
    setHasSnapshotButNoRun(false)
    try {
      // 1. Check legacy/direct analysis status first to determine if we have insufficient data
      const legacyData = await getFinancialHealthAnalysis()
      if (legacyData && legacyData.status === 'insufficient_data') {
        setAnalysis(legacyData)
        return
      }

      // 2. We have a workspace and active snapshot! Now check for latest run
      const workspaceId = localStorage.getItem('active_workspace_id')
      if (workspaceId) {
        const latestRun = await fetchLatestRunSafe(workspaceId, 'financial_health')
        if (latestRun) {
          const analysisData = {
            ...latestRun.results,
            run_metadata: {
              id: latestRun.id,
              runId: latestRun.id,
              snapshotId: latestRun.snapshotId,
              status: latestRun.status,
              runType: latestRun.runType,
              createdAt: latestRun.createdAt,
              logicVersion: latestRun.logicVersion,
              warningsCount: latestRun.warnings?.length ?? 0
            }
          }
          setAnalysis(analysisData)
        } else {
          // Snapshot exists, but no run yet
          setHasSnapshotButNoRun(true)
          setAnalysis(legacyData) // store legacyData just in case
        }
      } else {
        // No workspace selected
        setAnalysis({
          status: 'insufficient_data',
          missingRequirements: ['Please select or create a workspace in the Data Room.'],
          nextActions: ['Go to the Data Room']
        })
      }
    } catch (e) {
      console.error('Financial health load failed', e)
      setError('Financial Health is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const handleRunAnalysis = async () => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return
    setIsRunning(true)
    try {
      await triggerAnalysisRun(workspaceId, 'financial_health')
      await loadAnalysis()
    } catch (err: any) {
      console.error('Failed to trigger analysis run:', err)
      alert(`Failed to run analysis: ${err.message || err}`)
    } finally {
      setIsRunning(false)
    }
  }

  useEffect(() => {
    loadAnalysis()
  }, [])

  const isInsufficientData = useMemo(() => {
    return analysis && analysis.status === 'insufficient_data'
  }, [analysis])

  const metrics = useMemo<MetricCard[]>(() => {
    if (!analysis || isInsufficientData) return []
    return [
      { key: 'current', label: 'Current Ratio', metric: analysis.ratios.currentRatio, suffix: 'x', hint: 'Short-term liquidity buffer' },
      { key: 'quick', label: 'Quick Ratio', metric: analysis.ratios.quickRatio, suffix: 'x', hint: 'Liquid asset coverage' },
      { key: 'coverage', label: 'Interest Coverage', metric: analysis.ratios.interestCoverage, suffix: 'x', hint: 'EBIT / interest expense' },
      { key: 'dscr', label: 'DSCR', metric: analysis.ratios.dscr, suffix: 'x', hint: 'Cash available for debt service' },
      { key: 'debt', label: 'Debt Ratio', metric: analysis.ratios.debtRatio, suffix: 'x', hint: 'Debt load vs assets' },
      { key: 'netdebt', label: 'Net Debt / EBITDA', metric: analysis.ratios.netDebtToEbitda, suffix: 'x', hint: 'Leverage capacity' },
      { key: 'dso', label: 'DSO', metric: analysis.ratios.dso, suffix: ' days', hint: 'Collection cycle quality' },
      { key: 'wcgap', label: 'Working Capital Gap', metric: analysis.ratios.workingCapitalGap, hint: 'Estimated funding gap' },
    ]
  }, [analysis, isInsufficientData])

  if (loading) {
    return <PageLoadingSkeleton layout="health" />
  }

  if (isInsufficientData) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Financial Health"
          subtitle="Liquidity, leverage, coverage, receivables, projection, and valuation diagnostics from the active financial snapshot."
        />
        <WorkspaceInsufficientDataState
          missingRequirements={analysis?.missingRequirements}
          nextActions={analysis?.nextActions}
        />
      </div>
    )
  }

  if (hasSnapshotButNoRun) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Financial Health"
          subtitle="Liquidity, leverage, coverage, receivables, projection, and valuation diagnostics from the active financial snapshot."
        />
        <div className="flex flex-col items-center justify-center p-8 sm:p-12 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 flex items-center justify-center text-softform-teal-deep dark:text-softform-aqua-300">
            <TrendingUp size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Financial Health Analysis Needed</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              An active workspace snapshot exists, but no financial health analysis run has been triggered for this snapshot yet. Run the analysis to generate diagnostics.
            </p>
          </div>
          <button
            onClick={handleRunAnalysis}
            disabled={isRunning}
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-sm font-semibold rounded-full shadow-sm disabled:opacity-50 transition-colors"
          >
            {isRunning ? (
              <Loader2 size={16} className="animate-spin text-softform-teal-deep dark:text-softform-aqua-300" />
            ) : (
              <Play size={16} fill="currentColor" className="ml-0.5" />
            )}
            <span>Run Financial Health Analysis</span>
          </button>
        </div>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <ServiceErrorState
        message={error || 'Unable to connect to financial health services.'}
        onRetry={loadAnalysis}
      />
    )
  }

  const summary = analysis.summary
  const snapshot = analysis.snapshot
  const valuation = analysis.valuation
  const projections = analysis.projections
  const projectedYears = projections?.projectedYears ?? []
  const firstProjectedYear = projectedYears[0]
  const lastProjectedYear = projectedYears[projectedYears.length - 1]
  const dcf = valuation?.dcf
  const wacc = valuation?.wacc
  const failedChecks = analysis.integrityChecks.filter((check: IntegrityCheckResult) => !check.passed)
  const passedChecks = analysis.integrityChecks.length - failedChecks.length
  const isPersistent = Boolean(snapshot?.metadata?.persistent || snapshot?.metadata?.source === 'workspace_persistent_snapshot')
  const isPreview = Boolean(snapshot?.metadata?.preview_only || snapshot?.metadata?.previewOnly || snapshot?.metadata?.source === 'data_room_workspace_preview')

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Financial Health"
        subtitle="Liquidity, leverage, coverage, receivables, projection, and valuation diagnostics from the active financial snapshot."
        chip={
          <StatusChip variant={bandVariant(summary?.overallBand)}>
            {isPersistent ? formatBand(summary?.overallBand) : isPreview ? 'Preview analysis' : 'Demo sample'}
          </StatusChip>
        }
      />

      {/* Fallback Badges / Banners */}
      {!isPersistent && (
        <div className="rounded-[24px] border border-white bg-white/70 p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-softform-amber-500/10 text-softform-amber-500 border border-softform-amber-500/20">
              <AlertTriangle size={14} />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-semibold text-softform-navy-950">
                {isPreview ? "Preview Data Fallback" : "Demo Sample Data Fallback"}
              </p>
              <p className="text-xs text-softform-text-secondary leading-relaxed">
                {isPreview 
                  ? "Displaying diagnostics from temporary in-memory parsed statements. Re-compiling or restarting the server will reset this state. Please calibrate a persistent workspace snapshot in the Data Room." 
                  : "Displaying Harbour & Finch mock demo metrics because no persistent active snapshot exists. Go to the Data Room to upload company records and calibrate outcomes."}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        {analysis?.run_metadata && (
          <button
            onClick={handleRunAnalysis}
            disabled={isRunning}
            className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 text-xs font-semibold rounded-full shadow-sm transition-colors disabled:opacity-50"
          >
            {isRunning ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <RefreshCw size={12} />
            )}
            <span>Rerun Analysis</span>
          </button>
        )}
      </div>

      {/* Summary Cockpit Hero Section in Premium Navy Contrast Card */}
      <NavyHeroSection
        eyebrow="Financial Health Diagnostics"
        title={`${snapshot.companyName} · ${snapshot.reportingPeriod}`}
        description={summary?.disclaimer ?? 'This analysis is context-only and assumptions-based. Company records are required for production advisory or credit analysis.'}
        aside={
          <div className="flex flex-wrap items-center justify-around gap-6 bg-white/5 border border-white/10 rounded-[24px] p-6 backdrop-blur-md">
            <div className="flex items-center gap-4">
              <ScoreRing
                score={
                  summary?.overallBand === 'strong' ? 90 :
                  summary?.overallBand === 'adequate' ? 75 :
                  summary?.overallBand === 'watch' ? 48 :
                  summary?.overallBand === 'constrained' ? 35 : 20
                }
                size={80}
                showText={true}
                label="Health Score"
                textColor="text-white"
              />
              <div>
                <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Overall band</p>
                <p className="mt-1 text-lg font-bold text-white leading-tight">{formatBand(summary?.overallBand)}</p>
              </div>
            </div>
            <div className="h-12 w-[1px] bg-white/10 hidden sm:block" />
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span className="text-[10px] font-medium text-white/70">{passedChecks} integrity passes</span>
              </div>
              {failedChecks.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-amber-400" />
                  <span className="text-[10px] font-medium text-white/70">{failedChecks.length} flag warnings</span>
                </div>
              )}
            </div>
          </div>
        }
      />

      {/* Ratio Metric Grid */}
      <motion.section 
        className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
        variants={staggerContainer}
        initial="hidden"
        animate="show"
      >
        {metrics.map((item) => {
          const isCurrency = item.key === 'wcgap'
          const value = isCurrency ? formatHKD(item.metric?.value) : `${formatNumber(item.metric?.value)}${item.metric?.value !== null && item.metric?.value !== undefined ? item.suffix ?? '' : ''}`
          return (
            <motion.div 
              key={item.key} 
              variants={staggerItem}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className={`rounded-[22px] p-5 hover-lift transition-all duration-200 ${
                !item.metric?.warning
                  ? 'softform-metric-card'
                  : 'border border-softform-amber-300/35 bg-softform-cream/45 shadow-sm'
              }`}
            >
              <MetricDisplay
                label={item.label}
                value={value}
                description={item.hint}
                trend={item.metric?.warning ? { value: 'Review Needed', isPositive: false } : undefined}
              />
              {item.metric?.warning && (
                <p className="mt-3 flex gap-2 text-[11px] leading-relaxed text-softform-amber-500 border-t border-softform-amber-300/20 pt-2">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                  <span>{item.metric.warning}</span>
                </p>
              )}
            </motion.div>
          )
        })}
      </motion.section>

      {/* Integrity & Diagnostics Grid */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Integrity Checks"
          icon={<CheckCircle2 size={20} className="text-softform-teal-500" />}
          action={
            <StatusChip variant={failedChecks.length ? 'caution' : 'signal'}>
              {passedChecks}/{analysis.integrityChecks.length} passed
            </StatusChip>
          }
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {analysis.integrityChecks.slice(0, 5).map((check: any) => (
              <div key={check.checkName} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm flex gap-3 items-start justify-between">
                <div className="space-y-1">
                  <p className="font-semibold text-softform-navy-950">{check.checkName}</p>
                  <p className="text-xs leading-relaxed text-softform-text-secondary">{check.message}</p>
                </div>
                <span className={`shrink-0 flex items-center justify-center rounded-full w-5 h-5 text-xs font-semibold ${check.passed ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'}`}>
                  {check.passed ? '✓' : '✗'}
                </span>
              </div>
            ))}
          </div>
        </SectionBlock>

        <SectionBlock
          title="Risk Diagnostics"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={
            <StatusChip variant={bandVariant(analysis.riskDiagnostics?.altmanZScore?.band)}>
              {formatBand(analysis.riskDiagnostics?.altmanZScore?.band)}
            </StatusChip>
          }
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Altman Z''</p>
              <p className="mt-1 text-2xl font-bold text-softform-navy-950 tabular-finance">{formatNumber(analysis.riskDiagnostics?.altmanZScore?.value)}</p>
              <p className="mt-1 text-xs text-softform-text-secondary">{analysis.riskDiagnostics?.altmanZScore?.methodologyLabel}</p>
            </div>
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Receivables Risk</p>
              <p className="mt-1 text-2xl font-bold text-softform-navy-950">{formatBand(analysis.riskDiagnostics?.receivablesRisk?.zone)}</p>
              <p className="mt-1 text-xs text-softform-text-secondary">
                ECL ratio {formatNumber(analysis.riskDiagnostics?.receivablesRisk?.eclRatio, 4)}
              </p>
            </div>
          </div>
          {summary?.watchItems && summary.watchItems.length > 0 && (
            <div className="space-y-2 border-t border-softform-navy-950/5 pt-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-softform-text-muted">Watch items</p>
              {summary.watchItems.slice(0, 4).map((item: any, idx: number) => (
                <p key={idx} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs leading-relaxed text-softform-text-secondary">
                  {item}
                </p>
              ))}
            </div>
          )}
        </SectionBlock>
      </section>

      {/* Projections & Valuation Grid */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Projections Summary"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Forecast</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Year 1 FCFF</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatHKD(firstProjectedYear?.fcffPrimary)}</p>
            </div>
            <div className="rounded-xl border border-white/60 bg-white/45 px-4 py-3">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Terminal-year FCFF</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatHKD(lastProjectedYear?.fcffPrimary)}</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Forecast is driver-based and assumptions-only. Review revenue growth, EBIT margin, tax, CapEx, and NWC assumptions before using it for advisory decisions.
          </p>
        </SectionBlock>

        <SectionBlock
          title="Valuation Reference"
          icon={<Coins size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">DCF / WACC</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl bg-white/45 px-3.5 py-3 text-center border border-white/60">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Enterprise Value</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{formatHKD(dcf?.enterpriseValue)}</p>
            </div>
            <div className="rounded-xl bg-white/45 px-3.5 py-3 text-center border border-white/60">
              <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">WACC</p>
              <p className="mt-1 text-xl font-bold text-softform-navy-950 tabular-finance">{wacc?.wacc != null ? `${(wacc.wacc * 100).toFixed(2)}%` : 'N/A'}</p>
            </div>
          </div>
          <p className="text-xs leading-relaxed text-softform-text-secondary">
            Valuation is used as a context signal for funding capacity and business value narrative. It is not a formal appraisal.
          </p>
        </SectionBlock>
      </section>

      {/* Key Signals */}
      {summary?.keySignals && summary.keySignals.length > 0 && (
        <SectionBlock
          title="Key Financial Signals"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">Summary</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {summary.keySignals.slice(0, 6).map((signal: FinancialSignal) => (
              <div key={signal.key} className="rounded-[20px] border border-white/60 bg-white/45 p-4 shadow-sm hover-lift flex flex-col justify-between min-h-[140px]">
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{signal.label}</h3>
                    <span className="rounded bg-softform-mist-100 px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider text-softform-teal-deep">
                      {formatBand(signal.band)}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-softform-text-secondary">{signal.message}</p>
                </div>
                <p className="mt-3 border-t border-softform-navy-950/5 pt-2 text-[10px] leading-relaxed text-softform-text-muted">
                  {signal.evidence}
                </p>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* Footer Navigation */}
      <WorkflowFooter
        title="Continue to credit readiness"
        description="Use the Credit Readiness module to convert these financial signals into an explainable funding-readiness scorecard."
        linkTo="/platform/credit-readiness"
        linkLabel="Open Credit Readiness"
      />
    </div>
  )
}
