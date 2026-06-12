from typing import List, Optional, Tuple
from app.models.financials import FinancialAnalysisResponse
from app.models.advisory import (
    CdiMockResponse,
    LoanStructuringResponse,
    LoanFacilityRecommendation
)

def optimize_loan_structure(
    company_id: str,
    requested_amount_hkd: float,
    analysis: FinancialAnalysisResponse,
    cdi_data: Optional[CdiMockResponse] = None
) -> LoanStructuringResponse:
    """
    Implements a deterministic exhaustive/grid optimizer over 3 facilities:
    - SFGS 80
    - Trade Finance CDI
    - Working Capital Buffer
    
    Constraints:
    - LTV <= 70% (using enterprise value or total assets as proxy)
    - DSCR >= 1.25 base if possible
    - Facility caps
    """
    snapshot = analysis.snapshot
    ratios = analysis.ratios
    
    # Valuations and cash flows for constraints
    total_assets = snapshot.balance_sheet.total_assets if snapshot else 10000000.0
    enterprise_value = total_assets  # Proxy if DCF valuation not fully present
    if analysis.valuation and analysis.valuation.enterprise_value:
        enterprise_value = analysis.valuation.enterprise_value
        
    cads_base = 0.0
    total_debt = 0.0
    total_debt_service = 0.0
    if snapshot:
        ebitda = snapshot.income_statement.ebitda
        taxes = snapshot.income_statement.taxes
        capex = snapshot.cash_flow_statement.capex
        divs = snapshot.cash_flow_statement.dividends
        cads_base = ebitda - taxes - capex - divs
        
        total_debt = (
            snapshot.balance_sheet.short_term_debt +
            snapshot.balance_sheet.current_portion_long_term_debt +
            snapshot.balance_sheet.long_term_debt +
            snapshot.balance_sheet.lease_liabilities
        )
        total_debt_service = snapshot.debt_schedule.scheduled_interest + snapshot.debt_schedule.scheduled_principal

    cdi_collateral = cdi_data.alternative_collateral_hkd if cdi_data else 0.0
    
    # Facility definitions
    # 1. SFGS 80 (Max 18M, 4% / 400 bps)
    # 2. Trade Finance CDI (Max CDI Collateral * 1.5, 5% / 500 bps)
    # 3. Working Capital (No strict max, 7% / 700 bps)
    
    max_sfgs = 18_000_000.0
    max_trade = cdi_collateral * 1.5 if cdi_collateral > 0 else 0.0
    
    sfgs_rate = 400
    trade_rate = 500
    wc_rate = 700
    
    # Grid search (step size 100k or similar, or analytical resolution)
    # We want to minimize cost.
    # Cost = sfgs_amt * sfgs_rate + trade_amt * trade_rate + wc_amt * wc_rate
    # Since sfgs_rate < trade_rate < wc_rate, greedy approach is optimal here.
    
    sfgs_alloc = min(requested_amount_hkd, max_sfgs)
    remaining = requested_amount_hkd - sfgs_alloc
    
    trade_alloc = min(remaining, max_trade)
    remaining -= trade_alloc
    
    wc_alloc = remaining
    
    # Calculate costs
    sfgs_cost = sfgs_alloc * (sfgs_rate / 10000.0)
    trade_cost = trade_alloc * (trade_rate / 10000.0)
    wc_cost = wc_alloc * (wc_rate / 10000.0)
    
    total_cost = sfgs_cost + trade_cost + wc_cost
    weighted_avg_bps = int((total_cost / requested_amount_hkd) * 10000) if requested_amount_hkd > 0 else 0
    
    # Constraints check
    new_total_debt = total_debt + requested_amount_hkd
    ltv = new_total_debt / enterprise_value if enterprise_value > 0 else 1.0
    
    # Rough approximation of new debt service: 
    # SFGS (5 yr tenor), Trade (1 yr), WC (interest only)
    sfgs_ds = sfgs_cost + (sfgs_alloc / 5.0)
    trade_ds = trade_cost + trade_alloc
    wc_ds = wc_cost  # interest only assumption for short term buffer
    
    new_debt_service = total_debt_service + sfgs_ds + trade_ds + wc_ds
    dscr = cads_base / new_debt_service if new_debt_service > 0 else 0.0
    
    constraints_passed = []
    constraints_failed = []
    
    if ltv <= 0.70:
        constraints_passed.append(f"LTV <= 70% (Current: {ltv*100:.1f}%)")
    else:
        constraints_failed.append(f"LTV <= 70% (Current: {ltv*100:.1f}%)")
        
    if dscr >= 1.25:
        constraints_passed.append(f"DSCR >= 1.25x (Current: {dscr:.2f}x)")
    else:
        constraints_failed.append(f"DSCR >= 1.25x (Current: {dscr:.2f}x)")
        
    recommended = []
    if sfgs_alloc > 0:
        recommended.append(LoanFacilityRecommendation(
            facility="SFGS 80% Guarantee Product",
            amount=sfgs_alloc,
            interest_rate_bps=sfgs_rate,
            annual_cost=sfgs_cost,
            reason="Lowest cost facility. Maximized up to HKMC limit."
        ))
    if trade_alloc > 0:
        recommended.append(LoanFacilityRecommendation(
            facility="Trade Finance (CDI Supported)",
            amount=trade_alloc,
            interest_rate_bps=trade_rate,
            annual_cost=trade_cost,
            reason="Leverages CDI alternative logistics data for lower-rate trade financing."
        ))
    if wc_alloc > 0:
        recommended.append(LoanFacilityRecommendation(
            facility="Working Capital Buffer",
            amount=wc_alloc,
            interest_rate_bps=wc_rate,
            annual_cost=wc_cost,
            reason="Standard commercial overdraft/revolver to cover the remaining requested balance."
        ))
        
    summary = "Optimized facility split to minimize blended interest cost."
    if constraints_failed:
        summary = "Proposed split minimizes cost but violates some credit constraints. Recommend reducing requested amount or extending tenors."
        
    disclaimer = "This is a deterministic loan structuring proxy for BOCHK demo context. Not a real bank underwriting decision."
    
    return LoanStructuringResponse(
        company_id=company_id,
        requested_amount_hkd=requested_amount_hkd,
        recommended_facilities=recommended,
        total_estimated_cost=total_cost,
        weighted_average_cost_bps=weighted_avg_bps,
        constraints_passed=constraints_passed,
        constraints_failed=constraints_failed,
        recommendation_summary=summary,
        disclaimer=disclaimer
    )
