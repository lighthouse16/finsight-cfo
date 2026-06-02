from typing import Optional
from fastapi import APIRouter
from app.models.market_watch import RatesLiquidityResponse, FxGbaResponse, SectorBenchmarksResponse
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity
from app.services.market_watch.fx_gba_service import get_fx_gba
from app.services.market_watch.sector_benchmarks_service import get_sector_benchmarks

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

