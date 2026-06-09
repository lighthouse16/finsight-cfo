"""
Red Flags & Macro Risk Summary v1 for Market Watch.

Consolidates existing Market Watch phase 2 signals into a context-only
red-flag summary dashboard. This is NOT a credit decision, underwriting,
or lending recommendation.

If any underlying input fails or is unavailable, the service does not crash —
it adds a warning and continues with partial context.
"""

from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.models.market_watch import (
    RedFlagCategory,
    RedFlagItem,
    RedFlagMitigant,
    RedFlagProvenance,
    RedFlagsMacroSummaryResponse,
    RedFlagsSummaryComponent,
    RedFlagSeverity,
    SummaryBand,
)
from app.services.market_watch.fixtures import get_red_flags_macro_summary_fixture
from app.services.market_watch.timing_signal_service import get_timing_signal
from app.services.market_watch.industry_health_service import get_industry_health
from app.services.market_watch.funding_channel_ranking_service import get_funding_channel_ranking
from app.services.market_watch.cross_border_funding_context_service import get_cross_border_funding_context
from app.services.market_watch.company_context import get_demo_company_profile, get_company_exposures
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity
from app.services.market_watch.fx_gba_service import get_fx_gba

DISCLAIMER = (
    "Red Flags & Macro Risk Summary v1 is context-only for planning support. "
    "It consolidates market-watch signals and is not a credit decision, "
    "underwriting assessment, or lending recommendation."
)

_WARNING_BASE = (
    "Red Flags & Macro Risk Summary v1 is fixture/workspace-derived. "
    "Provider integration pending for CME FedWatch, ChinaData.live/IHS, and LPR references."
)


async def get_red_flags_macro_summary() -> RedFlagsMacroSummaryResponse:
    """Build context-only red-flag summary from available Phase 2 signals."""
    if settings.MARKET_WATCH_USE_FIXTURES:
        return get_red_flags_macro_summary_fixture()

    # --- Gather underlying inputs (each may fail independently) ---
    warnings: list[str] = [_WARNING_BASE]
    red_flags: list[RedFlagItem] = []
    mitigants: list[RedFlagMitigant] = []
    components: list[RedFlagsSummaryComponent] = []
    sources_used: list[str] = []

    # 1. Timing signal
    try:
        timing = await get_timing_signal()
        sources_used.append("timing_signal_v1")
        _add_timing_red_flag(timing, red_flags, components)
    except Exception as e:
        warnings.append(f"Timing signal unavailable: {e}")

    # 2. Industry health
    try:
        industry = await get_industry_health()
        sources_used.append("industry_health_v1")
        _add_sector_red_flag(industry, red_flags, components, mitigants)
    except Exception as e:
        warnings.append(f"Industry health signal unavailable: {e}")

    # 3. Funding channel ranking
    try:
        ranking = await get_funding_channel_ranking()
        sources_used.append("funding_channel_ranking_v1")
        _add_funding_red_flag(ranking, red_flags, components, mitigants)
    except Exception as e:
        warnings.append(f"Funding channel ranking unavailable: {e}")

    # 4. Cross-border funding context
    try:
        cb_context = await get_cross_border_funding_context()
        sources_used.append("cross_border_funding_context_v1")
        _add_cross_border_red_flag(cb_context, red_flags, components)
    except Exception as e:
        warnings.append(f"Cross-border funding context unavailable: {e}")

    # 5. Rates & liquidity
    try:
        rates_liquidity = await get_rates_liquidity()
        sources_used.append("rates_liquidity_v1")
        _add_rates_red_flag(rates_liquidity, red_flags, components)
    except Exception as e:
        warnings.append(f"Rates/liquidity data unavailable: {e}")

    # 6. FX & GBA for FX red flag
    try:
        fx_gba = await get_fx_gba()
        sources_used.append("fx_gba_v1")
        _add_fx_red_flag(fx_gba, red_flags, components)
    except Exception as e:
        warnings.append(f"FX/GBA data unavailable: {e}")

    # 7. Company context for liquidity / working-capital flags
    try:
        profile = get_demo_company_profile()
        sources_used.append("company_context_v1")
        _add_liquidity_red_flag(profile, red_flags, components, mitigants)
    except Exception as e:
        warnings.append(f"Company context unavailable: {e}")

    # --- Determine summary band ---
    summary_band, headline = _compute_summary_band(red_flags)

    # --- Provenance ---
    now = datetime.utcnow().isoformat() + "Z"
    provenance = RedFlagProvenance(
        source="market_watch_red_flags_macro_summary_v1",
        provider="FinSight CFO Market Watch",
        asOf=None,
        freshness="Workspace",
    )

    return RedFlagsMacroSummaryResponse(
        mode="context_only",
        summaryBand=summary_band,
        headline=headline,
        redFlags=red_flags,
        mitigants=mitigants,
        components=components,
        provenance=provenance,
        source=provenance,
        warnings=warnings,
        disclaimer=DISCLAIMER,
    )


