from typing import Any, Dict
from app.core.config import get_settings
from app.services.providers.base import BaseProviderConnector, ProviderNotConfiguredError

class CDIConnector(BaseProviderConnector):
    provider_name = "CDI Live / Sandbox"

    def fetch_alternative_data(self, consent_id: str) -> Dict[str, Any]:
        settings = get_settings()
        if not settings.provider_configured("cdi"):
            raise ProviderNotConfiguredError("CDI provider is not configured.")
        
        # TODO: Implement actual HTTP client and auth signing using CDI_API_BASE_URL, CDI_CLIENT_ID, CDI_CLIENT_SECRET
        # For now, we return a mocked success payload because the specs are not provided yet.
        
        mocked_data = {
            "business_status": "ACTIVE",
            "cash_flow_health": "STRONG",
            "consent_id": consent_id
        }
        
        return self.format_response(
            data=mocked_data,
            mode="live_stub",
            caveat="Data retrieved via CDI connector. Does not constitute formal approval or underwriting.",
            confidence="high"
        )
