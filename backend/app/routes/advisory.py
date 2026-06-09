from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.models.advisory import (
    HardGatePrecheckResult,
    UnifiedRiskScoreResult,
    StressTestingResponse,
    FacilityStructuringResponse,
    AdvisoryBlueprintResponse
)
from app.models.financials import FinancialAnalysisResponse, CompanyFinancialSnapshot
from app.routes.data_room import get_active_workspace_preview_context
from app.routes.financials import get_demo_analysis, _build_financial_analysis_response
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
from app.services.advisory.facility_structuring_engine import build_facility_structuring
from app.services.advisory.blueprint_engine import build_advisory_blueprint

router = APIRouter()


def _get_active_or_demo_analysis() -> FinancialAnalysisResponse:
    """
    Return the active Data Room preview analysis when a workspace snapshot has
    been activated; otherwise fall back to the demo company analysis.

    This keeps the hackathon demo safe and deterministic while allowing the
    end-to-end BOCHK workflow to run from uploaded statements -> financial
    analysis -> advisory blueprint.
    """
    context = get_active_workspace_preview_context()
    if context is None:
        return get_demo_analysis()

    try:
        snapshot = CompanyFinancialSnapshot.model_validate(context.snapshotPreview)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Active workspace preview context is incomplete or malformed.",
                "source": "data_room_workspace_preview",
                "previewOnly": True,
                "errors": exc.errors(),
            },
        ) from exc

    metadata = dict(snapshot.metadata or {})
    metadata.update(
        {
            "mode": "preview",
            "source": "data_room_workspace_preview",
            "preview_only": True,
            "activated_at": context.activatedAt,
            "advisory_pipeline_source": "active_data_room_preview",
        }
    )
    snapshot.metadata = metadata

    preview_warnings = [
        "Advisory pipeline is using temporary in-memory Data Room workspace preview context. Production analysis was not updated.",
        *context.warnings,
    ]
    return _build_financial_analysis_response(snapshot, preview_warnings)


@router.get("/demo-precheck", response_model=HardGatePrecheckResult)
def get_demo_precheck():
    """
    Consumes the active financial analysis output and returns a structured,
    explainable, context-only eligibility/risk precheck for advisory readiness.
    """
    analysis = _get_active_or_demo_analysis()
    return build_hard_gate_precheck(analysis)


@router.get("/demo-risk-score", response_model=UnifiedRiskScoreResult)
def get_demo_risk_score():
    """
    Consumes the active financial analysis output and advisory precheck to produce a
    unified, context-only risk scoring foundation for advisory readiness.
    """
    analysis = _get_active_or_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    return build_unified_risk_score(analysis, precheck)


@router.get("/demo-stress-tests", response_model=StressTestingResponse)
def get_demo_stress_tests():
    """
    Consumes the active financial analysis output and unified risk score to perform
    context-only deterministic scenario stress testing.
    """
    analysis = _get_active_or_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    return build_demo_stress_tests(analysis, risk_score)


@router.get("/demo-facility-structures", response_model=FacilityStructuringResponse)
def get_demo_facility_structures():
    """
    Consumes financial analysis, precheck, risk score, and stress tests to construct
    candidate facility structures with cost and fit estimations.
    """
    analysis = _get_active_or_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    return build_facility_structuring(analysis, precheck, risk_score, stress_tests)


@router.get("/demo-blueprint", response_model=AdvisoryBlueprintResponse)
def get_demo_blueprint():
    """
    Consolidates the financial analysis, precheck, risk score, stress tests, and
    facility structuring outputs into a deterministic advisor-ready briefing.
    """
    analysis = _get_active_or_demo_analysis()
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    return build_advisory_blueprint(analysis, precheck, risk_score, stress_tests, facility_structuring)
