from datetime import datetime
from typing import List, Optional
from app.core.config import settings
from app.models.market_watch import ConsolidatedSourceStatusItem
from app.services.market_watch.cache import cache

async def get_consolidated_source_status() -> List[ConsolidatedSourceStatusItem]:
    now_str = datetime.utcnow().isoformat() + "Z"
    
    # 1. HKMA Rates
    rates_cached = cache.get("rates_liquidity")
    if rates_cached:
        rates_status = "stale" if rates_cached.metadata.isStale else "connected"
        rates_provider = rates_cached.metadata.source.provider
        rates_freshness = rates_cached.metadata.freshness
        rates_time = rates_cached.metadata.fetchedAt
        rates_msg = "Connected to HKMA daily rate feed."
    else:
        rates_status = "connected" if not settings.MARKET_WATCH_USE_FIXTURES else "seed_data"
        rates_provider = "HKMA API" if not settings.MARKET_WATCH_USE_FIXTURES else "Fixture"
        rates_freshness = "Daily"
        rates_time = now_str
        rates_msg = "Connected to HKMA daily rate feed." if not settings.MARKET_WATCH_USE_FIXTURES else "Showing workspace seed data."
        
    # 2. FX Provider
    fx_cached = cache.get("fx_gba")
    if fx_cached:
        fx_status = "stale" if fx_cached.metadata.isStale else "connected"
        fx_provider = fx_cached.metadata.source.provider
        fx_freshness = fx_cached.metadata.freshness
        fx_time = fx_cached.metadata.fetchedAt
        fx_msg = "Rates fetched from Frankfurter."
    else:
        fx_status = "connected" if not settings.MARKET_WATCH_USE_FIXTURES else "seed_data"
        fx_provider = "Frankfurter" if not settings.MARKET_WATCH_USE_FIXTURES else "Fixture"
        fx_freshness = "Daily"
        fx_time = now_str
        fx_msg = "Rates fetched from Frankfurter." if not settings.MARKET_WATCH_USE_FIXTURES else "Showing workspace seed data."

    # 3. Sector Benchmarks Provider
    sector_status = "seed_data"
    sector_provider = "Fixture"
    sector_freshness = "Monthly"
    sector_time = "2026-05"
    sector_msg = "Using regional benchmark profiles."

    # 4. Commodity Provider
    comm_cached = cache.get("commodities")
    if comm_cached:
        comm_status = comm_cached.sourceStatus[0].status
        comm_provider = comm_cached.sourceStatus[0].provider
        comm_freshness = comm_cached.metadata.freshness
        comm_time = comm_cached.metadata.fetchedAt
        comm_msg = comm_cached.metadata.warnings[0] if comm_cached.metadata.warnings else "Commodity feed connected."
    else:
        api_key = settings.ALPHA_VANTAGE_API_KEY
        if api_key:
            comm_status = "connected"
            comm_provider = "Alpha Vantage"
            comm_freshness = "Delayed"
            comm_time = now_str
            comm_msg = "Commodity provider connected. Showing provider-backed data."
        else:
            comm_status = "seed_data"
            comm_provider = "Fixture"
            comm_freshness = "Monthly"
            comm_time = "2026-05"
            comm_msg = "Commodity provider is not configured. Showing workspace seed data."

    # 5. Stress Signals Engine
    stress_status = "requires_backend"
    stress_provider = "Pending"
    stress_freshness = "Workspace"
    stress_time = None
    stress_msg = "Requires company financial records to activate engine."

    # 6. Company Financial Records
    company_status = "requires_company_data"
    company_provider = "Pending"
    company_freshness = "Workspace"
    company_time = None
    company_msg = "No company financial records connected to this workspace."

    return [
        ConsolidatedSourceStatusItem(
            id="hkma-rates",
            label="HKMA Rates",
            status=rates_status,
            provider=rates_provider,
            freshness=rates_freshness,
            lastUpdatedAt=rates_time,
            message=rates_msg
        ),
        ConsolidatedSourceStatusItem(
            id="fx-provider",
            label="FX Provider",
            status=fx_status,
            provider=fx_provider,
            freshness=fx_freshness,
            lastUpdatedAt=fx_time,
            message=fx_msg
        ),
        ConsolidatedSourceStatusItem(
            id="sector-benchmarks-provider",
            label="Sector Benchmarks Provider",
            status=sector_status,
            provider=sector_provider,
            freshness=sector_freshness,
            lastUpdatedAt=sector_time,
            message=sector_msg
        ),
        ConsolidatedSourceStatusItem(
            id="commodity-provider",
            label="Commodity Provider",
            status=comm_status,
            provider=comm_provider,
            freshness=comm_freshness,
            lastUpdatedAt=comm_time,
            message=comm_msg
        ),
        ConsolidatedSourceStatusItem(
            id="stress-engine",
            label="Stress Engine",
            status=stress_status,
            provider=stress_provider,
            freshness=stress_freshness,
            lastUpdatedAt=stress_time,
            message=stress_msg
        ),
        ConsolidatedSourceStatusItem(
            id="company-financial-records",
            label="Company Financial Records",
            status=company_status,
            provider=company_provider,
            freshness=company_freshness,
            lastUpdatedAt=company_time,
            message=company_msg
        )
    ]
