/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState, useMemo } from 'react'
import { ShieldCheck, TrendingUp, AlertTriangle, Loader2, RefreshCw, Play } from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SectionBlock from '../../components/platform/SectionBlock'
import ScoreRing from '../../components/platform/ScoreRing'
import ServiceErrorState from '../../components/platform/ServiceErrorState'
import NavyHeroSection from '../../components/platform/NavyHeroSection'
import PageLoadingSkeleton from '../../components/platform/PageLoadingSkeleton'
import WorkflowFooter from '../../components/platform/WorkflowFooter'
import { getCreditScore } from '../advisory-blueprint/api/advisoryBlueprintApi'
import { createAndFetchMockCdiData } from '../cdi/cdiApi'
import type { CreditScoreFactor, FundingReadinessBand, PdRiskTier } from '../advisory-blueprint/types'
import type { CdiConsentSession, CdiMockDataResponse } from '../cdi/cdiApi'
import { formatHKD, formatPercent, formatBand } from '../../lib/formatters'
import { fetchLatestRunSafe, triggerAnalysisRun } from '../../lib/workspaceRunHelpers'

import WorkspaceInsufficientDataState from '../../components/platform/WorkspaceInsufficientDataState'

const readinessLabels: Record<FundingReadinessBand, string> = {
  ready_context: 'Ready context',
  bank_review_ready: 'Bank review ready',
  needs_review: 'Needs review',
  not_ready: 'Not ready',
  unavailable: 'Unavailable',
}

const tierLabels: Record<PdRiskTier, string> = {
  low: 'Low risk',
  moderate: 'Moderate risk',
  elevated: 'Elevated risk',
  high: 'High risk',
  unavailable: 'Unavailable',
}

function chipVariantForTier(tier: PdRiskTier): 'signal' | 'caution' | 'neutral' {
  if (tier === 'low' || tier === 'moderate') return 'signal'
  if (tier === 'elevated' || tier === 'high') return 'caution'
  return 'neutral'
}

function factorTone(factor: CreditScoreFactor) {
  if (factor.rawScore >= 75) return 'text-emerald-700 bg-emerald-500/10'
  if (factor.rawScore >= 55) return 'text-softform-amber-500 bg-softform-cream'
  return 'text-red-700 bg-red-500/10'
}

