/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Calculator, TrendingUp, BarChart3, Loader2, RefreshCw, Play, AlertTriangle, FolderOpen, Building2, FileSearch } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import MetricDisplay from '../../components/platform/MetricDisplay'
import ServiceErrorState from '../../components/platform/ServiceErrorState'
import NavyHeroSection from '../../components/platform/NavyHeroSection'
import PageLoadingSkeleton from '../../components/platform/PageLoadingSkeleton'
import WorkflowFooter from '../../components/platform/WorkflowFooter'
import type { ValuationOutput } from '../market-watch/types'
import { formatHKD, formatPercent, formatMultiple, bandVariant } from '../../lib/formatters'
import { fetchLatestRunSafe, triggerAnalysisRun } from '../../lib/workspaceRunHelpers'
import { fetchActiveWorkspaceSnapshot, fetchWorkspaceFiles } from '../data-room/api/dataRoomApi'
import { useWorkspace } from '../../context/workspaceContext'

type ValuationPrerequisite = 'no_workspace' | 'no_files' | 'no_snapshot' | 'no_run'

function assumptionNumber(valuation: ValuationOutput, key: string) {
  const value = valuation.assumptions?.[key]
  return typeof value === 'number' ? value : null
}

function getSnapshotId(snapshot: any): string | undefined {
  return snapshot?.id ?? snapshot?.snapshotId ?? snapshot?.metadata?.snapshotId
}

