/* eslint-disable @typescript-eslint/no-explicit-any */
export type BlueprintReadinessStatus =
  | 'ready_context'
  | 'watch_context'
  | 'constrained_context'
  | 'unavailable_context'

export interface AdvisoryBriefSection {
  sectionKey: string
  title: string
  summary: string
  signals: string[]
  constraints: string[]
  nextDataNeeded: string[]
  sourceRefs: string[]
  warnings: string[]
}

export interface AdvisoryBlueprintAction {
  actionKey: string
  label: string
  priority: 'high' | 'medium' | 'low'
  rationale: string
  ownerHint: string
  requiredData: string[]
  relatedCandidateKeys: string[]
}

export interface BlueprintKeySections {
  financialPosture: AdvisoryBriefSection
  advisoryReadiness: AdvisoryBriefSection
  stressContext: AdvisoryBriefSection
  candidateStructures: AdvisoryBriefSection
  dataReadiness: AdvisoryBriefSection
}

export interface AdvisoryBlueprintResponse {
  companyId: string
  companyName: string
  blueprintStatus: BlueprintReadinessStatus
  executiveBrief: string
  keySections: BlueprintKeySections
  recommendedActions: AdvisoryBlueprintAction[]
  sourceOutputs: string[]
  disclaimer: string
  warnings: string[]
  run_metadata?: any
}

export type HardGateStatus = 'pass' | 'watch' | 'fail' | 'unavailable'
export type HardGateSeverity = 'low' | 'medium' | 'high'

export interface HardGateCheck {
  key: string
  label: string
  status: HardGateStatus
  message: string
  evidence: string
  source: string
  severity: HardGateSeverity
  requiredAction?: string | null
  warnings: string[]
}

export interface HardGatePrecheckResult {
  companyId: string
  companyName: string
  overallStatus: HardGateStatus
  checks: HardGateCheck[]
  passCount: number
  watchCount: number
  failCount: number
  unavailableCount: number
  constraints: string[]
  nextDataNeeded: string[]
  disclaimer: string
  warnings: string[]
}

export type RiskScoreBand = 'low' | 'moderate' | 'elevated' | 'high' | 'unavailable'

export interface RiskScoreFactor {
  key: string
  label: string
  scoreImpact: number
  band: string
  message: string
  evidence: string
  source: string
  weight: number
  warnings: string[]
}

export interface UnifiedRiskScoreResult {
  companyId: string
  companyName: string
  score: number
  band: RiskScoreBand
  scoreScale: string
  factors: RiskScoreFactor[]
  strengths: string[]
  constraints: string[]
  watchItems: string[]
  hardGateStatus: string
  disclaimer: string
  warnings: string[]
}

export type PdRiskTier = 'low' | 'moderate' | 'elevated' | 'high' | 'unavailable'
export type FundingReadinessBand =
  | 'ready_context'
  | 'bank_review_ready'
  | 'needs_review'
  | 'not_ready'
  | 'unavailable'

export interface CreditScoreFactor {
  key: string
  label: string
  rawScore: number
  weightedScore: number
  weight: number
  band: string
  message: string
  evidence: string
  source: string
  positiveDriver?: string | null
  riskDriver?: string | null
  warnings: string[]
}

export interface CreditScoringResult {
  companyId: string
  companyName: string
  compositeScore: number
  scoreScale: string
  riskTier: PdRiskTier
  pdProxyBand: string
  fundingReadiness: FundingReadinessBand
  factors: CreditScoreFactor[]
  positiveDrivers: string[]
  riskDrivers: string[]
  hardConstraints: string[]
  nextDataNeeded: string[]
  methodologyLabel: string
  disclaimer: string
  warnings: string[]
}

export interface StressScenarioAssumption {
  scenarioKey: string
  label: string
  scenarioType: string
  description: string
  parameters: Record<string, unknown>
  source: string
  warnings: string[]
}

export interface StressScenarioImpact {
  metric: string
  baseValue: number
  stressedValue: number
  absoluteChange: number
  percentChange?: number | null
  unit?: string | null
  interpretation: string
  warnings: string[]
}

export interface StressScenarioResult {
  scenarioKey: string
  label: string
  scenarioType: string
  severity: string
  assumptions: StressScenarioAssumption[]
  impacts: StressScenarioImpact[]
  bandMovement?: string | null
  keyTakeaway: string
  warnings: string[]
  disclaimer: string
}

export interface StressTestingResponse {
  companyId: string
  companyName: string
  baseSummaryBand: string
  baseRiskScore: number
  scenarios: StressScenarioResult[]
  disclaimer: string
  warnings: string[]
}

export type FacilityType =
  | 'revolving_working_capital'
  | 'trade_finance'
  | 'receivables_finance'
  | 'term_loan'
  | 'fx_hedging_context'
  | 'liquidity_buffer'

export interface FacilityFitAssessment {
  fitBand: 'strong' | 'adequate' | 'watch' | 'constrained' | 'unavailable'
  rationale: string
  constraints: string[]
  watchItems: string[]
  requiredData: string[]
}

export interface FacilityCandidate {
  facilityKey: string
  facilityType: FacilityType
  label: string
  estimatedLimit?: number | null
  currency: string
  estimatedPricingBps?: number | null
  estimatedAnnualCost?: number | null
  tenorMonths?: number | null
  repaymentProfile: string
  purpose: string
  fitAssessment: FacilityFitAssessment
  supportingSignals: string[]
  sensitivityNotes: string
  warnings: string[]
  disclaimer: string
}

export interface FacilityStructuringResponse {
  companyId: string
  companyName: string
  baseRiskScore: number
  baseRiskBand: RiskScoreBand
  hardGateStatus: HardGateStatus
  candidates: FacilityCandidate[]
  preferredCandidateKeys: string[]
  constraints: string[]
  nextDataNeeded: string[]
  disclaimer: string
  warnings: string[]
}
