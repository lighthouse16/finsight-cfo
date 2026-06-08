import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.market_watch import (
    LiquidityEvent,
    RateSnapshot,
    TimingSignalComponent,
    TimingSignalProvenance,
    TimingSignalResponse,
)
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity

DISCLAIMER = "Timing context only. Not a financing instruction."


def _select_hibor_rate(rates: list[RateSnapshot]) -> RateSnapshot | None:
    preferred_ids = ["hibor-1m", "hibor-3m", "hibor-o/n"]
    by_id = {rate.id: rate for rate in rates}
    for rate_id in preferred_ids:
        if by_id.get(rate_id) and by_id[rate_id].value is not None:
            return by_id[rate_id]
    return next((rate for rate in rates if rate.id.startswith("hibor-") and rate.value is not None), None)


def _hibor_level_band(rate: RateSnapshot | None) -> tuple[str, str, str | None]:
    if not rate or rate.value is None:
        return "neutral", "HIBOR level unavailable; timing score uses neutral level context.", None
    value = rate.value
    display = rate.displayValue or f"{value:.2f}%"
    if value < 2.25:
        return "favorable", f"{rate.label} at {display} is below the v1 favorable threshold.", display
    if value <= 3.25:
        return "neutral", f"{rate.label} at {display} sits inside the v1 neutral range.", display
    return "cautious", f"{rate.label} at {display} is above the v1 caution threshold.", display


def _hibor_trend(rate: RateSnapshot | None) -> tuple[str, str, str | None]:
    if not rate or rate.changeBasisPoints is None:
        return "unavailable", "Recent basis-point change is unavailable from the selected HIBOR source.", None
    change = rate.changeBasisPoints
    display = f"{change:+.0f} bps"
    if change <= -10:
        return "easing", f"Selected HIBOR change of {display} indicates easing context.", display
    if change >= 10:
        return "tightening", f"Selected HIBOR change of {display} indicates tightening context.", display
    return "stable", f"Selected HIBOR change of {display} indicates stable context.", display


def _extract_hkd_millions(event: LiquidityEvent) -> int | None:
    match = re.search(r"HKD\s+(-?[\d,]+)M", event.event)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _liquidity_signal(events: list[LiquidityEvent]) -> tuple[str, str, str | None]:
    balance_values = [
        value for event in events
        if "Aggregate Balance" in event.event
        for value in [_extract_hkd_millions(event)]
        if value is not None
    ]
    if not balance_values:
        return "unavailable", "Aggregate balance liquidity context is unavailable from normalized HKMA events.", None
    latest = balance_values[-1]
    display = f"HKD {latest:,}M"
    if latest >= 55_000:
        return "favorable", f"Aggregate balance at {display} indicates more supportive liquidity context under v1 rules.", display
    if latest >= 35_000:
        return "neutral", f"Aggregate balance at {display} indicates neutral liquidity context under v1 rules.", display
    return "cautious", f"Aggregate balance at {display} indicates tighter liquidity context under v1 rules.", display


def _calendar_red_flag(now: datetime | None = None) -> tuple[str, str]:
    current = now or datetime.now(ZoneInfo("Asia/Hong_Kong"))
    if current.day < 25:
        return "none", "No month-end calendar flag is active."
    if current.month == 12:
        return "year_end", "Year-end calendar window can add liquidity and reporting pressure."
    if current.month == 6:
        return "half_year_end", "Half-year-end calendar window can add liquidity and reporting pressure."
    return "month_end", "Month-end calendar window can add liquidity and reporting pressure."


def _combine_band(level: str, trend: str, liquidity: str, calendar: str) -> str:
    caution_score = 0
    favorable_score = 0
    if level == "cautious":
        caution_score += 2
    elif level == "favorable":
        favorable_score += 2
    if trend == "tightening":
        caution_score += 1
    elif trend == "easing":
        favorable_score += 1
    if liquidity == "cautious":
        caution_score += 1
    elif liquidity == "favorable":
        favorable_score += 1
    if calendar != "none":
        caution_score += 1
    if caution_score >= 2:
        return "cautious"
    if favorable_score >= 2 and caution_score == 0:
        return "favorable"
    return "neutral"


async def get_timing_signal() -> TimingSignalResponse:
    rates_liquidity = await get_rates_liquidity()
    selected_rate = _select_hibor_rate(rates_liquidity.rates)
    level_band, level_explanation, level_value = _hibor_level_band(selected_rate)
    trend_signal, trend_explanation, trend_value = _hibor_trend(selected_rate)
    liquidity_signal, liquidity_explanation, liquidity_value = _liquidity_signal(rates_liquidity.liquidityEvents)
    calendar_flag, calendar_explanation = _calendar_red_flag()
    golden_band = _combine_band(level_band, trend_signal, liquidity_signal, calendar_flag)

    warnings = list(rates_liquidity.metadata.warnings)
    if trend_signal == "unavailable":
        warnings.append("HIBOR trend signal is unavailable because the selected source did not provide recent basis-point movement.")
    if liquidity_signal == "unavailable":
        warnings.append("Liquidity timing signal is unavailable because aggregate balance events were not normalized.")

    return TimingSignalResponse(
        hiborLevelBand=level_band,
        hiborTrendSignal=trend_signal,
        liquidityTimingSignal=liquidity_signal,
        calendarRedFlag=calendar_flag,
        goldenTimingBand=golden_band,
        explanation=(
            f"Golden Timing Index v1 is {golden_band} based on rule-based HIBOR level, "
            "HIBOR trend availability, HKMA aggregate balance context, and calendar timing."
        ),
        components=[
            TimingSignalComponent(band=level_band, label="HIBOR level", value=level_value, explanation=level_explanation),
            TimingSignalComponent(band=trend_signal, label="HIBOR trend", value=trend_value, explanation=trend_explanation),
            TimingSignalComponent(band=liquidity_signal, label="Liquidity context", value=liquidity_value, explanation=liquidity_explanation),
            TimingSignalComponent(band=calendar_flag, label="Calendar flag", value=calendar_flag, explanation=calendar_explanation),
        ],
        provenance=TimingSignalProvenance(
            source="market_watch_rates_liquidity",
            provider=rates_liquidity.metadata.source.provider,
            asOf=rates_liquidity.metadata.asOf,
            freshness=rates_liquidity.metadata.freshness,
        ),
        warnings=warnings,
        disclaimer=DISCLAIMER,
    )
