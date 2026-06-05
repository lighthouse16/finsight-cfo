from typing import List
from app.models.financials import CompanyFinancialSnapshot, IntegrityCheckResult
from app.services.financials.ratio_engine import calculate_total_debt

def run_integrity_checks(snapshot: CompanyFinancialSnapshot) -> List[IntegrityCheckResult]:
    """
    Runs integrity checks on the company financial snapshot to verify accounting consistency.
    """
    results = []
    bs = snapshot.balance_sheet
    cf = snapshot.cash_flow_statement
    is_statement = snapshot.income_statement

    # 1. Balance Sheet Identity: Total Assets = Total Liabilities + Equity
    assets = bs.total_assets
    liab_equity = bs.total_liabilities + bs.equity
    bs_diff = abs(assets - liab_equity)
    bs_passed = bs_diff < 1.0
    results.append(
        IntegrityCheckResult(
            check_name="Balance Sheet Identity",
            passed=bs_passed,
            message=(
                "Balance sheet is in balance." if bs_passed
                else f"Balance sheet is out of balance by {bs_diff:.2f}. Total Assets ({assets:.2f}) != Total Liabilities + Equity ({liab_equity:.2f})."
            ),
            details={
                "total_assets": assets,
                "total_liabilities": bs.total_liabilities,
                "equity": bs.equity,
                "difference": bs_diff
            }
        )
    )

    # 2. Total Debt definition confirmation: confirm that total debt calculation behaves as expected
    computed_debt = calculate_total_debt(
        short_term_debt=bs.short_term_debt,
        current_portion_long_term_debt=bs.current_portion_long_term_debt,
        long_term_debt=bs.long_term_debt,
        lease_liabilities=bs.lease_liabilities
    )
    # Confirm that total debt does not exceed total liabilities
    debt_liab_check = computed_debt <= bs.total_liabilities
    results.append(
        IntegrityCheckResult(
            check_name="Total Debt Definition Confirmation",
            passed=debt_liab_check,
            message=(
                "Total debt is properly defined and does not exceed total liabilities." if debt_liab_check
                else f"Computed total debt ({computed_debt:.2f}) exceeds total liabilities ({bs.total_liabilities:.2f}). Check classification of debt versus other liabilities."
            ),
            details={
                "short_term_debt": bs.short_term_debt,
                "current_portion_long_term_debt": bs.current_portion_long_term_debt,
                "long_term_debt": bs.long_term_debt,
                "lease_liabilities": bs.lease_liabilities,
                "computed_total_debt": computed_debt,
                "total_liabilities": bs.total_liabilities
            }
        )
    )

    # 3. Current Assets Reconciliation: cash + accounts_receivable + inventory + prepaid == current_assets
    computed_ca = bs.cash + bs.accounts_receivable + bs.inventory + bs.prepaid
    ca_diff = abs(bs.current_assets - computed_ca)
    ca_passed = ca_diff < 1.0
    results.append(
        IntegrityCheckResult(
            check_name="Current Assets Reconciliation",
            passed=ca_passed,
            message=(
                "Current assets component sum matches total current assets." if ca_passed
                else f"Current assets sum mismatch by {ca_diff:.2f}. Sum of components ({computed_ca:.2f}) != current_assets ({bs.current_assets:.2f})."
            ),
            details={
                "cash": bs.cash,
                "accounts_receivable": bs.accounts_receivable,
                "inventory": bs.inventory,
                "prepaid": bs.prepaid,
                "sum_components": computed_ca,
                "current_assets": bs.current_assets,
                "difference": ca_diff
            }
        )
    )

    # 4. Total Assets Reconciliation: current_assets + ppe_net == total_assets (or at least check if they match)
    computed_ta = bs.current_assets + bs.ppe_net
    ta_diff = abs(bs.total_assets - computed_ta)
    ta_passed = ta_diff < 1.0
    results.append(
        IntegrityCheckResult(
            check_name="Total Assets Reconciliation",
            passed=ta_passed,
            message=(
                "Current assets + Net PPE matches total assets." if ta_passed
                else f"Total assets mismatch by {ta_diff:.2f}. current_assets + ppe_net ({computed_ta:.2f}) != total_assets ({bs.total_assets:.2f})."
            ),
            details={
                "current_assets": bs.current_assets,
                "ppe_net": bs.ppe_net,
                "sum_components": computed_ta,
                "total_assets": bs.total_assets,
                "difference": ta_diff
            }
        )
    )

    # 5. Cash Flow Consistency: net_change_cash == cfo - capex + debt_issued - debt_repaid - dividends
    # Note: capex is usually represented as positive cash outflow in model, so we subtract it.
    computed_change = cf.cfo - cf.capex + cf.debt_issued - cf.debt_repaid - cf.dividends
    cf_diff = abs(cf.net_change_cash - computed_change)
    cf_passed = cf_diff < 1.0
    results.append(
        IntegrityCheckResult(
            check_name="Cash Flow Reconciliation",
            passed=cf_passed,
            message=(
                "Net change in cash matches the sum of cash flow components." if cf_passed
                else f"Cash flow components sum mismatch by {cf_diff:.2f}. CFO - CapEx + Debt Issued - Debt Repaid - Dividends ({computed_change:.2f}) != net_change_cash ({cf.net_change_cash:.2f})."
            ),
            details={
                "cfo": cf.cfo,
                "capex": cf.capex,
                "debt_issued": cf.debt_issued,
                "debt_repaid": cf.debt_repaid,
                "dividends": cf.dividends,
                "computed_change": computed_change,
                "net_change_cash": cf.net_change_cash,
                "difference": cf_diff
            }
        )
    )

    return results
