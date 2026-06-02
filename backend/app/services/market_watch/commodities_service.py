from typing import Optional
from app.models.market_watch import CommoditiesResponse
from app.services.market_watch.fixtures import get_commodities_fixture

async def get_commodities(
    sector: Optional[str] = None, 
    geography: Optional[str] = None
) -> CommoditiesResponse:
    """
    Returns fixture data for Commodities.
    Optionally accepts sector and geography query params.
    Production commodities provider will be integrated in Phase 3.
    """
    return get_commodities_fixture(sector=sector, geography=geography)
