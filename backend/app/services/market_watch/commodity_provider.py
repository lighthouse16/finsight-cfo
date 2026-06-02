from typing import Optional

class CommodityProvider:
    """
    Abstract interface/stub for future Commodity data providers.
    Actual external provider calls and Yahoo Finance / Alpha Vantage integrations will be handled in Phase 3.
    """
    async def fetch_commodity_exposures(self, sector: Optional[str] = None, geography: Optional[str] = None) -> dict:
        raise NotImplementedError("CommodityProvider is currently a stub interface.")
