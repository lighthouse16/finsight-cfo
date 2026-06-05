from fastapi import APIRouter
from app.models.advisory import (
    HardGatePrecheckResult,
    UnifiedRiskScoreResult,
    StressTestingResponse,
    FacilityStructuringResponse
)
from app.routes.financials import get_demo_analysis
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
from app.services.advisory.facility_structuring_engine import build_facility_structuring

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

@router.get("/demo-stress-tests", response_model=StressTestingResponse)
def get_demo_stress_tests():
    """
    Consumes the financial analysis output and unified risk score to perform
    context-only deterministic scenario stress testing.
    """
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    return build_demo_stress_tests(analysis, risk_score)

@router.get("/demo-facility-structures", response_model=FacilityStructuringResponse)
def get_demo_facility_structures():
    """
    Consumes financial analysis, precheck, risk score, and stress tests to construct
    candidate facility structures with cost and fit estimations.
    """
    analysis = get_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    return build_facility_structuring(analysis, precheck, risk_score, stress_tests)

