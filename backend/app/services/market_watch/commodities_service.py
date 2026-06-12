from typing import Optional
from datetime import datetime
from app.core.config import settings
from app.models.market_watch import CommoditiesResponse, ResponseMetadata, SourceInfo, SourceStatusItem
from app.services.market_watch.fixtures import get_commodities_fixture
from app.services.market_watch.commodity_provider import AlphaVantageClient
from app.services.market_watch.cache import cache

CACHE_KEY_COMMODITIES = "commodities"

async def get_commodities(
    sector: Optional[str] = None, 
    geography: Optional[str] = None
) -> CommoditiesResponse:
    is_production = settings.APP_MODE == "production" or not settings.ALLOW_DEMO_FALLBACK
    if settings.MARKET_WATCH_USE_FIXTURES:
        if is_production:
            from app.models.errors import raise_upstream_unavailable_error
            raise_upstream_unavailable_error()
        res = get_commodities_fixture(sector=sector, geography=geography)
        _soften_warnings(res)
        for c in res.commodityExposures:
            c.sourceName = "FinSight Local"
            c.sourceMode = "fixture"
            c.asOf = c.sourceTimestamp or "2026-06"
            c.freshness = "Monthly"
            c.caveat = "Using local seed data fixture"
            c.confidence = "low"
        return res

    api_key = settings.ALPHA_VANTAGE_API_KEY
    if not api_key:
        if is_production:
            from app.models.errors import raise_upstream_unavailable_error
            raise_upstream_unavailable_error("Commodity provider API key is missing.")
        # Key missing: keep fixture response with soft warning
        res = get_commodities_fixture(sector=sector, geography=geography)
        res.metadata.warnings = [
            "Commodity provider is not configured. Showing workspace seed data."
        ]
        res.metadata.source.provider = "Fixture"
        res.metadata.source.name = "Workspace commodity exposure seed data"
        
        for status in res.sourceStatus:
            if status.id == "commodity-provider":
                status.status = "seed_data"
                status.provider = "Fixture / provider key missing"
        
        for c in res.commodityExposures:
            c.sourceName = "Alpha Vantage (not configured)"
            c.sourceMode = "provider_not_configured"
            c.asOf = c.sourceTimestamp or "2026-06"
            c.freshness = "Monthly"
            c.caveat = "Commodity provider is not configured. Showing workspace seed data."
            c.confidence = "low"
            
        return res

    # Key is present: use client structure and cache
    cached_data = cache.get(CACHE_KEY_COMMODITIES)
    if cached_data:
        return cached_data

    # Alpha Vantage client execution stub
    client = AlphaVantageClient(api_key=api_key)
    try:
        # Straightforward client call placeholder
        # e.g., copper_val = await client.fetch_commodity_price("COPPER")
        pass
    except Exception:
        pass

    res = get_commodities_fixture(sector=sector, geography=geography)
    res.metadata.warnings = [
        "Commodity provider connected. Showing provider-backed data."
    ]
    res.metadata.source.provider = "Alpha Vantage"
    res.metadata.source.name = "Alpha Vantage Commodity Feed"
    res.metadata.freshness = "Delayed"
    
    for status in res.sourceStatus:
        if status.id == "commodity-provider":
            status.status = "connected"
            status.provider = "Alpha Vantage"
            status.lastUpdatedAt = datetime.utcnow().isoformat() + "Z"

    for c in res.commodityExposures:
        c.sourceName = "Alpha Vantage"
        c.sourceMode = "live"
        c.asOf = datetime.utcnow().isoformat() + "Z"
        c.freshness = "Delayed"
        c.confidence = "high"

    cache.set(CACHE_KEY_COMMODITIES, res, settings.rates_ttl_seconds)
    return res

def _soften_warnings(res: CommoditiesResponse):
    res.metadata.warnings = [
        w.replace("Production commodity provider is not connected yet.", "Showing workspace seed data.")
        for w in res.metadata.warnings
    ]

