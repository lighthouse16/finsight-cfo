from typing import Optional
from fastapi import APIRouter
from app.models.market_watch import (
    RatesLiquidityResponse,
    FxGbaResponse,
    SectorBenchmarksResponse,
    CommoditiesResponse,
    StressSignalsResponse
)
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity
from app.services.market_watch.fx_gba_service import get_fx_gba
from app.services.market_watch.sector_benchmarks_service import get_sector_benchmarks
from app.services.market_watch.commodities_service import get_commodities
from app.services.market_watch.stress_signals_service import get_stress_signals

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



