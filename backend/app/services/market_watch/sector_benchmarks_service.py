from typing import Optional
from app.models.market_watch import SectorBenchmarksResponse, SourceProvenance
from app.services.market_watch.fixtures import get_sector_benchmarks_fixture
from app.services.market_watch.source_registry import build_provenance

async def get_sector_benchmarks(
    sector: Optional[str] = None, 
    geography: Optional[str] = None
) -> SectorBenchmarksResponse:
    """
    Returns fixture data for Sector Benchmarks.
    Optionally accepts sector and geography query params.
    Production sector provider will be integrated in Phase 3.
    """
    res = get_sector_benchmarks_fixture(sector=sector, geography=geography)
    res.provenance = SourceProvenance(**build_provenance("sector_benchmarks_v1"))
    return res
