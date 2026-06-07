from typing import List, Literal, Optional
from pydantic import BaseModel, Field

DataRoomRecordStatus = Literal["demo_available", "missing", "connected", "optional"]
DataRoomRecordCategory = Literal[
    "Core Financials",
    "Debt & Credit",
    "Commercial & Trade",
    "Risk & Treasury",
]
DataRoomRequirement = Literal[
    "valuation",
    "risk diagnostics",
    "stress testing",
    "facility structuring",
]
DataRoomActionLabel = Literal["Upload", "Connect", "Review", "Coming soon"]


class DataRoomRecord(BaseModel):
    id: str
    name: str
    category: DataRoomRecordCategory
    purpose: str
    status: DataRoomRecordStatus
    requiredFor: List[DataRoomRequirement] = Field(default_factory=list)
    lastUpdated: Optional[str] = None
    actionLabel: DataRoomActionLabel


class DataRoomDependency(BaseModel):
    recordGroup: str
    outputs: List[str] = Field(default_factory=list)


class DataRoomReadinessSummary(BaseModel):
    totalRequired: int
    connectedRequired: int
    missingRequired: int
    readinessPercentage: int
    dataMode: Literal["demo_workspace", "connected", "seed_only"]


class DataRoomResponse(BaseModel):
    records: List[DataRoomRecord]
    dependencies: List[DataRoomDependency]
    summary: DataRoomReadinessSummary
