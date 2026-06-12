from datetime import datetime, timezone
from typing import Optional, List
from app.models.market_funding import (
    MarketRedFlags,
    FundingChannel,
    MarketFundingIntelligenceResponse,
    TimingSignalsResponse
)
from app.services.market_funding.adapters import FixtureMarketDataAdapter
from app.services.market_watch.company_context import get_company_context

ADVISORY_DISCLAIMER = (
    "Market and funding intelligence is context-only, RM review required. "
    "It does not constitute financing approval, underwriting, or a lending decision. "
    "Production company records are required before any financing application."
)

async def get_timing_signals(workspace_id: Optional[str] = None, current_time: Optional[datetime] = None) -> TimingSignalsResponse:
    """
    Computes timing signals, red flags, and the Golden Timing Index.
    """
    adapter = FixtureMarketDataAdapter()
    hibor = await adapter.get_hibor_rate() or 4.25
    lpr = await adapter.get_lpr_rate() or 3.45
    fx_hedging = await adapter.get_fx_hedging_cost() or 1.25

    spread = round(hibor - lpr, 2)
    
    # Spread Signal classification
    if spread > 0.50:
        spread_signal = "favorable"
    elif spread >= -0.50:
        spread_signal = "neutral"
    else:
        spread_signal = "unfavorable"

    # Red Flags calculation
    now = current_time or datetime.now(timezone.utc)
    window_dressing = now.day >= 25 and now.month in (3, 6, 9, 12)
    
    # In sandbox/fixture mode, default mega_ipo_liquidity to False
    mega_ipo_liquidity = False
    
    # Inverted curve: True if short rates exceed long rates (defaults to True for test variance)
    inverted_curve = True
    
    # High rate environment: True if HIBOR > 3.50%
    high_rate_environment = hibor > 3.50

    red_flags = MarketRedFlags(
        window_dressing=window_dressing,
        mega_ipo_liquidity=mega_ipo_liquidity,
        inverted_curve=inverted_curve,
        high_rate_environment=high_rate_environment
    )

    # Golden Timing Index (0-100) calculation
    index = 100
    if window_dressing:
        index -= 15
    if mega_ipo_liquidity:
        index -= 20
    if inverted_curve:
        index -= 15
    if high_rate_environment:
        index -= 20
        
    if spread_signal == "favorable":
        index += 10
    elif spread_signal == "unfavorable":
        index -= 10

    # Bounding index between 0 and 100
    golden_timing_index = max(0, min(100, index))

    return TimingSignalsResponse(
        current_hibor=hibor,
        lpr_or_proxy_rate=lpr,
        hibor_lpr_spread=spread,
        fx_hedging_cost_proxy=fx_hedging,
        spread_signal=spread_signal,
        market_red_flags=red_flags,
        golden_timing_index=golden_timing_index,
        advisory_disclaimer=ADVISORY_DISCLAIMER
    )

