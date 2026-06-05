from fastapi import APIRouter
from app.models.financials import FinancialAnalysisResponse
from app.services.financials.demo_company import get_demo_financial_snapshot
from app.services.financials.ratio_engine import calculate_ratios
from app.services.financials.integrity_checks import run_integrity_checks

router = APIRouter()

@router.get("/demo-analysis", response_model=FinancialAnalysisResponse)
def get_demo_analysis():
    """
    Returns the financial snapshot, integrity check validation results,
    calculated financial ratios, and any analysis warnings.
    """
    # 1. Fetch demo snapshot
    snapshot = get_demo_financial_snapshot()
    
    # 2. Run integrity checks
    checks = run_integrity_checks(snapshot)
    
    # 3. Calculate ratios
    ratios = calculate_ratios(snapshot)
    
    # 4. Consolidate warnings
    warnings = []
    
    # Add warnings from failed integrity checks
    for check in checks:
        if not check.passed:
            warnings.append(f"Integrity check failed: {check.check_name}. {check.message}")
            
    # Add warnings from ratio calculations (e.g. divide by zero, negative ebitda)
    for field_name, ratio_val in ratios:
        if ratio_val.warning:
            warnings.append(f"Ratio Warning ({ratio_val.label}): {ratio_val.warning}")
            
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

    return FinancialAnalysisResponse(
        snapshot=snapshot,
        integrityChecks=checks,
        ratios=ratios,
        warnings=warnings
    )
