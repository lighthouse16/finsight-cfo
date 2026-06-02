from fastapi import APIRouter
from app.models.market_watch import RatesLiquidityResponse
from app.services.market_watch.rates_liquidity_service import get_rates_liquidity

router = APIRouter()

@router.get("/rates-liquidity", response_model=RatesLiquidityResponse)
async def get_rates_liquidity_endpoint():
    return await get_rates_liquidity()
