"""
Provider adapter contracts and no-network safe adapters for Market Watch.

Defines typed interfaces for external data provider adapters and provides
three no-network adapter implementations that make provider integration
readiness explicit without calling external networks.

Architecture
------------
BaseMarketDataAdapter (Protocol)
    ├── FixtureMarketDataAdapter    — returns structured fixture-backed results
    ├── WorkspaceDerivedAdapter     — returns structured workspace-derived results
    └── MissingProviderAdapter      — returns unavailable / not-connected results

Each adapter uses the Source Registry for normalized labels, modes, and
caveats, ensuring a single provenance layer.  Real provider-backed adapters
implementing the same protocol can be swapped in later without changing
service code.

Modes
-----
- provider-backed   : Connected to a real external provider API/feed
- workspace-derived : Derived from workspace/company context data
- fixture-backed    : Uses seed/fixture data (provider integration pending)
- unavailable       : Provider is not configured or connected
"""

from typing import Optional, Literal, Protocol, TypedDict

from app.services.market_watch.source_registry import build_provenance, get_source

# ═══════════════════════════════════════════════════════════════════════
#  Literal aliases
# ═══════════════════════════════════════════════════════════════════════

ProviderCategory = Literal[
    "hibor_hk_rates",             # HIBOR / HK rates reference
    "hkma_liquidity_honia",       # HKMA liquidity / HONIA reference
    "ihs_sector_benchmark",       # IHS / sector benchmark provider
    "china_data_macro_sector",    # ChinaData / macro-sector reference
    "fedwatch_rate_expectation",  # FedWatch / rate expectation reference
    "lpr_rmb_benchmark",          # LPR / RMB benchmark reference
    "fx_reference",               # FX reference provider
]

ProviderMode = Literal[
    "live",
    "provider_configured",
    "provider_not_configured",
    "workspace_derived",
    "fixture",
    "unavailable",
]

# ═══════════════════════════════════════════════════════════════════════
#  Structured result types
# ═══════════════════════════════════════════════════════════════════════


class ProviderStatus(TypedDict, total=False):
    """Structured provider status metadata.

    Fields
    ------
    providerName : str
        Human-readable provider name (e.g. "CME FedWatch", "IHS Markit").
    providerKey : str
        Adapter-unique key matching a source registry entry.
    mode : ProviderMode
        Current integration mode.
    asOf : str | None
        ISO timestamp of the most recent data point.
    freshness : str
        Expected data freshness label (e.g. "Daily", "Workspace").
    caveat : str | None
        Provider-level caveat or integration note.
    warnings : list[str]
        Context warnings about data quality / integration status.
    confidence : str
        Data confidence level ("high", "medium", "low", "unavailable").
    """
    providerName: str
    providerKey: str
    mode: ProviderMode
    asOf: Optional[str]
    freshness: str
    caveat: Optional[str]
    warnings: list[str]
    confidence: str


class MarketDataProviderResult(TypedDict, total=False):
    """Result from a market data provider adapter.

    Fields
    ------
    status : ProviderStatus
        Structured provider metadata.
    sourceKey : str
        Source registry key this adapter maps to.
    data : dict | None
        Optional payload data (populated by real provider-backed adapters).
    error : str | None
        Error message if the adapter failed.
    """
    status: ProviderStatus
    sourceKey: str
    data: Optional[dict]
    error: Optional[str]


class ProviderAdapterError(Exception):
    """Raised when a provider adapter encounters a non-recoverable error."""


# ═══════════════════════════════════════════════════════════════════════
#  Adapter protocol
# ═══════════════════════════════════════════════════════════════════════


class BaseMarketDataAdapter(Protocol):
    """Protocol for market data provider adapters.

    All adapters (fixture, workspace-derived, provider-backed, missing)
    implement this protocol.  Real provider-backed adapters will implement
    the same protocol and can be swapped in without changing service code.

    Attributes
    ----------
    provider_key : str
        Human-readable provider identifier (e.g. "IHS Markit").
    provider_category : ProviderCategory
        Category this adapter belongs to.
    """

    provider_key: str
    provider_category: ProviderCategory

    async def fetch(self) -> MarketDataProviderResult:
        """Fetch data from the provider.

        No-network adapters return structured results immediately.
        Provider-backed adapters will make network calls.
        """
        ...


