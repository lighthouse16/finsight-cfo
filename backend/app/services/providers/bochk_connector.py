from typing import Any, Dict
from app.core.config import get_settings
from app.services.providers.base import BaseProviderConnector, ProviderNotConfiguredError

class BOCHKCatalogConnector(BaseProviderConnector):
    provider_name = "BOCHK / SFGS Product Catalog"

    def fetch_product_catalog(self) -> Dict[str, Any]:
        settings = get_settings()
        if not settings.provider_configured("bochk"):
            raise ProviderNotConfiguredError("BOCHK Catalog provider is not configured.")
        
        # TODO: Implement actual HTTP client and auth signing
        mocked_data = {
            "products": [
                {"id": "sfgs-80", "name": "SFGS 80% Guarantee Product"},
                {"id": "sfgs-100", "name": "SFGS 100% Guarantee Product"}
            ]
        }
        
        return self.format_response(
            data=mocked_data,
            mode="live_stub",
            caveat="Data retrieved via BOCHK Catalog connector. Does not constitute formal approval or underwriting.",
            confidence="high"
        )
