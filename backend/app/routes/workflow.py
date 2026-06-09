from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.routes.data_room import get_active_workspace_preview_context
from app.routes.financials import _build_financial_analysis_response, get_demo_analysis
from app.models.financials import CompanyFinancialSnapshot
from app.services.advisory.hard_gate_engine import build_hard_gate_precheck
from app.services.advisory.risk_score_engine import build_unified_risk_score
from app.services.advisory.credit_scoring_engine import build_credit_scoring_result
from app.services.advisory.stress_testing_engine import build_demo_stress_tests
from app.services.advisory.facility_structuring_engine import build_facility_structuring
from app.services.advisory.blueprint_engine import build_advisory_blueprint

router = APIRouter()


def _active_or_demo_analysis():
    """Build analysis from active Data Room preview context, otherwise demo data."""
    context = get_active_workspace_preview_context()
    if context is None:
        return get_demo_analysis(), "demo_financial_snapshot", [
            "No active Data Room preview context. Workflow runner used demo financial snapshot."
        ]

    snapshot = CompanyFinancialSnapshot.model_validate(context.snapshotPreview)
    metadata = dict(snapshot.metadata or {})
    metadata.update(
        {
            "mode": "preview",
            "source": "data_room_workspace_preview",
            "preview_only": True,
            "activated_at": context.activatedAt,
            "workflow_runner_source": "active_data_room_preview",
        }
    )
    snapshot.metadata = metadata
    warnings = [
        "Workflow runner is using temporary in-memory Data Room preview context. Production persistence is not enabled.",
        *context.warnings,
    ]
    return _build_financial_analysis_response(snapshot, warnings), "active_data_room_preview", warnings


def _stage(
    number: int,
    name: str,
    status: str,
    inputs: list[str],
    outputs: list[str],
    summary: str,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "stage": number,
        "name": name,
        "status": status,
        "inputs": inputs,
        "outputs": outputs,
        "summary": summary,
        "warnings": warnings or [],
    }


@router.get("/run")
def run_bochk_workflow() -> dict[str, Any]:
    """
    Execute the BOCHK challenge workflow as a deterministic demo pipeline.

    This endpoint intentionally reuses the existing financial/advisory engines so
    judges can inspect a single Stage 0 -> Stage 7 response without trusting UI
    stitching. It is context-only and not a production underwriting workflow.
    """
    analysis, data_source, source_warnings = _active_or_demo_analysis()

    precheck = build_hard_gate_precheck(analysis)
    risk_score = build_unified_risk_score(analysis, precheck)
    credit_score = build_credit_scoring_result(analysis)
    stress_tests = build_demo_stress_tests(analysis, risk_score)
    facility_structuring = build_facility_structuring(analysis, precheck, risk_score, stress_tests)
    blueprint = build_advisory_blueprint(
        analysis,
        precheck,
        risk_score,
        stress_tests,
        facility_structuring,
    )

    failed_integrity = [check for check in analysis.integrity_checks if not check.passed]
    valuation = analysis.valuation
    dcf = valuation.dcf if valuation else None
    wacc = valuation.wacc if valuation else None

    stages = [
        _stage(
            0,
            "Raw statement ingestion",
            "preview_ready" if data_source == "active_data_room_preview" else "demo_fallback",
            ["Data Room preview context or demo financial snapshot"],
            ["CompanyFinancialSnapshot"],
            "Workflow starts from the active Data Room preview when available; otherwise it uses the deterministic demo company snapshot.",
            source_warnings,
        ),
        _stage(
            1,
            "Standardization and integrity checks",
            "review" if failed_integrity else "passed",
            ["CompanyFinancialSnapshot"],
            ["IntegrityCheckResult[]", "canonical financial snapshot"],
            f"{len(analysis.integrity_checks) - len(failed_integrity)}/{len(analysis.integrity_checks)} integrity checks passed.",
            [f"{check.check_name}: {check.message}" for check in failed_integrity],
        ),
        _stage(
            2,
            "Historical financial metrics",
            "completed",
            ["Canonical income statement", "balance sheet", "cash-flow statement", "debt schedule"],
            ["FinancialRatios", "FinancialRiskDiagnostics"],
            "Liquidity, leverage, coverage, receivables, Altman Z'', and working-capital diagnostics were calculated.",
        ),
        _stage(
            3,
            "Forecast projections",
            "completed" if analysis.projections else "unavailable",
            ["Historical snapshot", "default projection assumptions"],
            ["ProjectionOutput", "projected FCFF/FCFE context"],
            f"Generated {len(analysis.projections.projected_years) if analysis.projections else 0} projected years.",
            analysis.projections.warnings if analysis.projections else ["Projection output unavailable."],
        ),
        _stage(
            4,
            "FCFF / FCFE bridge",
            "completed" if analysis.projections else "unavailable",
            ["ProjectionOutput"],
            ["projected fcff_primary", "projected fcfe_primary"],
            "Free-cash-flow outputs are available for valuation and debt-capacity context." if analysis.projections else "Free-cash-flow bridge unavailable.",
        ),
        _stage(
            5,
            "WACC build-up",
            "completed" if wacc else "unavailable",
            ["FinancialRatios", "valuation assumptions"],
            ["WaccOutput"],
            f"WACC={round(wacc.wacc * 100, 2)}%" if wacc and wacc.wacc is not None else "WACC unavailable.",
            wacc.warnings if wacc else ["WACC output unavailable."],
        ),
        _stage(
            6,
            "DCF valuation",
            "completed" if dcf else "unavailable",
            ["ProjectionOutput", "WaccOutput"],
            ["DcfOutput", "enterprise value", "equity value", "sanity checks"],
            f"Enterprise value={dcf.enterprise_value}, equity value={dcf.equity_value}." if dcf else "DCF output unavailable.",
            dcf.warnings if dcf else ["DCF output unavailable."],
        ),
        _stage(
            7,
            "Credit score, PD proxy, and funding decision context",
            "completed",
            ["FinancialAnalysisResponse", "valuation", "stress overlay", "hard-gate precheck"],
            ["CreditScoringResult", "FundingReadinessBand", "facility candidates", "advisory blueprint"],
            f"Composite score={credit_score.composite_score}; tier={credit_score.risk_tier}; readiness={credit_score.funding_readiness}.",
            credit_score.hard_constraints + credit_score.warnings,
        ),
    ]

    return {
        "workflowId": "bochk-business-valuation-credit-scoring-v1",
        "mode": "context_only_demo",
        "ranAt": datetime.now(timezone.utc).isoformat(),
        "dataSource": data_source,
        "company": {
            "companyId": analysis.snapshot.company_id,
            "companyName": analysis.snapshot.company_name,
            "currency": analysis.snapshot.currency,
            "reportingPeriod": analysis.snapshot.reporting_period,
        },
        "stageCoverage": {
            "totalStages": len(stages),
            "completedStages": sum(1 for stage in stages if stage["status"] in {"completed", "passed", "preview_ready", "demo_fallback"}),
            "reviewStages": sum(1 for stage in stages if stage["status"] == "review"),
            "unavailableStages": sum(1 for stage in stages if stage["status"] == "unavailable"),
        },
        "stages": stages,
        "outputs": {
            "financialAnalysis": analysis,
            "hardGatePrecheck": precheck,
            "unifiedRiskScore": risk_score,
            "creditScore": credit_score,
            "stressTests": stress_tests,
            "facilityStructuring": facility_structuring,
            "advisoryBlueprint": blueprint,
        },
        "disclaimer": "Workflow runner is for BOCHK challenge demonstration only. It is not a production credit approval, underwriting, valuation, or regulatory PD workflow.",
    }