# ---------------------------------------------------------------------------
# Individual red-flag builders
# ---------------------------------------------------------------------------


def _rates_red_flag_from_liquidity(
    rates_liquidity,  # RatesLiquidityResponse
    flag_key: str,
) -> tuple[RedFlagSeverity, str, str, str, list[str]]:
    """Build rates red flag from rates/liquidity data."""
    severity: RedFlagSeverity = "low"
    signal_text = "Rates & liquidity context: stable"
    rationale = (
        "HIBOR and aggregate balance data do not currently signal "
        "elevated rate pressure. Monitor weekly for shifts."
    )
    action = "No immediate action required. Continue monitoring HIBOR trends."
    support: list[str] = []

    try:
        hibor_rates = [
            r for r in rates_liquidity.rates
            if r.id.startswith("hibor-") and r.value is not None
        ]
        if hibor_rates:
            highest = max(hibor_rates, key=lambda r: r.value or 0)
            if highest.value and highest.value > 4.5:
                severity = "stressed"
                signal_text = "Rates & liquidity context: elevated HIBOR"
                rationale = (
                    f"{highest.label} at {highest.displayValue} exceeds "
                    "the elevated threshold. Floating-rate debt service costs may increase."
                )
                action = (
                    "Review floating-rate exposure and consider fixed-rate "
                    "hedging or rate-cap instruments."
                )
                support.append(f"{highest.label}: {highest.displayValue}")
            elif highest.value and highest.value > 3.5:
                severity = "elevated"
                signal_text = "Rates & liquidity context: HIBOR watch"
                rationale = (
                    f"{highest.label} at {highest.displayValue} is above "
                    "the neutral range. Rate sensitivity should be monitored."
                )
                action = (
                    "Review floating-rate exposure and debt-service coverage "
                    "under a moderate rate-shock scenario."
                )
                support.append(f"{highest.label}: {highest.displayValue}")
            elif highest.value and highest.value > 2.5:
                severity = "moderate"
                signal_text = "Rates & liquidity context: moderate"
                rationale = (
                    f"{highest.label} at {highest.displayValue} is above "
                    "the low threshold."
                )
                action = "Monitor rate trends in upcoming weeks."
                support.append(f"{highest.label}: {highest.displayValue}")
            else:
                severity = "low"
                signal_text = "Rates & liquidity context: benign"
                rationale = (
                    f"{highest.label} at {highest.displayValue} remains below "
                    "the watch threshold."
                )
                action = "No immediate action required."
                support.append(f"{highest.label}: {highest.displayValue}")

            # Add HIBOR trend context
            trending = [r for r in hibor_rates if r.trend in ("up", "down")]
            if trending:
                trend_rates = [f"{r.label}: trend {r.trend}" for r in trending[:2]]
                support.extend(trend_rates)
        else:
            severity = "unavailable"
            signal_text = "Rates & liquidity context: unavailable"
            rationale = "HIBOR rate data is unavailable."
            action = "Connect HIBOR provider to enable rates red-flag monitoring."
    except Exception:
        severity = "unavailable"
        signal_text = "Rates & liquidity context: error"
        rationale = "Could not process rates/liquidity data."
        action = "Check rates/liquidity source provider connection."

    return severity, signal_text, rationale, action, support


