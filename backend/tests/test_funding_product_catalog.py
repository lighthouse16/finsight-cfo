import pytest
import asyncio
from app.core.config import settings
from app.services.market_watch.product_catalog import ProductCatalogService
from app.services.market_watch.provider_adapters import BOCHKProductCatalogAdapter
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_bochk_settings():
    # Store initial value
    orig_val = settings.BOCHK_CATALOG_CONFIGURED
    yield
    # Restore initial value
    settings.BOCHK_CATALOG_CONFIGURED = orig_val

def test_local_json_catalog_loading():
    settings.BOCHK_CATALOG_CONFIGURED = False
    service = ProductCatalogService()
    
    # Run async function using asyncio.run
    products = asyncio.run(service.get_products())
    
    assert len(products) > 0
    for p in products:
        assert p.source_mode == "fixture"
        assert p.provider == "FinSight Local Demo"
        assert p.product_id.startswith("generic_")
        # Ensure no forbidden wording in generic products
        for field in [p.product_name, p.limits, p.tenor_range, p.collateral_requirements, p.caveats]:
            if field:
                lowered = field.lower()
                assert "guaranteed" not in lowered
                assert "approved" not in lowered
                assert "arbitrage profit" not in lowered
                assert "official bochk offer" not in lowered

def test_bochk_provider_configured_success():
    settings.BOCHK_CATALOG_CONFIGURED = True
    service = ProductCatalogService()
    
    products = asyncio.run(service.get_products())
    
    assert len(products) > 0
    for p in products:
        assert p.source_mode == "provider_configured"
        assert p.provider == "Bank of China (Hong Kong)"
        assert p.product_id.startswith("bochk_")

def test_bochk_provider_not_configured_adapter():
    settings.BOCHK_CATALOG_CONFIGURED = False
    adapter = BOCHKProductCatalogAdapter()
    
    result = asyncio.run(adapter.fetch())
    
    assert result["status"]["mode"] == "provider_not_configured"
    assert result["error"] is not None
    assert "not configured" in result["error"].lower()

def test_bochk_provider_failure_fallback(monkeypatch):
    settings.BOCHK_CATALOG_CONFIGURED = True
    
    # Mock adapter fetch to raise an error
    async def mock_fetch(self):
        return {
            "status": {
                "providerName": "Bank of China (Hong Kong)",
                "providerKey": "funding_channel_ranking_v1",
                "mode": "unavailable",
                "warnings": ["Simulated error"]
            },
            "sourceKey": "funding_channel_ranking_v1",
            "error": "Simulated error"
        }
    monkeypatch.setattr(BOCHKProductCatalogAdapter, "fetch", mock_fetch)
    
    service = ProductCatalogService()
    products = asyncio.run(service.get_products())
    
    # It should fall back to the local json catalog
    assert len(products) > 0
    for p in products:
        assert p.source_mode == "fixture"
        assert p.provider == "FinSight Local Demo"

def test_no_fake_source_claims():
    # When not configured, NO product can claim BOCHK
    settings.BOCHK_CATALOG_CONFIGURED = False
    service = ProductCatalogService()
    products = asyncio.run(service.get_products())
    
    for p in products:
        assert p.provider != "Bank of China (Hong Kong)"
        assert not p.product_id.startswith("bochk_")

def test_forbidden_language_scan_not_configured():
    settings.BOCHK_CATALOG_CONFIGURED = False
    
    # Request the channel ranking endpoint which matches products and returns items
    response = client.get("/api/market-watch/funding-channel-ranking")
    assert response.status_code == 200
    
    text = response.text.lower()
    
    # Scan for forbidden terms
    assert "guaranteed" not in text
    assert "approved" not in text
    assert "arbitrage profit" not in text
    assert "official bochk offer" not in text
