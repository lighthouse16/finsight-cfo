from app.models.market_watch import FxGbaResponse
from app.services.market_watch.fixtures import get_fx_gba_fixture

async def get_fx_gba() -> FxGbaResponse:
    """
    Returns fixture data for FX & GBA endpoint.
    Production FX provider will be integrated in Phase 2.
    """
    return get_fx_gba_fixture()
