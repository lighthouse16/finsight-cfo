from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

FreshnessStatus = Literal["Daily", "Monthly", "Delayed", "Workspace"]
SourceStatus = Literal[
    "connected", 
    "seed_data", 
    "requires_backend", 
    "requires_company_data", 
    "unavailable", 
    "stale"
]
SignalSeverity = Literal["Neutral", "Caution", "High", "Positive"]
Trend = Literal["up", "down", "flat", "unknown"]
Unit = Literal["percent", "bps", "index"]
TimingBand = Literal["favorable", "neutral", "cautious"]
TimingTrendSignal = Literal["easing", "stable", "tightening", "unavailable"]
LiquidityTimingSignal = Literal["favorable", "neutral", "cautious", "unavailable"]
CalendarRedFlag = Literal["none", "month_end", "half_year_end", "year_end"]

class SourceStatusItem(BaseModel):
    id: str
    label: str
    status: SourceStatus
    provider: Optional[str] = None
    lastUpdatedAt: Optional[str] = None

class SourceInfo(BaseModel):
    provider: str
    name: str
    url: Optional[str] = None

class ResponseMetadata(BaseModel):
    asOf: Optional[str] = None
    fetchedAt: str
    freshness: FreshnessStatus
    isStale: bool
    source: SourceInfo
    warnings: List[str] = Field(default_factory=list)

class RateSnapshot(BaseModel):
    id: str
    label: str
    tenor: str
    value: Optional[float] = None
    unit: Unit
    displayValue: str
    changeBasisPoints: Optional[float] = None
    trend: Trend
    context: str
    sourceTimestamp: Optional[str] = None

class LiquidityEvent(BaseModel):
    id: str
    date: str
    event: str
    impact: str
    severity: SignalSeverity

class RatesLiquidityResponse(BaseModel):
    metadata: ResponseMetadata
    rates: List[RateSnapshot]
    liquidityEvents: List[LiquidityEvent]
    sourceStatus: List[SourceStatusItem]


class TimingSignalComponent(BaseModel):
    band: str
    label: str
    value: Optional[str] = None
    explanation: str


class TimingSignalProvenance(BaseModel):
    source: str
    provider: str
    asOf: Optional[str] = None
    freshness: FreshnessStatus


class TimingSignalResponse(BaseModel):
    mode: Literal["context_only"] = "context_only"
    hiborLevelBand: TimingBand
    hiborTrendSignal: TimingTrendSignal
    liquidityTimingSignal: LiquidityTimingSignal
    calendarRedFlag: CalendarRedFlag
    goldenTimingBand: TimingBand
    explanation: str
    components: List[TimingSignalComponent]
    provenance: TimingSignalProvenance
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str


IndustryHealthBand = Literal["resilient", "stable", "watch", "stressed", "unavailable"]
DemandSignal = Literal["expanding", "stable", "softening", "unavailable"]
MarginSignal = Literal["expanding", "stable", "compressing", "unavailable"]
WorkingCapitalSignal = Literal["healthy", "watch", "stressed", "unavailable"]
BenchmarkSignal = Literal["favorable", "neutral", "cautious", "unavailable"]


class IndustryHealthComponent(BaseModel):
    signal: str
    label: str
    band: str
    value: Optional[str] = None
    explanation: str


class IndustryHealthProvenance(BaseModel):
    source: str
    provider: str
    asOf: Optional[str] = None
    freshness: FreshnessStatus


class IndustryHealthResponse(BaseModel):
    mode: Literal["context_only"] = "context_only"
    sectorName: str
    industryHealthBand: IndustryHealthBand
    demandSignal: DemandSignal
    marginSignal: MarginSignal
    workingCapitalSignal: WorkingCapitalSignal
    benchmarkSignal: BenchmarkSignal
    explanation: str
    components: List[IndustryHealthComponent]
    provenance: IndustryHealthProvenance
    source: IndustryHealthProvenance
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str


FundingChannelKey = Literal["working_capital_line", "receivables_financing", "trade_finance_lc", "term_loan", "fx_hedging_context"]
FundingFitBand = Literal["strong_fit", "moderate_fit", "watch_fit"]
FundingRankingBand = Literal["working_capital_priority", "trade_cycle_priority", "balance_sheet_review", "risk_context_priority"]


class FundingChannelComponent(BaseModel):
    signal: str
    label: str
    band: str
    explanation: str


