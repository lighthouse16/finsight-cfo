from typing import Optional
from app.core.config import settings
from app.models.market_watch import SectorBenchmarksResponse
from app.services.market_watch.fixtures import get_sector_benchmarks_fixture

async def get_sector_benchmarks(
    sector: Optional[str] = None, 
    geography: Optional[str] = None
) -> SectorBenchmarksResponse:
    """
    Returns Sector Benchmarks with source provenance.
    """
    res = get_sector_benchmarks_fixture(sector=sector, geography=geography)
    
    if settings.MARKET_WATCH_USE_FIXTURES:
        mode = "fixture"
        provider = "FinSight Local"
        caveat = "Using local seed data fixture"
        confidence = "low"
    elif not settings.IHS_MARKIT_API_KEY:
        mode = "provider_not_configured"
        provider = "IHS Markit (not configured)"
        caveat = "IHS Markit provider is not configured. Showing fallback workspace benchmarks."
        confidence = "low"
    else:
        mode = "provider_configured"
        provider = "IHS Markit"
        caveat = None
        confidence = "high"

    for b in res.benchmarks:
        b.sourceName = provider
        b.sourceMode = mode
        b.asOf = b.sourceTimestamp or "2026-06"
        b.freshness = "Monthly"
        b.caveat = caveat
        b.confidence = confidence

    return res

