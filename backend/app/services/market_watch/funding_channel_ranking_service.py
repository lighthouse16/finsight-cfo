"""
Funding Channel Ranking v1 for Market Watch.

Provides context-only ranking of candidate funding channels based on
fixture/workspace-derived company context, timing signals, and industry health.
This is NOT an approval, underwriting, or lending decision.
"""

from typing import Optional

from app.models.market_watch import (
    FundingChannelComponent,
    FundingChannelItem,
    FundingChannelKey,
    FundingChannelProvenance,
    FundingChannelRankingResponse,
    FundingCompanyContext,
    FundingFitBand,
    FundingRankingBand,
    IndustryHealthResponse,
    TimingSignalResponse,
)
from app.services.market_watch.company_context import (
    get_demo_company_profile,
    get_company_exposures,
)
from app.services.market_watch.timing_signal_service import get_timing_signal
from app.services.market_watch.industry_health_service import get_industry_health
from app.services.market_watch.source_registry import build_provenance

DISCLAIMER = (
    "Channel ranking is context-only for planning support. "
    "It does not constitute financing approval, underwriting, or a lending decision. "
    "Production company records and lender review are required before any financing application."
)

_WARNING_BASE = (
    "Funding Channel Ranking v1 is fixture/workspace-derived. "
    "Production company records required for lender review."
)


