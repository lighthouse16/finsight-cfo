from typing import Optional

class StressEngine:
    """
    Abstract interface/stub for future Stress Engine calculations.
    Actual mathematical modeling (DSCR, PD, credit score, runway shifts) will be handled in Phase 3.
    """
    async def simulate_stress(self, company_id: str, scenario_id: str) -> dict:
        raise NotImplementedError("StressEngine is currently a stub interface.")
