from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Header

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


CDI_TRUST_BRIDGE_DISCLAIMER = (
    "Mock CDI trust-bridge context is generated for BOCHK challenge demonstration only. "
    "It is not real CDI, CCRA, bureau, bank transaction, tax, MPF, or customer data. "
    "Production use requires explicit consent, audit logging, secure exchange, and PDPO/PIPL-aligned controls."
)


async def _active_or_demo_analysis(
    x_workspace_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
):
    """Build analysis from active Data Room workspace snapshot or preview context, otherwise demo data."""
    analysis = await get_demo_analysis(x_workspace_id=x_workspace_id, workspace_id=workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis, None, []

    is_preview = False
    if hasattr(analysis, "snapshot") and getattr(analysis, "snapshot") and getattr(analysis.snapshot, "metadata", None):
        is_preview = analysis.snapshot.metadata.get("source") != "demo_company"

    source_name = "active_workspace_snapshot" if is_preview else "demo_financial_snapshot"
    warnings = getattr(analysis, "warnings", [])
    return analysis, source_name, warnings


def _build_mock_trust_bridge_context(analysis) -> dict[str, Any]:
    """Build a deterministic CDI-style trust bridge for the workflow response."""
    # Handle dict if analysis is returned as a dict with status: insufficient_data
    if isinstance(analysis, dict):
        return {}
    company_id = getattr(analysis.snapshot, "company_id", "demo_company")
    company_name = getattr(analysis.snapshot, "company_name", "Demo Company")
    return {
        "consent": {
            "consentId": f"workflow_mock_cdi_{company_id}",
            "companyId": company_id,
            "companyName": company_name,
            "status": "authorized",
            "requestedScopes": [
                "bank_transactions",
                "trade_receivables",
                "credit_bureau_summary",
            ],
            "source": "workflow_mock_cdi_consent_gateway",
        },
        "cashflowSignal": {
            "averageMonthlyInflow": 1_280_000,
            "averageMonthlyOutflow": 1_075_000,
            "netCashflowTrend": "stable",
            "volatilityBand": "moderate",
            "bouncedPaymentCount6m": 0,
        },
        "receivablesSignal": {
            "verifiedInvoiceValue": 2_450_000,
            "eligibleInvoiceValue": 1_715_000,
            "topBuyerConcentration": 0.28,
            "averageDaysToCollect": 47.5,
            "digitalCollateralBand": "strong",
        },
        "creditBureauSignal": {
            "repaymentDelinquencyCount12m": 0,
            "bureauBand": "clear",
            "tradeReferenceCount": 8,
        },
        "fundingImplications": [
            "Verified invoice pool can support receivables-backed working-capital discussion.",
            "Stable bank-transaction inflows improve cash-flow verification for lender review.",
            "Clear mock bureau band reduces context-only red flags in the funding narrative.",
        ],
        "riskImplications": [
            "Moderate cash-flow volatility still requires stress testing under higher HIBOR assumptions.",
            "Top buyer concentration should be reviewed before setting advance rates.",
        ],
        "disclaimer": CDI_TRUST_BRIDGE_DISCLAIMER,
    }


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
async def run_bochk_workflow(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None,
) -> Any:
    """
    Execute the BOCHK challenge workflow as a deterministic demo pipeline.

    This endpoint intentionally reuses the existing financial/advisory engines so
    judges can inspect a single Stage 0 -> Stage 7 response without trusting UI
    stitching. It is context-only and not a production underwriting workflow.
    """
    ws_id = workspace_id or x_workspace_id
    workflow_run_record = None
    if ws_id:
        from app.services.analysis_run_service import execute_workflow_run
        workflow_run_record = await execute_workflow_run(ws_id)

    analysis, data_source, source_warnings = await _active_or_demo_analysis(x_workspace_id, workspace_id)
    if isinstance(analysis, dict) and analysis.get("status") == "insufficient_data":
        return analysis

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
    trust_bridge_context = _build_mock_trust_bridge_context(analysis)

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
            "Credit score, PD proxy, trust bridge, and funding decision context",
            "completed",
            ["FinancialAnalysisResponse", "valuation", "stress overlay", "hard-gate precheck", "mock CDI consent signals"],
            [
                "CreditScoringResult",
                "FundingReadinessBand",
                "facility candidates",
                "advisory blueprint",
                "trustBridgeContext",
            ],
            f"Composite score={credit_score.composite_score}; tier={credit_score.risk_tier}; readiness={credit_score.funding_readiness}; CDI bureau band={trust_bridge_context['creditBureauSignal']['bureauBand']}.",
            credit_score.hard_constraints + credit_score.warnings + trust_bridge_context["riskImplications"],
        ),
    ]

    res = {
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
            "trustBridgeContext": trust_bridge_context,
        },
        "disclaimer": "Workflow runner is for BOCHK challenge demonstration only. It is not a production credit approval, underwriting, valuation, CDI, or regulatory PD workflow.",
    }
    if workflow_run_record:
        res["run_metadata"] = {
            "id": workflow_run_record.id,
            "runId": workflow_run_record.id,
            "snapshotId": workflow_run_record.snapshot_id,
            "status": workflow_run_record.status,
            "runType": workflow_run_record.run_type,
            "createdAt": workflow_run_record.created_at,
            "logicVersion": workflow_run_record.logic_version,
            "warningsCount": len(workflow_run_record.warnings)
        }
    return res
