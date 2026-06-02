# FX & GBA Backend Plan

## 1. Product Purpose

FX & GBA provides source-fresh FX and cross-border funding context for SME cashflow and funding decisions.

## 2. Data Needed

- **USD/HKD** — core pegged rate, contextual for HKD-denominated cashflows
- **CNY/HKD** — cross-border repatriation reference
- **USD/CNY** or **CNH/HKD** — if the chosen provider supports onshore/offshore CNY
- **HIBOR 3M** — imported from existing HKMA rates endpoint (not a separate fetch)
- **LPR 1Y** — later phase, if a reliable source is selected
- **GBA funding context notes** — workspace-level observations derived from rate spreads (not hardcoded recommendations)

## 3. Realtime/Freshness Language

Use:
- source-fresh
- delayed
- daily
- provider timestamp

Do not claim universal realtime.
FX rates from free/dev tier providers are typically delayed by 10–15 minutes.
CNY crosses may have additional settlement-day latency.

## 4. Endpoint Contract

```
GET /api/market-watch/fx-gba
```

Response includes:
- `metadata` — shared response metadata
- `fxPairs` — list of FX rate observations
- `gbaFundingSignal` — actionable workspace-level signal (can be empty / neutral when no signal)
- `exposureNotes` — enumerated notes about cross-border exposure context
- `sourceStatus` — per-provider connection status

Warnings live inside `metadata.warnings`.

## 5. TypeScript-Compatible Contracts

```typescript
// FreshnessStatus
export type FreshnessStatus = 'Daily' | 'Monthly' | 'Delayed' | 'Workspace';

// SourceStatus — code-based values only
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

// FxPair
export interface FxPair {
  id: string;
  pair: string;
  value: number | null;
  unit: 'price' | 'percent';
  displayValue: string;
  trend: 'up' | 'down' | 'flat' | 'unknown';
  changePips: number | null;
  context: string;
  sourceTimestamp: string | null;
}

// GbaFundingSignal
export type SignalSeverity = 'Neutral' | 'Caution' | 'High' | 'Positive';

export interface GbaFundingSignal {
  id: string;
  title: string;
  description: string;
  severity: SignalSeverity;
}

// ExposureNote
export interface ExposureNote {
  id: string;
  category: string;
  note: string;
  severity: SignalSeverity;
}

// FxGbaResponse
export interface FxGbaResponse {
  metadata: ResponseMetadata;
  fxPairs: FxPair[];
  gbaFundingSignal: GbaFundingSignal[];
  exposureNotes: ExposureNote[];
  sourceStatus: SourceStatusItem[];
}

`gbaFundingSignal` remains an array so the backend can later return multiple signals, such as FX volatility, HIBOR/LPR spread context, and RMB funding context.

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

Do not hardcode one provider yet.
Define provider abstraction with:

```
backend/app/services/market_watch/
  fx_client.py          ← abstract FX provider client
  fx_gba_service.py     ← orchestration, mapping, cache/fallback
  fixtures.py           ← (extend existing) fixture fallback for FX & GBA
```

The first backend implementation may expose a fixture-backed endpoint that matches the contract before a production FX provider is selected. Fixture responses must be labeled with `sourceStatus = seed_data` and must not be described as source-fresh.

The first implementation may use fixture mode until a provider is chosen.
The `fx_client.py` should define an abstract base or duck-typed interface so different providers can be swapped without changing the service layer.

Candidate provider interface:

```python
class FxProvider:
    async def fetch_fx_pairs(self) -> list[dict]: ...
    @property
    def name(self) -> str: ...
    @property
    def base_url(self) -> str: ...
```

## 7. Source Selection Criteria

When choosing an FX provider, evaluate against:

| Criterion | Required | Notes |
|---|---:|---|
| Supports USD/HKD and CNY/HKD | Yes | Core FX pairs for HK/GBA context |
| Supports CNH/HKD or USD/CNY | Preferred | Useful for offshore/onshore RMB context |
| Clear per-rate timestamp | Yes | Needed for source freshness |
| Stable API uptime | Yes | Avoid unreliable market data UX |
| Allows local development | Yes | Must work in developer workflow |
| Free/dev tier or documented key setup | Yes | Required for MVP build |
| Acceptable terms for demo/MVP | Yes | No unclear licensing risk |
| No bank-verified claims required | Yes | Product must not imply bank verification |

Candidate providers to evaluate (not a decision):

- **ExchangeRate-API** — free tier supports USD/HKD, CNY/USD (indirect CNY/HKD via cross). Delayed, daily updated.
- **Open Exchange Rates** — free tier supports USD/HKD, limited CNY. Updated hourly on free plan.
- **Frankfurter** — EUR-based, free, no API key needed. Supports HKD and CNY via EUR cross rates.
- **HKMA** — does not publish live FX rates via the same public endpoint used for rates/liquidity.
- **CNY fixing (PBOC)** — daily central parity published openly, but requires custom parsing.

## 8. Fallback Behavior

- **provider success**: return normalized data with `isStale: false`
- **provider fails + cache exists**: return stale cache with `isStale: true`, add warning
- **provider fails + no cache + fixture mode enabled**: return fixture data with `status: "seed_data"`
- **provider fails + no cache + fixture mode disabled**: return structured `503` error via `MarketWatchError`

## 9. UI Integration Strategy

- Keep `marketWatchApi.ts` as swap point (already structured for this)
- Only the FX & GBA tab (`/platform/market-watch` → FX & GBA) will integrate
- Other tabs remain on seed data
- Frontend adapter maps backend `FxPair` (numeric `value` + `displayValue`) to existing frontend `FxPair` shape (string `rate`)
- Frontend maps `SourceStatus` codes to display labels
- Components should not call `fetch` directly

## 10. Safety Rules

- no fake realtime
- no borrowing recommendation
- no guaranteed cross-border funding advantage
- no bank-verified claim
- always show source/freshness when rendered

## 11. Implementation Phases

**Phase 1 (plan + contracts):**
- Create this plan document
- Define Pydantic models in `backend/app/models/market_watch.py`
- Add fixture endpoint for FX & GBA
- No provider selected yet

**Phase 2 (backend):**
- Provider selection and evaluation
- Implement `fx_client.py` with chosen provider
- Implement `fx_gba_service.py` with cache/fallback
- Register route `GET /api/market-watch/fx-gba`
- Extend fixtures

**Phase 3 (frontend):**
- Update `marketWatchApi.ts` to fetch FX & GBA from backend
- Update `FxGbaTab` to show source/freshness/warnings
- Add loading/fallback states
- Keep other tabs on seed data
