from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

ConsentStatus = Literal["created", "authorized", "expired", "revoked"]
ConsentScope = Literal[
    "bank_transactions",
    "trade_receivables",
    "tax_filing_summary",
    "payroll_mpf_signal",
    "credit_bureau_summary",
]


class CdiConsentCreateRequest(BaseModel):
    company_id: str = Field(..., alias="companyId")
    company_name: str = Field(..., alias="companyName")
    requested_scopes: list[ConsentScope] = Field(default_factory=list, alias="requestedScopes")
    callback_url: str | None = Field(None, alias="callbackUrl")


class CdiConsentSession(BaseModel):
    consent_id: str = Field(..., alias="consentId")
    company_id: str = Field(..., alias="companyId")
    company_name: str = Field(..., alias="companyName")
    status: ConsentStatus
    requested_scopes: list[ConsentScope] = Field(..., alias="requestedScopes")
    authorization_url: str = Field(..., alias="authorizationUrl")
    created_at: str = Field(..., alias="createdAt")
    expires_at: str = Field(..., alias="expiresAt")
    disclaimer: str


class CdiCashflowSignal(BaseModel):
    average_monthly_inflow: float = Field(..., alias="averageMonthlyInflow")
    average_monthly_outflow: float = Field(..., alias="averageMonthlyOutflow")
    net_cashflow_trend: Literal["improving", "stable", "deteriorating"] = Field(..., alias="netCashflowTrend")
    volatility_band: Literal["low", "moderate", "high"] = Field(..., alias="volatilityBand")
    bounced_payment_count_6m: int = Field(..., alias="bouncedPaymentCount6m")


class CdiReceivablesSignal(BaseModel):
    verified_invoice_value: float = Field(..., alias="verifiedInvoiceValue")
    eligible_invoice_value: float = Field(..., alias="eligibleInvoiceValue")
    top_buyer_concentration: float = Field(..., alias="topBuyerConcentration")
    average_days_to_collect: float = Field(..., alias="averageDaysToCollect")
    digital_collateral_band: Literal["strong", "moderate", "watch"] = Field(..., alias="digitalCollateralBand")


class CdiCreditBureauSignal(BaseModel):
    repayment_delinquency_count_12m: int = Field(..., alias="repaymentDelinquencyCount12m")
    bureau_band: Literal["clear", "watch", "adverse"] = Field(..., alias="bureauBand")
    trade_reference_count: int = Field(..., alias="tradeReferenceCount")


class CdiMockDataResponse(BaseModel):
    consent_id: str = Field(..., alias="consentId")
    company_id: str = Field(..., alias="companyId")
    company_name: str = Field(..., alias="companyName")
    status: ConsentStatus
    source: str
    generated_at: str = Field(..., alias="generatedAt")
    cashflow_signal: CdiCashflowSignal = Field(..., alias="cashflowSignal")
    receivables_signal: CdiReceivablesSignal = Field(..., alias="receivablesSignal")
    credit_bureau_signal: CdiCreditBureauSignal = Field(..., alias="creditBureauSignal")
    funding_implications: list[str] = Field(..., alias="fundingImplications")
    risk_implications: list[str] = Field(..., alias="riskImplications")
    disclaimer: str


_consent_sessions: dict[str, CdiConsentSession] = {}

DEFAULT_SCOPES: list[ConsentScope] = [
    "bank_transactions",
    "trade_receivables",
    "credit_bureau_summary",
]

DISCLAIMER = (
    "Mock CDI data is generated for BOCHK challenge demonstration only. It is "
    "not real bureau, bank transaction, CDI, CCRA, MPF, tax, or customer data. "
    "Production use requires explicit consent, secure data exchange, audit logs, "
    "model governance, and PDPO/PIPL-aligned controls."
)


@router.post("/mock-consent", response_model=CdiConsentSession)
def create_mock_cdi_consent(payload: CdiConsentCreateRequest) -> CdiConsentSession:
    """Create a deterministic mock consent session for the trust-bridge demo."""
    requested_scopes = payload.requested_scopes or DEFAULT_SCOPES
    now = datetime.now(timezone.utc)
    consent_id = f"mock_cdi_{uuid4().hex[:12]}"
    session = CdiConsentSession(
        consentId=consent_id,
        companyId=payload.company_id,
        companyName=payload.company_name,
        status="authorized",
        requestedScopes=requested_scopes,
        authorizationUrl=f"https://mock-cdi.local/authorize/{consent_id}",
        createdAt=now.isoformat(),
        expiresAt=(now + timedelta(days=90)).isoformat(),
        disclaimer=DISCLAIMER,
    )
    _consent_sessions[consent_id] = session
    return session


@router.get("/mock-consent/{consent_id}", response_model=CdiConsentSession)
def get_mock_cdi_consent(consent_id: str) -> CdiConsentSession:
    session = _consent_sessions.get(consent_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Mock CDI consent session not found")
    return session


@router.get("/mock-data/{consent_id}", response_model=CdiMockDataResponse)
def get_mock_cdi_data(consent_id: str) -> CdiMockDataResponse:
    """Return mock consent-based CDI signals for credit/funding demonstration."""
    session = _consent_sessions.get(consent_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Mock CDI consent session not found")
    if session.status != "authorized":
        raise HTTPException(status_code=409, detail="Mock CDI consent is not authorized")

    generated_at = datetime.now(timezone.utc).isoformat()
    return CdiMockDataResponse(
        consentId=session.consent_id,
        companyId=session.company_id,
        companyName=session.company_name,
        status=session.status,
        source="mock_cdi_consent_gateway",
        generatedAt=generated_at,
        cashflowSignal=CdiCashflowSignal(
            averageMonthlyInflow=1_280_000,
            averageMonthlyOutflow=1_075_000,
            netCashflowTrend="stable",
            volatilityBand="moderate",
            bouncedPaymentCount6m=0,
        ),
        receivablesSignal=CdiReceivablesSignal(
            verifiedInvoiceValue=2_450_000,
            eligibleInvoiceValue=1_715_000,
            topBuyerConcentration=0.28,
            averageDaysToCollect=47.5,
            digitalCollateralBand="strong",
        ),
        creditBureauSignal=CdiCreditBureauSignal(
            repaymentDelinquencyCount12m=0,
            bureauBand="clear",
            tradeReferenceCount=8,
        ),
        fundingImplications=[
            "Verified invoice pool can support receivables-backed working-capital discussion.",
            "Stable bank-transaction inflows improve cash-flow verification for lender review.",
            "Clear mock bureau band reduces context-only red flags in the funding narrative.",
        ],
        riskImplications=[
            "Moderate cash-flow volatility still requires stress testing under higher HIBOR assumptions.",
            "Top buyer concentration should be reviewed before setting advance rates.",
        ],
        disclaimer=DISCLAIMER,
    )
