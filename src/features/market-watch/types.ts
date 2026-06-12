/* eslint-disable @typescript-eslint/no-explicit-any */
export type FreshnessStatus = 'Daily' | 'Monthly' | 'Delayed' | 'Workspace'

export type SignalSeverity = 'Neutral' | 'Caution' | 'High' | 'Positive'

export type SourceStatus =
  | 'Ready for connector'
  | 'Seed data'
  | 'Requires backend'
  | 'Requires company data'
  | 'connected'
  | 'seed_data'
  | 'requires_backend'
  | 'requires_company_data'
  | 'unavailable'
  | 'stale'


export type TimingBand = 'favorable' | 'neutral' | 'cautious'
export type TimingTrendSignal = 'easing' | 'stable' | 'tightening' | 'unavailable'
export type LiquidityTimingSignal = 'favorable' | 'neutral' | 'cautious' | 'unavailable'
export type CalendarRedFlag = 'none' | 'month_end' | 'half_year_end' | 'year_end'

export interface TimingSignalComponent {
  band: string
  label: string
  value?: string | null
  explanation: string
}

export interface TimingSignalProvenance {
  source: string
  provider: string
  asOf?: string | null
  freshness: FreshnessStatus
}

export interface TimingSignalResponse {
  mode: 'context_only'
  hiborLevelBand: TimingBand
  hiborTrendSignal: TimingTrendSignal
  liquidityTimingSignal: LiquidityTimingSignal
  calendarRedFlag: CalendarRedFlag
  goldenTimingBand: TimingBand
  explanation: string
  components: TimingSignalComponent[]
  provenance: TimingSignalProvenance
  warnings: string[]
  disclaimer: string
}

export type IndustryHealthBand = 'resilient' | 'stable' | 'watch' | 'stressed' | 'unavailable'
export type DemandSignal = 'expanding' | 'stable' | 'softening' | 'unavailable'
export type MarginSignal = 'expanding' | 'stable' | 'compressing' | 'unavailable'
export type WorkingCapitalSignal = 'healthy' | 'watch' | 'stressed' | 'unavailable'
export type BenchmarkSignal = 'favorable' | 'neutral' | 'cautious' | 'unavailable'

export interface IndustryHealthComponent {
  signal: string
  label: string
  band: string
  value?: string | null
  explanation: string
}

export interface IndustryHealthProvenance {
  source: string
  provider: string
  asOf?: string | null
  freshness: FreshnessStatus
}

export interface IndustryHealthResponse {
  mode: 'context_only'
  sectorName: string
  industryHealthBand: IndustryHealthBand
  demandSignal: DemandSignal
  marginSignal: MarginSignal
  workingCapitalSignal: WorkingCapitalSignal
  benchmarkSignal: BenchmarkSignal
  explanation: string
  components: IndustryHealthComponent[]
  provenance: IndustryHealthProvenance
  source?: IndustryHealthProvenance
  warnings: string[]
  disclaimer: string
}

export type MarketMetric = {
  id: string
  label: string
  value: string
  interpretation: string
  severity: SignalSeverity
  freshness: FreshnessStatus
  source: string
}

export type MarketSignal = {
  id: string
  category: string
  title: string
  description: string
  severity: SignalSeverity
  cfoQuestion: string
  affectedArea: string
  timestamp: string
}

export type RateSnapshot = {
  id?: string
  label: string
  value: string
  changeBasisPoints: number
  trend: 'up' | 'down' | 'flat'
  context: string
}

export type LiquidityEvent = {
  id: string
  date: string
  event: string
  impact: string
  severity: SignalSeverity
}

export type FxPair = {
  pair: string
  rate: string
  trend: 'up' | 'down' | 'flat'
  context: string
}

export type GbaFundingSignal = {
  id: string
  title: string
  description: string
  severity: SignalSeverity
}

export type ExposureNote = {
  id: string
  category: string
  note: string
  severity: SignalSeverity
}