def _add_rates_red_flag(rates_liquidity, red_flags, components):
    """Add rates red flag and summary component."""
    severity, signal_text, rationale, action, support = (
        _rates_red_flag_from_liquidity(rates_liquidity, "rates_red_flag")
    )
    red_flags.append(RedFlagItem(
        flagKey="rates_red_flag",
        label="Rates & Liquidity Context",
        severity=severity,
        category="rates",
        signal=signal_text,
        rationale=rationale,
        suggestedReviewAction=action,
        supportingSignals=support,
        source="rates_liquidity_v1",
    ))
    components.append(RedFlagsSummaryComponent(
        label="Rates & liquidity",
        value=severity.replace("_", " "),
        signal=signal_text,
        explanation=rationale,
    ))


def _add_timing_red_flag(timing, red_flags, components):
    """Add timing red flag from golden timing signal."""
    severity: RedFlagSeverity
    signal_text = f"Timing band: {timing.goldenTimingBand}"

    if timing.goldenTimingBand == "cautious":
        if timing.calendarRedFlag != "none":
            severity = "stressed"
            signal_text = f"Timing context: cautious with {timing.calendarRedFlag} flag"
        else:
            severity = "elevated"
    elif timing.goldenTimingBand == "neutral":
        severity = "moderate" if timing.calendarRedFlag != "none" else "low"
    else:
        severity = "low"

    flag_key = "timing_red_flag"
    rationale = (
        timing.explanation
        if severity in ("elevated", "stressed")
        else "Market timing context is neutral or favourable; no immediate timing-related red flag."
    )
    action = (
        "Review floating-rate exposure and monitor rate trends. "
        "Calendar flag may add liquidity pressure."
        if severity in ("elevated", "stressed")
        else "No timing-related action required currently."
    )

    red_flags.append(RedFlagItem(
        flagKey=flag_key,
        label="Market Timing Context",
        severity=severity,
        category="timing",
        signal=signal_text,
        rationale=rationale,
        suggestedReviewAction=action,
        supportingSignals=["Golden Timing Index v1"],
        source="timing_signal_v1",
    ))
    components.append(RedFlagsSummaryComponent(
        label="Market timing",
        value=f"golden timing: {timing.goldenTimingBand}",
        signal=signal_text,
        explanation=timing.explanation,
    ))


def _add_sector_red_flag(industry, red_flags, components, mitigants):
    """Add sector red flag from industry health signal."""
    severity: RedFlagSeverity
    if industry.industryHealthBand in ("stressed",):
        severity = "elevated"
    elif industry.industryHealthBand in ("watch",):
        severity = "moderate"
    elif industry.industryHealthBand == "unavailable":
        severity = "unavailable"
    else:
        severity = "low"

    flag_key = "sector_red_flag"
    signal_text = f"Industry health: {industry.industryHealthBand}"
    rationale = (
        f"{industry.sectorName} sector health is rated {industry.industryHealthBand}. "
        f"Demand signal: {industry.demandSignal}. "
        f"Margin signal: {industry.marginSignal}."
    )
    action = (
        "Review sector-specific risks and consider how industry trends "
        "may affect company revenue and margin."
        if severity in ("elevated", "moderate")
        else "No sector-related red flag; continue monitoring industry trends."
    )

    red_flags.append(RedFlagItem(
        flagKey=flag_key,
        label="Sector Industry Health",
        severity=severity,
        category="sector",
        signal=signal_text,
        rationale=rationale,
        suggestedReviewAction=action,
        supportingSignals=[
            f"Sector: {industry.sectorName}",
            f"Demand: {industry.demandSignal}",
            f"Margin: {industry.marginSignal}",
        ],
        source="industry_health_v1",
    ))
    components.append(RedFlagsSummaryComponent(
        label="Sector health",
        value=industry.industryHealthBand,
        signal=signal_text,
        explanation=rationale,
    ))

    # Mitigant if sector is watch/stressed
    if industry.industryHealthBand in ("stressed", "watch"):
        mitigants.append(RedFlagMitigant(
            label="Sector diversification or hedging",
            rationale=(
                f"{industry.sectorName} faces headwinds; evaluate whether "
                "revenue diversification or input-cost hedging could offset sector-level pressure."
            ),
            source="industry_health_v1",
        ))