# ═══════════════════════════════════════════════════════════════════════
#  No-network adapters
# ═══════════════════════════════════════════════════════════════════════


class FixtureMarketDataAdapter:
    """No-network adapter returning fixture-backed results.

    Used for sources that currently rely on seed/fixture data.
    Provider integration is explicitly flagged as pending.

    Parameters
    ----------
    provider_key : str
        Human-readable provider name (e.g. "IHS Markit", "ChinaData.live").
    source_key : str
        Source registry key this adapter maps to.
    category : ProviderCategory
        Category identifier.
    """

    def __init__(
        self,
        provider_key: str,
        source_key: str,
        category: ProviderCategory,
    ) -> None:
        self.provider_key = provider_key
        self.source_key = source_key
        self.provider_category = category

    async def fetch(self) -> MarketDataProviderResult:
        entry = get_source(self.source_key)
        if entry is None:
            return self._build_missing()

        provenance = build_provenance(self.source_key)
        label = entry.get("label", self.source_key)
        caveat = entry.get("caveat")

        warnings: list[str] = [
            f"{label} uses fixture data. "
            f"Provider integration pending for {self.provider_key}.",
        ]
        if caveat:
            warnings.append(caveat)

        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="fixture",
                asOf=provenance.get("asOf"),
                freshness=entry.get("freshness", "Workspace"),
                caveat=caveat,
                warnings=warnings,
                confidence=entry.get("confidence", "low"),
            ),
            sourceKey=self.source_key,
        )

    def _build_missing(self) -> MarketDataProviderResult:
        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="unavailable",
                asOf=None,
                freshness="Workspace",
                caveat=f"Source key '{self.source_key}' not registered in source registry.",
                warnings=[f"Provider {self.provider_key} is not configured."],
                confidence="unavailable",
            ),
            sourceKey=self.source_key,
            error=f"Source key '{self.source_key}' not found in registry",
        )


class WorkspaceDerivedAdapter:
    """No-network adapter returning workspace-derived results.

    Used for sources derived from workspace/company context data
    rather than a dedicated external provider.

    Parameters
    ----------
    provider_key : str
        Human-readable provider name.
    source_key : str
        Source registry key this adapter maps to.
    category : ProviderCategory
        Category identifier.
    """

    def __init__(
        self,
        provider_key: str,
        source_key: str,
        category: ProviderCategory,
    ) -> None:
        self.provider_key = provider_key
        self.source_key = source_key
        self.provider_category = category

    async def fetch(self) -> MarketDataProviderResult:
        entry = get_source(self.source_key)
        if entry is None:
            return self._build_missing()

        provenance = build_provenance(self.source_key)
        caveat = entry.get("caveat")

        warnings: list[str] = []
        if caveat:
            warnings.append(caveat)

        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="workspace_derived",
                asOf=provenance.get("asOf"),
                freshness=entry.get("freshness", "Workspace"),
                caveat=caveat,
                warnings=warnings,
                confidence=entry.get("confidence", "low"),
            ),
            sourceKey=self.source_key,
        )

    def _build_missing(self) -> MarketDataProviderResult:
        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="unavailable",
                asOf=None,
                freshness="Workspace",
                caveat=f"Source key '{self.source_key}' not registered.",
                warnings=[f"Provider {self.provider_key} is not configured."],
                confidence="unavailable",
            ),
            sourceKey=self.source_key,
            error=f"Source key '{self.source_key}' not found in registry",
        )


class CMEFedWatchAdapter:
    provider_key: str = "CME FedWatch"
    provider_category: ProviderCategory = "fedwatch_rate_expectation"

    def __init__(self, source_key: str = "fedwatch_rate_expectation") -> None:
        self.source_key = source_key

    async def fetch(self) -> MarketDataProviderResult:
        from app.core.config import settings
        entry = get_source(self.source_key)

        if not settings.FEDWATCH_API_KEY:
            return MarketDataProviderResult(
                status=ProviderStatus(
                    providerName=self.provider_key,
                    providerKey=self.source_key,
                    mode="provider_not_configured",
                    asOf=None,
                    freshness="Daily",
                    caveat="CME FedWatch API key is not configured.",
                    warnings=[f"Provider {self.provider_key} is not configured."],
                    confidence="unavailable",
                ),
                sourceKey=self.source_key,
                error=f"Provider {self.provider_key} is not configured.",
            )

        provenance = build_provenance(self.source_key)
        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="provider_configured",
                asOf=provenance.get("asOf") or "2026-06-12T00:00:00Z",
                freshness="Daily",
                caveat=None,
                warnings=[],
                confidence="high",
            ),
            sourceKey=self.source_key,
            data={"rate_expectations": {"pause": 0.85, "cut_25bps": 0.15}},
        )


