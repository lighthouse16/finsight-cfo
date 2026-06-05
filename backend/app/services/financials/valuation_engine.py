import math
from typing import List, Optional
from app.models.financials import (
    CompanyFinancialSnapshot,
    FinancialRatios,
    ProjectionAnalysis,
    WaccAssumptions,
    WaccResult,
    DcfValuationYear,
    DcfValuationResult,
    ValuationSensitivityPoint,
    ValuationSanityCheck,
    ValuationAnalysis
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def calculate_book_debt(snapshot: CompanyFinancialSnapshot) -> float:
    """Total debt = STD + current LTD + LTD + leases."""
    bs = snapshot.balance_sheet
    return (
        bs.short_term_debt +
        bs.current_portion_long_term_debt +
        bs.long_term_debt +
        bs.lease_liabilities
    )

# ---------------------------------------------------------------------------
# Hamada Beta
# ---------------------------------------------------------------------------

def calculate_unlevered_beta(
    observed_levered_beta: float,
    debt_to_equity: float,
    tax_rate: float
) -> float:
    """
    Hamada unlevering:
    βU = βL / (1 + (1 - τ) × D/E)
    """
    denominator = 1.0 + (1.0 - tax_rate) * debt_to_equity
    if denominator <= 0.0:
        return observed_levered_beta
    return observed_levered_beta / denominator

def calculate_relevered_beta(
    unlevered_beta: float,
    target_debt_weight: float,
    target_equity_weight: float,
    tax_rate: float
) -> float:
    """
    Hamada relevering:
    βL_target = βU × (1 + (1 - τ) × D_target / E_target)
    """
    if target_equity_weight <= 0.0:
        return unlevered_beta
    target_de = target_debt_weight / target_equity_weight
    return unlevered_beta * (1.0 + (1.0 - tax_rate) * target_de)

# ---------------------------------------------------------------------------
# CAPM / CoE
# ---------------------------------------------------------------------------

def calculate_cost_of_equity(assumptions: WaccAssumptions, relevered_beta: float) -> float:
    """
    Extended CAPM:
    CoE = Rf + βL × ERP + SizePremium + IndustryRiskPremium + CompanySpecificPremium
    """
    return (
        assumptions.risk_free_rate +
        relevered_beta * assumptions.equity_risk_premium +
        assumptions.size_premium +
        assumptions.industry_risk_premium +
        assumptions.company_specific_premium
    )

def calculate_after_tax_cost_of_debt(pre_tax_cost_of_debt: float, tax_rate: float) -> float:
    """After-tax CoD = pre-tax CoD × (1 - τ)"""
    return pre_tax_cost_of_debt * (1.0 - tax_rate)

# ---------------------------------------------------------------------------
# Default Assumptions
# ---------------------------------------------------------------------------

def build_default_wacc_assumptions(
    snapshot: CompanyFinancialSnapshot,
    ratios: FinancialRatios,
    projections: ProjectionAnalysis
) -> WaccAssumptions:
    """
    Derives baseline WACC assumptions from the financial snapshot.
    Uses book-value weights as proxy; warns accordingly.
    """
    # Pre-tax cost of debt: derive or fallback
    total_debt = calculate_book_debt(snapshot)
    interest_expense = snapshot.income_statement.interest_expense
    if total_debt > 0.0:
        pre_tax_cod = interest_expense / total_debt
        pre_tax_cod = max(0.0, min(pre_tax_cod, 0.50))
    else:
        pre_tax_cod = 0.065

    tax_rate = projections.assumptions.tax_rate if projections else 0.165

    # Capital structure
    book_equity = snapshot.balance_sheet.equity
    total_capital = total_debt + book_equity
    use_book_proxy = True
    if total_capital > 0.0 and total_debt >= 0.0 and book_equity >= 0.0:
        target_debt_w = total_debt / total_capital
        target_equity_w = book_equity / total_capital
    else:
        target_debt_w = 0.30
        target_equity_w = 0.70

    return WaccAssumptions(
        riskFreeRate=0.04,
        observedBeta=1.10,
        targetDebtWeight=target_debt_w,
        targetEquityWeight=target_equity_w,
        equityRiskPremium=0.055,
        sizePremium=0.025,
        industryRiskPremium=0.010,
        companySpecificPremium=0.015,
        preTaxCostOfDebt=pre_tax_cod,
        taxRate=tax_rate,
        terminalGrowthRate=0.02,
        exitMultiple=6.5,          # 6.5x EBITDA for sanity comparison only
        currency=snapshot.currency,
        useBookWeightsAsProxy=use_book_proxy,
        comparableBetas=None
    )

# ---------------------------------------------------------------------------
# WACC
# ---------------------------------------------------------------------------

def calculate_wacc(
    snapshot: CompanyFinancialSnapshot,
    ratios: FinancialRatios,
    assumptions: WaccAssumptions
) -> WaccResult:
    """
    Calculates WACC with Hamada-adjusted relevered beta and extended CAPM.
    """
    warnings: List[str] = []

    # Hamada
    total_debt = calculate_book_debt(snapshot)
    book_equity = snapshot.balance_sheet.equity
    if book_equity > 0.0:
        current_de = total_debt / book_equity
    else:
        current_de = 0.0
        warnings.append("Book equity is zero or negative. Current D/E ratio defaulted to 0.")

    unlevered_beta = calculate_unlevered_beta(
        assumptions.observed_beta, current_de, assumptions.tax_rate
    )
    if assumptions.target_equity_weight > 0.0:
        relevered_beta = calculate_relevered_beta(
            unlevered_beta,
            assumptions.target_debt_weight,
            assumptions.target_equity_weight,
            assumptions.tax_rate
        )
    else:
        relevered_beta = unlevered_beta
        warnings.append("Target equity weight is zero. Relevered beta equals unlevered beta.")

    cost_of_equity = calculate_cost_of_equity(assumptions, relevered_beta)
    after_tax_cod = calculate_after_tax_cost_of_debt(
        assumptions.pre_tax_cost_of_debt, assumptions.tax_rate
    )

    debt_weight = assumptions.target_debt_weight
    equity_weight = assumptions.target_equity_weight

    # Normalize weights
    total_w = debt_weight + equity_weight
    if not math.isclose(total_w, 1.0, rel_tol=1e-4):
        warnings.append(
            f"Capital weights ({debt_weight:.2%} debt + {equity_weight:.2%} equity) do not sum to 100%. "
            "Normalizing for valuation context."
        )
        if total_w > 0.0:
            debt_weight /= total_w
            equity_weight /= total_w
        else:
            debt_weight, equity_weight = 0.30, 0.70

    if assumptions.use_book_weights_as_proxy:
        warnings.append(
            "Book-value weights are used as a proxy for market-value weights. "
            "Not a formal valuation opinion — company records required for production."
        )

    if total_debt <= 0.0:
        warnings.append("Total book debt is zero or negative. Pre-tax cost of debt falls back to assumption baseline.")

    total_capital = total_debt + book_equity
    if total_capital <= 0.0:
        warnings.append("Total capital is zero or negative. Capital weights fall back to target assumptions.")

    wacc = equity_weight * cost_of_equity + debt_weight * after_tax_cod

    return WaccResult(
        observedBeta=assumptions.observed_beta,
        unleveredBeta=unlevered_beta,
        releveredBeta=relevered_beta,
        costOfEquity=cost_of_equity,
        preTaxCostOfDebt=assumptions.pre_tax_cost_of_debt,
        afterTaxCostOfDebt=after_tax_cod,
        debtWeight=debt_weight,
        equityWeight=equity_weight,
        wacc=wacc,
        warnings=warnings
    )

# ---------------------------------------------------------------------------
# DCF
# ---------------------------------------------------------------------------

def calculate_dcf(
    snapshot: CompanyFinancialSnapshot,
    ratios: FinancialRatios,
    projections: ProjectionAnalysis,
    wacc_result: WaccResult,
    assumptions: WaccAssumptions
) -> DcfValuationResult:
    """
    Discounts explicit FCFF, computes Gordon Growth Terminal Value,
    derives Enterprise Value, Net Debt bridge, Equity Value, and sanity multiples.
    """
    warnings: List[str] = []
    wacc = wacc_result.wacc
    terminal_growth = assumptions.terminal_growth_rate

    total_debt = calculate_book_debt(snapshot)
    cash = snapshot.balance_sheet.cash
    net_debt = total_debt - cash

    # Guard: empty projections
    if not projections or not projections.projected_years:
        warnings.append("No projected FCFF years available. Valuation cannot be computed. Company records required for production.")
        return DcfValuationResult(
            valuationYears=[],
            pvExplicitFcff=0.0,
            terminalValueGordonGrowth=None,
            pvTerminalValue=None,
            enterpriseValue=None,
            totalDebt=total_debt,
            cash=cash,
            netDebt=net_debt,
            equityValue=None,
            impliedEvEbitda=None,
            terminalGrowthRate=terminal_growth,
            wacc=wacc,
            terminalValueShareOfEnterpriseValue=None,
            exitMultipleTerminalValue=None,
            impliedExitMultiple=None,
            warnings=warnings
        )

    # Check for negative FCFF years
    for yr in projections.projected_years:
        if yr.fcff_primary < 0.0:
            warnings.append(
                f"Projected FCFF in year {yr.year} is negative ({yr.fcff_primary:,.0f}). "
                "Assumptions-based valuation context — company records required for production."
            )

    # Check FCFF trend
    if len(projections.projected_years) >= 2:
        first_fcff = projections.projected_years[0].fcff_primary
        last_fcff = projections.projected_years[-1].fcff_primary
        if last_fcff < first_fcff and terminal_growth > 0.0:
            warnings.append(
                "Projected FCFF declines over the forecast period while terminal growth is positive. "
                "Review projection assumptions."
            )

    # Discount explicit FCFF years
    valuation_years: List[DcfValuationYear] = []
    pv_explicit_fcff = 0.0
    for idx, yr in enumerate(projections.projected_years):
        t = idx + 1
        df = 1.0 / ((1.0 + wacc) ** t)
        pv = yr.fcff_primary * df
        pv_explicit_fcff += pv
        valuation_years.append(DcfValuationYear(year=yr.year, fcff=yr.fcff_primary, discountFactor=df, pvFcff=pv))

    # Terminal value guard
    if wacc <= terminal_growth:
        warnings.append(
            f"WACC ({wacc:.2%}) ≤ terminal growth rate ({terminal_growth:.2%}). "
            "Infinite growth formula is mathematically invalid. Valuation fields suppressed. "
            "Assumptions-based context only."
        )
        return DcfValuationResult(
            valuationYears=valuation_years,
            pvExplicitFcff=pv_explicit_fcff,
            terminalValueGordonGrowth=None,
            pvTerminalValue=None,
            enterpriseValue=None,
            totalDebt=total_debt,
            cash=cash,
            netDebt=net_debt,
            equityValue=None,
            impliedEvEbitda=None,
            terminalGrowthRate=terminal_growth,
            wacc=wacc,
            terminalValueShareOfEnterpriseValue=None,
            exitMultipleTerminalValue=None,
            impliedExitMultiple=None,
            warnings=warnings
        )

    # Gordon Growth Terminal Value
    final_fcff = projections.projected_years[-1].fcff_primary
    tv_gordon = final_fcff * (1.0 + terminal_growth) / (wacc - terminal_growth)
    final_df = valuation_years[-1].discount_factor
    pv_tv = tv_gordon * final_df
    enterprise_value = pv_explicit_fcff + pv_tv

    equity_value = enterprise_value - net_debt

    # TV share
    tv_share = pv_tv / enterprise_value if enterprise_value > 0.0 else None

    # Implied EV/EBITDA
    latest_ebitda = snapshot.income_statement.ebitda
    if latest_ebitda <= 0.0:
        warnings.append("Latest EBITDA ≤ 0. Implied EV/EBITDA is not applicable.")
        implied_ev_ebitda = None
        implied_exit_multiple = None
    else:
        implied_ev_ebitda = enterprise_value / latest_ebitda
        implied_exit_multiple = implied_ev_ebitda  # same basis

    # Exit multiple terminal value (sanity comparison, not primary)
    exit_mul = assumptions.exit_multiple
    exit_multiple_tv = None
    if exit_mul is not None and latest_ebitda > 0.0:
        final_yr = projections.projected_years[-1]
        final_ebitda = final_yr.ebitda
        exit_multiple_tv = final_ebitda * exit_mul * final_df
        # Warn if divergence is large (> 30% of gordon TV)
        if pv_tv > 0.0:
            divergence = abs(exit_multiple_tv - pv_tv) / pv_tv
            if divergence > 0.30:
                warnings.append(
                    f"Gordon Growth PV TV ({pv_tv:,.0f}) and Exit Multiple PV TV ({exit_multiple_tv:,.0f}) "
                    f"diverge by {divergence:.0%}. Assumptions-based valuation context only."
                )

    if equity_value < 0.0:
        warnings.append(
            f"Implied equity value ({equity_value:,.0f}) is negative. "
            "Net debt exceeds enterprise value under these assumptions. "
            "Sensitivity context only — not a formal valuation opinion."
        )

    return DcfValuationResult(
        valuationYears=valuation_years,
        pvExplicitFcff=pv_explicit_fcff,
        terminalValueGordonGrowth=tv_gordon,
        pvTerminalValue=pv_tv,
        enterpriseValue=enterprise_value,
        totalDebt=total_debt,
        cash=cash,
        netDebt=net_debt,
        equityValue=equity_value,
        impliedEvEbitda=implied_ev_ebitda,
        terminalGrowthRate=terminal_growth,
        wacc=wacc,
        terminalValueShareOfEnterpriseValue=tv_share,
        exitMultipleTerminalValue=exit_multiple_tv,
        impliedExitMultiple=implied_exit_multiple,
        warnings=warnings
    )

# ---------------------------------------------------------------------------
# Sanity Checks
# ---------------------------------------------------------------------------

def run_valuation_sanity_checks(
    dcf_result: DcfValuationResult,
    projections: ProjectionAnalysis,
    assumptions: WaccAssumptions
) -> List[ValuationSanityCheck]:
    checks: List[ValuationSanityCheck] = []

    # 1. WACC > terminal growth
    if dcf_result.wacc > dcf_result.terminal_growth_rate:
        checks.append(ValuationSanityCheck(
            name="WACC vs Terminal Growth",
            status="pass",
            message=f"WACC ({dcf_result.wacc:.2%}) exceeds terminal growth rate ({dcf_result.terminal_growth_rate:.2%}).",
            value=dcf_result.wacc - dcf_result.terminal_growth_rate
        ))
    else:
        checks.append(ValuationSanityCheck(
            name="WACC vs Terminal Growth",
            status="fail",
            message=f"WACC ({dcf_result.wacc:.2%}) does not exceed terminal growth rate ({dcf_result.terminal_growth_rate:.2%}). Gordon Growth invalid.",
            value=dcf_result.wacc - dcf_result.terminal_growth_rate
        ))

    # 2. Terminal value share
    tv_share = dcf_result.terminal_value_share_of_enterprise_value
    if tv_share is not None:
        if tv_share > 0.85:
            checks.append(ValuationSanityCheck(
                name="Terminal Value Share",
                status="warning",
                message=f"Terminal value represents {tv_share:.0%} of enterprise value. Valuation is highly terminal-value-dependent.",
                value=tv_share
            ))
        elif 0.60 <= tv_share <= 0.85:
            checks.append(ValuationSanityCheck(
                name="Terminal Value Share",
                status="pass",
                message=f"Terminal value represents {tv_share:.0%} of enterprise value — within normal range (60%–85%).",
                value=tv_share
            ))
        else:
            checks.append(ValuationSanityCheck(
                name="Terminal Value Share",
                status="warning",
                message=f"Terminal value represents {tv_share:.0%} of enterprise value — below typical range (60%–85%).",
                value=tv_share
            ))

    # 3. Equity value
    ev = dcf_result.equity_value
    if ev is not None:
        if ev < 0.0:
            checks.append(ValuationSanityCheck(
                name="Equity Value",
                status="warning",
                message=f"Implied equity value ({ev:,.0f}) is negative under these assumptions. Not a formal valuation opinion.",
                value=ev
            ))
        else:
            checks.append(ValuationSanityCheck(
                name="Equity Value",
                status="pass",
                message=f"Implied equity value ({ev:,.0f}) is positive.",
                value=ev
            ))

    # 4. Implied EV/EBITDA range
    ev_ebitda = dcf_result.implied_ev_ebitda
    if ev_ebitda is not None:
        if ev_ebitda < 3.0:
            checks.append(ValuationSanityCheck(
                name="Implied EV/EBITDA",
                status="warning",
                message=f"Implied EV/EBITDA of {ev_ebitda:.1f}x is below 3.0x — materially low. Assumptions-based context only.",
                value=ev_ebitda
            ))
        elif ev_ebitda > 15.0:
            checks.append(ValuationSanityCheck(
                name="Implied EV/EBITDA",
                status="warning",
                message=f"Implied EV/EBITDA of {ev_ebitda:.1f}x is above 15.0x — materially high. Assumptions-based context only.",
                value=ev_ebitda
            ))
        else:
            checks.append(ValuationSanityCheck(
                name="Implied EV/EBITDA",
                status="pass",
                message=f"Implied EV/EBITDA of {ev_ebitda:.1f}x is within a typical range (3x–15x).",
                value=ev_ebitda
            ))

    return checks

# ---------------------------------------------------------------------------
# Sensitivity Grid
# ---------------------------------------------------------------------------

def build_sensitivity_grid(
    snapshot: CompanyFinancialSnapshot,
    ratios: FinancialRatios,
    projections: ProjectionAnalysis,
    assumptions: WaccAssumptions,
    base_wacc: float
) -> List[ValuationSensitivityPoint]:
    """
    3×3 sensitivity: WACC ±1%, terminal growth ±0.5%.
    Invalid (WACC ≤ g) points are flagged with is_valid=False.
    """
    base_g = assumptions.terminal_growth_rate
    wacc_shifts = [base_wacc - 0.01, base_wacc, base_wacc + 0.01]
    g_shifts = [base_g - 0.005, base_g, base_g + 0.005]

    total_debt = calculate_book_debt(snapshot)
    net_debt = total_debt - snapshot.balance_sheet.cash
    n = len(projections.projected_years)

    grid: List[ValuationSensitivityPoint] = []
    for w in wacc_shifts:
        for g in g_shifts:
            if w <= g:
                grid.append(ValuationSensitivityPoint(
                    wacc=w,
                    terminalGrowthRate=g,
                    enterpriseValue=None,
                    equityValue=None,
                    isValid=False,
                    warning=f"WACC ({w:.2%}) ≤ terminal growth ({g:.2%}). Gordon Growth invalid."
                ))
            else:
                pv_exp = sum(
                    yr.fcff_primary / ((1.0 + w) ** (i + 1))
                    for i, yr in enumerate(projections.projected_years)
                )
                final_fcff = projections.projected_years[-1].fcff_primary
                tv = final_fcff * (1.0 + g) / (w - g)
                pv_tv = tv / ((1.0 + w) ** n)
                ev = pv_exp + pv_tv
                eq = ev - net_debt
                grid.append(ValuationSensitivityPoint(
                    wacc=w,
                    terminalGrowthRate=g,
                    enterpriseValue=ev,
                    equityValue=eq,
                    isValid=True,
                    warning=None
                ))
    return grid

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def build_valuation_analysis(
    snapshot: CompanyFinancialSnapshot,
    ratios: FinancialRatios,
    projections: ProjectionAnalysis
) -> ValuationAnalysis:
    """
    Orchestrates WACC → DCF → sensitivity → sanity checks.
    All outputs are labelled as assumptions-based demo financial analysis.
    """
    warnings: List[str] = []

    assumptions = build_default_wacc_assumptions(snapshot, ratios, projections)
    wacc_res = calculate_wacc(snapshot, ratios, assumptions)
    warnings.extend(wacc_res.warnings)

    dcf_res = calculate_dcf(snapshot, ratios, projections, wacc_res, assumptions)
    warnings.extend(dcf_res.warnings)

    sensitivity = build_sensitivity_grid(snapshot, ratios, projections, assumptions, wacc_res.wacc)
    sanity_checks = run_valuation_sanity_checks(dcf_res, projections, assumptions)

    return ValuationAnalysis(
        assumptions=assumptions,
        wacc=wacc_res,
        dcf=dcf_res,
        sensitivity=sensitivity,
        sanityChecks=sanity_checks,
        warnings=warnings
    )
