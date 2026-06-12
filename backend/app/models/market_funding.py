from typing import List, Literal
from pydantic import BaseModel

class MarketRedFlags(BaseModel):
    window_dressing: bool
    mega_ipo_liquidity: bool
    inverted_curve: bool
    high_rate_environment: bool

class FundingChannel(BaseModel):
    name: str
    max_amount_hkd: float
    tenor: str
    estimated_cost_band: str
    speed_band: str
    eligibility_notes: str
    pros: List[str]
    cons: List[str]
    recommendation_reason: str

class MarketFundingIntelligenceResponse(BaseModel):
    current_hibor: float
    lpr_or_proxy_rate: float
    hibor_lpr_spread: float
    fx_hedging_cost_proxy: float
    spread_signal: Literal["favorable", "neutral", "unfavorable", "unavailable"]
    market_red_flags: MarketRedFlags
    golden_timing_index: int
    funding_channels: List[FundingChannel]
    advisory_disclaimer: str

class TimingSignalsResponse(BaseModel):
    current_hibor: float
    lpr_or_proxy_rate: float
    hibor_lpr_spread: float
    fx_hedging_cost_proxy: float
    spread_signal: Literal["favorable", "neutral", "unfavorable", "unavailable"]
    market_red_flags: MarketRedFlags
    golden_timing_index: int
    advisory_disclaimer: str