export type SectorBenchmark = {
  sector: string
  healthScore: number // 0-100
  pmi: number
  exportGrowth: string
  workingCapitalDays: number
  receivablesDays: number
  inventoryPressure: string
}

export type CommodityExposure = {
  commodity: string
  priceTrend: 'up' | 'down' | 'flat'
  yoyChange: string
  affectedSectors: string[]
  marginSensitivity: string
  displayValue?: string
}

export type StressScenario = {
  id: string
  title: string
  description: string
  affectedArea: string
  impactDirection: 'Negative' | 'Positive' | 'Mixed'
  severity: SignalSeverity
  cfoQuestion: string
  requiredDataStatus: string
  shockType?: 'rate' | 'fx' | 'commodity' | 'receivables' | 'liquidity'
  requiresCompanyData?: boolean
  requiredDataIds?: string[]
  status?: 'context_only' | 'requires_company_data' | 'ready_for_model'
  sourceTimestamp?: string | null
}

export interface StressSourceInfo {
  label: string
  asOf: string | null
  warnings: string[]
  freshness: FreshnessStatus
  workspaceContext: {
    id: string
    companyLabel: string
    sector: string
    geography: string
    description: string
  }
  requiredData: {
    id: string
    label: string
    status: string
    description: string
  }[]
  watchSignals: {
    id: string
    title: string
    description: string
    affectedArea: string
    severity: SignalSeverity
  }[]
  sourceStatus: {
    id: string
    label: string
    status: string
    provider?: string
    lastUpdatedAt?: string | null
  }[]
  isFallback?: boolean
}

export type SignalFeedItem = MarketSignal

export type SourceStatusItem = {
  label: string
  status: SourceStatus
}

export interface SectorHealthComponent {
  label: string
  value: number | null
  unit: 'index' | 'percent' | 'text'
  displayValue: string
  context: string
}

export interface SectorHealth {
  score: number | null
  label: string
  severity: SignalSeverity
  components: {
    pmi: SectorHealthComponent | null
    exportGrowth: SectorHealthComponent | null
    industrialProduction: SectorHealthComponent | null
    marginContext: SectorHealthComponent | null
  }
}

export interface SectorBenchmarkItem {
  id: string
  label: string
  value: number | null
  unit: 'days' | 'percent' | 'ratio' | 'index'
  displayValue: string
  comparison: string
  context: string
  severity: SignalSeverity
  sourceTimestamp: string | null
}

export interface SectorWatchSignal {
  id: string
  title: string
  description: string
  affectedArea: string
  severity: SignalSeverity
}

export interface SectorSourceInfo {
  label: string
  asOf: string | null
  warnings: string[]
  freshness: FreshnessStatus
  selectedSector: {
    id: string
    name: string
    code: string | null
    geography: string
    description: string
  }
  sectorHealth: SectorHealth
  watchSignals: SectorWatchSignal[]
  sourceStatus: {
    id: string
    label: string
    status: string
    provider?: string
    lastUpdatedAt?: string | null
  }[]
  isFallback?: boolean
}

export interface MarginPressureSignal {
  id: string
  label: string
  severity: SignalSeverity
  description: string
  affectedArea: string
  requiresCompanyData: boolean
}

export interface CommodityWatchSignal {
  id: string
  title: string
  description: string
  affectedArea: string
  severity: SignalSeverity
}

export interface CommoditySourceInfo {
  label: string
  asOf: string | null
  warnings: string[]
  freshness: FreshnessStatus
  selectedSector: {
    id: string
    name: string
    code: string | null
    geography: string
    description: string
  }
  marginPressureSignal: MarginPressureSignal[]
  watchSignals: CommodityWatchSignal[]
  sourceStatus: {
    id: string
    label: string
    status: string
    provider?: string
    lastUpdatedAt?: string | null
  }[]
  isFallback?: boolean
}


export interface ConsolidatedSourceStatusItem {
  id: string
  label: string
  status: SourceStatus
  provider?: string
  freshness?: string
  lastUpdatedAt?: string | null
  message?: string
}

