from fastapi import APIRouter
from app.models.advisory import HardGatePrecheckResult, UnifiedRiskScoreResult
from app.routes.financials import get_demo_analysis
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score

router = APIRouter()

@router.get("/demo-precheck", response_model=HardGatePrecheckResult)
def get_demo_precheck():
    """
    Consumes the financial analysis output and returns a structured,
    explainable, context-only eligibility/risk precheck for advisory readiness.
    """
    analysis = get_demo_analysis()
    return build_hard_gate_precheck(analysis)

@router.get("/demo-risk-score", response_model=UnifiedRiskScoreResult)
def get_demo_risk_score():
    """
    Consumes the financial analysis output and advisory precheck to produce a
    unified, context-only risk scoring foundation for advisory readiness.
    """
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    return build_unified_risk_score(analysis, precheck)
