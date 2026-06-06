import { useEffect, useState } from 'react'
import {
  BarChart3,
  ShieldCheck,
  AlertTriangle,
  Landmark,
  FolderOpen,
  RotateCw,
  CheckSquare,
} from 'lucide-react'
import PageHeader from '../../components/platform/PageHeader'
import StatusChip from '../../components/platform/StatusChip'
import SourceInfoTooltip from '../market-watch/components/SourceInfoTooltip'
import {
  getAdvisoryBlueprint,
  getAdvisoryRiskScore,
  getAdvisoryStressTests,
  getAdvisoryFacilityStructures,
} from './api/advisoryBlueprintApi'
import {
  AdvisoryBlueprintResponse,
  UnifiedRiskScoreResult,
  StressTestingResponse,
  FacilityStructuringResponse,
} from './types'

export default function AdvisoryBlueprintPage() {
  const [blueprint, setBlueprint] = useState<AdvisoryBlueprintResponse | null>(null)
  const [riskScore, setRiskScore] = useState<UnifiedRiskScoreResult | null>(null)
  const [stressTests, setStressTests] = useState<StressTestingResponse | null>(null)
  const [facilityStructures, setFacilityStructures] = useState<FacilityStructuringResponse | null>(null)

  const [loading, setLoading] = useState<boolean>(true)
  const [loadingStep, setLoadingStep] = useState<string>('Preparing advisory blueprint...')
  const [error, setError] = useState<string | null>(null)

  const loadAllData = async () => {
    setLoading(true)
    setError(null)
    try {
      setLoadingStep('Preparing advisory blueprint...')
      const bp = await getAdvisoryBlueprint()
      setBlueprint(bp)

      setLoadingStep('Loading facility context...')
      const rs = await getAdvisoryRiskScore().catch((e) => {
        console.warn('Risk score load failed', e)
        return null
      })
      setRiskScore(rs)

      setLoadingStep('Checking stress scenarios...')
      const [st, fs] = await Promise.all([
        getAdvisoryStressTests().catch((e) => {
          console.warn('Stress tests load failed', e)
          return null
        }),
        getAdvisoryFacilityStructures().catch((e) => {
          console.warn('Facility structures load failed', e)
          return null
        }),
      ])
      setStressTests(st)
      setFacilityStructures(fs)

      setLoading(false)
    } catch (e) {
      console.error('Failed to load advisory blueprint context', e)
      setError('Advisory blueprint is currently unavailable. Please check the backend connection.')
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAllData()
  }, [])

  // Maps blueprint status to calm, readable labels
  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'constrained_context':
        return 'Constrained context'
      case 'needs_data':
        return 'Needs data'
      case 'ready_for_review':
        return 'Ready for review'
      case 'unavailable':
      default:
        return 'Unavailable'
    }
  }

  // Formatting currency helper
  const formatHKD = (val?: number | null) => {
    if (val === undefined || val === null) return 'N/A'
    if (val >= 1_000_000) {
      return `HKD ${(val / 1_000_000).toFixed(2)}M`
    }
    return `HKD ${val.toLocaleString()}`
  }

  // Source provenance data
  const sourceItems = [
    { label: 'Demo Financial Analysis', mode: 'fixture-backed' as const, asOf: 'FY2025' },
    { label: 'Advisory Precheck Engine', mode: 'workspace-derived' as const },
    { label: 'Unified Risk Scoring Engine', mode: 'workspace-derived' as const },
    { label: 'Stress Testing Engine', mode: 'workspace-derived' as const },
    { label: 'Facility Structuring Engine', mode: 'workspace-derived' as const },
  ]

  if (loading) {
    return (
      <div className="flex min-h-[50dvh] flex-col items-center justify-center space-y-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-softform-mist-100 text-softform-teal-deep animate-spin">
          <RotateCw size={24} />
        </div>
        <p className="text-sm font-medium text-softform-text-secondary animate-pulse">
          {loadingStep}
        </p>
      </div>
    )
  }

  if (error || !blueprint) {
    return (
      <div className="softform-card rounded-[32px] p-8 sm:p-10 text-center">
        <div className="mx-auto flex max-w-md flex-col items-center">
          <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-[20px] bg-red-50 text-red-600">
            <AlertTriangle size={24} />
          </div>
          <p className="mb-2 text-lg font-semibold text-softform-navy-950">
            Service Connection Issue
          </p>
          <p className="mb-6 text-sm text-softform-text-secondary">
            {error || 'Unable to connect to the advisory services.'}
          </p>
          <button
            type="button"
            onClick={loadAllData}
            className="inline-flex items-center gap-2 rounded-xl bg-softform-navy-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-softform-navy-800 transition"
          >
            <RotateCw size={16} />
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  const { keySections, recommendedActions, executiveBrief, blueprintStatus, companyName } = blueprint

  return (
    <div className="space-y-8">
      {/* 1. Page Header */}
      <PageHeader
        title="Advisory Blueprint"
        subtitle="Context-only financing readiness brief based on demo financial analysis."
        titleAddon={
          <SourceInfoTooltip
            title="Advisory Blueprint Provenance"
            sources={sourceItems}
            ariaLabel="Advisory blueprint source information"
          />
        }
        chip={
          <StatusChip variant={blueprintStatus === 'constrained_context' ? 'caution' : 'neutral'}>
            {getStatusLabel(blueprintStatus)}
          </StatusChip>
        }
      />

      <div className="rounded-2xl border border-white/50 bg-white/20 p-4 backdrop-blur-sm">
        <p className="text-xs leading-relaxed text-softform-text-muted">
          <strong>Quiet Disclaimer:</strong> Not a formal credit decision. Company records are required for production use.
        </p>
      </div>

      {/* 2. Executive Brief Panel */}
      <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-4">
        <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
          <h2 className="text-lg font-bold text-softform-navy-950">Executive Briefing</h2>
          <span className="text-xs font-semibold uppercase tracking-wider text-softform-text-muted">
            {companyName}
          </span>
        </div>
        <p className="text-base leading-relaxed text-softform-text-secondary">
          {executiveBrief}
        </p>
      </section>

      {/* 3. Key Sections */}
      <section className="space-y-6">
        <h2 className="text-xl font-bold text-softform-navy-950">Key Sections Summary</h2>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Financial Posture */}
          {keySections.financialPosture && (
            <div className="softform-card rounded-2xl p-6 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-softform-mist-100 text-softform-teal-deep">
                      <BarChart3 size={16} />
                    </div>
                    <h3 className="font-bold text-softform-navy-950">
                      {keySections.financialPosture.title}
                    </h3>
                  </div>
                  <StatusChip variant="neutral">Financial</StatusChip>
                </div>
                <p className="text-sm leading-relaxed text-softform-text-secondary">
                  {keySections.financialPosture.summary}
                </p>
                {keySections.financialPosture.signals && keySections.financialPosture.signals.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <p className="text-xs font-semibold text-softform-text-secondary uppercase tracking-wider">
                      Signals
                    </p>
                    <ul className="space-y-1">
                      {keySections.financialPosture.signals.map((sig, i) => (
                        <li key={i} className="text-xs text-softform-text-secondary flex items-start gap-1.5">
                          <span className="text-softform-teal-deep mt-0.5">•</span>
                          <span>{sig}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {keySections.financialPosture.warnings && keySections.financialPosture.warnings.length > 0 && (
                <div className="rounded-xl bg-softform-cream/40 p-3 text-xs text-softform-amber-500 border border-softform-amber-200/20">
                  {keySections.financialPosture.warnings.map((w, idx) => (
                    <p key={idx} className="flex gap-1.5 items-start">
                      <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Advisory Readiness */}
          {keySections.advisoryReadiness && (
            <div className="softform-card rounded-2xl p-6 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-softform-mist-100 text-softform-teal-deep">
                      <ShieldCheck size={16} />
                    </div>
                    <h3 className="font-bold text-softform-navy-950">
                      {keySections.advisoryReadiness.title}
                    </h3>
                  </div>
                  <StatusChip variant="signal">Readiness</StatusChip>
                </div>
                <p className="text-sm leading-relaxed text-softform-text-secondary">
                  {keySections.advisoryReadiness.summary}
                </p>
                {keySections.advisoryReadiness.constraints && keySections.advisoryReadiness.constraints.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <p className="text-xs font-semibold text-softform-text-secondary uppercase tracking-wider">
                      Constraints
                    </p>
                    <ul className="space-y-1">
                      {keySections.advisoryReadiness.constraints.map((c, i) => (
                        <li key={i} className="text-xs text-softform-text-secondary flex items-start gap-1.5">
                          <span className="text-red-500 mt-0.5">•</span>
                          <span>{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {keySections.advisoryReadiness.warnings && keySections.advisoryReadiness.warnings.length > 0 && (
                <div className="rounded-xl bg-softform-cream/40 p-3 text-xs text-softform-amber-500 border border-softform-amber-200/20">
                  {keySections.advisoryReadiness.warnings.map((w, idx) => (
                    <p key={idx} className="flex gap-1.5 items-start">
                      <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Stress Context */}
          {keySections.stressContext && (
            <div className="softform-card rounded-2xl p-6 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-softform-mist-100 text-softform-teal-deep">
                      <AlertTriangle size={16} />
                    </div>
                    <h3 className="font-bold text-softform-navy-950">
                      {keySections.stressContext.title}
                    </h3>
                  </div>
                  <StatusChip variant="caution">Sensitivity</StatusChip>
                </div>
                <p className="text-sm leading-relaxed text-softform-text-secondary">
                  {keySections.stressContext.summary}
                </p>
                {keySections.stressContext.signals && keySections.stressContext.signals.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <p className="text-xs font-semibold text-softform-text-secondary uppercase tracking-wider">
                      Sensitivity Takeaways
                    </p>
                    <ul className="space-y-1">
                      {keySections.stressContext.signals.map((sig, i) => (
                        <li key={i} className="text-xs text-softform-text-secondary flex items-start gap-1.5">
                          <span className="text-softform-teal-deep mt-0.5">•</span>
                          <span>{sig}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {keySections.stressContext.warnings && keySections.stressContext.warnings.length > 0 && (
                <div className="rounded-xl bg-softform-cream/40 p-3 text-xs text-softform-amber-500 border border-softform-amber-200/20">
                  {keySections.stressContext.warnings.map((w, idx) => (
                    <p key={idx} className="flex gap-1.5 items-start">
                      <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Candidate Structures */}
          {keySections.candidateStructures && (
            <div className="softform-card rounded-2xl p-6 space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-softform-mist-100 text-softform-teal-deep">
                      <Landmark size={16} />
                    </div>
                    <h3 className="font-bold text-softform-navy-950">
                      {keySections.candidateStructures.title}
                    </h3>
                  </div>
                  <StatusChip variant="signal">Structures</StatusChip>
                </div>
                <p className="text-sm leading-relaxed text-softform-text-secondary">
                  {keySections.candidateStructures.summary}
                </p>
                {keySections.candidateStructures.signals && keySections.candidateStructures.signals.length > 0 && (
                  <div className="space-y-1.5 pt-2">
                    <p className="text-xs font-semibold text-softform-text-secondary uppercase tracking-wider">
                      Preferred Candidates
                    </p>
                    <ul className="space-y-1">
                      {keySections.candidateStructures.signals.map((sig, i) => (
                        <li key={i} className="text-xs text-softform-text-secondary flex items-start gap-1.5">
                          <span className="text-softform-teal-deep mt-0.5">•</span>
                          <span>{sig}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {keySections.candidateStructures.warnings && keySections.candidateStructures.warnings.length > 0 && (
                <div className="rounded-xl bg-softform-cream/40 p-3 text-xs text-softform-amber-500 border border-softform-amber-200/20">
                  {keySections.candidateStructures.warnings.map((w, idx) => (
                    <p key={idx} className="flex gap-1.5 items-start">
                      <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* 4. Recommended Actions */}
      <section className="space-y-6">
        <h2 className="text-xl font-bold text-softform-navy-950">Recommended Actions Workflow</h2>
        <div className="space-y-4">
          {recommendedActions.map((act) => {
            // Map action key to category and outcome context for display
            let category = 'Information Gathering'
            let expectedOutcome = 'Prepares the workspace for formal, record-backed review.'
            if (act.actionKey === 'review_debt_service_headroom') {
              category = 'Debt Optimization'
              expectedOutcome = 'Avoids over-leveraging and aligns sizing to current cash flow reality.'
            } else if (act.actionKey === 'compare_working_capital_options') {
              category = 'Treasury Comparison'
              expectedOutcome = 'Identifies structural alternatives that reduce financing costs.'
            }

            return (
              <div
                key={act.actionKey}
                className="softform-card rounded-2xl p-5 flex flex-col md:flex-row md:items-start justify-between gap-4"
              >
                <div className="space-y-3 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-softform-teal-deep">
                      {category}
                    </span>
                    <StatusChip variant={act.priority === 'high' ? 'caution' : 'neutral'}>
                      {act.priority} priority
                    </StatusChip>
                  </div>
                  <h3 className="font-bold text-softform-navy-950 text-base flex items-center gap-2">
                    <CheckSquare size={16} className="text-softform-teal-deep shrink-0" />
                    {act.label}
                  </h3>
                  <p className="text-sm text-softform-text-secondary leading-relaxed">
                    <strong>Rationale:</strong> {act.rationale}
                  </p>
                  <p className="text-sm text-softform-text-secondary leading-relaxed">
                    <strong>Expected Outcome:</strong> {expectedOutcome}
                  </p>
                  {act.requiredData && act.requiredData.length > 0 && (
                    <div className="pt-1.5">
                      <span className="text-xs font-semibold text-softform-text-secondary uppercase tracking-wider">
                        Required Records
                      </span>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {act.requiredData.map((d, idx) => (
                          <span
                            key={idx}
                            className="inline-block rounded-lg bg-softform-mist-100/50 px-2.5 py-1 text-xs text-softform-text-secondary border border-white/50"
                          >
                            {d}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                {act.ownerHint && (
                  <div className="shrink-0 text-xs text-softform-text-muted md:text-right md:border-l md:border-softform-navy-950/5 md:pl-4 md:h-full flex flex-col justify-center">
                    <span className="font-semibold text-softform-navy-950 block">Assigned Owner</span>
                    <span>{act.ownerHint}</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </section>

      {/* 5. Candidate Structure Summary */}
      {facilityStructures && (
        <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <Landmark size={20} className="text-softform-teal-deep" />
              Candidate Financing Structures
            </h2>
            <StatusChip variant="neutral">Baseline Fit</StatusChip>
          </div>
          <p className="text-sm leading-relaxed text-softform-text-secondary">
            Structured context-only financing packages under baseline metrics. Note: Limit and pricing metrics are assumptions-only and subject to lender review.
          </p>

          <div className="grid gap-6 sm:grid-cols-3">
            {facilityStructures.candidates.slice(0, 3).map((cand) => (
              <div
                key={cand.facilityKey}
                className="rounded-2xl bg-white/45 p-5 border border-white/60 shadow-sm flex flex-col justify-between gap-4"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-softform-navy-950 text-sm leading-snug">
                      {cand.label}
                    </h3>
                    <span
                      className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                        cand.fitAssessment.fitBand === 'strong'
                          ? 'bg-emerald-500/10 text-emerald-700'
                          : cand.fitAssessment.fitBand === 'adequate'
                          ? 'bg-softform-mist-100 text-softform-teal-deep'
                          : 'bg-softform-cream text-softform-amber-500'
                      }`}
                    >
                      {cand.fitAssessment.fitBand} fit
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div className="text-xs text-softform-text-secondary">
                      <span className="font-semibold">Est. Limit:</span> {formatHKD(cand.estimatedLimit)}
                    </div>
                    {cand.estimatedPricingBps !== undefined && cand.estimatedPricingBps !== null && (
                      <div className="text-xs text-softform-text-secondary">
                        <span className="font-semibold">Est. Pricing:</span> {cand.estimatedPricingBps} bps spread
                      </div>
                    )}
                    {cand.estimatedAnnualCost !== undefined && cand.estimatedAnnualCost !== null && (
                      <div className="text-xs text-softform-text-secondary">
                        <span className="font-semibold">Est. Annual Cost:</span> {formatHKD(cand.estimatedAnnualCost)}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-softform-text-secondary leading-relaxed">
                    <strong>Purpose:</strong> {cand.purpose}
                  </p>
                </div>
                <p className="text-[10px] text-softform-text-muted leading-relaxed italic border-t border-softform-navy-950/5 pt-2">
                  {cand.disclaimer}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 6. Risk Context Summary */}
      {riskScore && (
        <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <ShieldCheck size={20} className="text-softform-teal-deep" />
              Advisory Readiness Score Context
            </h2>
            <StatusChip variant="signal">Readiness Score</StatusChip>
          </div>
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-softform-mist-100/60 border border-softform-aqua-300/30 w-36 shrink-0 shadow-inner">
              <span className="text-3xl font-black text-softform-teal-deep">{riskScore.score}</span>
              <span className="text-[10px] uppercase tracking-wider font-semibold text-softform-text-muted mt-0.5">
                Scale 0-100
              </span>
              <span className="mt-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-softform-navy-950 text-white uppercase tracking-wider">
                {riskScore.band} Band
              </span>
            </div>
            <div className="space-y-3 flex-1">
              <p className="text-sm text-softform-text-secondary leading-relaxed">
                This score provides context for advisory readiness and financing fit only. It does not represent a probability of default or a credit rating.
              </p>
              {riskScore.factors && riskScore.factors.length > 0 && (
                <div className="grid gap-3 sm:grid-cols-2">
                  {riskScore.factors.slice(0, 4).map((f) => (
                    <div key={f.key} className="p-3 rounded-xl bg-white/40 border border-white/50 text-xs space-y-1">
                      <div className="flex justify-between font-semibold text-softform-navy-950">
                        <span>{f.label}</span>
                        <span className="text-softform-teal-deep">Impact: -{f.scoreImpact}</span>
                      </div>
                      <p className="text-softform-text-secondary">{f.message}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* 7. Stress Context Summary */}
      {stressTests && (
        <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <AlertTriangle size={20} className="text-softform-teal-deep" />
              Stress Test Sensitivity Context
            </h2>
            <StatusChip variant="caution">Sensitivity Model</StatusChip>
          </div>
          <p className="text-sm leading-relaxed text-softform-text-secondary">
            Simulated scenario shocks applied to baseline metrics. Displays impact on key performance signals.
          </p>

          <div className="grid gap-6 sm:grid-cols-2">
            {stressTests.scenarios.map((scen) => (
              <div
                key={scen.scenarioKey}
                className="p-5 rounded-2xl bg-white/45 border border-white/60 shadow-sm space-y-3"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-softform-navy-950 text-sm">{scen.label}</h3>
                  <span
                    className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${
                      scen.severity === 'high'
                        ? 'bg-red-500/10 text-red-700'
                        : scen.severity === 'elevated'
                        ? 'bg-softform-cream text-softform-amber-500'
                        : 'bg-softform-mist-100 text-softform-teal-deep'
                    }`}
                  >
                    {scen.severity} severity
                  </span>
                </div>
                <p className="text-xs text-softform-text-secondary italic">
                  {scen.keyTakeaway}
                </p>
                {scen.impacts && scen.impacts.length > 0 && (
                  <div className="border-t border-softform-navy-950/5 pt-2 space-y-2">
                    {scen.impacts.slice(0, 2).map((imp, idx) => (
                      <div key={idx} className="flex justify-between text-xs">
                        <span className="text-softform-text-secondary">{imp.metric}:</span>
                        <span className="font-medium text-softform-navy-950">
                          {imp.baseValue.toFixed(2)} → {imp.stressedValue.toFixed(2)} ({imp.interpretation})
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 8. Data Readiness Gaps */}
      {keySections.dataReadiness && (
        <section className="softform-card rounded-[32px] p-6 sm:p-8 space-y-4">
          <div className="flex items-center justify-between border-b border-softform-navy-950/5 pb-4">
            <h2 className="text-lg font-bold text-softform-navy-950 flex items-center gap-2">
              <FolderOpen size={20} className="text-softform-teal-deep" />
              Information Gaps for Production Advisory
            </h2>
            <StatusChip variant="neutral">Data Readiness</StatusChip>
          </div>
          <p className="text-sm leading-relaxed text-softform-text-secondary">
            The following documentation gaps must be resolved to transition from this demo context to a record-backed production analysis:
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {keySections.dataReadiness.nextDataNeeded.map((gap, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2.5 p-3.5 rounded-xl bg-white/45 border border-white/60 text-xs text-softform-text-secondary font-medium"
              >
                <div className="h-2 w-2 rounded-full bg-softform-teal-deep shrink-0" />
                <span>{gap}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Footer Info */}
      <footer className="pt-6 border-t border-softform-navy-950/5 text-center space-y-2">
        <p className="text-xs text-softform-text-muted">
          All data in this report is context-only, assumptions-based, and for planning purposes.
        </p>
        <p className="text-xs text-softform-text-muted">
          FinSight CFO Workspace • Powered by softform design token system.
        </p>
      </footer>
    </div>
  )
}
