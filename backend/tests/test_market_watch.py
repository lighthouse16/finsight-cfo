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

def test_fx_gba(monkeypatch):
    # Mock FrankfurterClient fetch_fx_rates
    async def mock_fetch_fx_rates(self):
        return {
            "usd": {
                "date": "2026-06-02",
                "rates": {"CNY": 6.7626, "HKD": 7.8374}
            },
            "cny": {
                "date": "2026-06-02",
                "rates": {"HKD": 1.1589}
            },
            "is_v2": False
        }
    
    from app.services.market_watch.fx_client import FrankfurterClient
    monkeypatch.setattr(FrankfurterClient, "fetch_fx_rates", mock_fetch_fx_rates)
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", False)

    response = client.get("/api/market-watch/fx-gba")
    assert response.status_code == 200
    data = response.json()
    
    # Verify provider is Frankfurter
    assert data["metadata"]["source"]["provider"] == "Frankfurter"
    assert isinstance(data["metadata"]["warnings"], list)
    
    fx_pairs = data["fxPairs"]
    assert isinstance(fx_pairs, list)
    pairs = [item["pair"] for item in fx_pairs]
    assert "USD/HKD" in pairs
    assert "CNY/HKD" in pairs
    
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [item["status"] for item in source_status]
    assert "connected" in statuses
    
    # Test fallback path
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", True)
    response_fallback = client.get("/api/market-watch/fx-gba")
    assert response_fallback.status_code == 200
    data_fallback = response_fallback.json()
    assert data_fallback["metadata"]["source"]["provider"] == "Fixture"
    assert data_fallback["sourceStatus"][0]["status"] == "seed_data"
    
    response_text_lower = response.text.lower()
    assert "realtime" not in response_text_lower
    assert "source-fresh" not in response_text_lower
    assert "source_fresh" not in response_text_lower


def test_sector_benchmarks():
    # 1. Test default query
    response = client.get("/api/market-watch/sector-benchmarks")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "selectedSector" in data
    assert "sectorHealth" in data
    assert "benchmarks" in data
    assert "watchSignals" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert metadata["source"]["provider"] == "Fixture"
    assert isinstance(metadata["warnings"], list)
    assert len(metadata["warnings"]) > 0
    assert "fixture-backed" in metadata["warnings"][0].lower()
    
    # Verify default sector
    selected_sector = data["selectedSector"]
    assert selected_sector["id"] == "trading-distribution"
    assert selected_sector["name"] == "Trading & Distribution"
    assert selected_sector["geography"] == "HK"
    assert selected_sector["code"] == "HK-SME-TRD"
    
    # Verify benchmarks and watch signals
    benchmarks = data["benchmarks"]
    assert isinstance(benchmarks, list)
    assert len(benchmarks) >= 3
    # Check DSO, DIO, DPO
    labels = [b["label"] for b in benchmarks]
    assert "Days Sales Outstanding" in labels
    assert "Inventory Days" in labels
    assert "Days Payable Outstanding" in labels
    
    watch_signals = data["watchSignals"]
    assert isinstance(watch_signals, list)
    assert len(watch_signals) >= 3
    
    # Verify sourceStatus includes seed_data
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [s["status"] for s in source_status]
    assert "seed_data" in statuses
    
    # Ensure no response text claims realtime/source-fresh/approved/certified
    response_text_lower = response.text.lower()
    assert "realtime" not in response_text_lower
    assert "source-fresh" not in response_text_lower
    assert "source_fresh" not in response_text_lower
    assert "approved" not in response_text_lower
    assert "certified" not in response_text_lower
    
    # 2. Test electronics-import custom query
    response_custom = client.get("/api/market-watch/sector-benchmarks?sector=electronics-import&geography=CN")
    assert response_custom.status_code == 200
    data_custom = response_custom.json()
    
    selected_sector_custom = data_custom["selectedSector"]
    assert selected_sector_custom["id"] == "electronics-import"
    assert selected_sector_custom["name"] == "Electronics Import"
    assert selected_sector_custom["geography"] == "CN"
    assert selected_sector_custom["code"] == "HK-SME-ELC"
    
    # Check that component display value is correctly fetched
    sector_health_custom = data_custom["sectorHealth"]
    assert sector_health_custom["components"]["pmi"]["displayValue"] == "52.4"


