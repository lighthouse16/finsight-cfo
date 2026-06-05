from typing import Optional
from app.models.financials import CompanyFinancialSnapshot, FinancialRatios, RatioMetric

def calculate_total_debt(
    short_term_debt: float,
    current_portion_long_term_debt: float,
    long_term_debt: float,
    lease_liabilities: float
) -> float:
    """
    total_debt = short_term_debt + current_portion_long_term_debt + long_term_debt + lease_liabilities
    Excludes accounts_payable and accrued liabilities.
    """
    return short_term_debt + current_portion_long_term_debt + long_term_debt + lease_liabilities

def calculate_net_debt(total_debt: float, cash: float) -> float:
    """net_debt = total_debt - cash"""
    return total_debt - cash

def get_days_in_period(reporting_period: str) -> int:
    """Determine days in period based on reporting period string."""
    period_lower = reporting_period.lower()
    if "q" in period_lower or "quarter" in period_lower:
        return 90
    elif "month" in period_lower or "m" in period_lower:
        # Check if it has something like M6 or 6M, which might be 180 days, but let's default standard months to 30
        if "6m" in period_lower or "6-month" in period_lower:
            return 180
        return 30
    return 365

def calculate_ratios(snapshot: CompanyFinancialSnapshot) -> FinancialRatios:
    """
    Calculates the financial ratios from the given snapshot.
    Handles division-by-zero, negative EBITDA, and missing receivables aging.
    """
    is_statement = snapshot.income_statement
    bs = snapshot.balance_sheet
    cf = snapshot.cash_flow_statement
    ds = snapshot.debt_schedule
    ar_aging = snapshot.receivables_aging

    # Pre-calculate helper totals
    total_debt = calculate_total_debt(
        short_term_debt=bs.short_term_debt,
        current_portion_long_term_debt=bs.current_portion_long_term_debt,
        long_term_debt=bs.long_term_debt,
        lease_liabilities=bs.lease_liabilities
    )
    net_debt = calculate_net_debt(total_debt, bs.cash)

    # 1. Current Ratio = current_assets / current_liabilities
    if bs.current_liabilities == 0:
        current_ratio = RatioMetric(
            value=None,
            warning="Current liabilities is zero.",
            label="Current Ratio"
        )
    else:
        current_ratio = RatioMetric(
            value=bs.current_assets / bs.current_liabilities,
            label="Current Ratio"
        )

    # 2. Quick Ratio = (current_assets - inventory - prepaid) / current_liabilities
    if bs.current_liabilities == 0:
        quick_ratio = RatioMetric(
            value=None,
            warning="Current liabilities is zero.",
            label="Quick Ratio"
        )
    else:
        quick_ratio = RatioMetric(
            value=(bs.current_assets - bs.inventory - bs.prepaid) / bs.current_liabilities,
            label="Quick Ratio"
        )

    # 3. Interest Coverage = ebit / interest_expense
    if is_statement.interest_expense == 0:
        interest_coverage = RatioMetric(
            value=None,
            warning="Interest expense is zero.",
            label="Interest Coverage"
        )
    else:
        interest_coverage = RatioMetric(
            value=is_statement.ebit / is_statement.interest_expense,
            label="Interest Coverage"
        )

    # 4. DSCR = CADS / total_debt_service
    # CADS = EBITDA - cash_taxes - unfinanced_capex - distributions
    # For now: cash_taxes = taxes, unfinanced_capex = max(capex, 0), distributions = dividends
    # total_debt_service = scheduled_interest + scheduled_principal
    cash_taxes = is_statement.taxes
    unfinanced_capex = max(cf.capex, 0.0)
    distributions = cf.dividends
    cads = is_statement.ebitda - cash_taxes - unfinanced_capex - distributions
    total_debt_service = ds.scheduled_interest + ds.scheduled_principal

    if total_debt_service == 0:
        dscr = RatioMetric(
            value=None,
            warning="Total debt service is zero.",
            label="Debt Service Coverage Ratio"
        )
    else:
        dscr = RatioMetric(
            value=cads / total_debt_service,
            label="Debt Service Coverage Ratio"
        )

    # 5. Debt Ratio = total_debt / total_assets
    if bs.total_assets == 0:
        debt_ratio = RatioMetric(
            value=None,
            warning="Total assets is zero.",
            label="Debt Ratio"
        )
    else:
        debt_ratio = RatioMetric(
            value=total_debt / bs.total_assets,
            label="Debt Ratio"
        )

    # 6. Net Debt to EBITDA = net_debt / ebitda
    if is_statement.ebitda <= 0:
        net_debt_to_ebitda = RatioMetric(
            value=None,
            warning=f"EBITDA is {'negative' if is_statement.ebitda < 0 else 'zero'} ({is_statement.ebitda}). Net Debt to EBITDA is undefined.",
            label="Net Debt / EBITDA"
        )
    else:
        net_debt_to_ebitda = RatioMetric(
            value=net_debt / is_statement.ebitda,
            label="Net Debt / EBITDA"
        )

    # 7. DSO = accounts_receivable / revenue * days_in_period
    days_in_period = get_days_in_period(snapshot.reporting_period)
    if is_statement.revenue == 0:
        dso = RatioMetric(
            value=None,
            warning="Revenue is zero.",
            label="Days Sales Outstanding"
        )
    else:
        dso = RatioMetric(
            value=(bs.accounts_receivable / is_statement.revenue) * days_in_period,
            label="Days Sales Outstanding"
        )

    # 8. Working Capital Gap = accounts_receivable + inventory + prepaid - accounts_payable - accrued
    working_capital_gap_val = bs.accounts_receivable + bs.inventory + bs.prepaid - bs.accounts_payable - bs.accrued
    working_capital_gap = RatioMetric(
        value=working_capital_gap_val,
        label="Working Capital Gap"
    )

    # 9. Expected Credit Loss (AR) = current_0_30 * 0.005 + days_31_60 * 0.02 + days_61_90 * 0.08 + days_90_plus * 0.25
    if ar_aging is None:
        expected_credit_loss_ar = RatioMetric(
            value=None,
            warning="Receivables aging data is missing.",
            label="Expected Credit Loss AR"
        )
    else:
        ecl_val = (
            ar_aging.current_0_30 * 0.005 +
            ar_aging.days_31_60 * 0.02 +
            ar_aging.days_61_90 * 0.08 +
            ar_aging.days_90_plus * 0.25
        )
        expected_credit_loss_ar = RatioMetric(
            value=ecl_val,
            label="Expected Credit Loss AR"
        )

    return FinancialRatios(
        current_ratio=current_ratio,
        quick_ratio=quick_ratio,
        interest_coverage=interest_coverage,
        dscr=dscr,
        debt_ratio=debt_ratio,
        net_debt_to_ebitda=net_debt_to_ebitda,
        dso=dso,
        working_capital_gap=working_capital_gap,
        expected_credit_loss_ar=expected_credit_loss_ar
    )
