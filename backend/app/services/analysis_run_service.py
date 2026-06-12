import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError
from app.models.workspace import AnalysisRun
from app.storage.workspace_store import WorkspaceStore
from app.models.financials import CompanyFinancialSnapshot
from app.models.errors import raise_missing_workspace_error, raise_insufficient_data_error
from app.core.config import settings

def _resolve_snapshot(workspace_id: str, snapshot_id: Optional[str] = None) -> Tuple[CompanyFinancialSnapshot, str]:
    workspace = WorkspaceStore.get_workspace(workspace_id)
    if not workspace:
        raise_missing_workspace_error("WORKSPACE_DATA_NOT_FOUND")
    
    if snapshot_id:
        snapshot = WorkspaceStore.get_snapshot(snapshot_id)
    else:
        snapshot = WorkspaceStore.get_active_snapshot(workspace_id)
        
    if not snapshot:
        raise_missing_workspace_error("ACTIVE_SNAPSHOT_NOT_FOUND")
        
    try:
        snap_data = CompanyFinancialSnapshot(
            company_id=snapshot.workspace_id,
            company_name=workspace.company_name,
            reporting_period=snapshot.reporting_period,
            currency=snapshot.currency,
            income_statement=snapshot.income_statement,
            balance_sheet=snapshot.balance_sheet,
            cash_flow_statement=snapshot.cash_flow_statement,
            debt_schedule=snapshot.debt_schedule,
            receivables_aging=snapshot.receivables_aging,
            metadata=snapshot.metadata,
        )
        return snap_data, snapshot.id
    except ValidationError as exc:
        missing = []
        for err in exc.errors():
            loc_str = " -> ".join(str(l) for l in err.get("loc", []))
            missing.append(f"{loc_str}: {err.get('msg')}")
        raise_insufficient_data_error(missing)


def execute_financial_health_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.routes.financials import _build_financial_analysis_response
    response = _build_financial_analysis_response(snap_data)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_fh_{uuid.uuid4().hex[:8]}"
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="financial_health",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=response.model_dump(by_alias=True),
        warnings=response.warnings,
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="ratio_engine_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "financial_health_run",
        f"Executed financial health analysis run {run_id}"
    )
    return analysis_run


def execute_valuation_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.services.financials.ratio_engine import calculate_ratios
    from app.services.financials.projection_engine import build_default_projection_assumptions, calculate_projection
    from app.services.financials.valuation_engine import build_valuation_analysis
    
    ratios = calculate_ratios(snap_data)
    projection_assumptions = build_default_projection_assumptions(snap_data)
    projections = calculate_projection(snap_data, projection_assumptions)
    valuation = build_valuation_analysis(snap_data, ratios, projections)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_val_{uuid.uuid4().hex[:8]}"
    
    warnings = list(valuation.warnings or [])
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="valuation",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=valuation.model_dump(by_alias=True),
        warnings=warnings,
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="valuation_engine_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "valuation_run",
        f"Executed valuation analysis run {run_id}"
    )
    return analysis_run


def execute_advisory_precheck_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.routes.financials import _build_financial_analysis_response
    from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
    
    analysis = _build_financial_analysis_response(snap_data)
    precheck = build_hard_gate_precheck(analysis)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_precheck_{uuid.uuid4().hex[:8]}"
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="advisory_precheck",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=precheck.model_dump(by_alias=True),
        warnings=[],
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="hard_gate_engine_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "advisory_precheck_run",
        f"Executed advisory precheck analysis run {run_id}"
    )
    return analysis_run


def execute_credit_score_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.routes.financials import _build_financial_analysis_response
    from app.services.advisory.credit_scoring_engine import build_credit_scoring_result
    
    analysis = _build_financial_analysis_response(snap_data)
    credit_score = build_credit_scoring_result(analysis)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_cs_{uuid.uuid4().hex[:8]}"
    
    warnings = list(credit_score.warnings or [])
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="credit_score",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=credit_score.model_dump(by_alias=True),
        warnings=warnings,
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="credit_scoring_engine_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "credit_score_run",
        f"Executed credit score analysis run {run_id}"
    )
    return analysis_run


def execute_stress_test_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.routes.financials import _build_financial_analysis_response
    from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
    from app.services.advisory.risk_score_engine import build_unified_risk_score
    from app.services.advisory.stress_testing_engine import build_demo_stress_tests
    
    analysis = _build_financial_analysis_response(snap_data)
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_stress_{uuid.uuid4().hex[:8]}"
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="stress_test",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=stress_tests.model_dump(by_alias=True),
        warnings=[],
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="stress_testing_engine_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "stress_test_run",
        f"Executed stress test analysis run {run_id}"
    )
    return analysis_run


def execute_facility_structuring_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.routes.financials import _build_financial_analysis_response
    from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
    from app.services.advisory.risk_score_engine import build_unified_risk_score
    from app.services.advisory.stress_testing_engine import build_demo_stress_tests
    from app.services.advisory.facility_structuring_engine import build_facility_structuring
    
    analysis = _build_financial_analysis_response(snap_data)
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_fac_{uuid.uuid4().hex[:8]}"
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="facility_structuring",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=facility_structuring.model_dump(by_alias=True),
        warnings=[],
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="facility_structuring_engine_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "facility_structuring_run",
        f"Executed facility structuring analysis run {run_id}"
    )
    return analysis_run


