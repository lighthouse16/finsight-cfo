# Market Watch Backend Plan

## 1. Backend Goal
Market Watch backend provides source-fresh market data for rates, liquidity, FX, sector benchmarks, commodities, and stress signals.

## 2. Realtime Definition
Use "source-fresh" and "near-real-time" carefully.
Do not claim everything is real-time.
Different sources have different freshness:
- **rates**: daily/source timestamp
- **liquidity**: daily or source-timestamped
- **FX**: delayed/near-real-time depending provider
- **sector macro**: monthly
- **commodities**: delayed/daily depending provider
- **stress signals**: derived from available company data and market data

## 3. API Endpoint Plan

Define endpoints:
- `GET /api/market-watch/overview`
- `GET /api/market-watch/rates-liquidity`
- `GET /api/market-watch/fx-gba`
- `GET /api/market-watch/sector-benchmarks`
- `GET /api/market-watch/commodities`
- `GET /api/market-watch/stress-signals`
- `GET /api/market-watch/source-status`
- `POST /api/market-watch/refresh`

## 4. Phase 1 Endpoint
Prioritize:
`GET /api/market-watch/rates-liquidity`

This should eventually replace seed data in:
`src/features/market-watch/api/marketWatchApi.ts`

## 5. Response Contracts

```typescript
// FreshnessStatus
export type FreshnessStatus = 'Daily' | 'Monthly' | 'Delayed' | 'Workspace';

// SourceStatus
export type SourceStatus =
  | 'connected'
  | 'seed_data'
  | 'requires_backend'
  | 'requires_company_data'
  | 'unavailable'
  | 'stale';

export interface SourceStatusItem {
  label: string;
  status: SourceStatus;
}

// Shared Response Metadata
export interface ResponseMetadata {
  asOf: string | null;
  fetchedAt: string;
  freshness: FreshnessStatus;
  isStale: boolean;
  source: {
    provider: string;
    name: string;
    url?: string;
  };
  warnings?: string[];
}

// RateSnapshot
export interface RateSnapshot {
  id: string;
  label: string;
  tenor: string;
  value: number | null;
  unit: 'percent' | 'bps' | 'index';
  displayValue: string;
  changeBasisPoints: number | null;
  trend: 'up' | 'down' | 'flat' | 'unknown';
  context: string;
  sourceTimestamp: string | null;
}

// LiquidityEvent
export type SignalSeverity = 'Neutral' | 'Caution' | 'High' | 'Positive';

export interface LiquidityEvent {
  id: string;
  date: string;
  event: string;
  impact: string;
  severity: SignalSeverity;
}

// RatesLiquidityResponse
export interface RatesLiquidityResponse {
  metadata: ResponseMetadata;
  rates: RateSnapshot[];
  liquidityEvents: LiquidityEvent[];
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
  details?: Record<string, any>;
}
```

## 6. Backend Architecture
Propose this structure:

```text
backend/
  app/
    main.py
    core/
      config.py
    routes/
      market_watch.py
    services/
      market_watch/
        hkma_client.py
        rates_liquidity_service.py
        source_status.py
        cache.py
    models/
      market_watch.py
    tests/
```

## 7. Data Freshness and Cache Strategy
- **source timestamp**: the original time the data point was published by the source.
- **fetched_at timestamp**: the time the backend successfully retrieved the data.
- **freshness label**: a clear string (`Daily`, `Delayed`) returned to the client to describe data age.

### Cache TTL Guidance (Phase 1)
- **rates**: 6-12h
- **liquidity**: 1-6h depending on source freshness
- **source status**: 5-15m
- **stale cache fallback**: allowed

### Fallback Behavior
- **upstream success**: return normalized data
- **upstream fail + cache exists**: return stale cache with warning (set `isStale: true` in metadata and add warning message)
- **upstream fail + no cache**: return explicit error (using `MarketWatchError` structure)
- **dev fixture**: can be used only for local development and must be clearly labeled (e.g., using `seed_data` status)

## 8. UI Integration Strategy
- keep `marketWatchApi.ts` as swap point.
- add environment variable for API base URL later.
- components should not call fetch directly.
- show loading/error/stale states.
- frontend maps `SourceStatus` codes to display labels.

## 9. Safety Rules
- no fake realtime claims.
- no fake approval probability.
- no fake credit score.
- no bank-verified claims.
- all market data must show source/freshness when rendered.

## 10. Implementation Phases

**Phase 1:**
- backend skeleton
- rates-liquidity endpoint
- HKMA client abstraction
- cache/fallback
- frontend marketWatchApi swap for Rates & Liquidity only

### Phase 1 Acceptance Criteria
- backend starts locally
- `GET /api/market-watch/rates-liquidity` returns typed JSON
- response includes metadata and source status
- no fake realtime claim
- frontend can keep using seed data until integration pass
- lint/build pass for frontend

**Phase 2:**
- FX & GBA provider
- source status expansion

**Phase 3:**
- sector benchmarks
- commodities

**Phase 4:**
- stress signals connected to company financials