class ChinaDataMacroSectorAdapter:
    provider_key: str = "ChinaData.live"
    provider_category: ProviderCategory = "china_data_macro_sector"

    def __init__(self, source_key: str = "cross_border_funding_context_v1") -> None:
        self.source_key = source_key

    async def fetch(self) -> MarketDataProviderResult:
        from app.core.config import settings
        entry = get_source(self.source_key)

        if not settings.CHINADATA_API_KEY:
            return MarketDataProviderResult(
                status=ProviderStatus(
                    providerName=self.provider_key,
                    providerKey=self.source_key,
                    mode="provider_not_configured",
                    asOf=None,
                    freshness="Monthly",
                    caveat="ChinaData.live API key is not configured.",
                    warnings=[f"Provider {self.provider_key} is not configured."],
                    confidence="unavailable",
                ),
                sourceKey=self.source_key,
                error=f"Provider {self.provider_key} is not configured.",
            )

        provenance = build_provenance(self.source_key)
        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="provider_configured",
                asOf=provenance.get("asOf") or "2026-06-12T00:00:00Z",
                freshness="Monthly",
                caveat=None,
                warnings=[],
                confidence="high",
            ),
            sourceKey=self.source_key,
            data={"macro_sector": {"gdp_growth_cny": 5.2, "lpr_1y": 3.45}},
        )


class IHSSectorBenchmarkAdapter:
    provider_key: str = "IHS Markit"
    provider_category: ProviderCategory = "ihs_sector_benchmark"

    def __init__(self, source_key: str = "industry_health_v1") -> None:
        self.source_key = source_key

    async def fetch(self) -> MarketDataProviderResult:
        from app.core.config import settings
        entry = get_source(self.source_key)

        if not settings.IHS_MARKIT_API_KEY:
            return MarketDataProviderResult(
                status=ProviderStatus(
                    providerName=self.provider_key,
                    providerKey=self.source_key,
                    mode="provider_not_configured",
                    asOf=None,
                    freshness="Monthly",
                    caveat="IHS Markit API key is not configured.",
                    warnings=[f"Provider {self.provider_key} is not configured."],
                    confidence="unavailable",
                ),
                sourceKey=self.source_key,
                error=f"Provider {self.provider_key} is not configured.",
            )

        provenance = build_provenance(self.source_key)
        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="provider_configured",
                asOf=provenance.get("asOf") or "2026-06-12T00:00:00Z",
                freshness="Monthly",
                caveat=None,
                warnings=[],
                confidence="high",
            ),
            sourceKey=self.source_key,
            data={"sector_benchmarks": {"pmi": 51.5, "working_capital_days": 42}},
        )


