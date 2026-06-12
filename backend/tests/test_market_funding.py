import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.services.market_funding.intelligence_service import (
    get_timing_signals,
    get_funding_channels,
    get_market_funding_intelligence
)

client = TestClient(app)

@pytest.mark.anyio
async def test_timing_signals():
    # Test neutral signal
    dt_mid = datetime(2026, 6, 15)
    res = await get_timing_signals(current_time=dt_mid)
    assert res.current_hibor == 4.25
    assert res.lpr_or_proxy_rate == 3.45
    assert res.hibor_lpr_spread == 0.80
    assert res.fx_hedging_cost_proxy == 1.25
    assert res.spread_signal == "favorable"
    assert res.market_red_flags.window_dressing is False
    assert res.market_red_flags.inverted_curve is True
    assert res.market_red_flags.high_rate_environment is True
    # Base 100 - 15 (inverted) - 20 (high_rate) + 10 (favorable) = 75
    assert res.golden_timing_index == 75
    assert "RM review required" in res.advisory_disclaimer

    # Test window dressing signal
    dt_end = datetime(2026, 6, 26)
    res_end = await get_timing_signals(current_time=dt_end)
    assert res_end.market_red_flags.window_dressing is True
    # 75 - 15 (window dressing) = 60
    assert res_end.golden_timing_index == 60

@pytest.mark.anyio
async def test_funding_channel_ranking():
    channels = await get_funding_channels()
    assert len(channels) == 5
    
    # Verify SFGS 80/90 exist
    names = [c.name for c in channels]
    assert "SFGS 80%" in names
    assert "SFGS 90%" in names
    assert "BOCHK SME / Trade Finance" in names
    assert "Virtual Bank Fast Liquidity" in names
    assert "Working Capital Buffer" in names

    # Verify channel fields
    for c in channels:
        assert c.name is not None
        assert c.max_amount_hkd > 0
        assert c.tenor is not None
        assert c.estimated_cost_band in ("Low", "Medium", "High")
        assert c.speed_band in ("Slow", "Medium", "Fast", "Very Fast")
        assert len(c.pros) > 0
        assert len(c.cons) > 0
        assert c.recommendation_reason is not None

@pytest.mark.anyio
async def test_market_funding_intelligence():
    res = await get_market_funding_intelligence()
    assert res.current_hibor == 4.25
    assert len(res.funding_channels) == 5
    assert "RM review required" in res.advisory_disclaimer

def test_api_routes():
    # Test GET /api/market-funding/intelligence
    response = client.get("/api/market-funding/intelligence")
    assert response.status_code == 200
    data = response.json()
    assert data["current_hibor"] == 4.25
    assert len(data["funding_channels"]) == 5
    assert "advisory_disclaimer" in data

    # Test GET /api/market-funding/funding-channels
    response = client.get("/api/market-funding/funding-channels")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["name"] is not None

    # Test GET /api/market-funding/timing-signals
    response = client.get("/api/market-funding/timing-signals")
    assert response.status_code == 200
    data = response.json()
    assert "golden_timing_index" in data
