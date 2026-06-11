from typing import Optional, Union, Any
from fastapi import APIRouter, HTTPException, Header
from pydantic import ValidationError

from app.models.advisory import (
    HardGatePrecheckResult,
    UnifiedRiskScoreResult,
    CreditScoringResult,
    StressTestingResponse,
    FacilityStructuringResponse,
    AdvisoryBlueprintResponse
)
from app.models.financials import FinancialAnalysisResponse, CompanyFinancialSnapshot
from app.routes.financials import get_demo_analysis
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.services.advisory.credit_scoring_engine import build_credit_scoring_result
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
from app.services.advisory.facility_structuring_engine import build_facility_structuring
from app.services.advisory.blueprint_engine import build_advisory_blueprint

router = APIRouter()


def _get_active_or_demo_analysis(
    x_workspace_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> Any:
    """
    Return the active Data Room preview/workspace analysis if available,
    otherwise fall back to the demo company analysis.
    """
    return get_demo_analysis(x_workspace_id=x_workspace_id, workspace_id=workspace_id)


@router.get("/demo-precheck")
def get_demo_precheck(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consumes the active financial analysis output and returns a structured,
    explainable, context-only eligibility/risk precheck for advisory readiness.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_advisory_precheck_run
        run = execute_advisory_precheck_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    return build_hard_gate_precheck(analysis)


@router.get("/demo-risk-score")
def get_demo_risk_score(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consumes the active financial analysis output and advisory precheck to produce a
    unified, context-only risk scoring foundation for advisory readiness.
    """
    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    return build_unified_risk_score(analysis, precheck)


@router.get("/credit-score")
def get_credit_score(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Produces a finance-first, explainable PD / credit scoring foundation using
    ratios, receivables diagnostics, FCFF/valuation context, and stress overlay.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_credit_score_run
        run = execute_credit_score_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    return build_credit_scoring_result(analysis)


@router.get("/demo-credit-score")
def get_demo_credit_score(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Backward-compatible demo alias for /credit-score.
    """
    return get_credit_score(x_workspace_id=x_workspace_id, workspace_id=workspace_id)


@router.get("/demo-stress-tests")
def get_demo_stress_tests(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consumes the active financial analysis output and unified risk score to perform
    context-only deterministic scenario stress testing.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_stress_test_run
        run = execute_stress_test_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    return build_demo_stress_tests(analysis, risk_score)


@router.get("/demo-facility-structures")
def get_demo_facility_structures(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consumes financial analysis, precheck, risk score, and stress tests to construct
    candidate facility structures with cost and fit estimations.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_facility_structuring_run
        run = execute_facility_structuring_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    return build_facility_structuring(analysis, precheck, risk_score, stress_tests)


@router.get("/demo-blueprint")
def get_demo_blueprint(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
):
    """
    Consolidates the financial analysis, precheck, risk score, stress tests, and
    facility structuring outputs into a deterministic advisor-ready briefing.
    """
    ws_id = workspace_id or x_workspace_id
    if ws_id:
        from app.services.analysis_run_service import execute_advisory_blueprint_run
        run = execute_advisory_blueprint_run(ws_id)
        res = dict(run.results)
        res["run_metadata"] = {
            "id": run.id,
            "runId": run.id,
            "snapshotId": run.snapshot_id,
            "status": run.status,
            "runType": run.run_type,
            "createdAt": run.created_at,
            "logicVersion": run.logic_version,
            "warningsCount": len(run.warnings)
        }
        return res

    analysis = _get_active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    return build_advisory_blueprint(analysis, precheck, risk_score, stress_tests, facility_structuring)
