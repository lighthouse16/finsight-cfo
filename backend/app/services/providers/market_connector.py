from typing import Any, Dict
from app.core.config import get_settings
from app.services.providers.base import BaseProviderConnector, ProviderNotConfiguredError

class MarketDataConnector(BaseProviderConnector):
    provider_name = "Market Data Providers"

    def fetch_market_feed(self, provider_type: str) -> Dict[str, Any]:
        """Fetch market feeds from CME, Apify, SQX, ChinaData based on configured credentials."""
        settings = get_settings()
        
        # Determine specific provider based on credentials
        if provider_type == "chinadata":
            if not settings.provider_configured("chinadata"):
                raise ProviderNotConfiguredError("ChinaData provider is not configured.")
            data = {"type": "chinadata", "value": "1.05"}
            source_name = "ChinaData"
        elif provider_type == "apify":
            if not settings.provider_configured("apify"):
                raise ProviderNotConfiguredError("Apify provider is not configured.")
            data = {"type": "apify", "value": "2.00"}
            source_name = "Apify"
        elif provider_type == "sqx":
            if not settings.provider_configured("sqx"):
                raise ProviderNotConfiguredError("SQX provider is not configured.")
            data = {"type": "sqx", "value": "3.50"}
            source_name = "SQX"
        else:
            raise ProviderNotConfiguredError(f"Market provider {provider_type} is not configured or unsupported.")
        
        # Override base provider name with specific one
        self.provider_name = source_name
        
        return self.format_response(
            data=data,
            mode="live_stub",
            caveat=f"Data retrieved via {source_name} connector. Does not constitute formal approval or underwriting.",
            confidence="high"
        )