def _add_funding_red_flag(ranking, red_flags, components, mitigants):
    """Add funding red flag from funding channel ranking."""
    watch_count = sum(1 for c in ranking.channels if c.fitBand == "watch_fit")
    moderate_count = sum(1 for c in ranking.channels if c.fitBand == "moderate_fit")

    severity: RedFlagSeverity
    if watch_count >= 3:
        severity = "stressed"
    elif watch_count >= 1:
        severity = "elevated"
    elif moderate_count >= 3:
        severity = "moderate"
    else:
        severity = "low"

    flag_key = "funding_red_flag"
    signal_text = (
        f"Funding channels: profile shows {watch_count} watch-fit "
        f"and {moderate_count} moderate-fit channels"
    )
    rationale = (
        f"Top channel: {ranking.topChannelKey.replace('_', ' ')}. "
        f"Ranking band: {ranking.rankingBand.replace('_', ' ')}. "
        f"A high number of watch-fit channels may indicate limited options."
    )
    action = (
        "Review company financials and address constraints for "
        "watch-fit channels to improve financing options."
        if severity in ("elevated", "stressed")
        else "Continue monitoring channel fit as company context evolves."
    )

    red_flags.append(RedFlagItem(
        flagKey=flag_key,
        label="Funding Channel Fit",
        severity=severity,
        category="funding",
        signal=signal_text,
        rationale=rationale,
        suggestedReviewAction=action,
        supportingSignals=[
            f"Top channel: {ranking.topChannelKey.replace('_', ' ')}",
            f"Ranking band: {ranking.rankingBand.replace('_', ' ')}",
        ],
        source="funding_channel_ranking_v1",
    ))
    components.append(RedFlagsSummaryComponent(
        label="Funding channel fit",
        value=f"{watch_count} watch / {moderate_count} moderate",
        signal=signal_text,
        explanation=rationale,
    ))

    if watch_count > 0:
        mitigants.append(RedFlagMitigant(
            label="Company financial review",
            rationale=(
                "Updating company financial records may improve funding "
                "channel fit assessments and reduce watch-fit counts."
            ),
            source="funding_channel_ranking_v1",
        ))


def _add_cross_border_red_flag(cb_context, red_flags, components):
    """Add cross-border red flag."""
    severity: RedFlagSeverity
    if cb_context.fxRiskBand == "elevated" and cb_context.crossBorderReviewBand in ("worth_reviewing", "monitor"):
        severity = "elevated"
    elif cb_context.fxRiskBand == "elevated":
        severity = "moderate"
    elif cb_context.fxRiskBand in ("low",) and cb_context.crossBorderReviewBand == "not_priority":
        severity = "low"
    elif cb_context.fxRiskBand == "unavailable":
        severity = "unavailable"
    else:
        severity = "moderate"

    flag_key = "cross_border_red_flag"
    signal_text = (
        f"Cross-border FX risk: {cb_context.fxRiskBand.replace('_', ' ')}, "
        f"review signal: {cb_context.crossBorderReviewBand.replace('_', ' ')}"
    )
    rationale = (
        f"HKD/RMB spread: {cb_context.spreadBand.replace('_', ' ')}. "
        f"FX risk band: {cb_context.fxRiskBand.replace('_', ' ')}. "
        f"Cross-border review: {cb_context.crossBorderReviewBand.replace('_', ' ')}."
    )
    action = (
        "Review cross-border funding exposure and consider whether "
        "FX hedging or RMB-denominated facilities should be evaluated."
        if severity in ("elevated", "moderate")
        else "Cross-border funding context does not currently flag concerns."
    )

    red_flags.append(RedFlagItem(
        flagKey=flag_key,
        label="Cross-border Funding Context",
        severity=severity,
        category="cross_border",
        signal=signal_text,
        rationale=rationale,
        suggestedReviewAction=action,
        supportingSignals=[
            f"Spread band: {cb_context.spreadBand}",
            f"FX risk: {cb_context.fxRiskBand}",
        ],
        source="cross_border_funding_context_v1",
    ))
    components.append(RedFlagsSummaryComponent(
        label="Cross-border context",
        value=cb_context.fxRiskBand.replace("_", " "),
        signal=signal_text,
        explanation=rationale,
    ))


