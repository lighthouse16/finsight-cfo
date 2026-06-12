from typing import Optional, List
from fastapi import APIRouter, Header

from app.models.market_funding import (
    MarketFundingIntelligenceResponse,
    FundingChannel,
    TimingSignalsResponse
)
from app.services.market_funding.intelligence_service import (
    get_market_funding_intelligence,
    get_funding_channels,
    get_timing_signals
)

router = APIRouter()

@router.get("/intelligence", response_model=MarketFundingIntelligenceResponse)
async def get_intelligence_endpoint(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None
):
    ws_id = workspace_id or x_workspace_id
    return await get_market_funding_intelligence(ws_id)

@router.get("/funding-channels", response_model=List[FundingChannel])
async def get_funding_channels_endpoint(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None
):
    ws_id = workspace_id or x_workspace_id
    return await get_funding_channels(ws_id)

@router.get("/timing-signals", response_model=TimingSignalsResponse)
async def get_timing_signals_endpoint(
    x_workspace_id: Optional[str] = Header(None, alias="x-workspace-id"),
    workspace_id: Optional[str] = None
):
    ws_id = workspace_id or x_workspace_id
    return await get_timing_signals(ws_id)
