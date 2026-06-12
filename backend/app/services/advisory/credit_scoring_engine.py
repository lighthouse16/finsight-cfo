from __future__ import annotations

from typing import Optional

from app.models.advisory import (
    CreditScoreFactor,
    CreditScoringResult,
    FundingReadinessBand,
    PdRiskTier,
)
from app.models.financials import FinancialAnalysisResponse, RatioMetric

DISCLAIMER = (
    "This is an indicative, context-only PD / credit scoring foundation for "
    "advisory readiness. It is not a calibrated regulatory PD model, formal "
    "underwriting output, or credit approval decision. Production use requires "
    "validated bureau/CDI data, model governance, calibration, and bank approval."
)


def _metric_value(metric: Optional[RatioMetric]) -> Optional[float]:
    if metric is None:
        return None
    return metric.value


def _score_by_thresholds(
    value: Optional[float],
    thresholds: list[tuple[float, int, str, str]],
    unavailable_message: str,
    higher_is_better: bool = True,
) -> tuple[int, str, str]:
    if value is None:
        return 35, "unavailable", unavailable_message

    for threshold, score, band, message in thresholds:
        if higher_is_better and value >= threshold:
            return score, band, message
        if not higher_is_better and value <= threshold:
            return score, band, message

    return thresholds[-1][1], thresholds[-1][2], thresholds[-1][3]


def _band_from_score(score: int) -> PdRiskTier:
    if score >= 80:
        return "low"
    if score >= 65:
        return "moderate"
    if score >= 50:
        return "elevated"
    if score >= 1:
        return "high"
    return "unavailable"


def _pd_proxy_band(score: int) -> str:
    if score >= 80:
        return "Indicative PD proxy: low, roughly < 2% under demo assumptions"
    if score >= 65:
        return "Indicative PD proxy: moderate, roughly 2% - 5% under demo assumptions"
    if score >= 50:
        return "Indicative PD proxy: elevated, roughly 5% - 10% under demo assumptions"
    if score >= 1:
        return "Indicative PD proxy: high, roughly > 10% under demo assumptions"
    return "Indicative PD proxy unavailable due to insufficient data"


def _funding_readiness(score: int, tier: PdRiskTier, hard_constraints: list[str]) -> FundingReadinessBand:
    if hard_constraints or tier == "high" or score < 50:
        return "not_ready"
    if tier == "elevated" or score < 65:
        return "needs_review"
    if tier == "moderate" or score < 80:
        return "bank_review_ready"
    return "ready_context"


def _make_factor(
    key: str,
    label: str,
    raw_score: int,
    weight: float,
    band: str,
    message: str,
    evidence: str,
    source: str,
    positive_driver: Optional[str] = None,
    risk_driver: Optional[str] = None,
    warnings: Optional[list[str]] = None,
) -> CreditScoreFactor:
    return CreditScoreFactor(
        key=key,
        label=label,
        raw_score=raw_score,
        weighted_score=round(raw_score * weight, 2),
        weight=weight,
        band=band,
        message=message,
        evidence=evidence,
        source=source,
        positive_driver=positive_driver,
        risk_driver=risk_driver,
        warnings=warnings or [],
    )