def _add_fx_red_flag(fx_gba, red_flags, components):
    """Add FX red flag from FX/GBA data."""
    severity: RedFlagSeverity = "low"
    signal_text = "FX context: no significant signals"
    rationale = "FX pair trends and GBA funding signals do not currently indicate elevated FX risk."
    action = "No FX-related action required currently."
    support: list[str] = []

    try:
        elevated_signals = [
            s for s in fx_gba.gbaFundingSignal
            if hasattr(s, 'severity') and s.severity in ("High", "Caution")
        ]
        if elevated_signals:
            severity = "elevated"
            signal_text = f"FX context: {len(elevated_signals)} watch signal(s)"
            rationale = (
                f"GBA funding signals include {len(elevated_signals)} item(s) "
                "at elevated severity. Monitor USD and CNY exposure."
            )
            action = (
                "Review FX exposure and consider hedging instruments "
                "if elevated signals align with company import/payable profile."
            )
            for s in elevated_signals[:2]:
                support.append(f"{s.title}: {s.description}")

        # FX pair trend check
        volatile_pairs = [
            p for p in fx_gba.fxPairs
            if p.trend in ("up", "down") and p.changePips is not None and abs(p.changePips) > 100
        ]
        if volatile_pairs and severity == "low":
            severity = "moderate"
            signal_text = "FX context: moderate volatility detected"
            rationale = (
                "One or more FX pairs show significant recent movement. "
                "Monitor for sustained trends."
            )
            action = "Review FX exposure and assess potential impact on import costs and supplier payables."

        # Exposure notes
        if hasattr(fx_gba, 'exposureNotes') and fx_gba.exposureNotes:
            high_exposures = [
                e for e in fx_gba.exposureNotes
                if e.severity in ("High", "Caution")
            ]
            if high_exposures and severity != "elevated":
                severity = "moderate"
                signal_text = "FX context: exposure watch items present"
                rationale = "Company FX exposure notes include watch-level items."
                action = "Review FX exposure notes and evaluate hedging requirements."
                for exp in high_exposures[:2]:
                    support.append(exp.note)

    except Exception:
        severity = "unavailable"
        signal_text = "FX context: data unavailable"
        rationale = "Could not process FX/GBA data for red-flag assessment."
        action = "Check FX provider connection."

    red_flags.append(RedFlagItem(
        flagKey="fx_red_flag",
        label="FX & Currency Context",
        severity=severity,
        category="fx",
        signal=signal_text,
        rationale=rationale,
        suggestedReviewAction=action,
        supportingSignals=support,
        source="fx_gba_v1",
    ))
    components.append(RedFlagsSummaryComponent(
        label="FX & currency",
        value=severity.replace("_", " "),
        signal=signal_text,
        explanation=rationale,
    ))