async def get_funding_channel_ranking() -> FundingChannelRankingResponse:
    """Build context-only funding channel ranking from available workspace context."""

    # --- Get underlying context ---
    profile = get_demo_company_profile()
    exposures = get_company_exposures()

    timing: TimingSignalResponse = await get_timing_signal()
    industry: IndustryHealthResponse = await get_industry_health()

    # --- Derive company context flags ---
    # DSCR: net income approximation from profile (margin * revenue = est. net)
    # Using rough estimate from available demo data
    dscr: Optional[float] = None
    est_annual_debt_service = profile.monthlyDebtServiceHkd * 12
    if est_annual_debt_service > 0:
        # Rough net income estimate based on gross margin and typical SME expense ratio
        est_net_income = int(profile.revenueTtmHkd * (profile.grossMarginPercent / 100) * 0.35)
        dscr = round(est_net_income / est_annual_debt_service, 2)

    floating_rate_note: Optional[str] = None
    for exp in exposures:
        if exp.id == "floating-rate-debt":
            floating_rate_note = f"HKD {profile.floatingRateDebtHkd:,} floating-rate facility"

    company_context = FundingCompanyContext(
        companyName=profile.companyName,
        sector=profile.sector,
        geography=profile.geography,
        dataMode="demo_workspace",
        dscr=dscr,
        floatingRateExposure=floating_rate_note,
        workingCapitalGap=f"HKD {profile.workingCapitalGapHkd:,}" if profile.workingCapitalGapHkd else None,
        dsoWatch=profile.dsoDays > 45,
        fxExposure=(
            profile.cnySupplierPayablesPercent > 20
            or profile.usdImportCostPercent > 30
        ),
        importCostStress=profile.usdImportCostPercent > 50,
    )

    # --- Rule-based scoring per channel ---
    # Score range 0-100; higher = more suitable given available context
    channels: list[tuple[FundingChannelKey, str, int, FundingFitBand, str, list[str], str, list[str]]] = []
    # (key, label, score, fitBand, rationale, supportingSignals, source, constraints)

    # 1. Working Capital Line
    wc_score = 50
    wc_signals: list[str] = []
    if company_context.workingCapitalGap:
        wc_score += 20
        wc_signals.append("working-capital gap present")
    if company_context.dsoWatch:
        wc_score += 10
        wc_signals.append("DSO above sector benchmark")
    if industry.workingCapitalSignal in ("stressed", "watch"):
        wc_score += 10
        wc_signals.append(f"industry working-capital context: {industry.workingCapitalSignal}")
    if timing.goldenTimingBand == "favorable":
        wc_score += 5
    elif timing.goldenTimingBand == "cautious":
        wc_score -= 5
    wc_fit: FundingFitBand = "strong_fit" if wc_score >= 75 else "moderate_fit" if wc_score >= 50 else "watch_fit"
    channels.append((
        "working_capital_line", "Working Capital Line", wc_score, wc_fit,
        "Working capital line addresses the identified working-capital gap and DSO stretch.",
        wc_signals if wc_signals else ["general working-capital context"],
        "company_context_v1 · timing_v1 · industry_health_v1",
        ["subject to lender review", "production company records required"],
    ))

    # 2. Receivables Financing
    rf_score = 40
    rf_signals: list[str] = []
    if company_context.dsoWatch:
        rf_score += 20
        rf_signals.append("DSO above benchmark suggests receivables monetisation opportunity")
    if profile.receivablesHkd > 0:
        rf_score += 10
        rf_signals.append(f"receivables base HKD {profile.receivablesHkd:,}")
    if industry.demandSignal == "expanding":
        rf_score += 5
        rf_signals.append("industry demand context supports receivables quality")
    if industry.workingCapitalSignal in ("stressed", "watch"):
        rf_score += 10
        rf_signals.append(f"industry working-capital context: {industry.workingCapitalSignal}")
    rf_fit: FundingFitBand = "strong_fit" if rf_score >= 75 else "moderate_fit" if rf_score >= 50 else "watch_fit"
    channels.append((
        "receivables_financing", "Receivables Financing", rf_score, rf_fit,
        "Receivables financing matches the elevated DSO and can improve working-capital liquidity.",
        rf_signals if rf_signals else ["receivables context from company profile"],
        "company_context_v1 · industry_health_v1",
        ["subject to lender review", "eligible receivables verification required", "production company records required"],
    ))

    # 3. Trade Finance / LC
    tf_score = 30
    tf_signals: list[str] = []
    if company_context.importCostStress:
        tf_score += 20
        tf_signals.append("USD import-cost stress present")
    if company_context.fxExposure:
        tf_score += 10
        tf_signals.append("FX exposure (CNY payables / USD imports) detected")
    if profile.cnySupplierPayablesPercent > 0:
        tf_score += 10
        tf_signals.append(f"CNY supplier payables {profile.cnySupplierPayablesPercent}%")
    if industry.demandSignal == "expanding":
        tf_score += 5
        tf_signals.append("industry demand supports trade flows")
    tf_fit: FundingFitBand = "strong_fit" if tf_score >= 75 else "moderate_fit" if tf_score >= 50 else "watch_fit"
    channels.append((
        "trade_finance_lc", "Trade Finance / LC", tf_score, tf_fit,
        "Trade finance or letter of credit aligns with the import-heavy cost structure and cross-border supplier exposure.",
        tf_signals if tf_signals else ["trade/cross-border context from company profile"],
        "company_context_v1 · industry_health_v1",
        ["subject to lender review", "trade documentation required", "production company records required"],
    ))

    # 4. Term Loan
    tl_score = 25
    tl_signals: list[str] = []
    if company_context.dscr is not None and company_context.dscr < 1.2:
        tl_score -= 15
        tl_signals.append(f"DSCR {company_context.dscr:.2f} suggests balance-sheet review before long-tenor debt")
    elif company_context.dscr is not None and company_context.dscr >= 1.5:
        tl_score += 10
        tl_signals.append(f"DSCR {company_context.dscr:.2f} supports longer-tenor consideration")
    if company_context.floatingRateExposure:
        tl_score -= 5
        tl_signals.append("existing floating-rate debt would increase fixed-charge burden")
    if industry.industryHealthBand in ("resilient", "stable"):
        tl_score += 10
        tl_signals.append(f"industry health context: {industry.industryHealthBand}")
    elif industry.industryHealthBand in ("stressed", "watch"):
        tl_score -= 5
        tl_signals.append(f"industry health context: {industry.industryHealthBand}")
    if timing.goldenTimingBand == "cautious":
        tl_score -= 5
    tl_score = max(tl_score, 0)
    tl_fit: FundingFitBand = "strong_fit" if tl_score >= 75 else "moderate_fit" if tl_score >= 50 else "watch_fit"
    channels.append((
        "term_loan", "Term Loan", tl_score, tl_fit,
        "Term loan is constrained by current DSCR context and floating-rate exposure. Balance-sheet review and production records would clarify tenor suitability.",
        tl_signals if tl_signals else ["balance-sheet context from company profile"],
        "company_context_v1 · timing_v1 · industry_health_v1",
        ["subject to lender review", "balance-sheet review recommended", "production records and company financials required"],
    ))

    # 5. FX Hedging Context
    fx_score = 20
    fx_signals: list[str] = []
    if company_context.fxExposure:
        fx_score += 20
        fx_signals.append("FX exposure (CNY payables / USD imports) detected")
    if company_context.importCostStress:
        fx_score += 15
        fx_signals.append("import-cost stress present")
    if timing.goldenTimingBand == "cautious":
        fx_score += 10
        fx_signals.append("market timing context suggests rate volatility watch")
    fx_fit: FundingFitBand = "strong_fit" if fx_score >= 75 else "moderate_fit" if fx_score >= 50 else "watch_fit"
    channels.append((
        "fx_hedging_context", "FX Hedging Context", fx_score, fx_fit,
        "FX hedging instruments (forwards, options) should be evaluated given the significant USD import and CNY payable exposure.",
        fx_signals if fx_signals else ["FX exposure from company profile"],
        "company_context_v1 · timing_v1",
        ["not a financing channel", "subject to counterparty credit review", "derivative documentation required"],
    ))

    # --- Sort by score descending ---
    channels_sorted = sorted(channels, key=lambda c: c[2], reverse=True)

    top_key = channels_sorted[0][0]

    # --- Determine ranking band ---
    top_score = channels_sorted[0][2]
    if top_score >= 70:
        ranking_band: FundingRankingBand = "working_capital_priority"
    elif top_key in ("working_capital_line", "receivables_financing"):
        ranking_band = "trade_cycle_priority"
    elif top_key == "term_loan":
        ranking_band = "balance_sheet_review"
    else:
        ranking_band = "risk_context_priority"

    # --- Build channel items ---
    channel_items = [
        FundingChannelItem(
            key=key,
            label=label,
            rank=idx + 1,
            fitBand=fit,
            score=score,
            useCase=_use_case_for_key(key),
            rationale=rationale,
            supportingSignals=signals,
            source=source,
            constraints=constraints,
        )
        for idx, (key, label, score, fit, rationale, signals, source, constraints) in enumerate(channels_sorted)
    ]

    # --- Build components ---
    components = [
        FundingChannelComponent(
            signal="timingContext",
            label="Market timing context",
            band=timing.goldenTimingBand,
            explanation=timing.explanation,
        ),
        FundingChannelComponent(
            signal="industryHealthContext",
            label="Industry health context",
            band=industry.industryHealthBand,
            explanation=industry.explanation,
        ),
        FundingChannelComponent(
            signal="dscrContext",
            label="Debt-service context",
            band="watch" if company_context.dscr is not None and company_context.dscr < 1.2 else "neutral",
            explanation=f"DSCR estimated at {company_context.dscr:.2f} based on demo financial profile." if company_context.dscr else "DSCR unavailable without company financials.",
        ),
        FundingChannelComponent(
            signal="fxExposureContext",
            label="FX / import-cost context",
            band="caution" if company_context.fxExposure else "neutral",
            explanation=f"USD import {profile.usdImportCostPercent}% of COGS, CNY payables {profile.cnySupplierPayablesPercent}% of payables." if company_context.fxExposure else "No significant FX exposure detected from available context.",
        ),
    ]

    # --- Provenance ---
    provenance = FundingChannelProvenance(
        **build_provenance("funding_channel_ranking_v1"),
    )

    # --- Explanation ---
    top_channel_label = channel_items[0].label
    explanation = (
        f"{company_context.companyName}'s context suggests {top_channel_label} as the "
        f"top candidate channel ({ranking_band.replace('_', ' ')}). "
        f"Ranking is based on company profile, working-capital context, market timing signal, "
        f"industry health context, and FX exposure. Production records and lender review required."
    )

    # --- Warnings ---
    warnings = [
        _WARNING_BASE,
    ]
    if timing.warnings:
        warnings.extend(timing.warnings[:1])
    if industry.warnings:
        warnings.extend(industry.warnings[:1])
    if company_context.dscr is not None and company_context.dscr < 1.0:
        warnings.append("Estimated DSCR is below 1.0x; debt-service capacity review recommended before any additional borrowing.")

    return FundingChannelRankingResponse(
        mode="context_only",
        companyContext=company_context,
        rankingBand=ranking_band,
        channels=channel_items,
        topChannelKey=top_key,
        explanation=explanation,
        components=components,
        provenance=provenance,
        source=provenance,
        warnings=warnings,
        disclaimer=DISCLAIMER,
    )


def _use_case_for_key(key: FundingChannelKey) -> str:
    mapping = {
        "working_capital_line": (
            "Short-term revolving liquidity for day-to-day operations, "
            "inventory builds, and bridging working-capital gaps."
        ),
        "receivables_financing": (
            "Monetisation of outstanding invoices to accelerate cash conversion "
            "and reduce DSO-driven working-capital pressure."
        ),
        "trade_finance_lc": (
            "Letters of credit or trade facilities to support import purchases, "
            "supplier payments, and cross-border transactions."
        ),
        "term_loan": (
            "Medium-to-long-term financing for capex, expansion, or balance-sheet "
            "restructuring; subject to DSCR and collateral review."
        ),
        "fx_hedging_context": (
            "Derivative instruments (forwards, options, swaps) to manage "
            "currency risk on USD import costs and CNY supplier payables."
        ),
    }
    return mapping.get(key, key)
