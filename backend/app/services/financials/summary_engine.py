"""
Financial Analysis Summary Engine
==================================
Consolidates ratio, risk diagnostics, projection, and valuation outputs into
a single context-only summary for downstream Phase 3 advisory usage.

All conclusions are context-only.  No underwriting, credit approval, or
lending decisions are expressed or implied.  Company records required for
production advisory or credit analysis.
"""
from typing import List, Optional

from app.models.financials import (
    CompanyFinancialSnapshot,
    FinancialRatios,
    FinancialRiskDiagnostics,
    ProjectionAnalysis,
    ValuationAnalysis,
    FinancialSignal,
    FinancialAnalysisSummary,
)

# ---------------------------------------------------------------------------
# Band helpers
# ---------------------------------------------------------------------------

BANDS = ("strong", "adequate", "watch", "constrained", "unavailable")

def _worst_band(*bands: str) -> str:
    priority = {b: i for i, b in enumerate(BANDS)}
    return max(bands, key=lambda b: priority.get(b, 0))

def _best_band(*bands: str) -> str:
    priority = {b: i for i, b in enumerate(BANDS)}
    return min(bands, key=lambda b: priority.get(b, 0))

# ---------------------------------------------------------------------------
# Individual signal builders
# ---------------------------------------------------------------------------

def _signal_dscr(ratios: FinancialRatios) -> FinancialSignal:
    metric = ratios.dscr
    if metric.value is None:
        return FinancialSignal(
            key="dscr",
            label="Debt Service Coverage Ratio (DSCR)",
            band="unavailable",
            message="DSCR could not be calculated from available data.",
            evidence="No DSCR value available.",
            source="financial_ratios",
            warnings=["DSCR unavailable — company records required for production analysis."]
        )
    v = metric.value
    if v >= 1.50:
        band, msg = "strong", f"DSCR of {v:.2f}x indicates comfortable debt service coverage."
    elif v >= 1.25:
        band, msg = "adequate", f"DSCR of {v:.2f}x meets standard banking-grade threshold (≥1.25x)."
    elif v >= 1.00:
        band, msg = "watch", f"DSCR of {v:.2f}x is between 1.0x and 1.25x — below standard banking-grade threshold. Debt service warrants monitoring."
    else:
        band, msg = "constrained", f"DSCR of {v:.2f}x is below 1.0x — current cash flow does not fully cover scheduled debt obligations under this demo analysis."

    return FinancialSignal(
        key="dscr",
        label="Debt Service Coverage Ratio (DSCR)",
        value=v,
        unit="x",
        band=band,
        message=msg,
        evidence=metric.label,
        source="financial_ratios",
        warnings=[metric.warning] if metric.warning else []
    )

def _signal_current_ratio(ratios: FinancialRatios) -> FinancialSignal:
    metric = ratios.current_ratio
    if metric.value is None:
        return FinancialSignal(
            key="current_ratio", label="Current Ratio", band="unavailable",
            message="Current ratio unavailable.", evidence="No value.", source="financial_ratios"
        )
    v = metric.value
    if v >= 1.50:
        band, msg = "adequate", f"Current ratio of {v:.2f}x indicates adequate short-term liquidity."
    elif v >= 1.00:
        band, msg = "watch", f"Current ratio of {v:.2f}x is below 1.5x — short-term liquidity warrants monitoring."
    else:
        band, msg = "constrained", f"Current ratio of {v:.2f}x is below 1.0x — current liabilities exceed current assets under this demo analysis."
    return FinancialSignal(
        key="current_ratio", label="Current Ratio", value=v, unit="x", band=band,
        message=msg, evidence=metric.label, source="financial_ratios",
        warnings=[metric.warning] if metric.warning else []
    )

def _signal_quick_ratio(ratios: FinancialRatios) -> FinancialSignal:
    metric = ratios.quick_ratio
    if metric.value is None:
        return FinancialSignal(
            key="quick_ratio", label="Quick Ratio", band="unavailable",
            message="Quick ratio unavailable.", evidence="No value.", source="financial_ratios"
        )
    v = metric.value
    if v >= 1.00:
        band, msg = "adequate", f"Quick ratio of {v:.2f}x indicates adequate near-term liquidity."
    elif v >= 0.75:
        band, msg = "watch", f"Quick ratio of {v:.2f}x is below 1.0x — near-term liquidity warrants monitoring."
    else:
        band, msg = "constrained", f"Quick ratio of {v:.2f}x is below 0.75x — limited liquid asset buffer under this demo analysis."
    return FinancialSignal(
        key="quick_ratio", label="Quick Ratio", value=v, unit="x", band=band,
        message=msg, evidence=metric.label, source="financial_ratios",
        warnings=[metric.warning] if metric.warning else []
    )

