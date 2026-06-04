# BOCHK Challenge 2026 — Project Tracker

> **Source of truth**: `BOCHK Challenge 2026.docx` (team document)
> **Repo**: `D:\projects\finsight-cfo`
> **Last updated**: 2026-06-04

---

## Architecture Principle

The team document defines the following core architecture:

| Principle | Definition | Repo status |
|---|---|---|
| **Unidirectional Data Pipeline** | All data flows in one direction: ingestion → standardization → metrics → prediction → advisory → output. No circular dependencies. | **Partial** — Market Watch frontend implements a unidirectional data pattern: `API → adapters → state → insights (rules) → UI`. However, no backend pipeline connecting Phase 1→2→3 exists yet. |
| **JSON Contracts Between Phases** | Each phase communicates via well-defined JSON schemas. | **Partial** — Market Watch backend has typed JSON response contracts (e.g., `RatesLiquidityResponse`, `FxGbaResponse`). Phase 1 financial statement contracts do not exist yet. |
| **Unified Risk Engine** | Single risk engine replaces duplicate credit scores. All risk/PD calculations route through one system. | **Not Started** — `StressEngine` is a stub interface ([stress_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/stress_engine.py)) with `NotImplementedError`. |

---

## Phase Tracker

### Phase 0: Infrastructure & Setup

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 0.1 | Khởi tạo Repo & API Gateway | **Done** | Repo initialized with Vite React TypeScript frontend + FastAPI backend. Frontend: [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) and [MarketWatchPage.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/MarketWatchPage.tsx). Backend: FastAPI app with [rates_liquidity_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/rates_liquidity_service.py), [fx_gba_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/fx_gba_service.py), etc. API base URL configured at `/api/market-watch/*`. |
| 0.2 | Setup Database & Timeseries | **Not Started** | No PostgreSQL or TimescaleDB setup in repo. Backend uses in-memory `SimpleCache` ([cache.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cache.py)) with no persistent storage. `requirements.txt` has no psycopg2 or timescaledb dependency. |
| 0.3 | Cấu hình Caching Layer | **Partial** | `SimpleCache` in [cache.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cache.py) provides in-memory TTL-based caching for HKMA/HKAB API responses. This is a lightweight local cache — not a dedicated Redis layer (< 50ms SLA not guaranteed under load). |
| 0.4 | Lập lịch Job Scheduler | **Not Started** | No Celery, cron, or scheduler setup. Frontend has `setInterval` auto-refresh ([MarketWatchPage.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/MarketWatchPage.tsx#L188-L196)) but backend lacks scheduled data ingestion. |

---

### Phase 1: Business Valuation

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 1.1 | Nhập liệu & Bóc tách BCTC | **Not Started** | No PDF ingestion, OCR, NER, or financial statement extraction exists. No P&L, Balance Sheet, or Cash Flow data types defined. No GB/T 4754-2017 industry code mapping. |
| 1.2 | Integrity Check (Cân bằng) | **Not Started** | No `TotalAssets = TotalLiabilities + Equity` validation. No `TotalDebt`/`NetDebt` calculation exists anywhere. |
| 1.3 | Trích xuất Chỉ số (Ratios) | **Not Started** | No ratio engine. Current Ratio, Quick Ratio, Interest Coverage, DSCR formulas are not implemented in code. Market Watch has placeholder `SectorBenchmarkItem` values (DSO 45d, DIO 65d, DPO 50d) but these are demo/workspace-derived, not computed from company data. |
| 1.4 | Động cơ Tính rủi ro (Z-Score) | **Not Started** | No Altman Z-Score or Expected Credit Loss (AR aging) implementation. No aging bucket loss rate logic. |
| 1.5 | Dự phóng Dòng tiền (FCFF) | **Not Started** | No FCFF calculation, no driver-based forecasting, no 5-year projection model. |
| 1.6 | Định giá Chiết khấu (DCF) | **Not Started** | No WACC, CAPM, Hamada beta, or terminal value computation. No DCF valuation whatsoever. |

**Phase 1 verdict**: ❌ **All tasks Not Started.** This is the critical gap. Market Watch has a polished frontend but zero company financial data pipeline.

---

### Phase 2: Market Prediction

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 2.1 | Gọi API Vĩ mô (WHEN Ingestion) | **Partial** | **HKMA HIBOR**: [hkma_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkma_client.py) — working. **HKAB HIBOR**: [hkab_web_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkab_web_client.py) — working (web scraping fallback). **FX Frankfurter**: [fx_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/fx_client.py) — working. **CME FedWatch**: Not implemented. **Apify/HKEX Mega IPO**: Not implemented. |
| 2.2 | Dự báo HIBOR & Red Flags | **Not Started** | No Prophet or LSTM model. No Golden Timing Index logic. No "Window Dressing" (end of Q2/Q4) or Mega IPO red flag detection. Market Watch has static "Rate sensitivity" context cards only. |
| 2.3 | Đối sánh Sức khỏe Ngành | **Not Started** | No ChinaData.live API integration. No IHS formula (ω1·f(PMI) + ω2·f(IIP) + ω3·f(IEX)). Sector benchmarks use workspace demo data ([marketWatchApi.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/api/marketWatchApi.ts#L490-L626)). |
| 2.4 | Quét Kênh tài trợ (WHERE) | **Not Started** | No web scraping of bank fee schedules. No APR comparison engine. No Virtual Bank vs Traditional Bank trade-off matrix. |
| 2.5 | Cross-border Arbitrage | **Not Started** | No HIBOR-LPR spread calculation. No BOCHK GBA cross-border lending advisory trigger. No FX hedging cost analysis. |

**Phase 2 verdict**: 🟡 **2.1 Partial — rest Not Started.** Market data ingestion (HKMA, HKAB, Frankfurter) is functional but prediction models (Prophet/LSTM), Chinese macro data, funding channel scraping, and cross-border arbitrage are absent.

---

### Phase 3: Advisory & Structuring

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 3.1 | Hard-gates & CDI Alternative Data | **Not Started** | No D&B CCRA Score integration. No HKMA CDI API. No Cargox logistics data extraction. No Economic Substance / MPF check. |
| 3.2 | Unified PD (Xác suất vỡ nợ) | **Not Started** | No logistic regression model. No Z = β0 + β1(DSCR) + β2(DebtRatio) + β3(Margin) equation. No Map-Reduce PD-to-Tier (A–E) function. |
| 3.3 | Stress-Testing Engine | **Not Started** | `StressEngine` is a stub ([stress_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/stress_engine.py)) — raises `NotImplementedError`. No HIBOR +150bps shock onto DSCR simulation. No "suggest IRS" reactive advisory. Existing stress scenarios in UI are [context-only placeholders](file:///D:/projects/finsight-cfo/src/features/market-watch/api/marketWatchApi.ts#L822-L853). |
| 3.4 | Băm nhỏ Gói vay (Optimization) | **Not Started** | No PuLP or scipy.optimize.linprog. No linear programming for minimize(TotalInterestCost). No 3-tranche structuring (SFGS + Trade Finance + Working Capital). |
| 3.5 | RAG & GenAI Output (Blueprint) | **Not Started** | No LLM integration. No RAG pipeline. No structured JSON → LLM blueprint generation. AI CFO feature section in [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx#L96-L103) is a placeholder page. |

**Phase 3 verdict**: ❌ **All Not Started.** The entire advisory and structuring layer is absent. This is expected — the doc's Phase 1–3 assumes a multi-month timeline.

---

### Phase 4: UI/UX & E2E Testing

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 4.1 | Interactive Dashboard | **Partial** | Market Watch UI tabs (Market Pulse, Rates & Liquidity, FX & GBA, Sector Benchmarks, Commodities, Stress Signals) are polished and interactive. However, **Phase 1 sliders** (HIBOR shock, commodity stress) and **AI CFO chat interface** do not exist. Motion system ([MotionReveal.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionReveal.tsx), [MotionStagger.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionStagger.tsx), [motion.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/utils/motion.ts)) is production-quality. |
| 4.2 | Nối luồng Backend E2E | **Not Started** | No end-to-end pipeline connecting Phase 1 → 2 → 3. Frontend fetches from separate backend endpoints independently. No unified JSON contract flows across phases. |
| 4.3 | E2E & Edge Case Testing | **Not Started** | No unit tests for financial ratio calculations, division-by-zero handling, or missing data scenarios. Backend has a test file ([backend/tests/test_market_watch.py](file:///D:/projects/finsight-cfo/backend/tests/test_market_watch.py)) but Phase 1/3 logic is unimplemented so meaningful tests are impossible. Frontend has no test infrastructure. |

**Phase 4 verdict**: 🟡 **4.1 Partial — rest Not Started.** UI is polished for Market Watch but lacks Phase 1 sliders and AI CFO chat. No E2E pipeline or testing.

---

### Phase 5: First Round (BOCHK Submission)

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 5.1 | Thiết kế Pitch Deck | **Not Started** | No pitch deck in repo. |
| 5.2 | Viết Tài liệu Kỹ thuật (Architecture) | **Partial** | Technical documentation exists: [SYSTEM_DESIGN.md](file:///D:/projects/finsight-cfo/docs/product/SYSTEM_DESIGN.md), [MARKET_WATCH_SOURCE_REGISTRY.md](file:///D:/projects/finsight-cfo/docs/product/MARKET_WATCH_SOURCE_REGISTRY.md), [DESIGN_SYSTEM.md](file:///D:/projects/finsight-cfo/docs/product/DESIGN_SYSTEM.md), [MARKET_WATCH_BACKEND_PLAN.md](file:///D:/projects/finsight-cfo/docs/product/MARKET_WATCH_BACKEND_PLAN.md), etc. However, there is no architectural doc covering the full 6-phase pipeline, JSON contract interfaces, or the Unified Risk Engine design. |
| 5.3 | Final Submission (Đóng gói) | **Not Started** | Package/deployment scripts not yet configured. |

**Phase 5 verdict**: 🟡 **5.2 Partial — rest Not Started.** Technical docs exist for Market Watch but full competition submission materials are missing.

---

### Phase 6: Finalist

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 6.1 | Quay Video Demo Prototype | **Not Started** | No demo video. |
| 6.2 | Chuẩn bị Bộ Q&A (Phòng thủ) | **Not Started** | No Q&A prep document. |

**Phase 6 verdict**: ❌ **All Not Started** (expected — only relevant after advancing to finalist stage).

---

## Summary Dashboard

| Phase | Tasks | Status |
|---|---|---|
| Phase 0: Infrastructure | 4 | 🟡 1 Done, 1 Partial, 2 Not Started |
| Phase 1: Business Valuation | 6 | 🔴 6 Not Started |
| Phase 2: Market Prediction | 5 | 🟡 1 Partial, 4 Not Started |
| Phase 3: Advisory & Structuring | 5 | 🔴 5 Not Started |
| Phase 4: UI/UX & E2E | 3 | 🟡 1 Partial, 2 Not Started |
| Phase 5: First Round | 3 | 🟡 1 Partial, 2 Not Started |
| Phase 6: Finalist | 2 | 🔴 2 Not Started |
| **Total** | **28** | **1 Done, 4 Partial, 23 Not Started** |

---

## Immediate Next Engineering Priorities

> These priorities **must** be executed in order. Each builds on the previous.

### Priority 1: Build Phase 1 CompanyFinancialSnapshot foundation
Create a `CompanyFinancialSnapshot` data structure in the backend representing:
- Three core statements: P&L, Balance Sheet, Cash Flow
- A synthetic/demo financial statement loader (static JSON or fixture) so all downstream development can proceed without real PDF ingestion
- Backend endpoint: `GET /api/financials/snapshot`

**Evidence of gap**: No P&L, BS, or CF types exist anywhere in the repo. [types.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/types.ts) has `CompanyProfile` and `CompanyExposure` but no financial statements.

### Priority 2: Implement financial ratio engine
Build a stateless calculation module in the backend:
- `current_ratio = current_assets / current_liabilities`
- `quick_ratio = (current_assets - inventory - prepaid) / current_liabilities`
- `total_debt = short_term_debt + current_portion_ltd + long_term_debt + leases`
- `net_debt = total_debt - cash`
- `interest_coverage = ebit / interest_expense`
- `dscr = cads / total_debt_service` where `CADS = EBITDA - CashTaxes - UnfinancedCapEx - Distributions`
- `dso` (from receivables and revenue)
- `working_capital_gap = current_assets - current_liabilities`
- All formulas must handle division-by-zero gracefully.

**Evidence of gap**: The team doc defines all formulas explicitly (Section 1.2–1.3 of Project Workflow). Zero lines of ratio code exist in the repo.

### Priority 3: Wire Market Watch company metrics to CompanyFinancialSnapshot
Currently Market Watch metrics (funding conditions, rate pressure, FX signal, sector health) are hardcoded or based on workspace-derived demo values ([marketWatchApi.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/api/marketWatchApi.ts#L364-L373), [seed data](file:///D:/projects/finsight-cfo/src/features/market-watch/data/marketWatchSeed.ts)). Replace:
- `getCompanyContext()` → return real snapshot-derived data
- Executive card values ("Funding Conditions", "Rate Pressure", "FX/GBA Signal", "Sector Health") → compute from real ratios + Market Watch external data
- Remove/replace hardcoded `seedMarketMetrics` with ratio-derived values

### Priority 4: Implement real stress engine after ratios exist
Once financial ratios are computed from real snapshot data:
- Implement `StressEngine.simulate_stress()`
- Scenario 1: HIBOR +150bps → increase Total Debt Service → decrease DSCR → Red Flag if DSCR < 1.1x
- Scenario 2: Raw material price increase (NBS data) → decrease EBITDA → increase P(Default)
- Wire to `/api/market-watch/stress-signals?companyId=...` endpoint
- Replace current context-only placeholder scenarios

---

## Do Not Over-Polish Before Data Foundation

> ⚠️ **Critical engineering discipline note**

Market Watch currently has a **polished prototype frontend** (6 tabs, motion system, source provenance tooltips, executive cards, tab persistence via URL params) sitting on top of a **near-empty data pipeline**.

**Risk**: The team may be tempted to continue UI polish (more animations, card redesigns, layout tweaks) while Phase 1 (company financial data) remains completely unimplemented. This would produce a beautiful shell with no substance for the judges.

**Rule**: No further Market Watch UI polish passes should be done until:
1. `CompanyFinancialSnapshot` data structure exists (P1)
2. Financial ratio engine computes at least 6 core ratios from snapshot data (P2)
3. Market Watch executive cards are wired to real ratio data (P3)

Market Watch UI should remain at its current polish level — clean and professional — but no new visual features until the data pipeline catches up.

---

## Appendix: Current Repo State — Source Integration Map

| Source | Status | Type | Backend | UI Tab |
|---|---|---|---|---|
| HKAB HIBOR (web scrape) | ✅ Live | Provider-backed | [hkab_web_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkab_web_client.py) | Rates & Liquidity |
| HKMA HONIA (API) | ✅ Live | Provider-backed | [hkma_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkma_client.py) | Rates & Liquidity |
| HKMA Interbank Liquidity (API) | ✅ Live | Provider-backed | [hkma_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkma_client.py) | Rates & Liquidity |
| Frankfurter FX (API) | ✅ Live | Provider-backed | [fx_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/fx_client.py) | FX & GBA |
| Sector Benchmarks | ⚠️ Partial | Workspace-derived fixtures | [sector_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/sector_provider.py) | Sector Benchmarks |
| Commodities | ⚠️ Partial | Workspace-derived fixtures | [commodity_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/commodity_provider.py) | Commodities |
| Stress Signals | ❌ Stub | Context-only placeholders | [stress_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/stress_engine.py) | Stress Signals |
| Company Context | ⚠️ Partial | Workspace-derived demo | [company_context.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/company_context.py) | All tabs (profile strip) |
| Company Financial Statements | ❌ Missing | Not implemented | — | — |
| Financial Ratio Engine | ❌ Missing | Not implemented | — | — |
