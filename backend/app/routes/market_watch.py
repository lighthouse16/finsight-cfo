from fastapi import APIRouter
from app.models.market_watch import RatesLiquidityResponse, FxGbaResponse
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity
from app.services.market_watch.fx_gba_service import get_fx_gba

router = APIRouter()

@router.get("/rates-liquidity", response_model=RatesLiquidityResponse)
async def get_rates_liquidity_endpoint():
    return await get_rates_liquidity()

@router.get("/fx-gba", response_model=FxGbaResponse)
async def get_fx_gba_endpoint():
    return await get_fx_gba()
