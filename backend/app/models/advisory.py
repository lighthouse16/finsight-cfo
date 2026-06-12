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

RiskScoreBand = Literal["low", "moderate", "elevated", "high", "unavailable"]

class RiskScoreFactor(AdvisoryBaseModel):
    key: str
    label: str
    score_impact: int
    band: str
    message: str
    evidence: str
    source: str
    weight: float
    warnings: List[str] = Field(default_factory=list)

class UnifiedRiskScoreResult(AdvisoryBaseModel):
    company_id: str
    company_name: str
    score: int
    band: RiskScoreBand
    score_scale: str = "0 to 100"
    factors: List[RiskScoreFactor]
    strengths: List[str]
    constraints: List[str]
    watch_items: List[str]
    hard_gate_status: str
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)


# Finance-first PD / Credit Scoring Models
PdRiskTier = Literal["low", "moderate", "elevated", "high", "unavailable"]
FundingReadinessBand = Literal["ready_context", "bank_review_ready", "needs_review", "not_ready", "unavailable"]

class CreditScoreFactor(AdvisoryBaseModel):
    key: str
    label: str
    raw_score: int
    weighted_score: float
    weight: float
    band: str
    message: str
    evidence: str
    source: str
    positive_driver: Optional[str] = None
    risk_driver: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

class CreditScoringResult(AdvisoryBaseModel):
    company_id: str
    company_name: str
    composite_score: int
    score_scale: str = "0 to 100"
    risk_tier: PdRiskTier
    pd_proxy_band: str
    funding_readiness: FundingReadinessBand
    factors: List[CreditScoreFactor]
    positive_drivers: List[str] = Field(default_factory=list)
    risk_drivers: List[str] = Field(default_factory=list)
    hard_constraints: List[str] = Field(default_factory=list)
    next_data_needed: List[str] = Field(default_factory=list)
    methodology_label: str
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)
    calibration_status: Optional[str] = "indicative_readiness_index"

class StressScenarioAssumption(AdvisoryBaseModel):
    scenario_key: str
    label: str
    scenario_type: str
    description: str
    parameters: dict
    source: str
    warnings: List[str] = Field(default_factory=list)

class StressScenarioImpact(AdvisoryBaseModel):
    metric: str
    base_value: float
    stressed_value: float
    absolute_change: float
    percent_change: Optional[float] = None
    unit: Optional[str] = None
    interpretation: str
    warnings: List[str] = Field(default_factory=list)

class StressScenarioResult(AdvisoryBaseModel):
    scenario_key: str
    label: str
    scenario_type: str
    severity: str  # low | moderate | elevated | high | unavailable
    assumptions: List[StressScenarioAssumption]
    impacts: List[StressScenarioImpact]
    band_movement: Optional[str] = None
    key_takeaway: str
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str

class StressTestingResponse(AdvisoryBaseModel):
    company_id: str
    company_name: str
    base_summary_band: str
    base_risk_score: int
    scenarios: List[StressScenarioResult]
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)


# Phase 3.4 Facility Structuring Models

from enum import Enum

class FacilityType(str, Enum):
    revolving_working_capital = "revolving_working_capital"
    trade_finance = "trade_finance"
    receivables_finance = "receivables_finance"
    term_loan = "term_loan"
    fx_hedging_context = "fx_hedging_context"
    liquidity_buffer = "liquidity_buffer"

class FacilityFitAssessment(AdvisoryBaseModel):
    fit_band: Literal["strong", "adequate", "watch", "constrained", "unavailable"]
    rationale: str
    constraints: List[str] = Field(default_factory=list)
    watch_items: List[str] = Field(default_factory=list)
    required_data: List[str] = Field(default_factory=list)

class FacilityCandidate(AdvisoryBaseModel):
    facility_key: str
    facility_type: FacilityType
    label: str
    estimated_limit: Optional[float] = None
    currency: str = "HKD"
    estimated_pricing_bps: Optional[int] = None
    estimated_annual_cost: Optional[float] = None
    tenor_months: Optional[int] = None
    repayment_profile: str
    purpose: str
    fit_assessment: FacilityFitAssessment
    supporting_signals: List[str] = Field(default_factory=list)
    sensitivity_notes: str
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str

class FacilityStructuringResponse(AdvisoryBaseModel):
    company_id: str
    company_name: str
    base_risk_score: int
    base_risk_band: RiskScoreBand
    hard_gate_status: HardGateStatus
    candidates: List[FacilityCandidate]
    preferred_candidate_keys: List[str]
    constraints: List[str] = Field(default_factory=list)
    next_data_needed: List[str] = Field(default_factory=list)
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)


# Phase 3.5 Advisory Blueprint Models

BlueprintReadinessStatus = Literal[
    "ready_context",
    "watch_context",
    "constrained_context",
    "unavailable_context",
]