export interface RefreshResponse {
  status: string
  message: string
  refreshedScope: string
  sources: ConsolidatedSourceStatusItem[]
}

export interface ConnectedRecord {
  id: string
  label: string
  status: string
}

export interface CompanyProfile {
  companyName: string
  sector: string
  geography: string
  revenueTtmHkd: number
  cashBalanceHkd: number
  receivablesHkd: number
  payablesHkd: number
  inventoryHkd: number
  dsoDays: number
  dpoDays: number
  inventoryDays: number
  grossMarginPercent: number
  floatingRateDebtHkd: number
  monthlyDebtServiceHkd: number
  cnySupplierPayablesPercent: number
  usdImportCostPercent: number
  topCustomerConcentrationPercent: number
  workingCapitalGapHkd: number
  connectedRecords: ConnectedRecord[]
  dscr?: number | null
  currentRatio?: number | null
  quickRatio?: number | null
  interestCoverage?: number | null
  netDebtToEbitda?: number | null
  isFallbackFinancials?: boolean
}

export interface CompanyExposure {
  id: string
  category: string
  label: string
  value: string
  severity: SignalSeverity
  context: string
}

export interface CompanyContext {
  profile: CompanyProfile
  exposures: CompanyExposure[]
  dataMode: string
}

export interface RatioMetric {
  value: number | null
  warning: string | null
  label: string
}

export interface FinancialRatios {
  currentRatio: RatioMetric
  quickRatio: RatioMetric
  interestCoverage: RatioMetric
  dscr: RatioMetric
  debtRatio: RatioMetric
  netDebtToEbitda: RatioMetric
  dso: RatioMetric
  workingCapitalGap: RatioMetric
  expectedCreditLossAr: RatioMetric
}

export interface IntegrityCheckResult {
  checkName: string
  passed: boolean
  message: string
  details?: Record<string, unknown> | null
}

export interface IncomeStatementPeriod {
  revenue: number
  cogs: number
  grossProfit?: number | null
  operatingExpenses: number
  ebit: number
  depreciationAmortization: number
  ebitda: number
  interestExpense: number
  ebt: number
  taxes: number
  netIncome: number
}

export interface BalanceSheetPeriod {
  cash: number
  accountsReceivable: number
  inventory: number
  prepaid: number
  currentAssets: number
  ppeNet: number
  totalAssets: number
  accountsPayable: number
  accrued: number
  shortTermDebt: number
  currentPortionLongTermDebt: number
  longTermDebt: number
  leaseLiabilities: number
  currentLiabilities: number
  totalLiabilities: number
  equity: number
}

export interface CashFlowStatementPeriod {
  cfo: number
  capex: number
  debtIssued: number
  debtRepaid: number
  dividends: number
  netChangeCash: number
}

export interface DebtSchedule {
  scheduledInterest: number
  scheduledPrincipal: number
  monthlyDebtService?: number | null
}

export interface ReceivablesAging {
  current030: number
  days3160: number
  days6190: number
  days90Plus: number
}


// ------------------------------------------------------------------
// Cross-border Funding Context v1 types
// ------------------------------------------------------------------

export type CrossBorderSpreadBand = 'hkd_advantage' | 'rmb_advantage' | 'balanced' | 'unavailable'
export type CrossBorderFxRiskBand = 'low' | 'moderate' | 'elevated' | 'unavailable'
export type CrossBorderReviewBand = 'worth_reviewing' | 'monitor' | 'not_priority' | 'unavailable'

export interface CrossBorderFundingReference {
  label: string
  currency: 'HKD' | 'RMB'
  value?: number | null
  unit: 'basis_points' | 'days' | 'percent' | 'price' | 'ratio' | 'text' | 'index'
  displayValue: string
  source: string
}

export interface CrossBorderFundingComponent {
  label: string
  value?: string | null
  signal: string
  explanation: string
}

export interface CrossBorderFundingProvenance {
  source: string
  provider: string
  asOf?: string | null
  freshness: FreshnessStatus
}