class FundingChannelItem(BaseModel):
    key: FundingChannelKey
    label: str
    rank: int
    fitBand: FundingFitBand
    score: int
    useCase: str
    rationale: str
    supportingSignals: List[str] = Field(default_factory=list)
    source: str
    constraints: List[str] = Field(default_factory=list)


class FundingChannelProvenance(BaseModel):
    source: str
    provider: str
    asOf: Optional[str] = None
    freshness: FreshnessStatus


class FundingCompanyContext(BaseModel):
    companyName: str
    sector: str
    geography: str
    dataMode: str
    dscr: Optional[float] = None
    floatingRateExposure: Optional[str] = None
    workingCapitalGap: Optional[str] = None
    dsoWatch: bool = False
    fxExposure: bool = False
    importCostStress: bool = False


class FundingChannelRankingResponse(BaseModel):
    mode: Literal["context_only"] = "context_only"
    companyContext: FundingCompanyContext
    rankingBand: FundingRankingBand
    channels: List[FundingChannelItem]
    topChannelKey: FundingChannelKey
    explanation: str
    components: List[FundingChannelComponent]
    provenance: FundingChannelProvenance
    source: FundingChannelProvenance
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str


CrossBorderSpreadBand = Literal["hkd_advantage", "rmb_advantage", "balanced", "unavailable"]
CrossBorderFxRiskBand = Literal["low", "moderate", "elevated", "unavailable"]
CrossBorderReviewBand = Literal["worth_reviewing", "monitor", "not_priority", "unavailable"]


class CrossBorderFundingReference(BaseModel):
    label: str
    currency: str
    value: Optional[float] = None
    unit: Unit
    displayValue: str
    source: str


class CrossBorderFundingComponent(BaseModel):
    label: str
    value: Optional[str] = None
    signal: str
    explanation: str


class CrossBorderFundingProvenance(BaseModel):
    source: str
    provider: str
    asOf: Optional[str] = None
    freshness: FreshnessStatus


class CrossBorderFundingContextResponse(BaseModel):
    mode: Literal["context_only"] = "context_only"
    baseCurrency: Literal["HKD"] = "HKD"
    comparisonCurrency: Literal["RMB"] = "RMB"
    hkdFundingReference: CrossBorderFundingReference
    rmbFundingReference: CrossBorderFundingReference
    spreadBps: Optional[float] = None
    spreadBand: CrossBorderSpreadBand
    fxRiskBand: CrossBorderFxRiskBand
    crossBorderReviewBand: CrossBorderReviewBand
    explanation: str
    components: List[CrossBorderFundingComponent]
    provenance: CrossBorderFundingProvenance
    source: CrossBorderFundingProvenance
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str


class MarketWatchError(BaseModel):
    code: str
    message: str
    statusCode: int
    source: Optional[str] = None
    retryable: bool
    fallbackUsed: bool
    details: Optional[dict] = None

class FxPair(BaseModel):
    id: str
    pair: str
    value: Optional[float] = None
    unit: Literal["price", "percent"]
    displayValue: str
    trend: Trend
    changePips: Optional[float] = None
    context: str
    sourceTimestamp: Optional[str] = None

class GbaFundingSignal(BaseModel):
    id: str
    title: str
    description: str
    severity: SignalSeverity

class ExposureNote(BaseModel):
    id: str
    category: str
    note: str
    severity: SignalSeverity

class FxGbaResponse(BaseModel):
    metadata: ResponseMetadata
    fxPairs: List[FxPair]
    gbaFundingSignal: List[GbaFundingSignal]
    exposureNotes: List[ExposureNote]
    sourceStatus: List[SourceStatusItem]