class AdvisoryBriefSection(AdvisoryBaseModel):
    section_key: str
    title: str
    summary: str
    signals: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    next_data_needed: List[str] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class AdvisoryBlueprintAction(AdvisoryBaseModel):
    action_key: str
    label: str
    priority: Literal["high", "medium", "low"]
    rationale: str
    owner_hint: str
    required_data: List[str] = Field(default_factory=list)
    related_candidate_keys: List[str] = Field(default_factory=list)

class BlueprintKeySections(AdvisoryBaseModel):
    financial_posture: AdvisoryBriefSection
    advisory_readiness: AdvisoryBriefSection
    stress_context: AdvisoryBriefSection
    candidate_structures: AdvisoryBriefSection
    data_readiness: AdvisoryBriefSection

class AdvisoryBlueprintResponse(AdvisoryBaseModel):
    company_id: str
    company_name: str
    blueprint_status: BlueprintReadinessStatus
    executive_brief: str
    key_sections: BlueprintKeySections
    recommended_actions: List[AdvisoryBlueprintAction]
    source_outputs: List[str] = Field(default_factory=list)
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)


# Phase 3 CDI Mock Models

class CdiInvoiceRecord(AdvisoryBaseModel):
    invoice_id: str
    buyer_name: str
    amount: float
    currency: str
    status: str
    expected_payment_date: str

class CdiMockResponse(AdvisoryBaseModel):
    consent_token: Optional[str] = None
    provider_name: str
    invoices: List[CdiInvoiceRecord] = Field(default_factory=list)
    delivered_invoice_total: float
    in_transit_invoice_total: float
    alternative_collateral_hkd: float
    disclaimer: str
    warnings: List[str] = Field(default_factory=list)

class CdiConsentRequest(AdvisoryBaseModel):
    company_id: str
    consent_granted: bool

class CdiConsentResponse(AdvisoryBaseModel):
    consent_token: Optional[str] = None
    status: str
    message: str

# Phase 3 PD Engine Models

class PdFactorContribution(AdvisoryBaseModel):
    factor: str
    value: float
    contribution: float

class PdEstimateResponse(AdvisoryBaseModel):
    company_id: str
    z_score: float
    probability_default: float
    tier: str
    score: int
    factor_contributions: List[PdFactorContribution]
    disclaimer: str
    calibration_status: Optional[str] = "indicative_readiness_index"

# Phase 3 BoCHK Stress Testing Models

class BochkStressRecommendation(AdvisoryBaseModel):
    action: str
    rationale: str

class BochkStressTestResponse(AdvisoryBaseModel):
    company_id: str
    base_dscr: float
    stressed_dscr: float
    shock_bps: int
    status: str
    recommendations: List[BochkStressRecommendation]
    disclaimer: str

# Phase 3 Loan Structuring Models

class LoanFacilityRecommendation(AdvisoryBaseModel):
    facility: str
    amount: float
    interest_rate_bps: int
    annual_cost: float
    reason: str

class LoanStructuringResponse(AdvisoryBaseModel):
    company_id: str
    requested_amount_hkd: float
    recommended_facilities: List[LoanFacilityRecommendation]
    total_estimated_cost: float
    weighted_average_cost_bps: int
    constraints_passed: List[str]
    constraints_failed: List[str]
    recommendation_summary: str
    disclaimer: str

# Phase 3 Funding Blueprint Models

class FundingBlueprintRequest(AdvisoryBaseModel):
    company_id: Optional[str] = None
    requested_amount_hkd: float = 10000000.0
    consent_granted: bool = False
    scenario_shock_bps: int = 150

class BlueprintSectionText(AdvisoryBaseModel):
    title: str
    content: str

class FundingBlueprintResponse(AdvisoryBaseModel):
    company_id: str
    hard_gate_summary: str
    unified_risk_score: int
    unified_risk_tier: str
    cdi_data: Optional[CdiMockResponse] = None
    pd_estimate: PdEstimateResponse
    stress_test: BochkStressTestResponse
    loan_structure: LoanStructuringResponse
    blueprint_sections: List[BlueprintSectionText]
    disclaimers: List[str]


# AI CFO Chat Models
class AdvisoryChatSource(AdvisoryBaseModel):
    """A cited source in a chat response."""
    title: str
    snippet: Optional[str] = None
    document_id: Optional[str] = None


class AdvisoryChatRequest(AdvisoryBaseModel):
    """Request payload for the AI CFO chat endpoint."""
    question: str
    workspace_id: Optional[str] = None


class AdvisoryChatResponse(AdvisoryBaseModel):
    """Response from the AI CFO chat endpoint."""
    ai_mode: str = "deterministic_fallback"
    answer: str
    sources: List[AdvisoryChatSource] = Field(default_factory=list)
    disclaimer: str = ""
    warnings: List[str] = Field(default_factory=list)

