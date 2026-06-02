from typing import Optional
from app.models.market_watch import SectorBenchmarksResponse
from app.services.market_watch.fixtures import get_sector_benchmarks_fixture

async def get_sector_benchmarks(
    sector: Optional[str] = None, 
    geography: Optional[str] = None
) -> SectorBenchmarksResponse:
    """
    Returns fixture data for Sector Benchmarks.
    Optionally accepts sector and geography query params.
    Production sector provider will be integrated in Phase 3.
    """
    return get_sector_benchmarks_fixture(sector=sector, geography=geography)
