# Market Watch Source Registry and API Provenance Registry

This document maps the data needs, current integration statuses, target public/paid APIs, fallback behavior, freshness requirements, and UI source labels for every data group within the Market Watch CFO dashboard. It serves as a blueprint for evolving from fixture-backed indicators to a robust production data pipeline.

---

## 1. Safety, Provenance & Copy Guidelines
All data sources, status banners, and tooltips must adhere to strict compliance and messaging guidelines:
- **Forbidden Wording**: Do not use terms like *realtime*, *live*, *bank verified*, *guaranteed*, *lender approved*, or *quantified DSCR impact* for unconfigured or mock data.
- **Allowed Wording**: Use terms like *source-fresh*, *daily*, *monthly*, *delayed*, *workspace-derived*, *fixture*, or *provider-backed*.

### Standardized `SourceProvenance` Schema
All Market Watch responses include a standardized `SourceProvenance` schema:
- `source_name`: User-facing source label (e.g., `"HKAB HIBOR"`, `"Frankfurter FX"`).
- `source_mode`: The operational mode of the data provider:
  - `live`: Connected to active public feeds without credentials.
  - `provider_configured`: Connected to paid/private endpoints with active credential configuration.
  - `provider_not_configured`: Paid/private provider is unconfigured. Warnings and configuration hints are returned; sandbox seed data is returned honestly.
  - `workspace_derived`: Dynamically computed from connected company records and regional scenario rules.
  - `fixture`: Static seed placeholder data.
  - `unavailable`: Data feed is explicitly disabled or down.
- `last_updated`: Timestamp of the last successful data fetch.
- `provider_adapter`: Identifier of the integration adapter (e.g., `"frankfurter_adapter"`, `"hkma_adapter"`).
- `confidence`: Confidence band (`"high"`, `"medium"`, `"low"`, or `"unavailable"`).
- `warning`: Detailed warning string or configuration hint.
- `docs_url` / `raw_url`: Reference links (where safe).

---

## 2. Module Registry

### A. Rates / HIBOR
- **Data Need**: Base reference interest rates for HKD-denominated floating credit facilities (Overnight, 1-Month, 3-Month, 6-Month, 12-Month fixing tenors).
- **Current Source**: HKAB public HIBOR page (HTML scraping) as primary; HKMA Open API as secondary fallback.
- **Target Source**: HKAB Interest Settlement Rate public page (primary) / Thomson Reuters or Bloomberg feed (production-grade paid feed).
- **Fallback Source**: HKMA Interest Settlement Rates Open API (delayed by up to 2-3 business days) / Stale local cache.
- **Freshness Expectation**: daily (updated at 11:15 AM HKT on Hong Kong business days).
- **API Key Required**: No.
- **Source Type**: Public / Scrape-based.
- **Implementation Priority**: High (Completed primary HKAB parser & fallback).
- **UI Label**: `HKAB public HIBOR page`

### B. HONIA
- **Data Need**: Hong Kong Dollar Overnight Index Average (HONIA) rate for tracking overnight interbank funding conditions.
- **Current Source**: HKMA Open API (`ir_monia` daily fixing endpoint).
- **Target Source**: HKMA Open API daily interest rate feed.
- **Fallback Source**: Stale cache / unavailable status.
- **Freshness Expectation**: daily (published next morning).
- **API Key Required**: No.
- **Source Type**: Public API.
- **Implementation Priority**: High (Completed integration).
- **UI Label**: `HKMA public API` or `unavailable`

### C. Liquidity Events
- **Data Need**: HKMA interbank liquidity indicators (Opening Aggregate Balance, Closing Aggregate Balance, Forecast T+1/T+2 Balance, Discount Window Base Rate, Exchange Fund Bills & Notes outstanding/issuance).
- **Current Source**: HKMA Open API (`interbank_liquidity` and daily monetary statistics).
- **Target Source**: HKMA Open API public endpoint.
- **Fallback Source**: Stale cache / unavailable status.
- **Freshness Expectation**: daily (forecasts update intra-day; actual balances update after 6:00 PM HKT).
- **API Key Required**: No.
- **Source Type**: Public API.
- **Implementation Priority**: High (Completed normalization and empty-state layout handling).
- **UI Label**: `HKMA liquidity` or `unavailable`

### D. FX (GBA Trade Pairs)
- **Data Need**: Foreign exchange reference rates (USD/HKD, CNY/HKD, USD/CNY) to monitor currency fluctuations within GBA trade routes.
- **Current Source**: Frankfurter API (open source) with triangulation for missing crosses.
- **Target Source**: Frankfurter (free/public) / OANDA or Open Exchange Rates (paid subscription target).
- **Fallback Source**: Triangulation from known pairs / Stale cache.
- **Freshness Expectation**: daily or delayed.
- **API Key Required**: No (for Frankfurter), Yes (for paid targets).
- **Source Type**: Public API (Frankfurter) or Paid API.
- **Implementation Priority**: Medium (Connected to Frankfurter).
- **UI Label**: `provider-backed` or `Frankfurter API`

