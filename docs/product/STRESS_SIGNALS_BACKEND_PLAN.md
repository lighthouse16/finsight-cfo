# Stress Signals Backend Plan

## 1. Product Purpose

Stress Signals provides scenario-based market pressure context for SME cashflow and funding decisions.

It helps CFOs answer:
- Which external shocks (rates, FX, raw materials, receivables, or liquidity) may pressure cashflow?
- Which stress scenarios need the company's financial records before sensitivity can be quantified?
- Which scenarios should CFOs review before lender conversations?
- What specific company records are missing before calculating actual impact?

> [!WARNING]
> **Safety Guardrails / Limits of Scope**:
> - This is **not** a credit scoring or credit rating model.
> - This is **not** a Probability of Default (PD) model.
> - This is **not** an automated debt service coverage ratio (DSCR) calculator (until company records are securely connected).
> - This is **not** a lender pre-approval engine or credit underwriting system.
> - Scenarios represent generalized sensitivity indicators, not verified bank analysis.

---

## 2. Data Needed

- **Selected workspace context** — sector and regional reference context (e.g., Trading & Distribution, geography: HK).
- **Stress scenarios** — defined scenario shocks across key areas:
  - Rate shock scenario (+150 bps HIBOR/Prime)
  - FX volatility scenario (RMB depreciation)
  - Commodity/input-cost shock scenario (+10% raw materials)
  - Receivables delay scenario (+15 days DSO stretch)
  - Liquidity squeeze scenario (interbank balance drops)
- **Required company data status** — configuration of records required to run the scenario calculations (e.g. Accounts Receivables, debt schedules, profit & loss, cash balances).
- **Metadata** — freshness status, as-of timestamps, source provider, and warning notices.
- **Provider status** — connection health for reference rates and corporate file storage integration.

---

## 3. Freshness Language

Use:
- **workspace**
- **derived context**
- **requires company data**
- **source-fresh** (only for connected HKMA/FX live reference inputs)

Do not claim realtime data or live bank verification for stress results. Scenarios are evaluated on workspace defaults or historical averages.

---

## 4. Endpoint Contract

```
GET /api/market-watch/stress-signals?companyId=demo&sector=trading-distribution
```

Query Parameters:
- `companyId` (string, optional): Company identifier for loading profile context. Optional in Phase 1.
- `sector` (string, optional): Target industry sector for context-only defaults. Optional in Phase 1.

Rules:
- If `companyId` or `sector` is omitted, the backend falls back to returning the default fixture workspace context.
- Phase 1 must not compute real DSCR, PD, credit score, or approval probability. All math is context-only until company data is linked.
- Future phases may ingest uploaded accounts receivables aging files, debt schedules, bank balances, and supplier invoices to run sensitivity simulations.

Response includes:
- `metadata` — shared response metadata, including warnings
- `workspaceContext` — details of the evaluated company sector and default assumptions
- `scenarios` — list of scenario shocks with requirements and readiness status
- `requiredData` — list of company data items needed for full calculations
- `watchSignals` — actionable items and warning checklists
- `sourceStatus` — integration status per component

---

## 5. TypeScript-Compatible Contracts

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

export interface WorkspaceContext {
  id: string;
  companyLabel: string;
  sector: string;
  geography: string;
  description: string;
}

export type ShockType = 'rate' | 'fx' | 'commodity' | 'receivables' | 'liquidity';
export type SignalSeverity = 'Neutral' | 'Caution' | 'High' | 'Positive';
export type ScenarioStatus = 'context_only' | 'requires_company_data' | 'ready_for_model';

export interface StressScenario {
  id: string;
  title: string;
  shockType: ShockType;
  severity: SignalSeverity;
  affectedArea: string;
  description: string;
  cfoQuestion: string;
  requiresCompanyData: boolean;
  requiredDataIds: string[];
  status: ScenarioStatus;
  sourceTimestamp: string | null;
}

export interface RequiredDataItem {
  id: string;
  label: string;
  status: SourceStatus;
  description: string;
}

export interface StressWatchSignal {
  id: string;
  title: string;
  description: string;
  affectedArea: string;
  severity: SignalSeverity;
}

