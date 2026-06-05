from fastapi import APIRouter
from app.models.advisory import HardGatePrecheckResult
from app.routes.financials import get_demo_analysis
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck

router = APIRouter()

@router.get("/demo-precheck", response_model=HardGatePrecheckResult)
def get_demo_precheck():
    """
    Consumes the financial analysis output and returns a structured,
    explainable, context-only eligibility/risk precheck for advisory readiness.
    """
    analysis = get_demo_analysis()
    return build_hard_gate_precheck(analysis)