export default function CreditReadinessPage() {
  const [creditScore, setCreditScore] = useState<any>(null)
  const [cdiConsent, setCdiConsent] = useState<CdiConsentSession | null>(null)
  const [cdiData, setCdiData] = useState<CdiMockDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasSnapshotButNoRun, setHasSnapshotButNoRun] = useState(false)
  const [isRunning, setIsRunning] = useState(false)

  const loadCreditScore = async () => {
    setLoading(true)
    setError(null)
    setHasSnapshotButNoRun(false)
    try {
      // 1. Check legacy/direct analysis status first
      const legacyData = await getCreditScore()
      if (legacyData && (legacyData as any).status === 'insufficient_data') {
        setCreditScore(legacyData)
        return
      }

      // 2. Check for latest credit score run
      const workspaceId = localStorage.getItem('active_workspace_id')
      if (workspaceId) {
        const latestRun = await fetchLatestRunSafe(workspaceId, 'credit_score')
        if (latestRun) {
          const scoreData = {
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
          
          const cdiContext = await createAndFetchMockCdiData({
            companyId: scoreData.companyId,
            companyName: scoreData.companyName,
          }).catch((e) => {
            console.warn('Mock CDI overlay unavailable for credit readiness', e)
            return null
          })
          setCdiConsent(cdiContext?.consent ?? null)
          setCdiData(cdiContext?.data ?? null)
          setCreditScore(scoreData)
        } else {
          // Snapshot exists, but no run yet
          setHasSnapshotButNoRun(true)
          setCreditScore(legacyData)
        }
      } else {
        setCreditScore({
          status: 'insufficient_data',
          missingRequirements: ['Please select or create a workspace in the Data Room.'],
          nextActions: ['Go to the Data Room']
        })
      }
    } catch (e) {
      console.error('Credit score load failed', e)
      setError('Credit readiness scorecard is currently unavailable. Please check the backend connection.')
    } finally {
      setLoading(false)
    }
  }

  const handleRunAnalysis = async () => {
    const workspaceId = localStorage.getItem('active_workspace_id')
    if (!workspaceId) return
    setIsRunning(true)
    try {
      await triggerAnalysisRun(workspaceId, 'credit_score')
      await loadCreditScore()
    } catch (err: any) {
      console.error('Failed to trigger credit score run:', err)
      alert(`Failed to run credit score: ${err.message || err}`)
    } finally {
      setIsRunning(false)
    }
  }

  useEffect(() => {
    loadCreditScore()
  }, [])

  const isInsufficientData = useMemo(() => {
    return creditScore && creditScore.status === 'insufficient_data'
  }, [creditScore])

  if (loading) {
    return <PageLoadingSkeleton layout="credit" />
  }

  if (isInsufficientData) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Credit Readiness"
          subtitle="Explainable SME PD proxy scorecard built from liquidity, leverage, coverage, receivables, FCFF, stress, and consent-based CDI signals."
        />
        <WorkspaceInsufficientDataState
          missingRequirements={creditScore?.missingRequirements}
          nextActions={creditScore?.nextActions}
        />
      </div>
    )
  }

  if (hasSnapshotButNoRun) {
    return (
      <div className="space-y-8 pb-12">
        <PageHeader
          title="Credit Readiness"
          subtitle="Explainable SME PD proxy scorecard built from liquidity, leverage, coverage, receivables, FCFF, stress, and consent-based CDI signals."
        />
        <div className="flex flex-col items-center justify-center p-8 sm:p-12 bg-white/40 dark:bg-slate-900/40 border border-white/60 dark:border-slate-800/60 rounded-3xl backdrop-blur-md shadow-sm max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-softform-teal-deep/10 dark:bg-softform-aqua-300/10 flex items-center justify-center text-softform-teal-deep dark:text-softform-aqua-300">
            <ShieldCheck size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Credit Readiness Analysis Needed</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              An active workspace snapshot exists, but no credit readiness analysis run has been triggered for this snapshot yet. Run the analysis to generate scorecard.
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
            <span>Run Credit Readiness Analysis</span>
          </button>
        </div>
      </div>
    )
  }

  if (error || !creditScore) {
    return (
      <ServiceErrorState
        message={error || 'Unable to connect to credit readiness services.'}
        onRetry={loadCreditScore}
      />
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <PageHeader
        title="Credit Readiness"
        subtitle="Explainable SME PD proxy scorecard built from liquidity, leverage, coverage, receivables, FCFF, stress, and consent-based CDI signals."
        chip={
          <StatusChip variant={chipVariantForTier(creditScore.riskTier as PdRiskTier)}>
            {tierLabels[creditScore.riskTier as PdRiskTier]}
          </StatusChip>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        {creditScore?.run_metadata && (
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

      {/* Hero Score Card in Premium Navy Contrast Card */}
      <NavyHeroSection
        eyebrow="Finance-first PD proxy"
        title={creditScore.companyName}
        description={`${creditScore.methodologyLabel}. This page is context-only and designed to explain the drivers behind lender-readiness, not to issue a formal credit decision.`}
        layoutClassName="relative flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between"
        badges={
          <div className="flex flex-wrap gap-2 pt-1">
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
              {readinessLabels[creditScore.fundingReadiness as FundingReadinessBand]}
            </span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
              {creditScore.pdProxyBand}
            </span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
              CDI {formatBand(cdiConsent?.status ?? 'not requested')}
            </span>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-white/80">
              PD Model: {(creditScore.calibrationStatus || creditScore.calibration_status) === 'calibrated' ? 'STATISTICALLY CALIBRATED' : 'INDICATIVE INDEX'}
            </span>
          </div>
        }
        aside={
          <div className="flex flex-col items-center justify-center rounded-[28px] bg-white/5 border border-white/10 p-6 backdrop-blur-md min-w-[200px] shrink-0">
            <ScoreRing
              score={creditScore.compositeScore}
              size={96}
              showText={true}
              label={creditScore.scoreScale}
              textColor="text-white"
            />
            <span className="mt-3 rounded-full bg-white text-softform-navy-950 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.15em]">
              {tierLabels[creditScore.riskTier as PdRiskTier]}
            </span>
          </div>
        }
      />


      {/* Positive and Risk Drivers */}
      <section className="grid gap-6 lg:grid-cols-2">
        <SectionBlock
          title="Positive Drivers"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-4"
        >
          {creditScore.positiveDrivers.length > 0 ? (
            <ul className="space-y-3">
              {creditScore.positiveDrivers.slice(0, 5).map((driver: any, idx: number) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-softform-text-secondary">
                  <span className="mt-1 h-2 w-2 rounded-full bg-softform-teal-deep shrink-0" />
                  <span>{driver}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-softform-text-secondary">No strong positive drivers detected yet.</p>
          )}
        </SectionBlock>

        <SectionBlock
          title="Risk Drivers"
          icon={<AlertTriangle size={20} className="text-softform-amber-500" />}
          containerType="card"
          className="rounded-[28px] p-6 sm:p-8 space-y-4"
        >
          {creditScore.riskDrivers.length > 0 ? (
            <ul className="space-y-3">
              {creditScore.riskDrivers.slice(0, 5).map((driver: any, idx: number) => (
                <li key={idx} className="flex items-start gap-2.5 text-sm text-softform-text-secondary">
                  <span className="mt-1 h-2 w-2 rounded-full bg-softform-amber-500 shrink-0" />
                  <span>{driver}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-softform-text-secondary">No major risk drivers detected under current assumptions.</p>
          )}
        </SectionBlock>
      </section>

      {/* CDI Overlay Section */}
      {cdiData && (
        <SectionBlock
          title="Consent-Based CDI Overlay"
          icon={<ShieldCheck size={20} className="text-softform-teal-500" />}
          action={<StatusChip variant="signal">{formatBand(cdiData.creditBureauSignal.bureauBand)}</StatusChip>}
          containerType="card"
          className="rounded-[32px] p-6 sm:p-8 space-y-6"
        >
          <div className="grid gap-4 lg:grid-cols-4">
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Net cash-flow trend</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950">{formatBand(cdiData.cashflowSignal.netCashflowTrend)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Eligible invoices</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatHKD(cdiData.receivablesSignal.eligibleInvoiceValue)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Buyer concentration</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{formatPercent(cdiData.receivablesSignal.topBuyerConcentration)}</p>
            </div>
            <div className="rounded-[18px] border border-white/60 bg-white/45 p-4">
              <p className="text-[9px] font-medium uppercase tracking-[0.14em] text-softform-text-muted">Delinquencies 12m</p>
              <p className="mt-1 text-lg font-bold text-softform-navy-950 tabular-finance">{cdiData.creditBureauSignal.repaymentDelinquencyCount12m}</p>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-2 pt-2">
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-teal-deep">CDI supports</p>
              {cdiData.fundingImplications.slice(0, 3).map((item) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Signal:</strong> {item}
                </p>
              ))}
            </div>
            <div className="rounded-[22px] border border-white/60 bg-white/45 p-5 space-y-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-softform-amber-500">CDI watch items</p>
              {cdiData.riskImplications.slice(0, 3).map((item: any) => (
                <p key={item} className="text-xs leading-relaxed text-softform-text-secondary">
                  <strong className="text-softform-navy-950 font-semibold">Watch:</strong> {item}
                </p>
              ))}
            </div>
          </div>
        </SectionBlock>
      )}

      {/* Score Factor Breakdown */}
      <SectionBlock
        title="Score Factor Breakdown"
        icon={<TrendingUp size={20} className="text-softform-teal-500" />}
        action={<StatusChip variant="neutral">Explainable Scorecard</StatusChip>}
        containerType="card"
        className="rounded-[32px] p-6 sm:p-8 space-y-6"
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {creditScore.factors.map((factor: any) => {
            const rawScore = factor.rawScore
            const barColor = rawScore >= 75 ? 'bg-emerald-500' : rawScore >= 55 ? 'bg-amber-500' : 'bg-red-500'
            return (
              <div key={factor.key} className="rounded-[22px] bg-white/45 border border-white/60 p-5 shadow-sm hover-lift space-y-4 flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-softform-navy-950 leading-snug">{factor.label}</h3>
                    <span className={`shrink-0 rounded px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider ${factorTone(factor)}`}>
                      {formatBand(factor.band)}
                    </span>
                  </div>

                  {/* Score progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-medium text-softform-text-secondary">
                      <span>Score</span>
                      <span className="font-semibold">{rawScore} / 100</span>
                    </div>
                    <div className="w-full h-2 bg-softform-text-muted/15 rounded-full overflow-hidden">
                      <div className={`h-full ${barColor}`} style={{ width: `${rawScore}%` }} />
                    </div>
                  </div>

                  <div className="space-y-1.5 text-xs text-softform-text-secondary border-t border-softform-navy-950/5 pt-3">
                    <div className="flex justify-between">
                      <span className="font-medium text-softform-navy-950/80">Weight</span>
                      <span className="tabular-finance font-semibold text-softform-navy-950">{Math.round(factor.weight * 100)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-softform-navy-950/80">Weighted Score</span>
                      <span className="tabular-finance font-semibold text-softform-navy-950">{factor.weightedScore.toFixed(2)}</span>
                    </div>
                  </div>
                  <p className="text-xs leading-relaxed text-softform-text-secondary">{factor.message}</p>
                </div>
                <p className="text-[10px] leading-relaxed text-softform-text-muted border-t border-softform-navy-950/5 pt-3 mt-2">
                  <strong className="font-semibold text-softform-navy-950">Evidence:</strong> {factor.evidence}
                </p>
              </div>
            )
          })}
        </div>
      </SectionBlock>

      {/* Constraints & Next Data */}
      {(creditScore.hardConstraints.length > 0 || creditScore.nextDataNeeded.length > 0) && (
        <section className="grid gap-6 lg:grid-cols-2">
          {creditScore.hardConstraints.length > 0 && (
            <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-4 border border-softform-amber-300/20">
              <h2 className="text-lg font-semibold text-softform-navy-950 flex items-center gap-2">
                <AlertTriangle size={18} className="text-softform-amber-500" />
                Hard Constraints
              </h2>
              <ul className="space-y-3">
                {creditScore.hardConstraints.map((item: any, idx: number) => (
                  <li key={idx} className="flex items-start gap-2.5 text-sm text-softform-text-secondary">
                    <AlertTriangle size={14} className="mt-0.5 text-softform-amber-500 shrink-0" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="softform-card rounded-[28px] p-6 sm:p-8 space-y-4">
            <h2 className="text-lg font-semibold text-softform-navy-950 flex items-center gap-2">
              <ShieldCheck size={18} className="text-softform-teal-500" />
              Next Data Needed
            </h2>
            <div className="grid gap-2">
              {creditScore.nextDataNeeded.slice(0, 6).map((item: any, idx: number) => (
                <div key={idx} className="rounded-xl border border-white/60 bg-white/45 px-4 py-3 text-xs font-semibold text-softform-text-secondary shadow-sm">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Continue CTA */}
      <WorkflowFooter
        title="Move from scorecard to advisory action"
        description="Use the Advisory Blueprint to convert this PD proxy context into facility options, stress interpretation, and next actions."
        linkTo="/platform/advisory-blueprint"
        linkLabel="Open Advisory Blueprint"
      />

      <footer className="pt-6 border-t border-softform-navy-950/5 text-center space-y-2">
        <p className="text-xs text-softform-text-muted">{creditScore.disclaimer}</p>
      </footer>
    </div>
  )
}
