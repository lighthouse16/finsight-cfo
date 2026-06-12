from typing import Protocol, Optional

class BaseMarketDataAdapter(Protocol):
    async def get_hibor_rate(self) -> Optional[float]:
        ...

    async def get_lpr_rate(self) -> Optional[float]:
        ...

    async def get_fx_hedging_cost(self) -> Optional[float]:
        ...

class FixtureMarketDataAdapter:
    """
    Deterministic mock adapter for rates and hedging cost proxies.
    Ensures tests can run stably without making external API or scraping requests.
    """
    async def get_hibor_rate(self) -> Optional[float]:
        # Future HKMA API integration point
        return 4.25

    async def get_lpr_rate(self) -> Optional[float]:
        # Future PBOC/HKMA GBA integration point
        return 3.45

    async def get_fx_hedging_cost(self) -> Optional[float]:
        # Future CDI/HKEX hedging cost integration point
        return 1.25