def test_commodities():
    # 1. Test default query
    response = client.get("/api/market-watch/commodities")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "selectedSector" in data
    assert "commodityExposures" in data
    assert "marginPressureSignal" in data
    assert "watchSignals" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert metadata["source"]["provider"] == "Fixture"
    assert isinstance(metadata["warnings"], list)
    assert len(metadata["warnings"]) > 0
    assert "fixture-backed" in metadata["warnings"][0].lower() or "not configured" in metadata["warnings"][0].lower()
    
    # Verify default sector
    selected_sector = data["selectedSector"]
    assert selected_sector["id"] == "electronics-import"
    assert selected_sector["name"] == "Electronics Import"
    assert selected_sector["geography"] == "HK"
    assert selected_sector["code"] == "HK-SME-ELEC"
    
    # Verify commodity exposures
    exposures = data["commodityExposures"]
    assert isinstance(exposures, list)
    assert len(exposures) >= 4
    
    commodities = [c["commodity"] for c in exposures]
    assert "Copper (LME)" in commodities
    assert "Steel / Iron Ore" in commodities
    assert "Cotton" in commodities
    assert "Energy / Oil (Brent)" in commodities
    assert "Freight / Logistics" in commodities
    
    # Verify margin pressure signals
    signals = data["marginPressureSignal"]
    assert isinstance(signals, list)
    assert len(signals) == 1
    assert signals[0]["requiresCompanyData"] is True
    
    # Verify sourceStatus includes seed_data
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [s["status"] for s in source_status]
    assert "seed_data" in statuses
    
    # Ensure no response text claims realtime/source-fresh/approved/certified/trading/lender approved
    response_text_lower = response.text.lower()
    assert "realtime" not in response_text_lower
    assert "source-fresh" not in response_text_lower
    assert "source_fresh" not in response_text_lower
    assert "approved" not in response_text_lower
    assert "certified" not in response_text_lower
    assert "trading advice" not in response_text_lower
    assert "investment recommendation" not in response_text_lower

    # 2. Test trading-distribution custom query
    response_custom = client.get("/api/market-watch/commodities?sector=trading-distribution&geography=CN")
    assert response_custom.status_code == 200
    data_custom = response_custom.json()
    
    selected_sector_custom = data_custom["selectedSector"]
    assert selected_sector_custom["id"] == "trading-distribution"
    assert selected_sector_custom["name"] == "Trading & Distribution"
    assert selected_sector_custom["geography"] == "CN"
    assert selected_sector_custom["code"] == "HK-SME-TRD"


def test_stress_signals():
    # 1. Test default query
    response = client.get("/api/market-watch/stress-signals")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert presence of key fields
    assert "metadata" in data
    assert "workspaceContext" in data
    assert "scenarios" in data
    assert "requiredData" in data
    assert "watchSignals" in data
    assert "sourceStatus" in data
    
    # Verify metadata fields
    metadata = data["metadata"]
    assert metadata["source"]["provider"] == "Fixture"
    assert isinstance(metadata["warnings"], list)
    assert len(metadata["warnings"]) > 0
    assert "fixture-backed" in metadata["warnings"][0].lower()
    
    # Verify workspace context
    context = data["workspaceContext"]
    assert context["id"] == "workspace-demo"
    assert context["companyLabel"] == "Workspace Demo Context (Trading & Distribution)"
    assert context["sector"] == "Trading & Distribution"
    assert context["geography"] == "HK"
    
    # Verify scenarios
    scenarios = data["scenarios"]
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 5
    
    titles = [s["title"] for s in scenarios]
    assert "Rate Shock (+150 bps)" in titles
    assert "CNY Depreciation (-5%)" in titles
    assert "Raw Material Input Squeeze (+10%)" in titles
    assert "Receivables Delay (+15 Days)" in titles
    assert "Liquidity Squeeze" in titles
    
    # Verify sourceStatus includes seed_data and requires_company_data
    source_status = data["sourceStatus"]
    assert isinstance(source_status, list)
    statuses = [s["status"] for s in source_status]
    assert "seed_data" in statuses
    assert "requires_company_data" in statuses
    
    # Ensure no response text claims forbidden phrases
    response_text_lower = response.text.lower()
    assert "predicted default" not in response_text_lower
    assert "approval probability" not in response_text_lower
    assert "lender approved" not in response_text_lower
    assert "guaranteed failure" not in response_text_lower
    assert "credit score impact" not in response_text_lower
    assert "bank verified" not in response_text_lower
    assert "quantified dscr impact" not in response_text_lower
    assert "quantify dscr" not in response_text_lower

    # 2. Test custom query
    response_custom = client.get("/api/market-watch/stress-signals?sector=Logistics")
    assert response_custom.status_code == 200
    data_custom = response_custom.json()
    
    context_custom = data_custom["workspaceContext"]
    assert context_custom["sector"] == "Logistics"


def test_source_status():
    response = client.get("/api/market-watch/source-status")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    sources = data["sources"]
    assert len(sources) == 6
    ids = [s["id"] for s in sources]
    assert "hkma-rates" in ids
    assert "fx-provider" in ids
    assert "commodity-provider" in ids


def test_refresh(monkeypatch):
    # Mock Frankfurter client
    async def mock_fetch_fx_rates(self):
        return {
            "usd": {
                "date": "2026-06-02",
                "rates": {"CNY": 6.7626, "HKD": 7.8374}
            },
            "cny": {
                "date": "2026-06-02",
                "rates": {"HKD": 1.1589}
            },
            "is_v2": False
        }
    from app.services.market_watch.fx_client import FrankfurterClient
    monkeypatch.setattr(FrankfurterClient, "fetch_fx_rates", mock_fetch_fx_rates)
    # Also mock HKMA calls by forcing settings
    monkeypatch.setattr(settings, "MARKET_WATCH_USE_FIXTURES", True)

    response = client.post("/api/market-watch/refresh", json={"scope": "all"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["refreshedScope"] == "all"
    assert "sources" in data

    response_single = client.post("/api/market-watch/refresh", json={"scope": "rates-liquidity"})
    assert response_single.status_code == 200
    data_single = response_single.json()
    assert data_single["status"] == "success"
    assert data_single["refreshedScope"] == "rates-liquidity"

    response_fixture = client.post("/api/market-watch/refresh", json={"scope": "sector-benchmarks"})
    assert response_fixture.status_code == 200
    data_fixture = response_fixture.json()
    assert data_fixture["status"] == "success"
    assert "retained" in data_fixture["message"]
def test_company_context():
    response = client.get("/api/market-watch/company-context")
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "exposures" in data
    assert "dataMode" in data
    assert data["profile"]["companyName"] == "Harbour & Finch Trading Ltd."
    assert len(data["exposures"]) > 0
