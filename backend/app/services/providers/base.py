from datetime import datetime, timezone
from typing import Any, Dict

class ProviderNotConfiguredError(Exception):
    """Exception raised when a provider is not configured with necessary credentials."""
    pass

class BaseProviderConnector:
    """Base class for all live provider connectors."""
    
    provider_name: str = "Base Provider"
    
    def format_response(self, data: Any, mode: str, caveat: str, confidence: str = "medium") -> Dict[str, Any]:
        """
        Format the response to include standard metadata.
        Note: The caveat should never claim formal approval or underwriting.
        """
        return {
            "source_name": self.provider_name,
            "source_mode": mode,
            "as_of": datetime.now(timezone.utc).isoformat(),
            "caveat": caveat,
            "confidence": confidence,
            "data": data
        }
