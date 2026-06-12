# Market Provider Integrations

This document details exactly how the Market Funding Intelligence layer fetches and processes data from external providers, standardizes source metadata (provenance), handles missing paid credentials, and degrades gracefully to fallback fixture data.

## 1. Core Source Metadata Principle

Every market value in the system must carry explicit provenance. No market data is rendered without the following fields:

* **source_name**: The name of the organization or provider fixing the rate (e.g., `HKAB / HKMA`, `Frankfurter`, `CME FedWatch`, `ChinaData.live`, `IHS Markit`).
* **source_mode**: Standardized integration status indicating data origin:
  * `live`: Live public API/feed.
  * `provider_configured`: Connected to a paid/proprietary API with valid credentials.
  * `provider_not_configured`: Paid/proprietary provider is active but missing required credentials (e.g. API keys).
  * `workspace_derived`: Value derived algorithmically from company context or other rates.
  * `fixture`: Fallback/seed data for testing or demo purposes.
  * `unavailable`: Data source is completely offline or not configured.
* **as_of**: ISO 8601 timestamp of when the rate was fixed by the provider.
* **freshness**: The frequency of update (e.g. `Daily`, `Monthly`, `Workspace`).
* **caveat**: Clear text indicating limitations (e.g. "CME FedWatch API key is not configured.").
* **confidence**: Qualitative trust level (`high`, `medium`, `low`, `unavailable`).

---

## 2. Integrated Providers & Feeds Matrix

The following table summarizes exactly which feeds are live public, paid proprietary, workspace-derived, or fixture-based:

| Source / Feed | Category | Mode (Default/Local) | Mode (Configured) | Provider Name | Confidence | Freshness |
|---|---|---|---|---|---|---|
| **HKMA Liquidity/HONIA** | Liquidity/Base Rates | `live` | `live` | HKAB / HKMA | High | Daily |
| **HKAB HIBOR** | Base Rates | `live` | `live` | HKAB / HKMA | High | Daily |
| **FX Reference** | FX Rates | `live` | `live` | Frankfurter | High | Daily |
| **LPR/RMB Benchmark** | Macro Rates | `fixture` | `provider_configured` | ChinaData.live | High (Conf.) / Low (Fixt.) | Monthly |
| **FedWatch Expectations** | Rate Expectations | `provider_not_configured` | `provider_configured` | CME FedWatch | High (Conf.) / N/A (Unconf.) | Daily |
| **Sector Benchmarks** | Industry Health | `provider_not_configured` | `provider_configured` | IHS Markit | High (Conf.) / N/A (Unconf.) | Monthly |
| **BOCHK Product Catalog** | Bank Catalog | `fixture` | `provider_configured` | Bank of China (Hong Kong) | High (Conf.) / Low (Fixt.) | Workspace |

---

## 3. Real Provider Adapters & Env Configuration

Paid or proprietary providers are driven by environment variables. They do **not** return fake data when unconfigured. Instead, they raise explicit `"provider_not_configured"` states and fall back to local JSON data or seed fixtures with clear warnings.

### Configuration Variables (`.env`)

```bash
# CME FedWatch Rate Expectations API
FEDWATCH_API_KEY=your_cme_api_key_here

# ChinaData Macro Sector & RMB LPR API
CHINADATA_API_KEY=your_chinadata_key_here

# IHS Markit Industry Sector Benchmarks API
IHS_MARKIT_API_KEY=your_ihs_key_here

# BOCHK Official Product Catalog Configuration
BOCHK_CATALOG_CONFIGURED=True
```

### Adapter Fallback & Graceful Degradation

If a provider adapter is requested but the API key is empty, the system returns a status block with `mode: "provider_not_configured"`. Downstream services consume this state to fallback safely:

* **FedWatch**: Falls back to baseline neutral expectations with warning messages.
* **ChinaData (LPR)**: Falls back to a local proxy (LPR 1Y fixed at `3.45%`) with a fixture warning.
* **IHS Markit**: Falls back to the in-memory sector benchmarks fixture.
* **BOCHK Catalog**: If `BOCHK_CATALOG_CONFIGURED` is `False`, the catalog service loads from [demo_data/funding_products.json](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/real-market-provider-integrations/backend/demo_data/funding_products.json) (generic items only, marked with `source_mode: "fixture"`).

---

## 4. Wording Safeness & Compliance

To prevent misleading recommendations or premature lending claims, the system runs a recursive sanitization scanner on final ranking responses if `BOCHK_CATALOG_CONFIGURED` is `False`. The scanner scrubs and replaces the following terms:

* `guaranteed` → `estimated`
* `approved` → `reviewed`
* `arbitrage profit` → `spread opportunity`
* `official BOCHK offer` → `indicative product reference`
