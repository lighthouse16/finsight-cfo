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