def _signal_interest_coverage(ratios: FinancialRatios) -> FinancialSignal:
    metric = ratios.interest_coverage
    if metric.value is None:
        return FinancialSignal(
            key="interest_coverage", label="Interest Coverage", band="unavailable",
            message="Interest coverage unavailable.", evidence="No value.", source="financial_ratios"
        )
    v = metric.value
    if v >= 4.0:
        band, msg = "strong", f"Interest coverage of {v:.2f}x indicates strong earnings buffer relative to interest expense."
    elif v >= 2.0:
        band, msg = "adequate", f"Interest coverage of {v:.2f}x is adequate."
    elif v >= 1.0:
        band, msg = "watch", f"Interest coverage of {v:.2f}x — earnings cover interest but with limited headroom."
    else:
        band, msg = "constrained", f"Interest coverage of {v:.2f}x — EBIT does not fully cover interest expense under this demo analysis."
    return FinancialSignal(
        key="interest_coverage", label="Interest Coverage", value=v, unit="x", band=band,
        message=msg, evidence=metric.label, source="financial_ratios",
        warnings=[metric.warning] if metric.warning else []
    )

def _signal_net_debt_ebitda(ratios: FinancialRatios) -> FinancialSignal:
    metric = ratios.net_debt_to_ebitda
    if metric.value is None:
        return FinancialSignal(
            key="net_debt_ebitda", label="Net Debt / EBITDA", band="unavailable",
            message="Net Debt / EBITDA unavailable.", evidence="No value.", source="financial_ratios"
        )
    v = metric.value
    if v < 2.0:
        band, msg = "strong", f"Net Debt / EBITDA of {v:.2f}x indicates low leverage relative to earnings."
    elif v < 3.5:
        band, msg = "watch", f"Net Debt / EBITDA of {v:.2f}x — moderate leverage. Warrants monitoring under this demo analysis."
    else:
        band, msg = "constrained", f"Net Debt / EBITDA of {v:.2f}x — high leverage relative to EBITDA under this demo analysis."
    return FinancialSignal(
        key="net_debt_ebitda", label="Net Debt / EBITDA", value=v, unit="x", band=band,
        message=msg, evidence=metric.label, source="financial_ratios",
        warnings=[metric.warning] if metric.warning else []
    )

def _signal_altman_z(risk_diagnostics: FinancialRiskDiagnostics) -> FinancialSignal:
    z = risk_diagnostics.altman_z_score
    if z.value is None:
        return FinancialSignal(
            key="altman_z", label="Altman Z'' Score", band="unavailable",
            message="Altman Z'' Score unavailable.", evidence="No value.", source="risk_diagnostics",
            warnings=z.warnings
        )
    v = z.value
    band_map = {"safe": "strong", "grey": "watch", "distress": "constrained"}
    band = band_map.get(z.band or "", "unavailable")
    msg_map = {
        "safe": f"Altman Z'' Score of {v:.2f} is in the safe zone — company profile indicates lower financial distress probability under this demo analysis.",
        "grey": f"Altman Z'' Score of {v:.2f} is in the grey zone — financial signals are mixed. Warrants monitoring.",
        "distress": f"Altman Z'' Score of {v:.2f} is in the distress zone — financial signals are weak under this demo analysis.",
    }
    msg = msg_map.get(z.band or "", f"Altman Z'' Score of {v:.2f}.")
    return FinancialSignal(
        key="altman_z", label="Altman Z'' Score", value=v, band=band,
        message=msg, evidence=z.methodology_label, source="risk_diagnostics",
        warnings=z.warnings
    )

def _signal_receivables(risk_diagnostics: FinancialRiskDiagnostics) -> FinancialSignal:
    r = risk_diagnostics.receivables_risk
    zone_map = {"low": "adequate", "moderate": "watch", "elevated": "constrained"}
    band = zone_map.get(r.zone or "", "unavailable")
    ecl_str = f"ECL ratio: {r.ecl_ratio:.2%}" if r.ecl_ratio is not None else "ECL ratio unavailable"
    conc_str = f"90+ day AR concentration: {r.ar_90_plus_concentration:.2%}" if r.ar_90_plus_concentration is not None else ""
    evidence = "; ".join(filter(None, [ecl_str, conc_str]))
    msg_map = {
        "adequate": "Receivables risk profile is within normal range under this demo analysis.",
        "watch": "Receivables profile warrants monitoring — ECL ratio or 90+ day AR concentration is above low-risk thresholds.",
        "constrained": "Elevated receivables risk — high ECL ratio or significant 90+ day AR concentration under this demo analysis.",
        "unavailable": "Receivables risk profile unavailable.",
    }
    return FinancialSignal(
        key="receivables_risk", label="Receivables Risk", value=r.ecl_ratio,
        unit="ecl_ratio", band=band,
        message=msg_map.get(band, ""),
        evidence=evidence or r.methodology_label,
        source="risk_diagnostics",
        warnings=r.warnings
    )

