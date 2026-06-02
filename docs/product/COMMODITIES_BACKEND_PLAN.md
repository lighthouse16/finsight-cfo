# Commodities Backend Plan

## 1. Product Purpose

Commodities provides input-cost and margin-pressure context for SME cashflow and funding decisions.

It helps CFOs answer:
- Are commodity/input costs creating margin pressure on gross margins or COGS?
- Which sectors are exposed to copper, steel, cotton, energy, or freight/oil movements?
- What should CFOs monitor before funding or working-capital conversations with lenders?

## 2. Data Needed

- **Selected sector** — sector representation (e.g. Trading & Distribution, Electronics Import)
- **Commodity exposures** — price trends and exposure context for key commodities:
  - Copper (LME or equivalent)
  - Steel / Iron Ore
  - Cotton
  - Energy / Oil (Brent Crude or WTI)
  - Freight / Logistics cost context (optional, if data available)
- **Margin pressure signal** — aggregated signal indicating cost pressure on sector margins
- **Affected sectors** — list of sectors impacted by each commodity movement
- **Source/freshness metadata** — provider info, last update timestamp, cache/fixture status
- **Provider status** — connection health for commodity data sources
- **Warnings** — alerts for missing data, fixture mode, or stale cache

## 3. Freshness Language

Use:
- **delayed**
- **daily**
- **monthly**
- **workspace**
- **source-fresh** (only when provider connected)

Do not claim universal realtime. Commodity futures data from free-tier providers is typically delayed by 15-20 minutes or more. End-of-day settlement prices may be published with T+1 delay.

Fixture data must be labeled `workspace` or `seed data`.

## 4. Endpoint Contract

```
GET /api/market-watch/commodities?sector=trading-distribution&geography=HK
```

Query Parameters:
- `sector` (string, optional): Selected sector identifier (e.g. `trading-distribution`, `electronics-import`). Optional in Phase 1.
- `geography` (string, optional): Regional context code (e.g. `HK`, `CN`). Optional in Phase 1.

Rules:
- If `sector` or `geography` is omitted, the backend falls back to returning the default fixture sector.
- In future phases, the backend may infer the sector dynamically using the user's company profile or uploaded financial records (e.g., supplier invoices showing raw material purchases).

Response includes:
- `metadata` — shared response metadata, including warnings
- `selectedSector` — the sector category metadata
- `commodityExposures` — list of commodity price trends and exposure context
- `marginPressureSignal` — aggregated margin pressure indicator
- `watchSignals` — actionable signals related to commodity movements
- `sourceStatus` — per-provider connection status

Warnings live inside `metadata.warnings`.

## 5. TypeScript-Compatible Contracts

```typescript
// FreshnessStatus
export type FreshnessStatus = 'Daily' | 'Monthly' | 'Delayed' | 'Workspace';

// SourceStatus — code-based values only, no display text
export type SourceStatus =
  | 'connected'
  | 'seed_data'
  | 'requires_backend'
  | 'requires_company_data'
  | 'unavailable'
  | 'stale';

export interface SourceStatusItem {
  id: string;
  label: string;
  status: SourceStatus;
  provider?: string;
  lastUpdatedAt?: string | null;
}

export interface SourceInfo {
  provider: string;
  name: string;
  url?: string;
}

export interface ResponseMetadata {
  asOf: string | null;
  fetchedAt: string;
  freshness: FreshnessStatus;
  isStale: boolean;
  source: SourceInfo;
  warnings: string[];
}

export interface SelectedSector {
  id: string;
  name: string;
  code: string | null;
  geography: string;
  description: string;
}

export type SignalSeverity = 'Neutral' | 'Caution' | 'High' | 'Positive';
export type Trend = 'up' | 'down' | 'flat' | 'unknown';

export interface CommodityExposure {
  id: string;
  commodity: string;
  category: string;
  value: number | null;
  unit: 'percent' | 'index' | 'price' | 'text';
  displayValue: string;
  trend: Trend;
  severity: SignalSeverity;
  exposedSectors: string[];
  marginContext: string;
  sourceTimestamp: string | null;
}

export interface MarginPressureSignal {
  id: string;
  label: string;
  severity: SignalSeverity;
  description: string;
  affectedArea: string;
  requiresCompanyData: boolean;
}

export interface CommodityWatchSignal {
  id: string;
  title: string;
  description: string;
  affectedArea: string;
  severity: SignalSeverity;
}

// CommoditiesResponse
export interface CommoditiesResponse {
  metadata: ResponseMetadata;
  selectedSector: SelectedSector;
  commodityExposures: CommodityExposure[];
  marginPressureSignal: MarginPressureSignal[];
  watchSignals: CommodityWatchSignal[];
  sourceStatus: SourceStatusItem[];
}

// MarketWatchError
export interface MarketWatchError {
  code: string;
  message: string;
  statusCode: number;
  source?: string;
  retryable: boolean;
  fallbackUsed: boolean;
  details?: Record<string, unknown>;
}
```

