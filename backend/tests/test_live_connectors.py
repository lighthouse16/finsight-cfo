import pytest
from app.core.config import Settings
from app.services.providers.base import ProviderNotConfiguredError
from app.services.providers.cdi_connector import CDIConnector
from app.services.providers.ccra_connector import CCRAConnector
from app.services.providers.mpf_connector import MPFConnector
from app.services.providers.cargox_connector import CargoXConnector
from app.services.providers.bochk_connector import BOCHKCatalogConnector
from app.services.providers.market_connector import MarketDataConnector

@pytest.fixture
def configured_settings(monkeypatch):
    monkeypatch.setenv("CDI_API_BASE_URL", "https://api.cdi.example.com")
    monkeypatch.setenv("CDI_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("CDI_CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("CCRA_API_BASE_URL", "https://api.ccra.example.com")
    monkeypatch.setenv("CCRA_API_KEY", "test_ccra_key")
    monkeypatch.setenv("MPF_API_BASE_URL", "https://api.mpf.example.com")
    monkeypatch.setenv("MPF_API_KEY", "test_mpf_key")
    monkeypatch.setenv("CARGOX_API_BASE_URL", "https://api.cargox.example.com")
    monkeypatch.setenv("CARGOX_API_KEY", "test_cargox_key")
    monkeypatch.setenv("BOCHK_CATALOG_API_BASE_URL", "https://api.bochk.example.com")
    monkeypatch.setenv("BOCHK_CATALOG_API_KEY", "test_bochk_key")
    monkeypatch.setenv("CHINADATA_API_KEY", "test_chinadata_key")
    
    settings = Settings()
    return settings

def test_provider_not_configured(monkeypatch):
    monkeypatch.setenv("CDI_API_BASE_URL", "")
    monkeypatch.setenv("CDI_CLIENT_ID", "")
    monkeypatch.setenv("CDI_CLIENT_SECRET", "")
    
    # We must patch get_settings to return the fresh instance
    import app.services.providers.cdi_connector as cdi_module
    cdi_module.get_settings = lambda: Settings()
    
    connector = CDIConnector()
    with pytest.raises(ProviderNotConfiguredError):
        connector.fetch_alternative_data(consent_id="test")

def test_cdi_mocked_success(configured_settings, monkeypatch):
    import app.services.providers.cdi_connector as cdi_module
    cdi_module.get_settings = lambda: configured_settings
    
    connector = CDIConnector()
    response = connector.fetch_alternative_data(consent_id="test_consent")
    
    assert response["source_name"] == "CDI Live / Sandbox"
    assert response["source_mode"] == "live_stub"
    assert "data" in response
    assert response["data"]["consent_id"] == "test_consent"
    
    # Ensure no secret leakage
    response_str = str(response)
    assert "test_client_secret" not in response_str
    assert "test_client_id" not in response_str

def test_ccra_mocked_success(configured_settings, monkeypatch):
    import app.services.providers.ccra_connector as ccra_module
    ccra_module.get_settings = lambda: configured_settings
    
    connector = CCRAConnector()
    response = connector.fetch_credit_report(company_id="comp_123")
    
    assert response["source_name"] == "CCRA / Dun & Bradstreet"
    assert response["data"]["company_id"] == "comp_123"
    assert "test_ccra_key" not in str(response)

def test_market_provider_routing(configured_settings, monkeypatch):
    import app.services.providers.market_connector as market_module
    market_module.get_settings = lambda: configured_settings
    
    connector = MarketDataConnector()
    
    # Test valid configured provider
    response = connector.fetch_market_feed(provider_type="chinadata")
    assert response["source_name"] == "ChinaData"
    
    # Test unconfigured provider
    with pytest.raises(ProviderNotConfiguredError):
        connector.fetch_market_feed(provider_type="apify")

@pytest.mark.skipif(True, reason="Live credentials not present for smoke tests")
def test_live_smoke_cdi():
    """Live smoke test gated by actual presence of credentials. Currently skipped."""
    pass