def _signal_fcff(projections: Optional[ProjectionAnalysis]) -> FinancialSignal:
    if projections is None or not projections.projected_years:
        return FinancialSignal(
            key="fcff_forecast", label="FCFF 5-Year Forecast", band="unavailable",
            message="No projection data available.", evidence="Projections not computed.",
            source="projection_engine"
        )
    negative_years = [yr.year for yr in projections.projected_years if yr.fcff_primary < 0.0]
    if not negative_years:
        avg = sum(yr.fcff_primary for yr in projections.projected_years) / len(projections.projected_years)
        return FinancialSignal(
            key="fcff_forecast", label="FCFF 5-Year Forecast", value=avg, unit="currency",
            band="adequate",
            message="Projected FCFF is positive across all 5 forecast years under current driver assumptions.",
            evidence="Assumptions-based driver forecast — company records required for production context.",
            source="projection_engine",
            warnings=projections.warnings
        )
    else:
        return FinancialSignal(
            key="fcff_forecast", label="FCFF 5-Year Forecast", band="watch",
            message=f"Projected FCFF is negative in year(s) {negative_years} under current driver assumptions. Warrants review.",
            evidence="Assumptions-based driver forecast — company records required for production context.",
            source="projection_engine",
            warnings=projections.warnings
        )

def _signal_valuation(valuation: Optional[ValuationAnalysis]) -> FinancialSignal:
    if valuation is None:
        return FinancialSignal(
            key="valuation_context", label="Valuation Context", band="unavailable",
            message="Valuation not computed.", evidence="No valuation data.", source="valuation_engine"
        )
    dcf = valuation.dcf
    ev = dcf.enterprise_value
    eq = dcf.equity_value
    tv_share = dcf.terminal_value_share_of_enterprise_value

    warnings: List[str] = list(valuation.warnings)
    if ev is None:
        return FinancialSignal(
            key="valuation_context", label="Valuation Context", band="unavailable",
            message="Enterprise value could not be computed under current assumptions.",
            evidence="WACC may be ≤ terminal growth rate — assumptions-based context only.",
            source="valuation_engine", warnings=warnings
        )
    if eq is not None and eq < 0.0:
        return FinancialSignal(
            key="valuation_context", label="Valuation Context",
            value=eq, unit="currency", band="constrained",
            message=f"Implied equity value ({eq:,.0f}) is negative — net debt exceeds enterprise value under current assumptions. Context only.",
            evidence="Assumptions-based DCF — company records required for production advisory.",
            source="valuation_engine", warnings=warnings
        )

    # Check sanity passes
    all_critical_pass = all(
        c.status == "pass"
        for c in valuation.sanity_checks
        if c.name in ("WACC vs Terminal Growth", "Implied EV/EBITDA")
    )
    band = "adequate" if all_critical_pass else "watch"
    tv_note = ""
    if tv_share is not None and tv_share > 0.85:
        band = "watch"
        tv_note = f" Terminal value represents {tv_share:.0%} of enterprise value — high dependency."

    ev_ebitda = dcf.implied_ev_ebitda
    ev_str = f"EV ~{ev:,.0f}" if ev else ""
    eq_str = f" / Equity ~{eq:,.0f}" if eq else ""
    ebitda_str = f" / EV/EBITDA ~{ev_ebitda:.1f}x" if ev_ebitda else ""

    return FinancialSignal(
        key="valuation_context", label="Valuation Context",
        value=ev, unit="currency", band=band,
        message=(
            f"Assumptions-based DCF valuation context: {ev_str}{eq_str}{ebitda_str}.{tv_note} "
            "Context only — company records required for production advisory."
        ),
        evidence="Assumptions-based WACC + DCF — demo financial analysis.",
        source="valuation_engine", warnings=warnings
    )

# ---------------------------------------------------------------------------
# Band aggregation
# ---------------------------------------------------------------------------

def _derive_liquidity_band(current: FinancialSignal, quick: FinancialSignal) -> str:
    return _worst_band(current.band, quick.band)

def _derive_debt_service_band(dscr: FinancialSignal, interest: FinancialSignal) -> str:
    return _worst_band(dscr.band, interest.band)

def _derive_leverage_band(nd_ebitda: FinancialSignal) -> str:
    return nd_ebitda.band

def _derive_receivables_band(rec: FinancialSignal) -> str:
    return rec.band

def _derive_valuation_band(val: FinancialSignal) -> str:
    return val.band