function ValuationPrerequisiteCard({
  state,
  isRunning,
  onRun,
}: {
  state: ValuationPrerequisite
  isRunning: boolean
  onRun: () => void
}) {
  const content: Record<ValuationPrerequisite, {
    icon: JSX.Element
    eyebrow: string
    title: string
    description: string
    primaryLabel: string
    to?: string
    onClick?: () => void
  }> = {
    no_workspace: {
      icon: <Building2 size={28} />,
      eyebrow: 'Workspace required',
      title: 'Create a company workspace first',
      description: 'Valuation models are generated from an active company workspace. Create or select a workspace before opening the valuation route directly.',
      primaryLabel: 'Create Workspace',
      to: '/platform/overview',
    },
    no_files: {
      icon: <FolderOpen size={28} />,
      eyebrow: 'Financial records required',
      title: 'Upload financial documents before valuation',
      description: 'Add the company financial statements in the Data Room so FinSight CFO can prepare the snapshot used by valuation.',
      primaryLabel: 'Open Data Room',
      to: '/platform/data-room',
    },
    no_snapshot: {
      icon: <FileSearch size={28} />,
      eyebrow: 'Snapshot review required',
      title: 'Review and activate a financial snapshot before valuation',
      description: 'Uploaded files need to be parsed, reviewed, and activated as the financial snapshot before valuation analysis can run.',
      primaryLabel: 'Review Snapshot',
      to: '/platform/data-room',
    },
    no_run: {
      icon: <Calculator size={28} />,
      eyebrow: 'Analysis run required',
      title: 'Run valuation analysis',
      description: 'An active financial snapshot is available, but valuation has not been run for this workspace yet. Run the backend analysis to generate valuation results.',
      primaryLabel: 'Run Valuation',
      onClick: onRun,
    },
  }

  const current = content[state]
  const buttonClass = 'inline-flex items-center justify-center gap-2 rounded-full bg-softform-navy-950 px-6 py-3 text-sm font-semibold text-white shadow-[0_18px_44px_rgba(8,17,31,0.22)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-softform-navy-800 disabled:cursor-not-allowed disabled:opacity-60'

  return (
    <div className="relative overflow-hidden rounded-[32px] border border-white/70 bg-white/70 p-7 shadow-[0_24px_80px_rgba(8,17,31,0.14),inset_0_1px_0_rgba(255,255,255,0.8)] backdrop-blur-xl sm:p-10">
      <div className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-softform-aqua-300/25 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-28 left-8 h-64 w-64 rounded-full bg-softform-amber-300/25 blur-3xl" />
      <div className="relative mx-auto flex max-w-2xl flex-col items-center text-center">
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/70 bg-white/70 text-softform-teal-deep shadow-[0_16px_40px_rgba(8,17,31,0.12)]">
          {current.icon}
        </div>
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-softform-teal-deep">{current.eyebrow}</p>
        <h2 className="mt-3 text-2xl font-bold tracking-tight text-softform-navy-950 sm:text-3xl">{current.title}</h2>
        <p className="mt-3 max-w-xl text-sm leading-6 text-softform-text-secondary">{current.description}</p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          {current.to ? (
            <Link id={`valuation-${state}-primary-cta`} to={current.to} className={buttonClass}>
              {current.primaryLabel}
            </Link>
          ) : (
            <button id="valuation-run-primary-cta" type="button" onClick={current.onClick} disabled={isRunning} className={buttonClass}>
              {isRunning ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} fill="currentColor" />}
              {current.primaryLabel}
            </button>
          )}
          {state === 'no_workspace' && (
            <Link id="valuation-workspaces-secondary-cta" to="/platform/overview" className="inline-flex items-center justify-center rounded-full border border-white/70 bg-white/60 px-6 py-3 text-sm font-semibold text-softform-navy-950 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-white/80">
              Workspaces
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ValuationPage() {
  const { activeWorkspace, isLoading: workspaceLoading } = useWorkspace()
  const [analysis, setAnalysis] = useState<any>(null)
  const [activeSnapshot, setActiveSnapshot] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [prerequisite, setPrerequisite] = useState<ValuationPrerequisite | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  const loadValuation = useCallback(async () => {
    if (workspaceLoading) return

    setLoading(true)
    setError(null)
    setPrerequisite(null)
    setAnalysis(null)
    setActiveSnapshot(null)

    const workspaceId = activeWorkspace?.id ?? localStorage.getItem('active_workspace_id')

    if (!workspaceId) {
      setPrerequisite('no_workspace')
      setLoading(false)
      return
    }

    try {
      const files = await fetchWorkspaceFiles(workspaceId)
      if (!Array.isArray(files) || files.length === 0) {
        setPrerequisite('no_files')
        return
      }

      let snapshotResponse
      try {
        snapshotResponse = await fetchActiveWorkspaceSnapshot(workspaceId)
      } catch (snapshotError: any) {
        if (snapshotError?.message?.includes('404') || snapshotError?.message?.toLowerCase?.().includes('not found')) {
          setPrerequisite('no_snapshot')
          return
        }
        throw snapshotError
      }

      if (!snapshotResponse?.snapshot || snapshotResponse.status === 'insufficient_data') {
        setPrerequisite('no_snapshot')
        return
      }

      setActiveSnapshot(snapshotResponse.snapshot)

      const latestRun = await fetchLatestRunSafe(workspaceId, 'valuation')
      if (!latestRun || !latestRun.results) {
        setPrerequisite('no_run')
        return
      }

      setAnalysis({
        ...latestRun.results,
        run_metadata: {
          id: latestRun.id,
          runId: latestRun.id,
          snapshotId: latestRun.snapshotId,
          status: latestRun.status,
          runType: latestRun.runType,
          createdAt: latestRun.createdAt,
          logicVersion: latestRun.logicVersion,
          warningsCount: latestRun.warnings?.length ?? 0,
        },
      })
    } catch (e) {
      console.error('Valuation load failed', e)
      setError('Valuation is currently unavailable. Please check the backend connection and retry.')
    } finally {
      setLoading(false)
    }
  }, [activeWorkspace?.id, workspaceLoading])

  const handleRunAnalysis = async () => {
    const workspaceId = activeWorkspace?.id ?? localStorage.getItem('active_workspace_id')
    if (!workspaceId) {
      setPrerequisite('no_workspace')
      return
    }
    setIsRunning(true)
    setError(null)
    try {
      await triggerAnalysisRun(workspaceId, 'valuation', getSnapshotId(activeSnapshot))
      await loadValuation()
    } catch (err: any) {
      console.error('Failed to trigger valuation run:', err)
      setError(`Failed to run valuation: ${err.message || err}`)
      setPrerequisite(null)
    } finally {
      setIsRunning(false)
    }
  }

  useEffect(() => {
    loadValuation()
  }, [loadValuation])

  if (loading || workspaceLoading) {
    return <PageLoadingSkeleton layout="valuation" metricCount={4} sectionCount={2} />
  }

  if (error) {
    return (
      <ServiceErrorState
        message={error}
        onRetry={loadValuation}
      />
    )
  }

  if (prerequisite) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Valuation"
          subtitle="Indicative WACC and DCF valuation view built from the active financial analysis snapshot."
        />
        <ValuationPrerequisiteCard state={prerequisite} isRunning={isRunning} onRun={handleRunAnalysis} />
      </div>
    )
  }

  if (!analysis) {
    return (
      <ServiceErrorState
        message="Unable to load valuation data. Please retry or run valuation after activating a workspace snapshot."
        onRetry={loadValuation}
      />
    )
  }

  const valuation = analysis.valuation ?? analysis ?? {}
  const snapshot = activeSnapshot ?? analysis.snapshot ?? {}
  const dcf = valuation.dcf
  const wacc = valuation.wacc
  const valuationYears = dcf?.valuationYears ?? []
  const sensitivity = valuation.sensitivity ?? []
  const sanityChecks = valuation.sanityChecks ?? []

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
        title={`${snapshot.companyName ?? activeWorkspace?.companyName ?? 'Workspace Company'} · ${snapshot.reportingPeriod ?? 'FY2025'}`}
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
