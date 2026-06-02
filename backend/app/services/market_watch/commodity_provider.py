import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    async def fetch_commodity_price(self, function_name: str) -> Optional[float]:
        """
        Fetches commodity price from Alpha Vantage (e.g., COPPER, BRENT, NATURAL_GAS).
        """
        if not self.api_key:
            return None
        params = {
            "function": function_name,
            "apikey": self.api_key
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                records = data.get("data", [])
                if records:
                    return float(records[0].get("value", 0.0))
                return None
        except Exception as e:
            logger.error(f"Alpha Vantage fetch error for {function_name}: {e}")
            return None
