"""
Cross-border Funding Context v1 for Market Watch.

Provides context-only comparison of HKD/HIBOR vs RMB/LPR-style funding
context and flags whether cross-border financing review may be worth
considering. This is NOT a financing recommendation or arbitrage signal.
"""

from datetime import datetime

from app.core.config import settings
from app.models.market_watch import (
    CrossBorderFundingComponent,
    CrossBorderFundingContextResponse,
    CrossBorderFundingProvenance,
    CrossBorderFundingReference,
    CrossBorderReviewBand,
    CrossBorderSpreadBand,
    CrossBorderFxRiskBand,
)
from app.services.market_watch.company_context import (
    get_demo_company_profile,
)
from app.services.market_watch.fixtures import (
    get_cross_border_funding_context_fixture,
)
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity

DISCLAIMER = (
    "Cross-border funding context is for planning support only. "
    "Not a financing recommendation, arbitrage instruction, or lending decision."
)

_WARNING_BASE = (
    "Cross-border Funding Context v1 is fixture/workspace-derived. "
    "LPR reference is a fixture placeholder pending provider connection."
)


async def get_cross_border_funding_context() -> CrossBorderFundingContextResponse:
    """Build context-only cross-border funding comparison."""
    if settings.MARKET_WATCH_USE_FIXTURES:
        return get_cross_border_funding_context_fixture()

    # Gather live data
    profile = get_demo_company_profile()
    # exposures available for context expansion
    rates_liquidity = await get_rates_liquidity()

    # --- HKD reference: pick best HIBOR rate ---
    preferred_hibor_ids = ["hibor-1m", "hibor-3m", "hibor-o/n"]
    hkd_rate = None
    for rid in preferred_hibor_ids:
        match = next(
            (r for r in rates_liquidity.rates if r.id == rid and r.value is not None),
            None,
        )
        if match:
            hkd_rate = match
            break
    if not hkd_rate:
        hkd_rate = next(
            (r for r in rates_liquidity.rates if r.value is not None), None
        )

    if hkd_rate:
        hkd_reference = CrossBorderFundingReference(
            label=hkd_rate.label,
            currency="HKD",
            value=hkd_rate.value,
            unit="percent",
            displayValue=hkd_rate.displayValue,
            source=f"{hkd_rate.context}",
        )
        hkd_value = hkd_rate.value
    else:
        hkd_reference = CrossBorderFundingReference(
            label="HIBOR reference unavailable",
            currency="HKD",
            value=None,
            unit="percent",
            displayValue="Unavailable",
            source="No HIBOR rate available from upstream",
        )
        hkd_value = None

    # --- RMB reference: fixture LPR proxy ---
    # LPR provider is not connected yet; use fixture placeholder
    rmb_value = 3.45  # 1Y LPR proxy
    rmb_reference = CrossBorderFundingReference(
        label="LPR 1Y (fixture proxy)",
        currency="RMB",
        value=rmb_value,
        unit="percent",
        displayValue=f"{rmb_value:.2f}%",
        source="Fixture placeholder — LPR provider pending",
    )

    # --- Spread calculation ---
    spread_bps: float | None = None
    if hkd_value is not None:
        spread_bps = round((hkd_value - rmb_value) * 100, 1)

    # --- Bands ---
    spread_band: CrossBorderSpreadBand = _compute_spread_band(spread_bps)
    fx_risk_band: CrossBorderFxRiskBand = _compute_fx_risk_band(profile)
    review_band: CrossBorderReviewBand = _compute_review_band(
        spread_band, fx_risk_band
    )

    # --- Explanation ---
    explanation = _build_explanation(
        review_band, spread_bps, hkd_value, rmb_value, profile.companyName
    )

    # --- Components ---
    components = _build_components(
        hkd_reference, rmb_reference, spread_bps, spread_band,
        fx_risk_band, review_band, profile,
    )

    # --- Provenance ---
    now = datetime.utcnow().isoformat() + "Z"
    provenance = CrossBorderFundingProvenance(
        source="market_watch_cross_border_funding_context_v1",
        provider="FinSight CFO Market Watch",
        asOf=None,
        freshness="Workspace",
    )

    # --- Warnings ---
    warnings = [
        _WARNING_BASE,
        "LPR reference is a fixture placeholder. Production LPR provider integration required for actual rates.",
    ]

    return CrossBorderFundingContextResponse(
        mode="context_only",
        baseCurrency="HKD",
        comparisonCurrency="RMB",
        hkdFundingReference=hkd_reference,
        rmbFundingReference=rmb_reference,
        spreadBps=spread_bps,
        spreadBand=spread_band,
        fxRiskBand=fx_risk_band,
        crossBorderReviewBand=review_band,
        explanation=explanation,
        components=components,
        provenance=provenance,
        source=provenance,
        warnings=warnings,
        disclaimer=DISCLAIMER,
    )


