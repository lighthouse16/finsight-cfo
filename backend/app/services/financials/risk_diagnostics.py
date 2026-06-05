from typing import List, Optional
from app.models.financials import (
    CompanyFinancialSnapshot,
    AltmanZScoreResult,
    ReceivablesRiskResult
)

def calculate_altman_z_service(snapshot: CompanyFinancialSnapshot) -> AltmanZScoreResult:
    """
    Calculates the Altman Z'' Score for service/non-manufacturing firms.
    Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4
    where:
    X1 = Working Capital / Total Assets
    X2 = Retained Earnings / Total Assets
    X3 = EBIT / Total Assets
    X4 = Equity / Total Liabilities
    """
    warnings = []
    bs = snapshot.balance_sheet
    is_statement = snapshot.income_statement

    methodology = "Altman Z'' Score for Services/Non-Manufacturing"
    source = "company_financial_snapshot"

    # Verify retained earnings existence
    if bs.retained_earnings is None:
        warnings.append("Retained earnings data is missing. Z'' Score cannot be calculated.")
        return AltmanZScoreResult(
            value=None,
            band=None,
            components=None,
            warnings=warnings,
            source=source,
            methodology_label=methodology
        )

    # Verify asset/liability denominators
    if bs.total_assets == 0:
        warnings.append("Total assets is zero. Z'' Score cannot be calculated.")
        return AltmanZScoreResult(
            value=None,
            band=None,
            components=None,
            warnings=warnings,
            source=source,
            methodology_label=methodology
        )

    if bs.total_liabilities == 0:
        warnings.append("Total liabilities is zero. Z'' Score cannot be calculated.")
        return AltmanZScoreResult(
            value=None,
            band=None,
            components=None,
            warnings=warnings,
            source=source,
            methodology_label=methodology
        )

    # Calculate Working Capital
    working_capital = bs.current_assets - bs.current_liabilities

    X1 = working_capital / bs.total_assets
    X2 = bs.retained_earnings / bs.total_assets
    X3 = is_statement.ebit / bs.total_assets
    X4 = bs.equity / bs.total_liabilities

    z_score = 6.56 * X1 + 3.26 * X2 + 6.72 * X3 + 1.05 * X4

    # Determine band
    if z_score > 2.60:
        band = "safe"
    elif z_score >= 1.10:
        band = "grey"
    else:
        band = "distress"

    return AltmanZScoreResult(
        value=z_score,
        band=band,
        components={
            "X1": X1,
            "X2": X2,
            "X3": X3,
            "X4": X4
        },
        warnings=warnings,
        source=source,
        methodology_label=methodology
    )

def calculate_receivables_risk(snapshot: CompanyFinancialSnapshot) -> ReceivablesRiskResult:
    """
    Analyzes receivables credit risk using aging buckets and expected credit loss.
    """
    warnings = []
    bs = snapshot.balance_sheet
    aging = snapshot.receivables_aging

    methodology = "AR Aging Bucket Loss Analysis"
    source = "company_financial_snapshot"
    total_ar = bs.accounts_receivable

    if total_ar == 0:
        warnings.append("Accounts receivable balance is zero. Credit risk is not applicable.")
        return ReceivablesRiskResult(
            total_ar=0.0,
            expected_credit_loss=0.0,
            ecl_ratio=None,
            ar_90_plus_concentration=None,
            zone=None,
            warnings=warnings,
            source=source,
            methodology_label=methodology
        )

    if aging is None:
        warnings.append("Receivables aging profile is missing. Detailed Credit Risk Analysis is pending.")
        return ReceivablesRiskResult(
            total_ar=total_ar,
            expected_credit_loss=None,
            ecl_ratio=None,
            ar_90_plus_concentration=None,
            zone=None,
            warnings=warnings,
            source=source,
            methodology_label=methodology
        )

    # Calculate Expected Credit Loss
    ecl = (
        aging.current_0_30 * 0.005 +
        aging.days_31_60 * 0.02 +
        aging.days_61_90 * 0.08 +
        aging.days_90_plus * 0.25
    )

    ecl_ratio = ecl / total_ar
    ar_90_plus_concentration = aging.days_90_plus / total_ar

    # Zone classification
    if ar_90_plus_concentration > 0.15 or ecl_ratio > 0.05:
        zone = "elevated"
    elif ar_90_plus_concentration > 0.05 or ecl_ratio > 0.02:
        zone = "moderate"
    else:
        zone = "low"

    return ReceivablesRiskResult(
        total_ar=total_ar,
        expected_credit_loss=ecl,
        ecl_ratio=ecl_ratio,
        ar_90_plus_concentration=ar_90_plus_concentration,
        zone=zone,
        warnings=warnings,
        source=source,
        methodology_label=methodology
    )