// StressSignalsResponse
export interface StressSignalsResponse {
  metadata: ResponseMetadata;
  workspaceContext: WorkspaceContext;
  scenarios: StressScenario[];
  requiredData: RequiredDataItem[];
  watchSignals: StressWatchSignal[];
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

---

## 6. Provider / Engine Strategy

Do not build a real stress engine yet. The endpoint orchestrates input mapping from references and stub components.

The directory structure in Phase 2 will align with:
```
backend/app/services/market_watch/
  stress_engine.py               ← future stress engine simulation algorithms (stub in Phase 1)
  stress_signals_service.py      ← orchestration, mapping, metadata assembly
  fixtures.py                    ← (extend existing) fixture data generator
```

Future inputs to evaluate:
- **Reference Rates** — floating HIBOR / Prime shifts (derived from rates & liquidity client).
- **FX Volatility** — RMB depreciation offsets (derived from FX & GBA client).
- **Raw Materials** — metals / energy input cost movements (derived from Commodities service).
- **Corporate Profile** — sector exposure maps and debt schedules.
- **Company Files** — Accounts Receivables (AR) aging, Accounts Payables (AP), P&L, bank balances.

Phase 1 must not compute real credit health scores or underwriting results.

---

## 7. Fixture Strategy

First implementation will expose a fixture-backed endpoint matching the defined response contract.

Fixture responses must be labeled:
- `sourceStatus = "seed_data"` or `"requires_company_data"`
- `metadata.source.provider = "Fixture"`
- `freshness = "Workspace"`
- `metadata.warnings` must include a notice stating: *"Stress Signals endpoint is currently fixture-backed. Company financial data is required before impact can be quantified."*

Fixture scenarios should be displayed as context cards, not as quantified outputs.

Default Fixture Behavior:
- **Workspace Context**: Default geography: `HK`, Company label: `Workspace Demo Context (Trading & Distribution)`.
- **Fixture Scenarios**:
  - **Rate Shock (+150 bps)**:
    - title: "Rate Shock (+150 bps)"
    - shockType: "rate"
    - severity: "High"
    - affectedArea: "Debt Service Coverage Ratio (DSCR)"
    - description: "Frames a placeholder rate-shock scenario for floating HIBOR/Prime-linked credit facilities. Debt schedules and revolving limit records are required before debt-service sensitivity can be quantified."
    - cfoQuestion: "Would current operational cashflow cover interest payments under a 150 bps facility rate increase?"
    - requiresCompanyData: true
    - requiredDataIds: ["debt-schedule", "revolving-facility-limits"]
    - status: "requires_company_data"
  - **FX Volatility Scenario**:
    - title: "CNY Depreciation (-5%)"
    - shockType: "fx"
    - severity: "Caution"
    - affectedArea: "Repatriated Onshore Earnings"
    - description: "Models a placeholder shock scenario of the RMB against HKD/USD. Frames margin sensitivity on cross-border earnings and raises importing payables."
    - cfoQuestion: "Are our CNY revenues hedged, and how will USD importing costs be affected by a 5% CNY drop?"
    - requiresCompanyData: true
    - requiredDataIds: ["cross-border-payables", "hedging-contracts"]
    - status: "requires_company_data"
  - **Commodity Shock (+10%)**:
    - title: "Raw Material Input Squeeze (+10%)"
    - shockType: "commodity"
    - severity: "Caution"
    - affectedArea: "Gross Operating Margin"
    - description: "Models a placeholder shock scenario for raw material increases in copper, energy, and freight indexes. Illustrates where company data would be needed to map operating margin pressure."
    - cfoQuestion: "Can we pass a 10% raw material cost spike to buyers, or do supplier agreements have price-protection clauses?"
    - requiresCompanyData: true
    - requiredDataIds: ["supplier-contracts", "cost-of-goods-sold"]
    - status: "requires_company_data"
  - **Receivables Delay Scenario (+15 Days)**:
    - title: "Receivables Delay (+15 Days)"
    - shockType: "receivables"
    - severity: "Caution"
    - affectedArea: "Working Capital Runway"
    - description: "Models a placeholder shock scenario of payments stretching by two weeks. Illustrates where company data would be needed to map working-capital gap and revolving utilization."
    - cfoQuestion: "Do we have sufficient revolving credit to bridge a 15-day gap in collection cycles?"
    - requiresCompanyData: true
    - requiredDataIds: ["receivables-aging", "operating-cash-runway"]
    - status: "requires_company_data"
  - **Liquidity Squeeze Scenario**:
    - title: "Liquidity Squeeze"
    - shockType: "liquidity"
    - severity: "Neutral"
    - affectedArea: "Short-Term Revolving Access"
    - description: "Models a placeholder shock scenario of interbank liquidity contraction. Rates spike briefly, narrowing secondary funding windows."
    - cfoQuestion: "Are credit lines committed or subject to immediate recall during regional liquidity dips?"
    - requiresCompanyData: false
    - requiredDataIds: []
    - status: "context_only"

Use careful contextual wording. Do not use words like:
- "Predicted default"
- "Approval probability"
- "Lender approved"
- "Guaranteed failure"
- "Credit score impact"
- "Bank verified"

Safe alternatives include: requires company data, context only, pending financial records, and before impact can be quantified.

---

## 8. UI Integration Strategy

- **API Swap Point**: Update `marketWatchApi.ts` on the frontend to fetch stress signals from `/api/market-watch/stress-signals`, falling back to local client seed data if the backend is down.
- **Isolation**: Only the Stress Signals tab will connect to the new endpoint.
- **Fallback Behavior**: Display warning banner: *"Backend unavailable. Showing workspace seed data."*

---

## 9. Safety Rules

- **No credit scoring**: Never imply the tool generates a bank credit score, credit rating, or formal creditworthiness metric.
- **No underwriting simulation**: Stress signals are illustrative simulations. They do not constitute lender underwriting, loan approvals, or financial guarantees.
- **No default predictions**: Do not project default probabilities or insolvencies. Scenarios map sensitivity indicators.
- **Show metadata clear status**: Always print the `sourceStatus` and warnings to prevent data misinterpretation.

---

## 10. Implementation Phases

### Phase 1: Planning & Contracts (Current)
- [x] Create this plan document (`docs/product/STRESS_SIGNALS_BACKEND_PLAN.md`)
- [ ] Define backend models (`backend/app/models/market_watch.py`)
- [ ] Add fixture data generator (`backend/app/services/market_watch/fixtures.py`)
- [ ] Create stub service and endpoint route (`backend/app/routes/market_watch.py`)
- [ ] Implement backend smoke test verification

### Phase 2: Frontend Integration with Fallback
- [ ] Connect the frontend Stress Signals tab to `/api/market-watch/stress-signals`
- [ ] Adapt response mapping and handle backend failure fallbacks
- [ ] Align UI display text to match required data statuses and warning banners

### Phase 3: Connect Company Financial Data
- [ ] Implement secure file parsing hooks (receivables aging sheets, P&L statements, debt registers)
- [ ] Execute sensitivity calculations only after company records are connected, such as debt-service sensitivity, cash runway shifts, and working-capital gap analysis.
- [ ] Implement Stress Engine calculations