def _derive_overall_band(
    liquidity: str,
    debt_service: str,
    leverage: str,
    receivables: str,
    valuation: str
) -> str:
    all_bands = [liquidity, debt_service, leverage, receivables, valuation]
    # Constrained if any critical section is constrained
    if "constrained" in (liquidity, debt_service):
        return "constrained"
    # Watch if 2+ sections are watch/constrained
    watch_count = sum(1 for b in all_bands if b in ("watch", "constrained"))
    if watch_count >= 2:
        return "watch"
    if all(b in ("strong", "adequate") for b in all_bands):
        if all(b == "strong" for b in all_bands if b != "unavailable"):
            return "strong"
        return "adequate"
    return "watch"

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_financial_analysis_summary(
    snapshot: CompanyFinancialSnapshot,
    ratios: FinancialRatios,
    risk_diagnostics: FinancialRiskDiagnostics,
    projections: Optional[ProjectionAnalysis],
    valuation: Optional[ValuationAnalysis]
) -> FinancialAnalysisSummary:
    """
    Builds a unified Financial Analysis Summary from all Phase 1 outputs.

    All language is context-only.  No underwriting, credit decisions, or
    lending approvals are expressed or implied.
    """
    # --- Build individual signals ---
    sig_dscr = _signal_dscr(ratios)
    sig_current = _signal_current_ratio(ratios)
    sig_quick = _signal_quick_ratio(ratios)
    sig_interest = _signal_interest_coverage(ratios)
    sig_nd_ebitda = _signal_net_debt_ebitda(ratios)
    sig_altman = _signal_altman_z(risk_diagnostics)
    sig_rec = _signal_receivables(risk_diagnostics)
    sig_fcff = _signal_fcff(projections)
    sig_val = _signal_valuation(valuation)

    key_signals = [
        sig_dscr,
        sig_current,
        sig_quick,
        sig_interest,
        sig_nd_ebitda,
        sig_altman,
        sig_rec,
        sig_fcff,
        sig_val,
    ]

    # --- Aggregate bands ---
    liquidity_band = _derive_liquidity_band(sig_current, sig_quick)
    debt_service_band = _derive_debt_service_band(sig_dscr, sig_interest)
    leverage_band = _derive_leverage_band(sig_nd_ebitda)
    receivables_band = _derive_receivables_band(sig_rec)
    valuation_band = _derive_valuation_band(sig_val)
    overall_band = _derive_overall_band(
        liquidity_band, debt_service_band, leverage_band,
        receivables_band, valuation_band
    )

    # --- Build watch items, strengths, constraints ---
    watch_items: List[str] = []
    strengths: List[str] = []
    constraints: List[str] = []

    for sig in key_signals:
        if sig.band == "constrained":
            constraints.append(f"{sig.label}: {sig.message}")
        elif sig.band == "watch":
            watch_items.append(f"{sig.label}: {sig.message}")
        elif sig.band in ("strong", "adequate"):
            strengths.append(f"{sig.label}: {sig.message}")

    # Altman Z insights
    if sig_altman.band == "watch":
        watch_items.append(
            "Altman Z'' Score is in the grey zone — financial signals are mixed. "
            "Company records required for production assessment."
        )

    # TV concentration watch
    if valuation is not None and valuation.dcf.terminal_value_share_of_enterprise_value is not None:
        tv_share = valuation.dcf.terminal_value_share_of_enterprise_value
        if tv_share > 0.85:
            watch_items.append(
                f"Terminal value represents {tv_share:.0%} of enterprise value — "
                "valuation context is highly sensitive to terminal growth assumptions."
            )

    # --- Deduplicate ---
    def _dedup(lst: List[str]) -> List[str]:
        seen = set()
        out = []
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    watch_items = _dedup(watch_items)
    strengths = _dedup(strengths)
    constraints = _dedup(constraints)

    # --- Next data needed ---
    next_data_needed = [
        "Audited financial statements for production financial analysis.",
        "Debt schedule with full amortization detail.",
        "Receivables aging report (actual, not estimated).",
    ]
    if projections is None:
        next_data_needed.append("Management cash flow projections for forecast validation.")
    if valuation is None or valuation.dcf.enterprise_value is None:
        next_data_needed.append("Market comparables and industry beta data for production valuation context.")

    # --- Collect summary warnings ---
    summary_warnings: List[str] = [
        "This is a demo financial analysis summary. "
        "All outputs are assumptions-based and context-only. "
        "Company records required for production advisory or credit analysis."
    ]

    return FinancialAnalysisSummary(
        overallBand=overall_band,
        liquidityBand=liquidity_band,
        debtServiceBand=debt_service_band,
        leverageBand=leverage_band,
        receivablesBand=receivables_band,
        valuationBand=valuation_band,
        keySignals=key_signals,
        watchItems=watch_items,
        strengths=strengths,
        constraints=constraints,
        nextDataNeeded=next_data_needed,
        warnings=summary_warnings,
    )
