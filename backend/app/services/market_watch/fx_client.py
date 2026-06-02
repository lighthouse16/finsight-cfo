from typing import Protocol, List, Dict, Any

class FxProvider(Protocol):
    """
    Abstract interface for an FX data provider.
    This will be implemented in Phase 2 when a provider is selected.
    """
    async def fetch_fx_pairs(self) -> List[Dict[str, Any]]: ...
    
    @property
    def name(self) -> str: ...
    
    @property
    def base_url(self) -> str: ...
