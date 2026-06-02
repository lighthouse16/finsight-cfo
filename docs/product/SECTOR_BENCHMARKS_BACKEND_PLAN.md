# Sector Benchmarks Backend Plan

## 1. Product Purpose

Sector Benchmarks provides sector health, working capital benchmarks, receivables, inventory cycles, and benchmark context for SME cashflow and funding decisions.

## 2. Data Needed

- **Selected sector** — sector representation (e.g. Manufacturing, Retail, Tech)
- **Sector code** — industry standard codes if available (e.g. HS, NAICS, ISIC)
- **Industry health score** — aggregated health metric (1-100 scale or normalized index)
- **PMI context** — Purchasing Managers' Index (e.g., above/below 50 expansion/contraction threshold)
- **Export growth context** — month-over-month or year-over-year trade indicators
- **Working capital benchmark** — standard cycle days (Days Sales Outstanding, Days Inventory Outstanding, Days Payable Outstanding)
- **Receivables benchmark** — industry average collection delays and collection rates
- **Inventory pressure** — inventory buildup or destocking rates
- **Documentation quality / lender readiness context** — sector-specific compliance, transaction records, and documentation guidelines for financing
- **Source/freshness metadata** — provider info, last update timestamp, and cache status

## 3. Freshness Language

Use:
- **monthly**
- **workspace**
- **source-fresh** (only when provider connected)
- **benchmark context**

Do not claim realtime. Sector economic indices, PMI values, and working capital ratios are published monthly or quarterly. Realtime claims are misleading for industry benchmarks and risk metrics.

## 4. Endpoint Contract

```
GET /api/market-watch/sector-benchmarks?sector=trading-distribution&geography=HK
```

Query Parameters:
- `sector` (string, optional): Selected sector identifier (e.g. `trading-distribution`, `electronics-import`). Optional in Phase 1.
- `geography` (string, optional): Regional context code (e.g. `HK`, `CN`). Optional in Phase 1.

Rules:
- If `sector` or `geography` is omitted, the backend falls back to returning the default fixture sector.
- In future phases, the backend may infer the sector dynamically using the user's company profile or uploaded transaction/receivables records.


Response includes:
- `metadata` — shared response metadata, including warnings
- `selectedSector` — the sector category metadata
- `sectorHealth` — index scores, PMI, and output growth metrics
- `benchmarks` — working capital ratios and collection periods
- `watchSignals` — risks, opportunities, or supply chain bottlenecks
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

export interface SectorHealthComponent {
  label: string;
  value: number | null;
  unit: 'index' | 'percent' | 'text';
  displayValue: string;
  context: string;
}

export interface SectorHealth {
  score: number | null;
  label: string;
  severity: SignalSeverity;
  components: {
    pmi: SectorHealthComponent | null;
    exportGrowth: SectorHealthComponent | null;
    industrialProduction: SectorHealthComponent | null;
    marginContext: SectorHealthComponent | null;
  };
}

export interface SectorBenchmark {
  id: string;
  label: string;
  value: number | null;
  unit: 'days' | 'percent' | 'ratio' | 'index';
  displayValue: string;
  comparison: string;
  context: string;
  severity: SignalSeverity;
  sourceTimestamp: string | null;
}

export interface SectorWatchSignal {
  id: string;
  title: string;
  description: string;
  affectedArea: string;
  severity: SignalSeverity;
}

// SectorBenchmarksResponse
export interface SectorBenchmarksResponse {
  metadata: ResponseMetadata;
  selectedSector: SelectedSector;
  sectorHealth: SectorHealth;
  benchmarks: SectorBenchmark[];
  watchSignals: SectorWatchSignal[];
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
  sector_provider.py            ← future provider abstraction / interface
  sector_benchmarks_service.py  ← orchestration, mapping, cache/fallback
  fixtures.py                  ← (extend existing) fixture data generator
```

Clarifications:
- Phase 1 must not make calls to external providers.
- `sector_provider.py` will serve as a placeholder/stub only if useful to outline future signatures.
- Production provider selection will occur in a later phase.

Future providers to evaluate:
- **ChinaData / NBS** (National Bureau of Statistics) — for Mainland trade & manufacturing indicators.
- **Internal Benchmark Config** — structured workspace configuration mapping SME profiles to credit criteria.
- **SME Benchmark Database** — industry collection cycles, average payables/receivables days.

## 7. Fixture Strategy

First implementation will expose a fixture-backed endpoint matching the defined response contract.
Fixture responses must be labeled:
- `sourceStatus = "seed_data"`
- `metadata.source.provider = "Fixture"`
- `freshness = "Workspace"` or `"Monthly"`
- `metadata.warnings` must include a notice stating that the production sector provider is not connected yet.

Default Fixture Behavior:
- The default fixture sector should be `Trading & Distribution` or `Electronics Import` (e.g., ID: `trading-distribution` or `electronics-import`).
- Fixture values must be labeled `seed_data` and must not imply or state official industry certification or lender approval.

## 8. UI Integration Strategy

- **API Swap Point**: Update `marketWatchApi.ts` on the frontend to fetch sector benchmark data from the backend when active, falling back to local client seed data if the backend is down.
- **Isolation**: Only the Sector Benchmarks tab will integrate with this endpoint. All other tabs (Rates & Liquidity, FX & GBA, Stress Testing) will remain unaffected.
- **No Direct Calls**: All visual components must fetch data through the API service layer rather than making raw HTTP requests.

## 9. Safety Rules

- **No fake realtime**: Never imply that sector indices or working capital days are real-time feeds.
- **No fake industry certification**: Do not claim industry validation, government backing, or official certification unless a verified provider is successfully connected.
- **No fake lender approval**: Ratios are context indicators. They do not constitute a credit decision, lender pre-approval, or guarantee of financing.
- **No fake benchmark certainty**: Remind users that benchmark values represent regional/sector averages, which may vary based on specific transaction structures.
- **Always show source/freshness**: Always display the source provider and freshness tag in the UI to ensure compliance and avoid data misinterpretation.

## 10. Implementation Phases

### Phase 1: Planning & Contracts (Current)
- [x] Create this plan document (`docs/product/SECTOR_BENCHMARKS_BACKEND_PLAN.md`)
- [ ] Define backend models (`backend/app/models/market_watch.py`)
- [ ] Add fixture-backed endpoint response logic (`backend/app/services/market_watch/fixtures.py`)
- [ ] Add basic smoke tests for validation

### Phase 2: Frontend Integration with Fallback
- [ ] Connect the frontend Sector Benchmarks tab to the local `/api/market-watch/sector-benchmarks` endpoint
- [ ] Ensure seamless fallback to client-side seed data if backend is unreachable
- [ ] Align UI display text with metadata warnings and source status tags

### Phase 3: Provider Connection & Research
- [ ] Evaluate potential benchmark providers (NBS, trade databases, or localized survey data)
- [ ] Integrate external client/API call logic and establish backend caching