def build_credit_scoring_result(analysis: FinancialAnalysisResponse) -> CreditScoringResult:
    """
    Build a deterministic, explainable PD / credit scoring foundation from the
    finance core outputs in the BOCHK workflow: ratios, receivables diagnostics,
    valuation/cash-flow cushion, and stress-oriented debt-service sensitivity.
    """
    snapshot = analysis.snapshot
    ratios = analysis.ratios
    risk_diagnostics = analysis.risk_diagnostics
    valuation = analysis.valuation

    factors: list[CreditScoreFactor] = []
    warnings: list[str] = list(analysis.warnings or [])
    hard_constraints: list[str] = []

    current_ratio = _metric_value(ratios.current_ratio)
    quick_ratio = _metric_value(ratios.quick_ratio)
    liquidity_anchor = None
    if current_ratio is not None and quick_ratio is not None:
        liquidity_anchor = min(current_ratio, quick_ratio * 1.2)
    elif current_ratio is not None:
        liquidity_anchor = current_ratio
    elif quick_ratio is not None:
        liquidity_anchor = quick_ratio * 1.2

    liquidity_score, liquidity_band, liquidity_message = _score_by_thresholds(
        liquidity_anchor,
        [
            (2.0, 92, "strong", "Liquidity headroom is strong relative to short-term liabilities."),
            (1.5, 78, "adequate", "Liquidity is acceptable for bank review, with manageable short-term pressure."),
            (1.1, 58, "watch", "Liquidity is tight and should be supported with cash-flow evidence."),
            (0.0, 35, "constrained", "Liquidity is constrained; near-term obligations may pressure funding readiness."),
        ],
        "Liquidity score unavailable because current/quick ratio data is incomplete.",
    )
    factors.append(
        _make_factor(
            key="liquidity",
            label="Liquidity and working-capital buffer",
            raw_score=liquidity_score,
            weight=0.18,
            band=liquidity_band,
            message=liquidity_message,
            evidence=f"Current ratio={current_ratio}, Quick ratio={quick_ratio}",
            source="Financial ratio engine: current ratio, quick ratio",
            positive_driver="Solid current/quick ratio supports near-term repayment capacity" if liquidity_score >= 75 else None,
            risk_driver="Short-term liquidity buffer is thin" if liquidity_score < 60 else None,
        )
    )

    debt_ratio = _metric_value(ratios.debt_ratio)
    net_debt_to_ebitda = _metric_value(ratios.net_debt_to_ebitda)
    leverage_score_candidates: list[int] = []
    leverage_messages: list[str] = []
    if debt_ratio is not None:
        score, band, message = _score_by_thresholds(
            debt_ratio,
            [
                (0.35, 90, "strong", "Debt ratio is conservative."),
                (0.55, 74, "adequate", "Debt ratio is manageable."),
                (0.70, 55, "watch", "Debt ratio is high and should be supported by cash flow."),
                (1.00, 32, "constrained", "Debt ratio is very high."),
            ],
            "Debt ratio unavailable.",
            higher_is_better=False,
        )
        leverage_score_candidates.append(score)
        leverage_messages.append(message)
    if net_debt_to_ebitda is not None:
        score, band, message = _score_by_thresholds(
            net_debt_to_ebitda,
            [
                (1.5, 90, "strong", "Net debt / EBITDA is conservative."),
                (3.0, 73, "adequate", "Net debt / EBITDA is acceptable for review."),
                (4.5, 52, "watch", "Net debt / EBITDA is elevated."),
                (99.0, 30, "constrained", "Net debt / EBITDA is highly leveraged."),
            ],
            "Net debt / EBITDA unavailable.",
            higher_is_better=False,
        )
        leverage_score_candidates.append(score)
        leverage_messages.append(message)
    leverage_score = round(sum(leverage_score_candidates) / len(leverage_score_candidates)) if leverage_score_candidates else 35
    leverage_band = _band_from_score(leverage_score)
    factors.append(
        _make_factor(
            key="leverage",
            label="Leverage and balance-sheet capacity",
            raw_score=leverage_score,
            weight=0.20,
            band=leverage_band,
            message=" ".join(leverage_messages) if leverage_messages else "Leverage score unavailable because debt metrics are incomplete.",
            evidence=f"Debt ratio={debt_ratio}, Net debt/EBITDA={net_debt_to_ebitda}",
            source="Financial ratio engine: debt ratio, net debt / EBITDA",
            positive_driver="Leverage profile leaves room for additional facilities" if leverage_score >= 75 else None,
            risk_driver="Leverage profile constrains incremental borrowing capacity" if leverage_score < 60 else None,
        )
    )

    interest_coverage = _metric_value(ratios.interest_coverage)
    dscr = _metric_value(ratios.dscr)
    coverage_anchor = None
    if interest_coverage is not None and dscr is not None:
        coverage_anchor = min(interest_coverage / 3.0, dscr)
    elif dscr is not None:
        coverage_anchor = dscr
    elif interest_coverage is not None:
        coverage_anchor = interest_coverage / 3.0
    coverage_score, coverage_band, coverage_message = _score_by_thresholds(
        coverage_anchor,
        [
            (1.8, 92, "strong", "Debt-service capacity is strong under current financials."),
            (1.25, 76, "adequate", "Debt-service capacity is acceptable for bank review."),
            (1.05, 55, "watch", "Debt-service cushion is thin and sensitive to rate or cash-flow shocks."),
            (0.0, 28, "constrained", "Debt-service metrics indicate constrained repayment capacity."),
        ],
        "Coverage score unavailable because interest coverage / DSCR data is incomplete.",
    )
    if dscr is not None and dscr < 1.0:
        hard_constraints.append("DSCR below 1.0x indicates repayment capacity stress under current assumptions.")
    elif dscr is not None and dscr < 1.1:
        hard_constraints.append("DSCR below 1.1x is a bank-review watch threshold and should be supported by refreshed cash-flow evidence.")
    factors.append(
        _make_factor(
            key="coverage",
            label="Interest coverage and DSCR",
            raw_score=coverage_score,
            weight=0.22,
            band=coverage_band,
            message=coverage_message,
            evidence=f"Interest coverage={interest_coverage}, DSCR={dscr}",
            source="Financial ratio engine: interest coverage, DSCR",
            positive_driver="Coverage metrics support bank-review readiness" if coverage_score >= 75 else None,
            risk_driver="Coverage cushion is weak under current debt-service load" if coverage_score < 60 else None,
        )
    )

    dso = _metric_value(ratios.dso)
    ecl_ar = _metric_value(ratios.expected_credit_loss_ar)
    receivables_zone = risk_diagnostics.receivables_risk.zone
    receivables_base = 80
    if receivables_zone == "low":
        receivables_base = 86
    elif receivables_zone == "moderate":
        receivables_base = 65
    elif receivables_zone == "elevated":
        receivables_base = 42
    elif receivables_zone is None:
        receivables_base = 40
    if dso is not None and dso > 90:
        receivables_base -= 15
    elif dso is not None and dso > 60:
        receivables_base -= 8
    receivables_score = max(20, min(95, receivables_base))
    factors.append(
        _make_factor(
            key="receivables_quality",
            label="Receivables quality and collection risk",
            raw_score=receivables_score,
            weight=0.15,
            band=_band_from_score(receivables_score),
            message=f"Receivables risk zone is {receivables_zone or 'unavailable'}.",
            evidence=f"DSO={dso}, Expected credit loss AR={ecl_ar}, zone={receivables_zone}",
            source="Receivables risk diagnostics and ratio engine",
            positive_driver="Receivables quality supports working-capital financing" if receivables_score >= 75 else None,
            risk_driver="Receivables ageing may reduce advance rate or increase monitoring" if receivables_score < 60 else None,
        )
    )

    projected_fcff = []
    if analysis.projections:
        projected_fcff = [year.fcff_primary for year in analysis.projections.projected_years]
    positive_fcff_years = sum(1 for value in projected_fcff if value > 0)
    cashflow_score = 35
    cashflow_message = "Projected FCFF unavailable or insufficient for cash-flow cushion scoring."
    if projected_fcff:
        ratio_positive = positive_fcff_years / len(projected_fcff)
        average_fcff = sum(projected_fcff) / len(projected_fcff)
        if ratio_positive >= 0.8 and average_fcff > 0:
            cashflow_score = 85
            cashflow_message = "Projected FCFF is mostly positive, supporting debt capacity."
        elif ratio_positive >= 0.6:
            cashflow_score = 68
            cashflow_message = "Projected FCFF is mixed but generally serviceable under assumptions."
        elif ratio_positive >= 0.4:
            cashflow_score = 50
            cashflow_message = "Projected FCFF is volatile and should be monitored."
        else:
            cashflow_score = 30
            cashflow_message = "Projected FCFF is weak or negative across most forecast years."
    factors.append(
        _make_factor(
            key="cashflow_valuation_cushion",
            label="Cash-flow and valuation cushion",
            raw_score=cashflow_score,
            weight=0.13,
            band=_band_from_score(cashflow_score),
            message=cashflow_message,
            evidence=f"Positive projected FCFF years={positive_fcff_years}/{len(projected_fcff) if projected_fcff else 0}",
            source="Projection engine and DCF valuation output",
            positive_driver="Forecast FCFF supports debt capacity" if cashflow_score >= 75 else None,
            risk_driver="Forecast FCFF does not provide a strong cushion" if cashflow_score < 60 else None,
        )
    )

    stress_score = coverage_score
    stress_message = "Stress overlay inferred from current DSCR and interest coverage."
    if dscr is not None:
        estimated_rate_shock_dscr = dscr * 0.88
        if estimated_rate_shock_dscr < 1.0:
            stress_score = min(stress_score, 38)
            stress_message = "Estimated rate-shock DSCR falls below 1.0x; stress resilience is constrained."
        elif estimated_rate_shock_dscr < 1.1:
            stress_score = min(stress_score, 52)
            stress_message = "Estimated rate-shock DSCR is close to covenant-style watch levels."
        elif estimated_rate_shock_dscr < 1.25:
            stress_score = min(stress_score, 66)
            stress_message = "Estimated rate-shock DSCR remains serviceable but with limited cushion."
        else:
            stress_score = min(stress_score, 82)
            stress_message = "Estimated rate-shock DSCR remains above key review thresholds."
    factors.append(
        _make_factor(
            key="stress_resilience",
            label="Stress resilience overlay",
            raw_score=stress_score,
            weight=0.12,
            band=_band_from_score(stress_score),
            message=stress_message,
            evidence=f"Base DSCR={dscr}, base interest coverage={interest_coverage}",
            source="Debt-service sensitivity overlay aligned to HIBOR/rate-shock stress testing",
            positive_driver="Debt-service cushion appears resilient to simple rate stress" if stress_score >= 75 else None,
            risk_driver="Rate or cash-flow stress could push coverage into watch range" if stress_score < 60 else None,
        )
    )

    weighted_score = round(sum(f.weighted_score for f in factors))
    composite_score = max(0, min(100, int(weighted_score)))

    # Integrity failures are a data-quality constraint, not an automatic business failure.
    failed_integrity = [check for check in analysis.integrity_checks if not check.passed]
    if failed_integrity:
        composite_score = max(0, composite_score - min(12, len(failed_integrity) * 4))
        hard_constraints.append("One or more accounting integrity checks failed; bank review requires corrected statements.")

    tier = _band_from_score(composite_score)
    readiness = _funding_readiness(composite_score, tier, hard_constraints)

    positive_drivers = [factor.positive_driver for factor in factors if factor.positive_driver]
    risk_drivers = [factor.risk_driver for factor in factors if factor.risk_driver]
    if failed_integrity:
        risk_drivers.append("Accounting integrity check failures reduce confidence in the scoring output")

    next_data_needed = []
    if analysis.snapshot.metadata and analysis.snapshot.metadata.get("preview_only"):
        next_data_needed.append("Persist verified Data Room records before production credit review")
    next_data_needed.extend(
        [
            "Consent-based CDI / bank transaction data for cash-flow verification",
            "Credit bureau / CCRA trade repayment history",
            "MPF or payroll signals for operating continuity where applicable",
            "Updated debt schedule with amortization and covenant terms",
        ]
    )

    return CreditScoringResult(
        company_id=snapshot.company_id,
        company_name=snapshot.company_name,
        composite_score=composite_score,
        risk_tier=tier,
        pd_proxy_band=_pd_proxy_band(composite_score),
        funding_readiness=readiness,
        factors=factors,
        positive_drivers=positive_drivers,
        risk_drivers=risk_drivers,
        hard_constraints=hard_constraints,
        next_data_needed=next_data_needed,
        methodology_label="Deterministic SME PD Proxy Scorecard: ratios + receivables + FCFF + stress overlay",
        disclaimer=DISCLAIMER,
        warnings=warnings,
    )