export interface CrossBorderFundingContextResponse {
  mode: 'context_only'
  baseCurrency: string
  comparisonCurrency: string
  hkdFundingReference: CrossBorderFundingReference
  rmbFundingReference: CrossBorderFundingReference
  spreadBps: number | null
  spreadBand: string
  fxRiskBand: string
  crossBorderReviewBand: string
  explanation: string
  components: CrossBorderFundingComponent[]
  provenance: CrossBorderFundingProvenance
  source: CrossBorderFundingProvenance
  warnings: string[]
  disclaimer: string
}

export type RedFlagSeverity = 'low' | 'moderate' | 'elevated' | 'stressed' | 'unavailable'
export type RedFlagCategory = 'rates' | 'fx' | 'sector' | 'funding' | 'cross_border' | 'timing' | 'liquidity'
export type SummaryBand = 'clear' | 'watch' | 'elevated' | 'stressed' | 'unavailable'

export interface RedFlagProvenance {
  source: string
  provider: string
  asOf?: string | null
  freshness: FreshnessStatus
}

export interface RedFlagMitigant {
  label: string
  rationale: string
  source: string
}

export interface RedFlagItem {
  flagKey: string
  label: string
  severity: RedFlagSeverity
  category: RedFlagCategory
  signal: string
  rationale: string
  suggestedReviewAction: string
  supportingSignals: string[]
  source: string
}

export interface RedFlagsSummaryComponent {
  label: string
  value?: string | null
  signal: string
  explanation: string
}

export interface RedFlagsMacroSummaryResponse {
  mode: 'context_only'
  summaryBand: SummaryBand
  headline: string
  redFlags: RedFlagItem[]
  mitigants: RedFlagMitigant[]
  components: RedFlagsSummaryComponent[]
  provenance: RedFlagProvenance
  source: RedFlagProvenance
  warnings: string[]
  disclaimer: string
}

// ------------------------------------------------------------------
// Funding Channel Ranking v1 types
// ------------------------------------------------------------------

export type FundingChannelKey =
  | 'working_capital_line'
  | 'receivables_financing'
  | 'trade_finance_lc'
  | 'term_loan'
  | 'fx_hedging_context'

export type FundingFitBand = 'strong_fit' | 'moderate_fit' | 'watch_fit'

export type FundingRankingBand =
  | 'working_capital_priority'
  | 'trade_cycle_priority'
  | 'balance_sheet_review'
  | 'risk_context_priority'

export interface FundingChannelComponent {
  signal: string
  label: string
  band: string
  explanation: string
}

export interface FundingChannelProvenance {
  source: string
  provider: string
  asOf?: string | null
  freshness: FreshnessStatus
}

export interface FundingCompanyContext {
  companyName: string
  sector: string
  geography: string
  dataMode: string
  dscr?: number | null
  floatingRateExposure?: string | null
  workingCapitalGap?: string | null
  dsoWatch: boolean
  fxExposure: boolean
  importCostStress: boolean
}

export interface FundingChannelItem {
  key: FundingChannelKey
  label: string
  rank: number
  fitBand: FundingFitBand
  score: number
  useCase: string
  rationale: string
  supportingSignals: string[]
  source: string
  constraints: string[]
}

export interface FundingChannelRankingResponse {
  mode: 'context_only'
  companyContext: FundingCompanyContext
  rankingBand: FundingRankingBand
  channels: FundingChannelItem[]
  topChannelKey: FundingChannelKey
  explanation: string
  components: FundingChannelComponent[]
  provenance: FundingChannelProvenance
  source: FundingChannelProvenance
  warnings: string[]
  disclaimer: string
  run_metadata?: any
}

export interface CompanyFinancialSnapshot {
  companyId: string
  companyName: string
  sectorCode?: string | null
  sectorName?: string | null
  reportingPeriod: string
  currency: string
  incomeStatement: IncomeStatementPeriod
  balanceSheet: BalanceSheetPeriod
  cashFlowStatement: CashFlowStatementPeriod
  debtSchedule: DebtSchedule
  receivablesAging?: ReceivablesAging | null
  metadata?: Record<string, unknown> | null
}

