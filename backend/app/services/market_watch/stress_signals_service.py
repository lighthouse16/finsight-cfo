from typing import Optional
from app.models.market_watch import StressSignalsResponse, SourceProvenance
from app.services.market_watch.fixtures import get_stress_signals_fixture
from app.services.market_watch.source_registry import build_provenance

async def get_stress_signals(
    company_id: Optional[str] = None, 
    sector: Optional[str] = None
) -> StressSignalsResponse:
    """
    Returns fixture data for Stress Signals.
    Optionally accepts company_id and sector query params.
    Production stress engine calculations will be integrated in Phase 3.
    """
    res = get_stress_signals_fixture(company_id=company_id, sector=sector)
    res.provenance = SourceProvenance(**build_provenance("stress_signals_v1"))
    return res