### E. Sector Benchmarks
- **Data Need**: Macroeconomic indexes (SME PMI, industrial production growth, export/import statistics) and financial benchmarks (DSO, DPO, gross margins) for the manufacturing and electronics export sectors.
- **Current Source**: Fixture-backed seed data.
- **Target Source**: Census and Statistics Department (C&SD) of Hong Kong / data.gov.hk APIs (for macro indexes), and Dun & Bradstreet or Bloomberg (for DSO/DPO ratio benchmarks).
- **Fallback Source**: Workspace default fixtures.
- **Freshness Expectation**: monthly / quarterly.
- **API Key Required**: No (for Gov APIs), Yes (for commercial database feeds).
- **Source Type**: Public API (Gov data) / Paid subscription (commercial benchmarks).
- **Implementation Priority**: Medium-Low.
- **UI Label**: `fixture-backed` or `C&SD / data.gov.hk`

### F. Commodities (Input Costs)
- **Data Need**: Base cost tracking for key physical inputs (LME Copper, Brent Crude, Steel, Cotton) affecting SME procurement margins.
- **Current Source**: Fixture-backed seed data.
- **Target Source**: Alpha Vantage API (Freemium) or FRED (Federal Reserve Economic Data) for energy/oil, World Bank Pink Sheets API (monthly fallback), or TradingEconomics/LME feed (paid commercial).
- **Fallback Source**: World Bank Monthly Commodity Prices (free public feed) / local fixtures.
- **Freshness Expectation**: delayed / monthly.
- **API Key Required**: Yes (for Alpha Vantage/FRED).
- **Source Type**: Public API (FRED / World Bank) / Paid feed (TradingEconomics).
- **Implementation Priority**: Medium.
- **UI Label**: `fixture-backed` or `Alpha Vantage API` / `FRED`

### G. Freight / Logistics
- **Data Need**: Global shipping spot rates (Shanghai Containerized Freight Index - SCFI, Baltic Dry Index - BDI) to monitor transportation and logistics margins.
- **Current Source**: Fixture-backed seed data.
- **Target Source**: Baltic Exchange API or Freightos Baltic Index (FBX) API.
- **Fallback Source**: Local seed fixture data.
- **Freshness Expectation**: delayed (weekly/daily).
- **API Key Required**: Yes (paid subscription required).
- **Source Type**: Paid API (with commercial licensing restrictions).
- **Implementation Priority**: Low.
- **UI Label**: `fixture-backed` or `Freightos Baltic Index`

### H. Company Financial Records
- **Data Need**: Company-specific exposure inputs (revolving limits, collections age, floating debt schedules, supplier invoice schedules).
- **Current Source**: Workspace-derived mock profile.
- **Target Source**: Customer upload engine (CSV / XLSX invoice & debt parse) as primary; future API connections to cloud accounting (Xero, QuickBooks) and Open Banking APIs.
- **Fallback Source**: Empty profile / prompt to upload.
- **Freshness Expectation**: workspace-derived (updated upon sync or file upload).
- **API Key Required**: Yes (for accounting software integration).
- **Source Type**: Internal / User-uploaded / Partner API.
- **Implementation Priority**: Medium-High.
- **UI Label**: `connected workspace context` or `demo workspace context`

### I. Stress Signals
- **Data Need**: Simulated scenario analysis (Interest Rate shock, Collections delay, CNY depreciation shock) mapping rate shifts to workspace-specific cash flows.
- **Current Source**: Seed fixture-backed scenarios.
- **Target Source**: Internal workspace engine calculating cash-burn, runway impact, and debt service coverage dynamically using connected company records + active rate inputs.
- **Fallback Source**: Static scenario templates / context-only view.
- **Freshness Expectation**: workspace-derived.
- **API Key Required**: No.
- **Source Type**: Internal workspace calculation (no external API should generate credit/underwriting claims).
- **Implementation Priority**: Medium.
- **UI Label**: `workspace-derived`

---

## 3. API Investigation & Integration Strategy

### Next Immediate Integration: Commodities (FRED & World Bank Fallback)
1. **Source Selection**: Federal Reserve Economic Data (FRED) provides a free public API containing commodity indices and energy prices (e.g., Brent Crude, Industrial Metals Index). The World Bank Commodity Price database provides free monthly Pink Sheets data.
2. **Implementation Action**: Add a commodities fetch client `fred_client.py` using a free FRED API key to pull Brent Crude and metal indices. Map these to the existing commodities response contracts.
3. **Fallback**: If FRED fails, use the World Bank Monthly Commodity Price API as a static monthly fallback before reverting to local cache.

### Commercial/Paid Provider Strategy (remain fixture-backed)
- **Sector DSO/DPO Benchmarks** and **Freight Indices (Baltic Exchange / Freightos)** require expensive commercial data contracts and redistribution licensing. 
- These indicators should **remain fixture-backed** in the platform's core code. The UI must clearly label these as `fixture-backed` or `workspace seed` until the enterprise configures a private paid provider key.

### Demotion and Visibility Rules (if unavailable)
- **Rates (HIBOR)**: Must always remain visible. If HKAB scrapers fail, fall back to HKMA Open API with a clear warnings list (`HKAB HIBOR page unavailable. Using HKMA Open API fallback.`).
- **HONIA**: If HKMA response does not contain HONIA rates, hide the HONIA rate card from the list or label the card `unavailable` (preventing any false claims).
- **Liquidity events**: If the HKMA interbank liquidity feed is unavailable or cannot be normalized, demote the prominent panels. The `Liquidity Watch` card is removed entirely, and the dashboard renders a compact inline status row: `"Liquidity events: unavailable - HKMA interbank liquidity source is not available for this view."`
- **Funding Window Context**: If liquidity events are unavailable, the derived Funding Window score card should be styled as disabled/secondary and display `"Funding window context requires liquidity history."` instead of displaying a calculated score.
