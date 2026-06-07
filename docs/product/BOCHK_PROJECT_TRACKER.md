# BOCHK Challenge 2026 — Project Tracker

> **Source of truth**: `BOCHK Challenge 2026.docx` (team document)
> **Repo**: `D:\projects\finsight-cfo`
> **Last updated**: 2026-06-07

---

## Architecture Principle

The team document defines the following core architecture:

| Principle | Definition | Repo status |
|---|---|---|
| **Unidirectional Data Pipeline** | All data flows in one direction: ingestion → standardization → metrics → prediction → advisory → output. No circular dependencies. | **Partial** — Market Watch frontend implements a unidirectional data pattern: `API → adapters → state → insights (rules) → UI`. Demo pipeline now flows: Data Room readiness → Financial analysis summary → Market Watch context → Advisory precheck → Unified risk score → Stress tests → Facility structures → Advisory blueprint UI. No persistent ingestion or production pipeline exists. |
| **JSON Contracts Between Phases** | Each phase communicates via well-defined JSON schemas. | **Partial** — Backend has typed JSON response contracts: `MarketWatchSummary`, `FinancialAnalysisSummary`, `AdvisoryPrecheckResponse`, `AdvisoryRiskScoreResponse`, `AdvisoryStressTestResponse`, `AdvisoryFacilityStructureResponse`, `AdvisoryBlueprintResponse`, `DataRoomResponse`. Contracts are demo-context-only; no user-uploaded company data flows through them. |
| **Unified Risk Engine** | Single risk engine replaces duplicate credit scores. All risk/PD calculations route through one system. | **Partial** — [advisory/precheck_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/precheck_engine.py) hard-gate precheck, [unified_risk_score_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/unified_risk_score_engine.py) risk scoring (0-100 scale), [stress_testing_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/stress_testing_engine.py) deterministic stress testing, and [facility_structuring_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/facility_structuring_engine.py) candidate structuring are all foundation-level. Not calibrated with historical default data. |

---

## Current Architecture Snapshot

The demo advisory pipeline now operates end-to-end through the following stages:

```
Data Room readiness (/api/data-room/demo-readiness)
  ↓ records, dependencies, readiness percentage
Financial demo analysis (/api/financials/demo-analysis)
  ↓ CompanyFinancialSnapshot → integrity checks → ratios → risk diagnostics → projections → WACC/DCF
Financial Analysis Summary (FinancialAnalysisSummary)
  ↓ band classifications, key signals, watch items, strengths, constraints
Market Watch context (/api/market-watch/*)
  ↓ rates, FX, sector benchmarks, commodities, stress signals
Advisory precheck (/api/advisory/demo-precheck)
  ↓ hard-gate pass/fail checks (Data Integrity, DSCR, Liquidity, Leverage, etc.)
Unified risk score (/api/advisory/demo-risk-score)
  ↓ 0-100 score with explainable penalties
Stress tests (/api/advisory/demo-stress-tests)
  ↓ rate, DSO, input cost, FX import-cost shock scenarios
Facility structures (/api/advisory/demo-facility-structures)
  ↓ candidate limits, pricing spreads, annual costs
Advisory blueprint UI (/platform/advisory-blueprint)
  ↓ advisor-ready JSON brief, consolidated view
```

**Important**: This pipeline operates entirely on demo/fixture data. No real company documents are uploaded, parsed, or persisted.

---

## Phase Tracker

