import httpx
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class FrankfurterClient:
    def __init__(self):
        self.base_url = settings.FX_PROVIDER_BASE_URL
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    @property
    def name(self) -> str:
        return "Frankfurter"

    @property
    def base_url_str(self) -> str:
        return self.base_url

    async def fetch_fx_rates(self) -> Dict[str, Any]:
        """
        Fetches latest USD and CNY rates from Frankfurter.
        """
        is_v2 = "v2" in self.base_url
        
        if is_v2:
            url_usd = f"{self.base_url}/rates?base=USD&quotes=HKD,CNY"
            url_cny = f"{self.base_url}/rates?base=CNY&quotes=HKD"
        else:
            url_usd = f"{self.base_url}/latest?from=USD&to=HKD,CNY"
            url_cny = f"{self.base_url}/latest?from=CNY&to=HKD"
            
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            res_usd = await client.get(url_usd)
            res_usd.raise_for_status()
            data_usd = res_usd.json()

            res_cny = await client.get(url_cny)
            res_cny.raise_for_status()
            data_cny = res_cny.json()
            
            return {
                "usd": data_usd,
                "cny": data_cny,
                "is_v2": is_v2
            }
