from typing import Optional

class SectorProvider:
    """
    Abstract interface/stub for future Sector Benchmark data providers.
    Actual external provider calls and NBS/ChinaData integrations will be handled in Phase 3.
    """
    async def fetch_sector_benchmarks(self, sector: Optional[str] = None, geography: Optional[str] = None) -> dict:
        raise NotImplementedError("SectorProvider is currently a stub interface.")