class SelectedSector(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    geography: str
    description: str


class SectorHealthComponent(BaseModel):
    label: str
    value: Optional[float] = None
    unit: Literal["index", "percent", "text"]
    displayValue: str
    context: str


class SectorHealthComponents(BaseModel):
    pmi: Optional[SectorHealthComponent] = None
    exportGrowth: Optional[SectorHealthComponent] = None
    industrialProduction: Optional[SectorHealthComponent] = None
    marginContext: Optional[SectorHealthComponent] = None


class SectorHealth(BaseModel):
    score: Optional[float] = None
    label: str
    severity: SignalSeverity
    components: SectorHealthComponents


class SectorBenchmark(BaseModel):
    id: str
    label: str
    value: Optional[float] = None
    unit: Literal["days", "percent", "ratio", "index"]
    displayValue: str
    comparison: str
    context: str
    severity: SignalSeverity
    sourceTimestamp: Optional[str] = None


class SectorWatchSignal(BaseModel):
    id: str
    title: str
    description: str
    affectedArea: str
    severity: SignalSeverity


class SectorBenchmarksResponse(BaseModel):
    metadata: ResponseMetadata
    selectedSector: SelectedSector
    sectorHealth: SectorHealth
    benchmarks: List[SectorBenchmark]
    watchSignals: List[SectorWatchSignal]
    sourceStatus: List[SourceStatusItem]


class CommodityExposure(BaseModel):
    id: str
    commodity: str
    category: str
    value: Optional[float] = None
    unit: Literal["percent", "index", "price", "text"]
    displayValue: str
    trend: Trend
    severity: SignalSeverity
    exposedSectors: List[str]
    marginContext: str
    sourceTimestamp: Optional[str] = None


class MarginPressureSignal(BaseModel):
    id: str
    label: str
    severity: SignalSeverity
    description: str
    affectedArea: str
    requiresCompanyData: bool


class CommodityWatchSignal(BaseModel):
    id: str
    title: str
    description: str
    affectedArea: str
    severity: SignalSeverity


class CommoditiesResponse(BaseModel):
    metadata: ResponseMetadata
    selectedSector: SelectedSector
    commodityExposures: List[CommodityExposure]
    marginPressureSignal: List[MarginPressureSignal]
    watchSignals: List[CommodityWatchSignal]
    sourceStatus: List[SourceStatusItem]


ShockType = Literal["rate", "fx", "commodity", "receivables", "liquidity"]
ScenarioStatus = Literal["context_only", "requires_company_data", "ready_for_model"]


class WorkspaceContext(BaseModel):
    id: str
    companyLabel: str
    sector: str
    geography: str
    description: str


class StressScenario(BaseModel):
    id: str
    title: str
    shockType: ShockType
    severity: SignalSeverity
    affectedArea: str
    description: str
    cfoQuestion: str
    requiresCompanyData: bool
    requiredDataIds: List[str] = Field(default_factory=list)
    status: ScenarioStatus
    sourceTimestamp: Optional[str] = None


class RequiredDataItem(BaseModel):
    id: str
    label: str
    status: SourceStatus
    description: str


class StressWatchSignal(BaseModel):
    id: str
    title: str
    description: str
    affectedArea: str
    severity: SignalSeverity


class StressSignalsResponse(BaseModel):
    metadata: ResponseMetadata
    workspaceContext: WorkspaceContext
    scenarios: List[StressScenario]
    requiredData: List[RequiredDataItem]
    watchSignals: List[StressWatchSignal]
    sourceStatus: List[SourceStatusItem]


class ConsolidatedSourceStatusItem(BaseModel):
    id: str
    label: str
    status: SourceStatus
    provider: Optional[str] = None
    freshness: Optional[str] = None
    lastUpdatedAt: Optional[str] = None
    message: Optional[str] = None


class ConsolidatedSourceStatusResponse(BaseModel):
    sources: List[ConsolidatedSourceStatusItem]


class RefreshRequest(BaseModel):
    scope: Optional[Literal[
        "overview", 
        "rates-liquidity", 
        "fx-gba", 
        "sector-benchmarks", 
        "commodities", 
        "stress-signals", 
        "all"
    ]] = "all"


class RefreshResponse(BaseModel):
    status: str
    message: str
    refreshedScope: str
    sources: List[ConsolidatedSourceStatusItem]


class ConnectedRecord(BaseModel):
    id: str
    label: str
    status: str  # connected, partial, missing


class CompanyProfile(BaseModel):
    companyName: str
    sector: str
    geography: str
    revenueTtmHkd: int
    cashBalanceHkd: int
    receivablesHkd: int
    payablesHkd: int
    inventoryHkd: int
    dsoDays: int
    dpoDays: int
    inventoryDays: int
    grossMarginPercent: float
    floatingRateDebtHkd: int
    monthlyDebtServiceHkd: int
    cnySupplierPayablesPercent: int
    usdImportCostPercent: int
    topCustomerConcentrationPercent: int
    workingCapitalGapHkd: int
    connectedRecords: List[ConnectedRecord]


class CompanyExposure(BaseModel):
    id: str
    category: str
    label: str
    value: str
    severity: SignalSeverity
    context: str


class CompanyContextResponse(BaseModel):
    profile: CompanyProfile
    exposures: List[CompanyExposure]
    dataMode: str  # "demo_workspace", "connected", "seed_only"