def _compute_spread_band(spread_bps: float | None) -> CrossBorderSpreadBand:
    if spread_bps is None:
        return "unavailable"
    if spread_bps > 50:
        return "hkd_advantage"
    if spread_bps < -50:
        return "rmb_advantage"
    return "balanced"


def _compute_fx_risk_band(profile) -> CrossBorderFxRiskBand:
    """Assess FX risk from company's import/payable profile."""
    risk_score = 0
    if profile.usdImportCostPercent > 50:
        risk_score += 2
    elif profile.usdImportCostPercent > 30:
        risk_score += 1
    if profile.cnySupplierPayablesPercent > 30:
        risk_score += 2
    elif profile.cnySupplierPayablesPercent > 15:
        risk_score += 1

    if risk_score >= 3:
        return "elevated"
    if risk_score >= 1:
        return "moderate"
    return "low"


def _compute_review_band(
    spread_band: CrossBorderSpreadBand,
    fx_risk_band: CrossBorderFxRiskBand,
) -> CrossBorderReviewBand:
    if spread_band == "unavailable" and fx_risk_band == "unavailable":
        return "unavailable"
    if spread_band in ("hkd_advantage", "rmb_advantage") and fx_risk_band in ("elevated", "moderate"):
        return "worth_reviewing"
    if spread_band != "balanced" or fx_risk_band != "low":
        return "monitor"
    return "not_priority"


def _build_explanation(
    review_band: CrossBorderReviewBand,
    spread_bps: float | None,
    hkd_value: float | None,
    rmb_value: float,
    company_name: str,
) -> str:
    parts = [
        f"{company_name}'s cross-border funding context review:"
    ]
    if spread_bps is not None and hkd_value is not None:
        parts.append(
            f"HIBOR ({hkd_value:.2f}%) vs LPR proxy ({rmb_value:.2f}%) "
            f"spread of {spread_bps:+.1f} bps indicates "
        )
        if spread_bps > 50:
            parts.append("HKD-funding is materially more expensive on a rate basis.")
        elif spread_bps < -50:
            parts.append("RMB-funding is materially more expensive on a rate basis.")
        else:
            parts.append("rate context is broadly balanced between HKD and RMB.")
    else:
        parts.append("Rate spread is unavailable for comparison.")

    if review_band == "worth_reviewing":
        parts.append(
            " Combined with FX exposure and import-cost context, "
            "cross-border funding review may be worth considering."
        )
    elif review_band == "monitor":
        parts.append(
            " Monitor evolving conditions; current data does not "
            "strongly suggest cross-border funding review."
        )
    else:
        parts.append(
            " Current data does not suggest cross-border funding review is a priority."
        )

    parts.append(
        " Production company records and lender consultation are required "
        "before any financing decision."
    )
    return " ".join(parts)


def _build_components(
    hkd_ref: CrossBorderFundingReference,
    rmb_ref: CrossBorderFundingReference,
    spread_bps: float | None,
    spread_band: CrossBorderSpreadBand,
    fx_risk_band: CrossBorderFxRiskBand,
    review_band: CrossBorderReviewBand,
    profile,
) -> list[CrossBorderFundingComponent]:
    components = [
        CrossBorderFundingComponent(
            signal="hkdFundingRate",
            label="HKD funding reference",
            value=hkd_ref.displayValue,
            explanation=(
                f"{hkd_ref.label} as the HKD reference rate. "
                f"Source: {hkd_ref.source}."
            ),
        ),
        CrossBorderFundingComponent(
            signal="rmbFundingRate",
            label="RMB funding reference",
            value=rmb_ref.displayValue,
            explanation=(
                f"LPR 1Y proxy at {rmb_ref.displayValue} as RMB reference. "
                f"Source: {rmb_ref.source}."
            ),
        ),
        CrossBorderFundingComponent(
            signal="rateSpread",
            label="Rate spread",
            value=f"{spread_bps:+.1f} bps" if spread_bps is not None else "Unavailable",
            explanation=(
                f"Spread band: {spread_band.replace('_', ' ')}. "
                "Positive spread = HKD more expensive; negative = RMB more expensive."
                if spread_bps is not None
                else "Spread cannot be calculated without both reference rates."
            ),
        ),
        CrossBorderFundingComponent(
            signal="fxRiskBand",
            label="FX risk context",
            value=fx_risk_band.replace("_", " "),
            explanation=(
                f"USD import costs at {profile.usdImportCostPercent}% of COGS, "
                f"CNY payables at {profile.cnySupplierPayablesPercent}% of payables."
            ),
        ),
        CrossBorderFundingComponent(
            signal="reviewSignal",
            label="Cross-border review signal",
            value=review_band.replace("_", " "),
            explanation=(
                "Cross-border funding review may be worth considering "
                "if rate spread and FX exposure both signal opportunity."
                if review_band == "worth_reviewing"
                else "Current context does not strongly signal cross-border review."
            ),
        ),
    ]
    return components
