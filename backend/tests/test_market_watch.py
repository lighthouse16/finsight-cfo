import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_rates_liquidity(monkeypatch):
    # Enable fixture mode to avoid external HKMA calls
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", True)
    
    response = client.get("/api/market-watch/rates-liquidity")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "rates" in data
    assert "liquidityEvents" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert "fetchedAt" in metadata
    assert "freshness" in metadata
    
    # Verify field types
    assert isinstance(data["rates"], list)
    assert isinstance(data["sourceStatus"], list)
    assert isinstance(data["liquidityEvents"], list)

def test_fx_gba():
    response = client.get("/api/market-watch/fx-gba")
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify provider is Fixture
    assert data["metadata"]["source"]["provider"] == "Fixture"
    
    # Verify warnings is an array
    assert isinstance(data["metadata"]["warnings"], list)
    
    # Verify fxPairs includes USD/HKD and CNY/HKD
    fx_pairs = data["fxPairs"]
    assert isinstance(fx_pairs, list)
    pairs = [item["pair"] for item in fx_pairs]
    assert "USD/HKD" in pairs
    assert "CNY/HKD" in pairs
    
    # Verify sourceStatus includes seed_data
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [item["status"] for item in source_status]
    assert "seed_data" in statuses
    
    # Ensure no response text claims realtime/source-fresh
    response_text_lower = response.text.lower()
    assert "realtime" not in response_text_lower
    assert "source-fresh" not in response_text_lower
    assert "source_fresh" not in response_text_lower