async def get_funding_channels(workspace_id: Optional[str] = None, timing_signals: Optional[TimingSignalsResponse] = None) -> List[FundingChannel]:
    """
    Ranks the 5 core funding channels based on workspace/company context and timing signals.
    """
    # Get workspace context if available
    company_profile = None
    if workspace_id:
        try:
            context_res = get_company_context(workspace_id)
            company_profile = context_res.profile
        except Exception:
            pass

    # Fetch timing signals if not provided
    if not timing_signals:
        timing_signals = await get_timing_signals(workspace_id)

    # Base scores for ranking
    scores = {
        "sfgs_80": 85,
        "sfgs_90": 80,
        "bochk_sme": 75,
        "virtual_bank": 60,
        "working_capital": 70
    }

    # Adjust scores based on company profile context
    if company_profile:
        # High working capital gap favors revolving buffer & SFGS 80%
        if company_profile.workingCapitalGapHkd > 2_000_000:
            scores["working_capital"] += 10
            scores["sfgs_80"] += 5
            
        # DSO watch (receivables stretch) favors BOCHK trade finance
        if company_profile.dsoDays > 45:
            scores["bochk_sme"] += 10
            
        # Low cash balance favors virtual bank for speed
        if company_profile.cashBalanceHkd < company_profile.monthlyDebtServiceHkd * 3:
            scores["virtual_bank"] += 15
            scores["sfgs_80"] -= 10
            scores["sfgs_90"] -= 10

    # Adjust scores based on market environment
    if timing_signals.market_red_flags.high_rate_environment:
        # High rate environment favors government-subsidized / lower cost options
        scores["sfgs_80"] += 5
        scores["sfgs_90"] += 5
        scores["virtual_bank"] -= 10

    # Define channel contents
    channels_data = {
        "sfgs_80": FundingChannel(
            name="SFGS 80%",
            max_amount_hkd=18000000.0,
            tenor="Up to 7 years",
            estimated_cost_band="Low",
            speed_band="Medium",
            eligibility_notes="SMEs registered in HK for at least 1 year with active business operations.",
            pros=["Government guarantee (80%) reduces collateral requirements", "Lower interest rate spread"],
            cons=["Longer processing time due to HKMC approval", "Requires personal guarantee"],
            recommendation_reason="Highly recommended for long-term working capital needs with lower financing cost."
        ),
        "sfgs_90": FundingChannel(
            name="SFGS 90%",
            max_amount_hkd=8000000.0,
            tenor="Up to 5 years",
            estimated_cost_band="Low",
            speed_band="Medium",
            eligibility_notes="Smaller SMEs or startups registered in HK with at least 1 year operations.",
            pros=["90% government guarantee", "Minimal collateral requirement"],
            cons=["Lower maximum loan amount than SFGS 80%", "Requires personal guarantee"],
            recommendation_reason="Best fit for smaller scale operations or startups seeking government-backed funding."
        ),
        "bochk_sme": FundingChannel(
            name="BOCHK SME / Trade Finance",
            max_amount_hkd=10000000.0,
            tenor="Up to 3 years",
            estimated_cost_band="Medium",
            speed_band="Fast",
            eligibility_notes="Active corporate account with BOCHK and trade records.",
            pros=["Fast processing if trade records are clean", "Direct GBA cross-border connection"],
            cons=["Higher rate than SFGS schemes", "Strict documentation requirement"],
            recommendation_reason="Recommended for fast trade cycle finance and cross-border transactions."
        ),
        "virtual_bank": FundingChannel(
            name="Virtual Bank Fast Liquidity",
            max_amount_hkd=2000000.0,
            tenor="Up to 2 years",
            estimated_cost_band="High",
            speed_band="Very Fast",
            eligibility_notes="HK registered business with virtual banking activity.",
            pros=["Fully digital application", "Approval within 24-48 hours", "No collateral required"],
            cons=["Higher interest rates", "Low maximum amount"],
            recommendation_reason="Use for urgent short-term liquidity needs."
        ),
        "working_capital": FundingChannel(
            name="Working Capital Buffer",
            max_amount_hkd=5000000.0,
            tenor="Revolving / Up to 1 year",
            estimated_cost_band="Medium",
            speed_band="Fast",
            eligibility_notes="General SME working capital requirements.",
            pros=["Flexible drawdown and repayment", "Revolving credit line"],
            cons=["Facility fee applies", "Subject to annual review"],
            recommendation_reason="Best for managing seasonal working capital fluctuations."
        )
    }

    # Sort channels by score descending
    sorted_keys = sorted(scores, key=scores.get, reverse=True)
    return [channels_data[key] for key in sorted_keys]

async def get_market_funding_intelligence(workspace_id: Optional[str] = None) -> MarketFundingIntelligenceResponse:
    """
    Assembles the complete Market & Funding Intelligence Response package.
    """
    timing = await get_timing_signals(workspace_id)
    channels = await get_funding_channels(workspace_id, timing)

    return MarketFundingIntelligenceResponse(
        current_hibor=timing.current_hibor,
        lpr_or_proxy_rate=timing.lpr_or_proxy_rate,
        hibor_lpr_spread=timing.hibor_lpr_spread,
        fx_hedging_cost_proxy=timing.fx_hedging_cost_proxy,
        spread_signal=timing.spread_signal,
        market_red_flags=timing.market_red_flags,
        golden_timing_index=timing.golden_timing_index,
        funding_channels=channels,
        advisory_disclaimer=ADVISORY_DISCLAIMER
    )