### Phase 0: Infrastructure & Setup

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 0.1 | Khởi tạo Repo & API Gateway | **Done** | Repo initialized with Vite React TypeScript frontend + FastAPI backend. Frontend: [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) with route lazy loading. Backend: FastAPI app with routers for `/api/market-watch`, `/api/financials`, `/api/advisory`, `/api/data-room`. Health check at `/health`. |
| 0.2 | Setup Database & Timeseries | **Not Started** | No PostgreSQL or TimescaleDB setup in repo. Backend uses in-memory `SimpleCache` ([cache.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cache.py)) with no persistent storage. `requirements.txt` has no psycopg2 or timescaledb dependency. |
| 0.3 | Cấu hình Caching Layer | **Partial** | `SimpleCache` in [cache.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cache.py) provides in-memory TTL-based caching for HKMA/HKAB API responses. This is a lightweight local cache — not a dedicated Redis layer. |
| 0.4 | Lập lịch Job Scheduler | **Not Started** | No Celery, cron, or scheduler setup. Frontend has `setInterval` auto-refresh ([MarketWatchPage.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/MarketWatchPage.tsx#L188-L196)) but backend lacks scheduled data ingestion. |
| 0.5 | Route Lazy Loading & Bundle Optimization | **Done** | [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) uses `React.lazy` + `Suspense` with [RouteLoadingFallback.tsx](file:///D:/projects/finsight-cfo/src/components/platform/RouteLoadingFallback.tsx) for all major platform routes (Market Watch, Advisory Blueprint, Data Room) and auth routes. Non-critical chunks split below 500 kB. |

**Phase 0 verdict**: 🟡 **2 Done, 1 Partial, 2 Not Started.** Frontend foundation is solid with lazy loading, backend caching is functional, but persistent storage and scheduling remain unimplemented.

---

### Phase 1: Business Valuation

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 1.1 | Nhập liệu & Bóc tách BCTC | **Not Started** | No PDF ingestion, OCR, NER, or financial statement extraction exists. No P&L, Balance Sheet, or Cash Flow data types defined. Demo pipeline uses hardcoded `CompanyFinancialSnapshot`. No GB/T 4754-2017 industry code mapping. |
| 1.2 | Integrity Check (Cân bằng) | **Partial** | Pydantic models for `BalanceSheetPeriod` etc. and `run_integrity_checks` service in [integrity_checks.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/integrity_checks.py) validates `TotalAssets = TotalLiabilities + Equity` with 1.0 tolerance. Tested in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). No DB persistence/user upload yet. |
| 1.3 | Trích xuất Chỉ số (Ratios) | **Partial** | Stateless [ratio_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/ratio_engine.py) calculates Current Ratio, Quick Ratio, Interest Coverage, DSCR, Debt Ratio, Net Debt/EBITDA, DSO, Working Capital Gap, and ECL AR from normalized CompanyFinancialSnapshot. Tested in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). No historical metrics database or dashboard wired yet. |
| 1.4 | Động cơ Tính rủi ro (Z-Score) | **Partial** | Altman Z'' Score and Receivables Risk diagnostics implemented in [risk_diagnostics.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/risk_diagnostics.py) and integrated into the `GET /api/financials/demo-analysis` endpoint. Validated in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). Full PD model integration remains. |
| 1.5 | Dự phóng Dòng tiền (FCFF) | **Partial** | Driver-based 5-year projections and primary/cross-check FCFF calculations implemented in [projection_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/projection_engine.py). Fully validated in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). Integration with actual historical database remains. |
| 1.6 | Định giá Chiết khấu (DCF) | **Partial** | WACC calculation (Hamada beta, extended CAPM with industry/company-specific premium), 5-year DCF discount schedule, Gordon Growth + exit multiple sanity comparison, 3×3 sensitivity grid with `isValid` flags, and sanity checks implemented in [valuation_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/valuation_engine.py). Integrated into demo endpoint. Tested in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). Production integration pending. |
| 1.7 | Financial Analysis Summary (Bridge to Phase 3) | **Done** | Unified context-only summary contract implemented in [summary_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/summary_engine.py). Consolidates ratios, risk diagnostics, projections, and valuation into `FinancialAnalysisSummary` with band classifications (strong/adequate/watch/constrained/unavailable), key signals, watch items, strengths, constraints, and next data needed. Integrated into `GET /api/financials/demo-analysis`. 13 new tests in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py) including language safety scan. |