## 6. Provider Strategy

Do not choose a production provider yet. The architecture will abstract the data acquisition layer so different sources can be integrated later without affecting downstream services.

The service directory structure will be expanded as follows:
```
backend/app/services/market_watch/
  commodity_provider.py          ← future provider abstraction / interface
  commodities_service.py         ← orchestration, mapping, cache/fallback
  fixtures.py                    ← (extend existing) fixture data generator
```

Clarifications:
- Phase 1 must not make calls to external providers.
- `commodity_provider.py` will serve as a placeholder/stub only if useful to outline future signatures.
- Production provider selection will occur in a later phase.

Future providers to evaluate:
- **Yahoo Finance / Stooq** — for commodity futures data (copper, oil, steel). Free tier typically has 15-20 minute delay.
- **Alpha Vantage** — commodities endpoint if API key setup is acceptable for dev/demo.
- **Nasdaq Data Link (formerly Quandl)** — if licensing terms allow for MVP/demo usage.
- **Public energy/oil references** — if suitable and stable.
- **Internal sector-to-commodity exposure mapping** — structured configuration mapping SME sector profiles to input cost sensitivities.

## 7. Fixture Strategy

First implementation will expose a fixture-backed endpoint matching the defined response contract.

Fixture responses must be labeled:
- `sourceStatus = "seed_data"`
- `metadata.source.provider = "Fixture"`
- `freshness = "Workspace"` or `"Delayed"`
- `metadata.warnings` must include a notice stating: *"Commodities endpoint is currently fixture-backed. Production commodity provider is not connected yet."*

Default Fixture Behavior:
- The default fixture sector should be `Trading & Distribution` or `Electronics Import` (e.g., ID: `trading-distribution` or `electronics-import`).
- Fixture exposures should include:
  - Copper (LME)
  - Steel / Iron Ore
  - Cotton
  - Energy / Oil (Brent Crude or equivalent)
  - Freight / Logistics cost context (if useful)
- Fixture values must be labeled `seed_data` and must not imply live prices, official certification, or verified benchmark data.
- Use safe contextual language like:
  - "YoY change: +14%" (historical reference)
  - "Trend: up" (directional indicator)
  - "Affects: Electronics, Construction" (sector exposure context)
- Do not use:
  - "Live price"
  - "Realtime quote"
  - "Trading recommendation"
  - "Verified margin impact"

## 8. UI Integration Strategy

- **API Swap Point**: Update `marketWatchApi.ts` on the frontend to fetch commodities data from the backend when active, falling back to local client seed data if the backend is down.
- **Isolation**: Only the Commodities tab will integrate with this endpoint. All other tabs (Rates & Liquidity, FX & GBA, Sector Benchmarks, Stress Testing) will remain unaffected.
- **No Direct Calls**: All visual components must fetch data through the API service layer rather than making raw HTTP requests.
- **Fallback Behavior**: If backend fetch fails, display soft warning: *"Backend unavailable. Showing workspace seed data."*

## 9. Safety Rules

- **No fake realtime**: Never imply that commodity prices are live or realtime feeds unless a verified provider is successfully connected and documented.
- **No trading advice**: Commodity trends are context indicators. They do not constitute trading advice, investment recommendations, or guaranteed margin impact.
- **No lender approval implication**: Margin pressure signals do not constitute a credit decision, lender pre-approval, or guarantee of financing.
- **No guaranteed margin impact**: Commodity exposures represent sector-level context. Actual margin impact depends on company-specific input costs, supplier contracts, and hedging strategies.
- **Always show source/freshness**: Always display the source provider and freshness tag in the UI to ensure compliance and avoid data misinterpretation.
- **Commodity exposure is context only**: Until company financials are connected, exposure signals are sector-level benchmarks, not company-specific margin calculations.

## 10. Implementation Phases

### Phase 1: Planning & Contracts (Current)
- [x] Create this plan document (`docs/product/COMMODITIES_BACKEND_PLAN.md`)
- [ ] Define backend models (`backend/app/models/market_watch.py`)
- [ ] Add fixture-backed endpoint response logic (`backend/app/services/market_watch/fixtures.py`)
- [ ] Add basic smoke tests for validation

### Phase 2: Frontend Integration with Fallback
- [ ] Connect the frontend Commodities tab to the local `/api/market-watch/commodities` endpoint
- [ ] Ensure seamless fallback to client-side seed data if backend is unreachable
- [ ] Align UI display text with metadata warnings and source status tags

### Phase 3: Provider Connection & Research
- [ ] Evaluate potential commodity providers (Yahoo Finance, Alpha Vantage, Nasdaq Data Link, or localized sector exposure mappings)
- [ ] Integrate external client/API call logic and establish backend caching
- [ ] Connect company financial data for actual margin sensitivity calculations