def _add_liquidity_red_flag(profile, red_flags, components, mitigants):
    """Add liquidity red flag from company context profile."""
    severity: RedFlagSeverity = "low"
    signal_text = "Liquidity context: adequate"
    rationale = "Working capital gap and DSO data do not currently indicate liquidity stress."
    action = "No liquidity-related action required currently."
    support: list[str] = []

    stress_points = 0

    if profile.workingCapitalGapHkd > 0:
        gap_m = profile.workingCapitalGapHkd / 1_000_000
        support.append(f"Working capital gap: HKD {gap_m:.1f}M")
        if gap_m > 10:
            stress_points += 2
        elif gap_m > 5:
            stress_points += 1

    if profile.dsoDays > 60:
        stress_points += 2
        support.append(f"DSO: {profile.dsoDays}d (elevated)")
    elif profile.dsoDays > 45:
        stress_points += 1
        support.append(f"DSO: {profile.dsoDays}d (watch)")

    if profile.cashBalanceHkd < profile.monthlyDebtServiceHkd * 3:
        stress_points += 1
        support.append("Cash balance below 3x monthly debt service")

    if stress_points >= 3:
        severity = "stressed"
        signal_text = "Liquidity context: stressed"
        rationale = "Working capital gap, elevated DSO, and cash coverage gaps indicate potential liquidity pressure."
        action = (
            "Prioritise working capital management: review receivables "
            "collections, negotiate supplier terms, and evaluate short-term liquidity facilities."
        )
    elif stress_points >= 1:
        severity = "moderate"
        signal_text = "Liquidity context: watch"
        rationale = "One or more liquidity indicators warrant attention."
        action = (
            "Review working capital position and consider whether "
            "a working capital facility or receivables financing could "
            "improve liquidity buffer."
        )
    else:
        severity = "low"
        signal_text = "Liquidity context: adequate"
        rationale = "Working capital indicators appear within normal ranges."
        action = "No liquidity-related action required."

    red_flags.append(RedFlagItem(
        flagKey="liquidity_red_flag",
        label="Liquidity & Working Capital",
        severity=severity,
        category="liquidity",
        signal=signal_text,
        rationale=rationale,
        suggestedReviewAction=action,
        supportingSignals=support,
        source="company_context_v1",
    ))
    components.append(RedFlagsSummaryComponent(
        label="Liquidity & working capital",
        value=severity.replace("_", " "),
        signal=signal_text,
        explanation=rationale,
    ))

    if severity in ("stressed", "moderate"):
        mitigants.append(RedFlagMitigant(
            label="Working capital optimisation",
            rationale=(
                "Addressing DSO stretch and working capital gap through "
                "receivables discipline and supplier terms negotiation may "
                "improve liquidity context."
            ),
            source="company_context_v1",
        ))


# ---------------------------------------------------------------------------
# Summary band computation
# ---------------------------------------------------------------------------


def _compute_summary_band(red_flags: list[RedFlagItem]) -> tuple[SummaryBand, str]:
    """Determine overall summary band from individual red-flag severities."""
    if not red_flags:
        return "unavailable", "Insufficient data to generate red-flag summary."

    stressed_count = sum(1 for f in red_flags if f.severity == "stressed")
    elevated_count = sum(1 for f in red_flags if f.severity == "elevated")
    moderate_count = sum(1 for f in red_flags if f.severity == "moderate")
    low_count = sum(1 for f in red_flags if f.severity == "low")

    # stressed if 2+ stressed red flags
    if stressed_count >= 2:
        band: SummaryBand = "stressed"
        headline = (
            f"{stressed_count} stressed and {elevated_count} elevated red flag(s) "
            "detected. Review highlighted areas and assess impact on financing readiness."
        )
        return band, headline

    # stressed if severe liquidity/fx/rates stack
    critical_categories = {"liquidity", "fx", "rates"}
    critical_stressed = sum(
        1 for f in red_flags
        if f.severity == "stressed" and f.category in critical_categories
    )
    critical_elevated = sum(
        1 for f in red_flags
        if f.severity == "elevated" and f.category in critical_categories
    )
    if critical_stressed >= 1 and critical_elevated >= 1:
        band = "stressed"
        headline = (
            "Severe liquidity, FX, or rate conditions detected. "
            "Review interest-rate exposure and working-capital buffers."
        )
        return band, headline

    # elevated if 2+ elevated red flags
    if elevated_count >= 2:
        band = "elevated"
        headline = (
            f"{elevated_count} elevated red flag(s) — review highlighted "
            "areas for potential impact on financing context."
        )
        return band, headline

    # watch if any moderate/elevated red flag
    if moderate_count >= 1 or elevated_count >= 1:
        band = "watch"
        if elevated_count:
            headline = (
                f"{elevated_count} elevated red flag(s) and "
                f"{moderate_count} moderate signal(s) present. "
                "Situation awareness recommended."
            )
        else:
            headline = (
                f"{moderate_count} moderate signal(s) present. "
                "Monitor highlighted areas for changes."
            )
        return band, headline

    # clear if all low
    if low_count == len(red_flags):
        band = "clear"
        headline = (
            "No significant red flags detected across monitored signals. "
            "Continue regular monitoring."
        )
        return band, headline

    # fallback
    band = "watch"
    headline = "Mixed signals across monitored areas. Review individual flags."
    return band, headline