**Phase 1 verdict**: 🟡 **6 Tasks Partial, 1 Done — ingestion Not Started.** The data structure foundation, ratios, risk diagnostics, FCFF projections, WACC + DCF foundations, and unified Financial Analysis Summary are ready and validated (91 tests pass). The summary contract bridges Phase 1 outputs to Phase 3 advisory. Ingestion (Phase 1.1) remains the critical gap.

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
| 3.1 | Hard-gates & CDI Alternative Data | **Partial** | Hard-gate precheck backend foundation implemented in [precheck_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/precheck_engine.py). Standard checks (Data Integrity, DSCR, Liquidity, Leverage, Receivables, Distress, FCFF, Valuation) consume demo financial analysis responses. Alternative data (CDI, CCRA, Cargox, MPF) pending. |
| 3.2 | Unified PD (Xác suất vỡ nợ) | **Partial** | Unified risk scoring foundation added in [unified_risk_score_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/unified_risk_score_engine.py). Score scale 0-100 built on top of financial summary and precheck factors with explainable penalties. Not a calibrated PD engine yet (future production PD requires historical default data and calibration). |
| 3.3 | Stress-Testing Engine | **Partial** | Deterministic stress testing foundation added in [stress_testing_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/stress_testing_engine.py) applying rate, DSO, input cost, and FX import-cost shocks. Reports deltas for DSCR, EBITDA, FCFF, etc. Context-only sensitivity analysis, not a lender decision engine. Production requires company records and calibrated market scenarios. |
| 3.4 | Băm nhỏ Gói vay (Optimization) | **Partial** | Candidate structure foundation added in [facility_structuring_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/facility_structuring_engine.py). Estimates limits, pricing spreads, and annual costs under baseline, hard-gate, and stress scenario constraints. Assumptions-based and subject to lender review. Full multi-tranche structuring optimization remains. |
| 3.5 | RAG & GenAI Output (Blueprint) | **Partial** | Deterministic advisory blueprint foundation added in [blueprint_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/blueprint_engine.py). `GET /api/advisory/demo-blueprint` consolidates financial summary, hard-gate precheck, unified risk score, stress tests, and facility structuring into an advisor-ready JSON brief without calling an LLM. RAG pipeline and GenAI generation remain future work. |

**Phase 3 verdict**: 🟡 **3.1, 3.2, 3.3, 3.4, & 3.5 Partial.** Hard-gate precheck, unified risk scoring, deterministic stress testing, facility structuring, and deterministic advisory blueprint foundations implemented and tested. Labeled historical data calibration, full loan optimization, CDI alternative data integrations, RAG, and GenAI generation remain.

---

