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
