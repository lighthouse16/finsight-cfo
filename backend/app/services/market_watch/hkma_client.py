import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings

class HKMAClient:
    def __init__(self):
        self.base_url = settings.HKMA_BASE_URL
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    async def _fetch(self, path: str, params: Dict[str, str]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            # Handle specifically to allow upstream error propagation
            raise Exception(f"HKMA HTTP error: {str(e)}")
        except Exception as e:
            raise Exception(f"HKMA generic error: {str(e)}")

    async def get_hibor_fixing(self) -> List[Dict[str, Any]]:
        path = "/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily"
        params = {"segment": "hibor.fixing", "offset": "0"}
        data = await self._fetch(path, params)
        return data.get("result", {}).get("records", [])

    async def get_honia(self) -> List[Dict[str, Any]]:
        path = "/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily"
        params = {"segment": "honia", "offset": "0"}
        data = await self._fetch(path, params)
        return data.get("result", {}).get("records", [])

    async def get_interbank_liquidity(self) -> List[Dict[str, Any]]:
        path = "/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity"
        params = {"offset": "0"}
        data = await self._fetch(path, params)
        return data.get("result", {}).get("records", [])

hkma_client = HKMAClient()
