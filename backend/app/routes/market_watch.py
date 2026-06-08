from typing import Optional
from fastapi import APIRouter
from app.models.market_watch import (
    RatesLiquidityResponse,
    FxGbaResponse,
    SectorBenchmarksResponse,
    CommoditiesResponse,
    StressSignalsResponse,
    ConsolidatedSourceStatusResponse,
    RefreshRequest,
    RefreshResponse,
    TimingSignalResponse,
    IndustryHealthResponse,
    FundingChannelRankingResponse
)
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity
from app.services.market_watch.fx_gba_service import get_fx_gba
from app.services.market_watch.sector_benchmarks_service import get_sector_benchmarks
from app.services.market_watch.commodities_service import get_commodities
from app.services.market_watch.stress_signals_service import get_stress_signals
from app.services.market_watch.source_status import get_consolidated_source_status
from app.services.market_watch.timing_signal_service import get_timing_signal
from app.services.market_watch.industry_health_service import get_industry_health
from app.services.market_watch.funding_channel_ranking_service import get_funding_channel_ranking
from app.services.market_watch.cache import cache

router = APIRouter()

@router.get("/rates-liquidity", response_model=RatesLiquidityResponse)
async def get_rates_liquidity_endpoint():
    return await get_rates_liquidity()

@router.get("/fx-gba", response_model=FxGbaResponse)
async def get_fx_gba_endpoint():
    return await get_fx_gba()

@router.get("/sector-benchmarks", response_model=SectorBenchmarksResponse)
async def get_sector_benchmarks_endpoint(
    sector: Optional[str] = None,
    geography: Optional[str] = None
):
    return await get_sector_benchmarks(sector=sector, geography=geography)

@router.get("/commodities", response_model=CommoditiesResponse)
async def get_commodities_endpoint(
    sector: Optional[str] = None,
    geography: Optional[str] = None
):
    return await get_commodities(sector=sector, geography=geography)

@router.get("/stress-signals", response_model=StressSignalsResponse)
async def get_stress_signals_endpoint(
    companyId: Optional[str] = None,
    sector: Optional[str] = None
):
    return await get_stress_signals(company_id=companyId, sector=sector)

@router.get("/timing-signal", response_model=TimingSignalResponse)
async def get_timing_signal_endpoint():
    return await get_timing_signal()

@router.get("/industry-health", response_model=IndustryHealthResponse)
async def get_industry_health_endpoint(
    sector: Optional[str] = None,
    geography: Optional[str] = None
):
    return await get_industry_health(sector=sector, geography=geography)

@router.get("/funding-channel-ranking", response_model=FundingChannelRankingResponse)
async def get_funding_channel_ranking_endpoint():
    return await get_funding_channel_ranking()

@router.get("/source-status", response_model=ConsolidatedSourceStatusResponse)
async def get_source_status_endpoint():
    sources = await get_consolidated_source_status()
    return ConsolidatedSourceStatusResponse(sources=sources)

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_endpoint(request: RefreshRequest):
    scope = request.scope or "all"
    
    refreshed_any = False
    fixture_retained = False
    
    if scope in ("rates-liquidity", "all"):
        cache.delete("rates_liquidity")
        await get_rates_liquidity()
        refreshed_any = True
        
    if scope in ("fx-gba", "all"):
        cache.delete("fx_gba")
        await get_fx_gba()
        refreshed_any = True
        
    if scope in ("commodities", "all"):
        cache.delete("commodities")
        await get_commodities()
        refreshed_any = True
        
    if scope in ("sector-benchmarks", "stress-signals", "overview"):
        fixture_retained = True
        
    sources = await get_consolidated_source_status()
    
    if fixture_retained and not refreshed_any:
        msg = "No live provider configured; fixture data retained."
    else:
        msg = f"Successfully refreshed scope: {scope}"
        
    return RefreshResponse(
        status="success",
        message=msg,
        refreshedScope=scope,
        sources=sources
    )


from app.models.market_watch import CompanyContextResponse
from app.services.market_watch.company_context import (
    get_demo_company_profile,
    get_company_exposures
)

@router.get("/company-context", response_model=CompanyContextResponse)
async def get_company_context_endpoint():
    profile = get_demo_company_profile()
    exposures = get_company_exposures()
    return CompanyContextResponse(
        profile=profile,
        exposures=exposures,
        dataMode="demo_workspace"
    )



