/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useMemo } from 'react'
import { Calculator, TrendingUp, BarChart3, Loader2, RefreshCw, Play, AlertTriangle } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import ServiceErrorState from '../../components/platform/ServiceErrorState'
import NavyHeroSection from '../../components/platform/NavyHeroSection'
import PageLoadingSkeleton from '../../components/platform/PageLoadingSkeleton'
import WorkflowFooter from '../../components/platform/WorkflowFooter'
import { getFinancialHealthAnalysis } from '../financial-health/financialHealthApi'
import type { ValuationOutput } from '../market-watch/types'
import { formatHKD, formatPercent, formatMultiple, bandVariant } from '../../lib/formatters'
import RunMetadataBadge from '../../components/platform/RunMetadataBadge'
import { fetchLatestRunSafe, triggerAnalysisRun } from '../../lib/workspaceRunHelpers'

import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'

function assumptionNumber(valuation: ValuationOutput, key: string) {
  const value = valuation.assumptions?.[key]
  return typeof value === 'number' ? value : null
}

export default function ValuationPage() {
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasSnapshotButNoRun, setHasSnapshotButNoRun] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const loadValuation = async () => {
    setLoading(true)
    setError(null)
    setHasSnapshotButNoRun(false)
    try {
      // 1. Check legacy/direct analysis status first
      const legacyData = await getFinancialHealthAnalysis()
      if (legacyData && legacyData.status === 'insufficient_data') {
        setAnalysis(legacyData)
        return
      }

      // 2. Check for latest valuation run
      const workspaceId = localStorage.getItem('active_workspace_id')
      if (workspaceId) {
        const latestRun = await fetchLatestRunSafe(workspaceId, 'valuation')
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
          setAnalysis(legacyData)
        }
      } else {
        setAnalysis({
          status: 'insufficient_data',
          missingRequirements: ['Please select or create a workspace in the Data Room.'],
          nextActions: ['Go to the Data Room']
        })
      }
    } catch (e) {
      console.error('Valuation load failed', e)
      setError('Valuation is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const handleRunAnalysis = async () => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return
    setIsRunning(true)
    try {
      await triggerAnalysisRun(workspaceId, 'valuation')
      await loadValuation()
    } catch (err: any) {
      console.error('Failed to trigger valuation run:', err)
      alert(`Failed to run valuation: ${err.message || err}`)
    } finally {
      setIsRunning(false)
    }
  }

  useEffect(() => {
    loadValuation()
  }, [])

  const isInsufficientData = useMemo(() => {
    return analysis && analysis.status === 'insufficient_data'
  }, [analysis])

  if (loading) {
    return <PageLoadingSkeleton layout="valuation" metricCount={4} sectionCount={2} />
  }

  if (isInsufficientData) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Valuation"
          subtitle="Indicative WACC and DCF valuation view built from the active financial analysis snapshot."
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
          title="Valuation"
          subtitle="Indicative WACC and DCF valuation view built from the active financial analysis snapshot."
        />
        <div className="flex flex-col items-center justify-center p-8 sm:p-12 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 flex items-center justify-center text-softform-teal-deep dark:text-softform-aqua-300">
            <Calculator size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Valuation Analysis Needed</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              An active workspace snapshot exists, but no valuation analysis run has been triggered for this snapshot yet. Run the analysis to generate models.
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
            <span>Run Valuation Analysis</span>
          </button>
        </div>
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <ServiceErrorState
        message={error || 'Unable to connect to valuation services.'}
        onRetry={loadValuation}
      />
    )
  }

  const valuation = analysis.valuation ?? {}
  const snapshot = analysis.snapshot
  const dcf = valuation.dcf
  const wacc = valuation.wacc
  const valuationYears = dcf?.valuationYears ?? []
  const sensitivity = valuation.sensitivity ?? []
  const sanityChecks = valuation.sanityChecks ?? []
  const modelWarnings = Array.from(
    new Set([
      ...(valuation.warnings ?? []),
      ...(dcf?.warnings ?? []),
      ...(wacc?.warnings ?? []),
    ])
  )
  const isPersistent = Boolean(snapshot?.metadata?.persistent || snapshot?.metadata?.source === 'workspace_persistent_snapshot')
  const isPreview = Boolean(snapshot?.metadata?.preview_only || snapshot?.metadata?.previewOnly || snapshot?.metadata?.source === 'data_room_workspace_preview')

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Valuation"
        subtitle="Indicative WACC and DCF valuation view built from the active financial analysis snapshot."
        chip={
          <StatusChip variant="neutral">
            {isPersistent ? 'Context valuation' : isPreview ? 'Preview valuation' : 'Demo sample'}
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
                  ? "Displaying valuation models from temporary in-memory parsed statements. Re-compiling or restarting the server will reset this state. Please calibrate a persistent workspace snapshot in the Data Room." 
                  : "Displaying Harbour & Finch mock demo valuation models because no persistent active snapshot exists. Go to the Data Room to upload company records and calibrate outcomes."}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <RunMetadataBadge metadata={analysis?.run_metadata} />
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

      {/* Business Valuation Hero Section in Premium Navy Contrast Card */}
      <NavyHeroSection
        eyebrow="Business valuation engine"
        title={`${snapshot.companyName} · ${snapshot.reportingPeriod}`}
        description="This DCF view is assumptions-based and intended to support the CFO narrative, funding readiness, and advisory preparation. It is not a formal appraisal or investment recommendation."
        aside={
          <div className="flex flex-wrap items-center justify-around gap-6 bg-white/5 border border-white/10 rounded-[24px] p-6 backdrop-blur-md">
            <div className="space-y-2.5 w-full">
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Enterprise value</span>
                <span className="text-sm font-bold text-white tabular-finance">{formatHKD(dcf?.enterpriseValue)}</span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-1">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">Equity value</span>
                <span className="text-sm font-bold text-white tabular-finance">{formatHKD(dcf?.equityValue)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-white/50">WACC</span>
                <span className="text-sm font-bold text-white tabular-finance">{formatPercent(wacc?.wacc)}</span>
              </div>
            </div>
          </div>
        }
      />


      {/* KPI metric grid */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="PV explicit FCFF"
            value={formatHKD(dcf?.pvExplicitFcff)}
            description="Discounted operating cash flows"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="PV terminal value"
            value={formatHKD(dcf?.pvTerminalValue)}
            description="Long-term value component"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Net debt bridge"
            value={formatHKD(dcf?.netDebt)}
            description="Total debt less cash"
          />
        </div>
        <div className="softform-metric-card rounded-[22px] p-5 hover-lift">
          <MetricDisplay
            label="Implied EV / EBITDA"
            value={formatMultiple(dcf?.impliedEvEbitda)}
            description="Sanity-check multiple"
          />
        </div>
      </section>

      {/* WACC and DCF Bridge */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="WACC Build-Up"
          icon={<Calculator size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">CAPM-style</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              ['Cost of equity', formatPercent(wacc?.costOfEquity)],
              ['After-tax debt cost', formatPercent(wacc?.afterTaxCostOfDebt)],
              ['Debt weight', formatPercent(wacc?.debtWeight)],
              ['Equity weight', formatPercent(wacc?.equityWeight)],
              ['Risk-free rate', formatPercent(assumptionNumber(valuation, 'riskFreeRate'))],
              ['Terminal growth', formatPercent(assumptionNumber(valuation, 'terminalGrowthRate'))],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 flex justify-between items-center text-xs">
                <span className="font-semibold text-softform-text-secondary">{label}</span>
                <span className="font-bold text-softform-navy-950 tabular-finance">{value}</span>
              </div>
            ))}
          </div>
        </SectionBlock>

        <SectionBlock
          title="DCF Bridge"
          icon={<TrendingUp size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">EV to Equity</StatusChip>}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-5"
        >
          <div className="space-y-3">
            {[
              ['Enterprise value', formatHKD(dcf?.enterpriseValue)],
              ['Less net debt', formatHKD(dcf?.netDebt)],
              ['Equity value', formatHKD(dcf?.equityValue)],
              ['Terminal value share', formatPercent(dcf?.terminalValueShareOfEnterpriseValue)],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm">
                <span className="font-semibold text-softform-text-secondary">{label}</span>
                <span className="font-bold text-softform-navy-950 tabular-finance">{value}</span>
              </div>
            ))}
          </div>
        </SectionBlock>
      </section>

      {/* Valuation Years */}
      {valuationYears.length > 0 && (
        <SectionBlock
          title="Valuation Years"
          icon={<BarChart3 size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="neutral">FCFF PV</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {valuationYears.slice(0, 5).map((year: any) => (
              <div key={year.year} className="rounded-[20px] border border-white/60 bg-white/45 p-4 shadow-sm hover-lift flex flex-col justify-between min-h-[120px]">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">Year {year.year}</p>
                  <p className="mt-2 text-sm font-semibold text-softform-navy-950">FCFF {formatHKD(year.fcff)}</p>
                  <p className="mt-1 text-xs text-softform-text-secondary">PV {formatHKD(year.pvFcff)}</p>
                </div>
                <p className="mt-2 border-t border-softform-navy-950/5 pt-1.5 text-[10px] text-softform-text-muted">
                  Discount {year.discountFactor.toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        </SectionBlock>
      )}

      {/* Sensitivity & Sanity Checks */}
      <section className="grid gap-6 lg:grid-cols-2">
        {sensitivity.length > 0 && (
          <SectionBlock
            title="Sensitivity Points"
            action={<StatusChip variant="neutral">WACC / Growth</StatusChip>}
            containerType="card"
            className="rounded-[28px] p-6 sm:p-8 space-y-5"
          >
            <div className="space-y-3">
              {sensitivity.slice(0, 5).map((point: any, idx: number) => (
                <div key={`${point.wacc}-${point.terminalGrowthRate}-${idx}`} className="grid grid-cols-3 gap-2 rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs items-center">
                  <span className="font-semibold text-softform-text-secondary">{formatPercent(point.wacc)}</span>
                  <span className="font-semibold text-softform-text-secondary text-center">g {formatPercent(point.terminalGrowthRate)}</span>
                  <span className="text-right font-bold text-softform-navy-950 tabular-finance">{formatHKD(point.enterpriseValue)}</span>
                </div>
              ))}
            </div>
          </SectionBlock>
        )}

        {sanityChecks.length > 0 && (
          <SectionBlock
            title="Valuation Sanity Checks"
            action={<StatusChip variant="neutral">Review</StatusChip>}
            containerType="card"
            className="rounded-[28px] p-6 sm:p-8 space-y-5"
          >
            <div className="space-y-3">
              {sanityChecks.slice(0, 5).map((check: any) => (
                <div key={check.name} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-sm flex gap-3 items-start justify-between">
                  <div className="space-y-1">
                    <p className="font-semibold text-softform-navy-950">{check.name}</p>
                    <p className="text-xs leading-relaxed text-softform-text-secondary">{check.message}</p>
                  </div>
                  <StatusChip variant={bandVariant(check.status)} className="text-[9px] px-2 py-0.5 shrink-0">
                    {check.status}
                  </StatusChip>
                </div>
              ))}
            </div>
          </SectionBlock>
        )}
      </section>

      {/* Model Warnings */}
      {modelWarnings.length > 0 && (
        <section className="rounded-[24px] border border-softform-amber-300/25 bg-softform-cream/35 p-5 shadow-soft-inner">
          <div className="flex items-start gap-3">
            <div className="space-y-2">
              <p className="text-sm font-semibold text-softform-navy-950">Model Warnings</p>
              {modelWarnings.slice(0, 5).map((warning: any, idx: number) => (
                <p key={idx} className="text-xs leading-relaxed text-softform-text-secondary">{warning}</p>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Bottom Navigation */}
      <WorkflowFooter
        title="Use valuation in the funding narrative"
        description="Continue to Funding Strategy to compare channel fit and facility structures using this valuation context."
        linkTo="/platform/funding-strategy"
        linkLabel="Open Funding Strategy"
      />
    </div>
  )
}