### Phase 4: UI/UX & E2E Testing

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 4.1 | Interactive Dashboard | **Partial** | Market Watch UI tabs (Market Pulse, Rates & Liquidity, FX & GBA, Sector Benchmarks, Commodities, Stress Signals) are polished and interactive. Motion system ([MotionReveal.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionReveal.tsx), [MotionStagger.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionStagger.tsx), [motion.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/utils/motion.ts)) is production-quality. However, **Phase 1 sliders** (HIBOR shock, commodity stress) and **AI CFO chat interface** do not exist. |
| 4.2 | Advisory Blueprint UI | **Done** | [AdvisoryBlueprintPage.tsx](file:///D:/projects/finsight-cfo/src/features/advisory-blueprint/AdvisoryBlueprintPage.tsx) at `/platform/advisory-blueprint` consumes `demo-blueprint`, `demo-precheck`, `demo-risk-score`, `demo-stress-tests`, and `demo-facility-structures` backend endpoints. Context-only financing readiness brief. Lazy-loaded. |
| 4.3 | Data Room UI Foundation | **Done** | [DataRoomPage.tsx](file:///D:/projects/finsight-cfo/src/features/data-room/DataRoomPage.tsx) at `/platform/data-room` displays financial record readiness with backend integration via [dataRoomApi.ts](file:///D:/projects/finsight-cfo/src/features/data-room/api/dataRoomApi.ts). Falls back to local seed data when backend unavailable. No real upload/OCR. Lazy-loaded. |
| 4.4 | Data Room Backend API Integration | **Done** | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) serves `GET /api/data-room/demo-readiness` with records, dependencies, and summary. [demo_data_room.py](file:///D:/projects/finsight-cfo/backend/app/services/data_room/demo_data_room.py) provides deterministic demo data. [test_data_room.py](file:///D:/projects/finsight-cfo/backend/tests/test_data_room.py) validates contract. |
| 4.5 | Platform Workflow Navigation | **Done** | [SidebarNav.tsx](file:///D:/projects/finsight-cfo/src/components/platform/SidebarNav.tsx) connects Data Room → Market Watch → Advisory Blueprint workflow. Cross-page CTAs link between modules. Workflow section groups these routes logically. |
| 4.6 | Route Lazy Loading & Bundle Optimization | **Done** | [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) uses `React.lazy` + `Suspense` for Market Watch, Advisory Blueprint, Data Room, and auth routes. [RouteLoadingFallback.tsx](file:///D:/projects/finsight-cfo/src/components/platform/RouteLoadingFallback.tsx) provides polished loading state. |
| 4.7 | Accessibility Label Fix | **Done** | Fixed disabled search input in [TopCommandBar.tsx](file:///D:/projects/finsight-cfo/src/components/platform/TopCommandBar.tsx) — added `id`, `name`, `aria-label`. Audit confirmed all form controls have proper labels, icon-only buttons have accessible names, and status chips include text labels. |
| 4.8 | Nối luồng Backend E2E | **Partial** | Demo pipeline now connects Data Room → Financial Analysis → Market Watch → Advisory (precheck → risk score → stress tests → facility structures → blueprint). However, no real company data flows through; all demo-context-only. No persistent state between sessions. |
| 4.9 | E2E & Edge Case Testing | **Partial** | Backend has 91 passing tests across `test_financials.py`, `test_market_watch.py`, `test_advisory.py`, `test_advisory_blueprint.py`, `test_health.py`, `test_data_room.py`. Frontend has no test infrastructure. Division-by-zero handling exists in ratio engine. |

**Phase 4 verdict**: 🟡 **4.1 Partial, 4.2-4.7 Done, 4.8 Partial, 4.9 Partial.** Platform UI foundation is strong — Market Watch, Advisory Blueprint, Data Room pages exist with workflow navigation, lazy loading, and accessibility fixes. Still lacks real upload/OCR/parser flow, AI CFO chat, Phase 1 sliders, and frontend test infrastructure.

---

### Phase 5: First Round (BOCHK Submission)

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 5.1 | Thiết kế Pitch Deck | **Not Started** | No pitch deck in repo. |
| 5.2 | Viết Tài liệu Kỹ thuật (Architecture) | **Partial** | Technical documentation exists: [SYSTEM_DESIGN.md](file:///D:/projects/finsight-cfo/docs/product/SYSTEM_DESIGN.md), [MARKET_WATCH_SOURCE_REGISTRY.md](file:///D:/projects/finsight-cfo/docs/product/MARKET_WATCH_SOURCE_REGISTRY.md), [DESIGN_SYSTEM.md](file:///D:/projects/finsight-cfo/docs/product/DESIGN_SYSTEM.md), [COMPONENT_ARCHITECTURE.md](file:///D:/projects/finsight-cfo/docs/product/COMPONENT_ARCHITECTURE.md), [BOCHK_PROJECT_TRACKER.md](file:///D:/projects/finsight-cfo/docs/product/BOCHK_PROJECT_TRACKER.md). Architecture snapshot covers demo pipeline but full 6-phase pipeline documentation remains incomplete. |
| 5.3 | Final Submission (Đóng gói) | **Not Started** | Package/deployment scripts not yet configured. |

**Phase 5 verdict**: 🟡 **5.2 Partial — rest Not Started.** Technical docs exist for Market Watch, design system, and component architecture but full competition submission materials are missing.

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
| Phase 0: Infrastructure | 5 | 🟡 2 Done, 1 Partial, 2 Not Started |
| Phase 1: Business Valuation | 7 | 🟡 6 Partial, 1 Not Started |
| Phase 2: Market Prediction | 5 | 🟡 1 Partial, 4 Not Started |
| Phase 3: Advisory & Structuring | 5 | 🟡 5 Partial |
| Phase 4: UI/UX & E2E | 9 | 🟢 6 Done, 3 Partial |
| Phase 5: First Round | 3 | 🟡 1 Partial, 2 Not Started |
| Phase 6: Finalist | 2 | 🔴 2 Not Started |
| **Total** | **36** | **8 Done, 22 Partial, 6 Not Started** |

---

## Production Gaps

The following gaps must be addressed before the platform can move from demo context to production-ready:

### Data Ingestion & Storage
- Real company document upload (PDF, CSV, XLSX) with file metadata persistence
- OCR / PDF parser / financial statement normalization pipeline
- Accounting connector (Xero, QuickBooks API integration)
- Bank/account connector (Open Banking API)
- Persistent PostgreSQL / TimescaleDB database
- Redis cache layer for production SLA
- Celery / scheduler for recurring data ingestion jobs

### Financial Modeling
- Calibrated PD / default model requiring historical default data
- Lender product catalog / rate data for facility structuring
- Real benchmark provider integrations (C&SD, D&B, Bloomberg)
- Real commodity provider integrations (FRED, Alpha Vantage, LME)
- Real freight / logistics provider integrations (Baltic Exchange, Freightos)

### Market Data
- CME FedWatch integration
- ChinaData.live macro data integration (PMI, IIP, IEX)
- HIBOR-LPR spread calculation for cross-border advisory
- Bank fee schedule scraping / APR comparison

### Platform Hardening
- Authentication / authorization hardening (production-grade auth, not mock)
- Frontend test infrastructure (unit, integration, E2E)
- Backend integration tests for full pipeline flow
- Rate limiting, input validation hardening
- Deployment pipeline / Docker configuration

---

## Immediate Next Engineering Priorities

> These priorities follow the current implementation state and build on the demo pipeline foundation.

### Priority 1: Data Room Upload Contract with File Metadata
Create a minimal upload contract in the backend:
- `POST /api/data-room/upload` accepting file metadata (filename, type, category, size)
- Store metadata in-memory for now (database comes later)
- Return a `DataRoomUploadResponse` with record ID and status
- Update Data Room UI to show upload form with drag-drop zone
- **No OCR / parsing yet** — just metadata capture

### Priority 2: Financial Document Ingestion Parser Prototype
Build a structured CSV/XLSX parser for financial statements:
- Parse columnar financial data into `CompanyFinancialSnapshot` format
- Support P&L, Balance Sheet, and Cash Flow templates
- Validate parsed data against existing integrity check rules
- Connect to Data Room upload flow as first real ingestion path

### Priority 3: Persist Company Financial Snapshot
Replace the hardcoded demo `CompanyFinancialSnapshot` with persisted data:
- Store parsed snapshots in-memory (or SQLite for demo)
- `GET /api/financials/snapshot/{companyId}` returning stored snapshot
- Update financial analysis endpoint to consume stored snapshot
- Maintain demo fallback when no company data exists

### Priority 4: Connect Advisory Blueprint to Company Workspace State
Make the advisory pipeline workspace-aware:
- Advisory precheck, risk score, stress tests, and facility structures consume stored snapshot instead of hardcoded demo
- Data Room readiness reflects actual uploaded record status
- Market Watch executive cards update based on company-specific ratios

### Priority 5: Market Watch Provenance Audit
Audit remaining fixture/workspace-derived content:
- Sector benchmarks: identify which can connect to real provider data
- Commodities: evaluate FRED / World Bank integration feasibility
- Stress signals: clarify which scenarios can use financial summary inputs
- Update [MARKET_WATCH_SOURCE_REGISTRY.md](file:///D:/projects/finsight-cfo/docs/product/MARKET_WATCH_SOURCE_REGISTRY.md) with audit findings

### Priority 6: Real-Time Sliders for Market Watch
Add interactive shock parameters to Market Watch:
- HIBOR rate shock slider (+50, +100, +150, +200 bps)
- Commodity cost increase slider
- Connected to financial summary DSCR / EBITDA impact
- Display advisory implications in context-only language

---

## Do Not Over-Polish Before Data Foundation

> ⚠️ **Critical engineering discipline note**

Market Watch currently has a **polished prototype frontend** (6 tabs, motion system, source provenance tooltips, executive cards, tab persistence via URL params) sitting on top of a **demo-context data pipeline**.

**Risk**: The team may be tempted to continue UI polish (more animations, card redesigns, layout tweaks) while real data ingestion remains unimplemented. This would produce a beautiful shell with no substance for the judges.

**Rule**: No further Market Watch UI polish passes should be done until:
1. Real company document upload exists (Priority 1)
2. Financial statement parser produces `CompanyFinancialSnapshot` from uploaded data (Priority 2)
3. Market Watch executive cards consume real ratio data (Priority 4)

Market Watch UI should remain at its current polish level — clean and professional — but no new visual features until the data pipeline catches up.

---

## Appendix: Current Repo State — Source Integration Map

| Source | Status | Type | Backend | UI Tab |
|---|---|---|---|---|
| HKAB HIBOR (web scrape) | ✅ Live | Provider-backed | [hkab_web_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkab_web_client.py) | Rates & Liquidity |
| HKMA HONIA (API) | ✅ Live | Provider-backed | [hkma_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkma_client.py) | Rates & Liquidity |
| HKMA Interbank Liquidity (API) | ✅ Live | Provider-backed | [hkma_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkma_client.py) | Rates & Liquidity |
| Frankfurter FX (API) | ✅ Live | Provider-backed | [fx_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/fx_client.py) | FX & GBA |
| Financial Analysis Summary | ✅ Demo | Demo-context | [summary_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/summary_engine.py) | Market Watch, Advisory |
| Advisory Precheck | ✅ Demo | Demo-context | [precheck_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/precheck_engine.py) | Advisory Blueprint |
| Unified Risk Score | ✅ Demo | Demo-context | [unified_risk_score_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/unified_risk_score_engine.py) | Advisory Blueprint |
| Stress Tests | ✅ Demo | Demo-context | [stress_testing_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/stress_testing_engine.py) | Advisory Blueprint |
| Facility Structures | ✅ Demo | Demo-context | [facility_structuring_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/facility_structuring_engine.py) | Advisory Blueprint |
| Advisory Blueprint | ✅ Demo | Demo-context | [blueprint_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/blueprint_engine.py) | Advisory Blueprint |
| Data Room Readiness | ✅ Demo | Demo-context | [demo_data_room.py](file:///D:/projects/finsight-cfo/backend/app/services/data_room/demo_data_room.py) | Data Room |
| Sector Benchmarks | ⚠️ Partial | Workspace-derived fixtures | [sector_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/sector_provider.py) | Sector Benchmarks |
| Commodities | ⚠️ Partial | Workspace-derived fixtures | [commodity_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/commodity_provider.py) | Commodities |
| Stress Signals (Market) | ⚠️ Partial | Workspace-derived with demo analysis inputs | [stress_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/stress_engine.py) | Stress Signals |
| Company Context | ⚠️ Partial | Workspace-derived demo | [company_context.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/company_context.py) | All tabs (profile strip) |
| Company Financial Records | ❌ Missing | Not implemented (no upload) | — | Data Room (readiness only) |
| Financial Ratio Engine | ✅ Demo | Demo-context | [ratio_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/ratio_engine.py) | — (internal pipeline) |
