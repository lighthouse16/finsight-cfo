from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.models.financials import (
    CompanyFinancialSnapshot,
    FinancialAnalysisResponse,
    FinancialRiskDiagnostics,
)
from app.routes.data_room import get_active_workspace_preview_context
from app.services.financials.demo_company import get_demo_financial_snapshot
from app.services.financials.ratio_engine import calculate_ratios
from app.services.financials.integrity_checks import run_integrity_checks
from app.services.financials.risk_diagnostics import (
    calculate_altman_z_service,
    calculate_receivables_risk
)
from app.services.financials.projection_engine import (
    build_default_projection_assumptions,
    calculate_projection
)
from app.services.financials.valuation_engine import build_valuation_analysis
from app.services.financials.summary_engine import build_financial_analysis_summary

router = APIRouter()


def _build_financial_analysis_response(
    snapshot: CompanyFinancialSnapshot,
    extra_warnings: list[str] | None = None,
) -> FinancialAnalysisResponse:
    """
    Build a full financial analysis response from the supplied snapshot.

    The caller controls the snapshot source; this helper does not persist or
    mutate any workspace, demo, or production state.
    """
    # 1. Run integrity checks
    checks = run_integrity_checks(snapshot)
    
    # 2. Calculate ratios
    ratios = calculate_ratios(snapshot)
    
    # 3. Calculate risk diagnostics
    altman_z = calculate_altman_z_service(snapshot)
    receivables_risk = calculate_receivables_risk(snapshot)
    
    risk_diagnostics = FinancialRiskDiagnostics(
        altmanZScore=altman_z,
        receivablesRisk=receivables_risk
    )
    
    # 4. Calculate projections
    projection_assumptions = build_default_projection_assumptions(snapshot)
    projections = calculate_projection(snapshot, projection_assumptions)
    
    # 5. Calculate valuation analysis
    valuation = build_valuation_analysis(snapshot, ratios, projections)
    
    # 6. Build Financial Analysis Summary
    summary = build_financial_analysis_summary(
        snapshot=snapshot,
        ratios=ratios,
        risk_diagnostics=risk_diagnostics,
        projections=projections,
        valuation=valuation,
    )

    # 7. Consolidate warnings
    warnings = list(extra_warnings or [])

    # Add warnings from failed integrity checks
    for check in checks:
        if not check.passed:
            warnings.append(f"Integrity check failed: {check.check_name}. {check.message}")
            
    # Add warnings from ratio calculations (e.g. divide by zero, negative ebitda)
    for field_name, ratio_val in ratios:
        if ratio_val.warning:
            warnings.append(f"Ratio Warning ({ratio_val.label}): {ratio_val.warning}")
            
    # Add warnings from risk diagnostics
    if altman_z.warnings:
        for w in altman_z.warnings:
            warnings.append(f"Risk Diagnostic Warning (Altman Z''): {w}")
    if receivables_risk.warnings:
        for w in receivables_risk.warnings:
            warnings.append(f"Risk Diagnostic Warning (AR Risk): {w}")
            
    # Add warnings from projections
    if projections.warnings:
        for w in projections.warnings:
            warnings.append(f"Projection Warning: {w} Company records required for production forecast context.")

    # Add warnings from valuation
    if valuation.warnings:
        for w in valuation.warnings:
            warnings.append(f"Valuation Warning: {w} Company records required for production valuation context.")

    # Add general financial risk warnings based on ratio values
    if ratios.dscr.value is not None and ratios.dscr.value < 1.25:
        warnings.append(
            f"Debt Service Coverage Ratio (DSCR) is {ratios.dscr.value:.2f}x, "
            "which is below the standard banking-grade threshold of 1.25x. "
            "Suggest reviewing debt amortization schedules or exploring refinancing options."
        )
        
    if ratios.current_ratio.value is not None and ratios.current_ratio.value < 1.5:
        warnings.append(
            f"Current Ratio is {ratios.current_ratio.value:.2f}x. "
            "A current ratio under 1.5x may indicate tight short-term liquidity."
        )

    # Add warnings based on risk diagnostics outcomes (using safe, context-only language)
    if altman_z.value is not None:
        if altman_z.band == "distress":
            warnings.append("Altman Z'' independent distress check indicates distress zone. Company records required for production risk diagnostics.")
        elif altman_z.band == "grey":
            warnings.append("Altman Z'' independent distress check indicates grey zone. Suggest close monitoring of balance sheet leverage.")

    if receivables_risk.zone == "elevated":
        warnings.append("Receivables Credit Risk zone is elevated. Days past due and Expected Credit Loss exceed standard parameters.")
    elif receivables_risk.zone == "moderate":
        warnings.append("Receivables Credit Risk zone is moderate. Suggest review of collection cycles.")

    return FinancialAnalysisResponse(
        snapshot=snapshot,
        integrityChecks=checks,
        ratios=ratios,
        riskDiagnostics=risk_diagnostics,
        projections=projections,
        valuation=valuation,
        summary=summary,
        warnings=warnings
    )


@router.get("/demo-analysis", response_model=FinancialAnalysisResponse)
def get_demo_analysis():
    """
    Returns the financial snapshot, integrity check validation results,
    calculated financial ratios, risk diagnostics, projections, valuations,
    financial analysis summary, and any analysis warnings.
    """
    return _build_financial_analysis_response(get_demo_financial_snapshot())


@router.get("/preview-analysis", response_model=FinancialAnalysisResponse)
def get_preview_analysis():
    """
    Return financial analysis derived from the active Data Room preview snapshot.

    This preview mode is separate from /api/financials/demo-analysis. It reads
    the temporary in-memory workspace preview context only and does not persist
    data or mutate the demo analysis snapshot.
    """
    context = get_active_workspace_preview_context()
    if context is None:
        raise HTTPException(
            status_code=404,
            detail="No active workspace preview context is available.",
        )

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
        }
    )
    snapshot.metadata = metadata

    preview_warnings = [
        "Preview analysis mode is using temporary in-memory Data Room workspace context. Production analysis was not updated.",
        *context.warnings,
    ]
    return _build_financial_analysis_response(snapshot, preview_warnings)


