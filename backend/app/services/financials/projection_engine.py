import re
import math
from typing import List, Optional
from app.models.financials import (
    CompanyFinancialSnapshot,
    ProjectionAssumptions,
    ProjectedFinancialYear,
    ProjectionAnalysis
)

def get_start_year(reporting_period: str) -> int:
    """Extracts numeric year from reporting period and returns next year."""
    match = re.search(r'\d+', reporting_period)
    if match:
        return int(match.group(0)) + 1
    return 2026

def build_default_projection_assumptions(snapshot: CompanyFinancialSnapshot) -> ProjectionAssumptions:
    """
    Builds default projection assumptions derived from the given snapshot.
    """
    revenue = snapshot.income_statement.revenue
    ebit = snapshot.income_statement.ebit
    da = snapshot.income_statement.depreciation_amortization
    capex = snapshot.cash_flow_statement.capex
    ebt = snapshot.income_statement.ebt
    taxes = snapshot.income_statement.taxes
    
    current_assets = snapshot.balance_sheet.current_assets
    current_liabilities = snapshot.balance_sheet.current_liabilities
    
    ebit_margin = ebit / revenue if revenue > 0 else 0.0
    da_percent = da / revenue if revenue > 0 else 0.0
    capex_percent = capex / revenue if revenue > 0 else 0.0
    
    # Calculate NWC percent of revenue as a proxy for incremental NWC requirements
    nwc = current_assets - current_liabilities
    nwc_percent = nwc / revenue if revenue > 0 else 0.0
    
    tax_rate = taxes / ebt if ebt > 0 else 0.165
    # Clamp tax rate to a safe 0 - 0.5 range
    tax_rate = max(0.0, min(tax_rate, 0.5))
    
    return ProjectionAssumptions(
        forecastYears=5,
        revenueGrowthStart=0.05,
        revenueGrowthTerminal=0.02,
        ebitMargin=ebit_margin,
        daPercentRevenue=da_percent,
        capexPercentRevenue=capex_percent,
        nwcPercentIncrementalRevenue=nwc_percent,
        taxRate=tax_rate,
        terminalGrowthReference=0.02,
        currency=snapshot.currency
    )

def calculate_projection(snapshot: CompanyFinancialSnapshot, assumptions: ProjectionAssumptions) -> ProjectionAnalysis:
    """
    Calculates the 5-year driver-based projections and FCFF for the company.
    """
    warnings = []
    
    # Validate assumptions and generate warnings/clamps
    forecast_years = assumptions.forecast_years
    if not (3 <= forecast_years <= 10):
        warnings.append(f"Forecast years {forecast_years} is out of safe bounds (3 to 10). Clamping to range.")
        clamped_years = max(3, min(forecast_years, 10))
    else:
        clamped_years = forecast_years

    tax_rate = assumptions.tax_rate
    if not (0.0 <= tax_rate <= 0.5):
        warnings.append(f"Tax rate {tax_rate:.4f} is out of standard corporate tax bounds (0 to 50%). Clamping to range.")
        clamped_tax_rate = max(0.0, min(tax_rate, 0.5))
    else:
        clamped_tax_rate = tax_rate

    ebit_margin = assumptions.ebit_margin
    if not (-1.0 <= ebit_margin <= 1.0):
        warnings.append(f"EBIT margin {ebit_margin:.4f} is out of standard bounds (-100% to 100%). Clamping to range.")
        clamped_ebit_margin = max(-1.0, min(ebit_margin, 1.0))
    else:
        clamped_ebit_margin = ebit_margin

    growth_start = assumptions.revenue_growth_start
    if not (-0.5 <= growth_start <= 0.5):
        warnings.append(f"Revenue growth start {growth_start:.4f} is outside standard bounds (-50% to 50%). Clamping to range.")
        clamped_growth_start = max(-0.5, min(growth_start, 0.5))
    else:
        clamped_growth_start = growth_start

    growth_terminal = assumptions.revenue_growth_terminal
    if not (-0.5 <= growth_terminal <= 0.5):
        warnings.append(f"Revenue growth terminal {growth_terminal:.4f} is outside standard bounds (-50% to 50%). Clamping to range.")
        clamped_growth_terminal = max(-0.5, min(growth_terminal, 0.5))
    else:
        clamped_growth_terminal = growth_terminal

    # Check CapEx vs D&A for growing scenario
    avg_growth = (clamped_growth_start + clamped_growth_terminal) / 2.0
    if assumptions.capex_percent_revenue < assumptions.da_percent_revenue and avg_growth > 0.0:
        warnings.append(
            f"CapEx percentage ({assumptions.capex_percent_revenue:.2%}) is below D&A percentage ({assumptions.da_percent_revenue:.2%}) "
            "in a revenue growth scenario. This may indicate long-term asset underinvestment under current driver assumptions."
        )

    start_year = get_start_year(snapshot.reporting_period)
    current_rev = snapshot.income_statement.revenue
    prev_rev = current_rev
    
    projected_years = []
    
    for i in range(clamped_years):
        t = i + 1
        year_num = start_year + i
        
        # Linearly fade growth rate from start to terminal
        if clamped_years > 1:
            growth_rate = clamped_growth_start + (t - 1) * (clamped_growth_terminal - clamped_growth_start) / (clamped_years - 1)
        else:
            growth_rate = clamped_growth_start
            
        revenue = prev_rev * (1.0 + growth_rate)
        incremental_rev = revenue - prev_rev
        
        ebit = revenue * clamped_ebit_margin
        da = revenue * assumptions.da_percent_revenue
        ebitda = ebit + da
        
        taxes = max(ebit * clamped_tax_rate, 0.0)
        capex = revenue * assumptions.capex_percent_revenue
        delta_nwc = incremental_rev * assumptions.nwc_percent_incremental_revenue
        
        # CFO Estimate & Interest Tax Adjustment
        interest = snapshot.income_statement.interest_expense
        interest_tax_adjustment = interest * (1.0 - clamped_tax_rate)
        cfo_estimate = ebit * (1.0 - clamped_tax_rate) - interest_tax_adjustment + da - delta_nwc
        
        # FCFF calculations
        fcff_primary = ebit * (1.0 - clamped_tax_rate) + da - capex - delta_nwc
        fcff_cross_check = cfo_estimate + interest_tax_adjustment - capex
        fcff_variance = fcff_primary - fcff_cross_check
        
        if math.isnan(fcff_variance) or math.isinf(fcff_variance):
            fcff_variance = 0.0
            
        year_warnings = ["CFO is estimated using operating assumptions, not statement-reported."]
        
        projected_years.append(ProjectedFinancialYear(
            year=year_num,
            revenue=revenue,
            revenueGrowth=growth_rate,
            ebit=ebit,
            depreciationAmortization=da,
            ebitda=ebitda,
            taxes=taxes,
            capex=capex,
            deltaNwc=delta_nwc,
            cfoEstimate=cfo_estimate,
            interestTaxAdjustment=interest_tax_adjustment,
            fcffPrimary=fcff_primary,
            fcffCrossCheck=fcff_cross_check,
            fcffVariance=fcff_variance,
            warnings=year_warnings
        ))
        
        prev_rev = revenue
        
    return ProjectionAnalysis(
        assumptions=assumptions,
        projectedYears=projected_years,
        warnings=warnings
    )