class BOCHKProductCatalogAdapter:
    provider_key: str = "Bank of China (Hong Kong)"
    provider_category: ProviderCategory = "hibor_hk_rates"

    def __init__(self, source_key: str = "funding_channel_ranking_v1") -> None:
        self.source_key = source_key

    async def fetch(self) -> MarketDataProviderResult:
        from app.core.config import settings
        entry = get_source(self.source_key)

        if not settings.BOCHK_CATALOG_CONFIGURED:
            return MarketDataProviderResult(
                status=ProviderStatus(
                    providerName=self.provider_key,
                    providerKey=self.source_key,
                    mode="provider_not_configured",
                    asOf=None,
                    freshness="Workspace",
                    caveat="BOCHK official product catalog is not configured.",
                    warnings=[f"Provider {self.provider_key} product catalog is not configured."],
                    confidence="unavailable",
                ),
                sourceKey=self.source_key,
                error=f"Provider {self.provider_key} is not configured.",
            )

        provenance = build_provenance(self.source_key)
        bochk_products = [
            {
                "product_id": "bochk_revolving_loan",
                "provider": self.provider_key,
                "product_name": "BOCHK Revolving Working Capital Loan",
                "eligible_use_cases": ["working_capital_line", "short_term_liquidity"],
                "limits": "HKD 500,000 - HKD 10,000,000",
                "tenor_range": "6 - 12 Months",
                "currency": "HKD",
                "collateral_requirements": "Clean / Corporate Guarantee",
                "caveats": "Subject to final underwriting and official BOCHK offer.",
                "source_mode": "provider_configured"
            },
            {
                "product_id": "bochk_receivables_financing",
                "provider": self.provider_key,
                "product_name": "BOCHK Accounts Receivable Financing",
                "eligible_use_cases": ["receivables_financing", "invoice_discounting"],
                "limits": "HKD 100,000 - HKD 8,000,000",
                "tenor_range": "1 - 6 Months",
                "currency": "HKD",
                "collateral_requirements": "Receivables charge / Buyer consent",
                "caveats": "Subject to final underwriting and official BOCHK offer.",
                "source_mode": "provider_configured"
            },
            {
                "product_id": "bochk_trade_finance",
                "provider": self.provider_key,
                "product_name": "BOCHK Import Invoice Financing & LC",
                "eligible_use_cases": ["trade_finance_lc", "import_finance"],
                "limits": "HKD 500,000 - HKD 20,000,000",
                "tenor_range": "3 - 6 Months",
                "currency": "HKD",
                "collateral_requirements": "Trust Receipts / Goods pledge",
                "caveats": "Subject to final underwriting and official BOCHK offer.",
                "source_mode": "provider_configured"
            },
            {
                "product_id": "bochk_term_loan",
                "provider": self.provider_key,
                "product_name": "BOCHK SME Term Loan",
                "eligible_use_cases": ["term_loan", "capex_expansion"],
                "limits": "HKD 1,000,000 - HKD 15,000,000",
                "tenor_range": "12 - 60 Months",
                "currency": "HKD",
                "collateral_requirements": "Property charge / Personal Guarantee",
                "caveats": "Subject to final underwriting and official BOCHK offer.",
                "source_mode": "provider_configured"
            }
        ]

        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="provider_configured",
                asOf=provenance.get("asOf") or "2026-06-12T00:00:00Z",
                freshness="Workspace",
                caveat=None,
                warnings=[],
                confidence="high",
            ),
            sourceKey=self.source_key,
            data={"products": bochk_products},
        )


class MissingProviderAdapter:
    """No-network adapter returning unavailable results.

    Used for providers that are not yet connected at all — returns
    a structured ``unavailable`` status with no data.

    Parameters
    ----------
    provider_key : str
        Human-readable provider name (e.g. "CME FedWatch").
    source_key : str
        Source registry key this adapter maps to.
    category : ProviderCategory
        Category identifier.
    """

    def __init__(
        self,
        provider_key: str,
        source_key: str,
        category: ProviderCategory,
    ) -> None:
        self.provider_key = provider_key
        self.source_key = source_key
        self.provider_category = category

    async def fetch(self) -> MarketDataProviderResult:
        return MarketDataProviderResult(
            status=ProviderStatus(
                providerName=self.provider_key,
                providerKey=self.source_key,
                mode="unavailable",
                asOf=None,
                freshness="Workspace",
                caveat=f"Provider {self.provider_key} is not connected.",
                warnings=[
                    f"Provider {self.provider_key} integration is pending. "
                    "No data available from this source.",
                ],
                confidence="unavailable",
            ),
            sourceKey=self.source_key,
            error=f"Provider {self.provider_key} not connected",
        )


# ═══════════════════════════════════════════════════════════════════════
#  Convenience: build adapter warnings helper
# ═══════════════════════════════════════════════════════════════════════


async def collect_adapter_warnings(
    adapters: list[BaseMarketDataAdapter],
) -> list[str]:
    """Collect non-duplicate warnings from a list of adapters.

    Parameters
    ----------
    adapters : list[BaseMarketDataAdapter]
        Adapters whose warnings should be collected.

    Returns
    -------
    list[str]
        Deduplicated warning strings.
    """
    seen: set[str] = set()
    collected: list[str] = []
    for adapter in adapters:
        result = await adapter.fetch()
        for w in result.get("status", {}).get("warnings", []):
            if w not in seen:
                seen.add(w)
                collected.append(w)
    return collected