/** Band returned by the backend Financial Analysis Summary engine */
export type FinancialBand = 'strong' | 'adequate' | 'watch' | 'constrained' | 'unavailable'

export interface FinancialSignal {
  key: string
  label: string
  value?: number | null
  unit?: string | null
  band: FinancialBand
  message: string
  evidence: string
  source: string
  warnings: string[]
}

export interface FinancialAnalysisSummary {
  overallBand: FinancialBand
  liquidityBand: FinancialBand
  debtServiceBand: FinancialBand
  leverageBand: FinancialBand
  receivablesBand: FinancialBand
  valuationBand: FinancialBand
  keySignals: FinancialSignal[]
  watchItems: string[]
  strengths: string[]
  constraints: string[]
  nextDataNeeded: string[]
  warnings: string[]
  disclaimer?: string
}

export interface ReceivablesRiskDiagnostic {
  zone?: string | null
  eclRatio?: number | null
  warning?: string | null
}

export interface AltmanZScoreDiagnostic {
  value?: number | null
  band?: string | null
  methodologyLabel?: string | null
  warning?: string | null
}

export interface RiskDiagnostics {
  altmanZScore?: AltmanZScoreDiagnostic | null
  receivablesRisk?: ReceivablesRiskDiagnostic | null
  warnings?: string[]
}

export interface ProjectedValuationYear {
  year: number
  revenue?: number | null
  ebit?: number | null
  nopat?: number | null
  capex?: number | null
  depreciationAmortization?: number | null
  changeInNwc?: number | null
  fcffPrimary?: number | null
  fcfePrimary?: number | null
}

export interface ProjectionOutput {
  projectedYears: ProjectedValuationYear[]
  warnings?: string[]
}

export interface WaccOutput {
  costOfEquity?: number | null
  preTaxCostOfDebt?: number | null
  afterTaxCostOfDebt?: number | null
  debtWeight?: number | null
  equityWeight?: number | null
  wacc?: number | null
  unleveredBeta?: number | null
  releveredBeta?: number | null
  warnings?: string[]
}

export interface DcfValuationYear {
  year: number
  fcff: number
  discountFactor: number
  pvFcff: number
}

export interface DcfOutput {
  valuationYears?: DcfValuationYear[]
  pvExplicitFcff?: number | null
  terminalValueGordonGrowth?: number | null
  pvTerminalValue?: number | null
  enterpriseValue?: number | null
  totalDebt?: number | null
  cash?: number | null
  netDebt?: number | null
  equityValue?: number | null
  impliedEvEbitda?: number | null
  terminalGrowthRate?: number | null
  wacc?: number | null
  terminalValueShareOfEnterpriseValue?: number | null
  exitMultipleTerminalValue?: number | null
  impliedExitMultiple?: number | null
  warnings?: string[]
}

export interface ValuationSensitivityPoint {
  wacc: number
  terminalGrowthRate: number
  enterpriseValue?: number | null
  equityValue?: number | null
}

export interface ValuationSanityCheck {
  name: string
  status: string
  message: string
  value?: number | null
}

export interface ValuationOutput {
  assumptions?: Record<string, number | string | null>
  wacc?: WaccOutput | null
  dcf?: DcfOutput | null
  sensitivity?: ValuationSensitivityPoint[]
  sanityChecks?: ValuationSanityCheck[]
  warnings?: string[]
}

export interface FinancialAnalysisResponse {
  snapshot: CompanyFinancialSnapshot
  integrityChecks: IntegrityCheckResult[]
  ratios: FinancialRatios
  summary?: FinancialAnalysisSummary | null
  riskDiagnostics?: RiskDiagnostics | null
  projections?: ProjectionOutput | null
  valuation?: ValuationOutput | null
  warnings: string[]
}