async def execute_funding_strategy_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.services.market_watch.funding_channel_ranking_service import get_funding_channel_ranking
    result = await get_funding_channel_ranking(workspace_id)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_fund_{uuid.uuid4().hex[:8]}"
    
    warnings = []
    if hasattr(result, "warnings") and result.warnings:
        warnings = list(result.warnings)
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="funding_strategy",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=result.model_dump(by_alias=True),
        warnings=warnings,
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="funding_channel_ranking_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "funding_strategy_run",
        f"Executed funding strategy analysis run {run_id}"
    )
    return analysis_run


def execute_advisory_blueprint_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    from app.routes.financials import _build_financial_analysis_response
    from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
    from app.services.advisory.risk_score_engine import build_unified_risk_score
    from app.services.advisory.stress_testing_engine import build_demo_stress_tests
    from app.services.advisory.facility_structuring_engine import build_facility_structuring
    from app.services.advisory.blueprint_engine import build_advisory_blueprint
    
    analysis = _build_financial_analysis_response(snap_data)
    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    blueprint = build_advisory_blueprint(analysis, precheck, risk_score, stress_tests, facility_structuring)
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_bp_{uuid.uuid4().hex[:8]}"
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="advisory_blueprint",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=blueprint.model_dump(by_alias=True),
        warnings=[],
        errors=[],
        sourceTrace={"snapshot_source": "workspace_uploaded_statements", "app_mode": settings.APP_MODE},
        logicVersion="blueprint_engine_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "advisory_blueprint_run",
        f"Executed advisory blueprint analysis run {run_id}"
    )
    return analysis_run


async def execute_workflow_run(workspace_id: str, snapshot_id: Optional[str] = None) -> AnalysisRun:
    start_time = time.time()
    snap_data, resolved_snapshot_id = _resolve_snapshot(workspace_id, snapshot_id)
    
    run_fh = execute_financial_health_run(workspace_id, resolved_snapshot_id)
    run_val = execute_valuation_run(workspace_id, resolved_snapshot_id)
    run_precheck = execute_advisory_precheck_run(workspace_id, resolved_snapshot_id)
    run_cs = execute_credit_score_run(workspace_id, resolved_snapshot_id)
    run_stress = execute_stress_test_run(workspace_id, resolved_snapshot_id)
    run_fac = execute_facility_structuring_run(workspace_id, resolved_snapshot_id)
    run_bp = execute_advisory_blueprint_run(workspace_id, resolved_snapshot_id)
    run_fund = await execute_funding_strategy_run(workspace_id, resolved_snapshot_id)
    
    sub_runs = {
        "financial_health": run_fh.id,
        "valuation": run_val.id,
        "advisory_precheck": run_precheck.id,
        "credit_score": run_cs.id,
        "stress_test": run_stress.id,
        "facility_structuring": run_fac.id,
        "advisory_blueprint": run_bp.id,
        "funding_strategy": run_fund.id
    }
    
    stage_coverage = {
        "totalStages": 8,
        "completedStages": 8,
        "reviewStages": 0,
        "unavailableStages": 0
    }
    
    # Product-appropriate analysis coverage summary alongside legacy stage wording
    total_analyses = len(sub_runs)
    completed_analyses = len([rid for rid in sub_runs.values() if rid])
    missing_analyses = total_analyses - completed_analyses
    unavailable_analyses = 0
    coverage_summary = {
        "totalAnalyses": total_analyses,
        "completedAnalyses": completed_analyses,
        "missingAnalyses": missing_analyses,
        "unavailableAnalyses": unavailable_analyses,
    }
    
    duration_ms = int((time.time() - start_time) * 1000)
    run_id = f"run_wf_{uuid.uuid4().hex[:8]}"
    
    fallback_allowed = getattr(settings, "ALLOW_DEMO_FALLBACK", False)
    
    results = {
        "statusSummary": "all_stages_completed",
        "stageCoverage": stage_coverage,
        "coverageSummary": coverage_summary,
        "subRunIds": sub_runs,
        "subRunTypes": list(sub_runs.keys()),
        "missingStages": [],
        "warnings": []
    }
    
    analysis_run = AnalysisRun(
        id=run_id,
        workspaceId=workspace_id,
        snapshotId=resolved_snapshot_id,
        runType="workflow_run",
        status="completed",
        inputs={"workspace_id": workspace_id, "snapshot_id": resolved_snapshot_id},
        results=results,
        warnings=[],
        errors=[],
        sourceTrace={
            "workspace_id": workspace_id,
            "snapshot_id": resolved_snapshot_id,
            "sub_run_ids": list(sub_runs.values()),
            "app_mode": settings.APP_MODE,
            "fallback_allowed": fallback_allowed
        },
        logicVersion="workflow_orchestrator_v1",
        createdAt=datetime.now(timezone.utc).isoformat(),
        durationMs=duration_ms
    )
    
    WorkspaceStore.save_analysis_run(analysis_run)
    WorkspaceStore.log_audit_event(
        workspace_id,
        "workflow_run",
        f"Executed workflow orchestration run {run_id}"
    )
    return analysis_run
