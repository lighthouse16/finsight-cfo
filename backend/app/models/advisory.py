from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class AdvisoryBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

HardGateStatus = Literal["pass", "watch", "fail", "unavailable"]
HardGateSeverity = Literal["low", "medium", "high"]

class HardGateCheck(AdvisoryBaseModel):
    key: str
    label: str
    status: HardGateStatus
    message: str
    evidence: str
    source: str
    severity: HardGateSeverity
    required_action: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

class HardGatePrecheckResult(AdvisoryBaseModel):
    company_id: str
    company_name: str
    overall_status: HardGateStatus
    checks: List[HardGateCheck]
    pass_count: int
    watch_count: int
    fail_count: int
    unavailable_count: int
    constraints: List[str]
    next_data_needed: List[str]
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)
