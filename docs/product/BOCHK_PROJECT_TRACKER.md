# BOCHK Challenge 2026 — Project Tracker

> **Source of truth**: `BOCHK Challenge 2026.docx` (team document)
> **Repo**: `D:\projects\finsight-cfo`
> **Last updated**: 2026-06-07

---

## Architecture Principle

The team document defines the following core architecture:

| Principle | Definition | Repo status |
|---|---|---|
| **Unidirectional Data Pipeline** | All data flows in one direction: ingestion → standardization → metrics → prediction → advisory → output. No circular dependencies. | **Partial** — Market Watch frontend implements a unidirectional data pattern: `API → adapters → state → insights (rules) → UI`. Demo pipeline now flows: Data Room readiness → Financial analysis summary → Market Watch context → Advisory precheck → Unified risk score → Stress tests → Facility structures → Advisory blueprint UI. Data Room preview flow now adds: readiness API → upload metadata stub → structured parse preview → snapshot preview → local preview session → local workspace context provenance → downstream banners. Production analysis is not updated and backend persistence is pending. |
| **JSON Contracts Between Phases** | Each phase communicates via well-defined JSON schemas. | **Partial** — Backend has typed JSON response contracts: `MarketWatchSummary`, `FinancialAnalysisSummary`, `AdvisoryPrecheckResponse`, `AdvisoryRiskScoreResponse`, `AdvisoryStressTestResponse`, `AdvisoryFacilityStructureResponse`, `AdvisoryBlueprintResponse`, `DataRoomResponse`, upload metadata responses, parse preview responses, and snapshot preview responses. Contracts are demo/preview-only; no persisted company records flow through production analysis. |
| **Unified Risk Engine** | Single risk engine replaces duplicate credit scores. All risk/PD calculations route through one system. | **Partial** — [advisory/precheck_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/precheck_engine.py) hard-gate precheck, [unified_risk_score_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/unified_risk_score_engine.py) risk scoring (0-100 scale), [stress_testing_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/stress_testing_engine.py) deterministic stress testing, and [facility_structuring_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/advisory/facility_structuring_engine.py) candidate structuring are all foundation-level. Not calibrated with historical default data. |

---

The platform now has two related but separate flows:

### Data Room preview ingestion flow

```
Data Room readiness API (/api/data-room/demo-readiness)
  ↓ readiness records, dependencies, readiness percentage
Upload metadata stub (/api/data-room/demo-upload-metadata)
  ↓ selected file metadata; no permanent file storage
Structured parse preview (/api/data-room/demo-parse-preview)
  ↓ CSV/XLSX rows normalized into preview record sets
Snapshot preview (/api/data-room/demo-snapshot-preview)
  ↓ temporary CompanyFinancialSnapshot preview, integrity checks, core ratios
Local preview session (browser localStorage)
  ↓ refresh-safe parsed record sets and snapshot preview state
Local workspace context provenance (browser localStorage)
  ↓ explicit preview activation; backend persistence pending
Market Watch / Advisory Blueprint banners
  ↓ downstream pages disclose local preview context while demo/provider data remains active
```

### Current backend analysis pipeline

```
Financial demo analysis (/api/financials/demo-analysis)
  ↓ CompanyFinancialSnapshot → integrity checks → ratios → risk diagnostics → projections → WACC/DCF
Financial Analysis Summary (FinancialAnalysisSummary)
  ↓ band classifications, key signals, watch items, strengths, constraints
Market Watch context (/api/market-watch/*)
  ↓ rates, FX, sector benchmarks, commodities, stress signals
Advisory precheck (/api/advisory/demo-precheck)
  ↓ hard-gate checks (Data Integrity, DSCR, Liquidity, Leverage, etc.)
Unified risk score (/api/advisory/demo-risk-score)
  ↓ 0-100 score with explainable penalties
Stress tests (/api/advisory/demo-stress-tests)
  ↓ rate, DSO, input cost, FX import-cost shock scenarios
Facility structures (/api/advisory/demo-facility-structures)
  ↓ candidate limits, pricing spreads, annual costs
Advisory blueprint UI (/platform/advisory-blueprint)
  ↓ advisor-ready JSON brief, consolidated view
```

**Important**: Data Room ingestion is preview-only. Production analysis is not updated, no files are permanently stored, and Market Watch / Advisory Blueprint still use backend demo analysis with local preview provenance banners only.

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
| 1.1 | Nhập liệu & Bóc tách BCTC | **Partial** | Structured CSV/XLSX parse preview exists via Data Room preview ingestion. `POST /api/data-room/demo-parse-preview` normalizes simple structured records into preview record sets, and `POST /api/data-room/demo-snapshot-preview` builds a temporary snapshot preview for integrity checks and core ratios. This remains preview-only: no OCR/PDF parsing, no permanent storage, no backend workspace persistence, and production analysis is not updated. |
| 1.2 | Integrity Check (Cân bằng) | **Partial** | Pydantic models for `BalanceSheetPeriod` etc. and `run_integrity_checks` service in [integrity_checks.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/integrity_checks.py) validates `TotalAssets = TotalLiabilities + Equity` with 1.0 tolerance. Data Room snapshot preview can run these checks on preview records. No DB persistence yet. |
| 1.3 | Trích xuất Chỉ số (Ratios) | **Partial** | Stateless [ratio_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/ratio_engine.py) calculates Current Ratio, Quick Ratio, Interest Coverage, DSCR, Debt Ratio, Net Debt/EBITDA, DSO, Working Capital Gap, and ECL AR from normalized CompanyFinancialSnapshot. Snapshot preview can show core ratios from structured preview records. No historical metrics database or production dashboard binding yet. |
| 1.4 | Động cơ Tính rủi ro (Z-Score) | **Partial** | Altman Z'' Score and Receivables Risk diagnostics implemented in [risk_diagnostics.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/risk_diagnostics.py) and integrated into the `GET /api/financials/demo-analysis` endpoint. Validated in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). Full PD model integration remains. |
| 1.5 | Dự phóng Dòng tiền (FCFF) | **Partial** | Driver-based 5-year projections and primary/cross-check FCFF calculations implemented in [projection_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/projection_engine.py). Fully validated in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). Integration with actual historical database remains. |
| 1.6 | Định giá Chiết khấu (DCF) | **Partial** | WACC calculation (Hamada beta, extended CAPM with industry/company-specific premium), 5-year DCF discount schedule, Gordon Growth + exit multiple sanity comparison, 3×3 sensitivity grid with `isValid` flags, and sanity checks implemented in [valuation_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/valuation_engine.py). Integrated into demo endpoint. Tested in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py). Production integration pending. |
| 1.7 | Financial Analysis Summary (Bridge to Phase 3) | **Done** | Unified context-only summary contract implemented in [summary_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/summary_engine.py). Consolidates ratios, risk diagnostics, projections, and valuation into `FinancialAnalysisSummary` with band classifications (strong/adequate/watch/constrained/unavailable), key signals, watch items, strengths, constraints, and next data needed. Integrated into `GET /api/financials/demo-analysis`. 13 new tests in [test_financials.py](file:///D:/projects/finsight-cfo/backend/tests/test_financials.py) including language safety scan. |

**Phase 1 verdict**: 🟡 **6 Tasks Partial, 1 Done.** The data structure foundation, ratios, risk diagnostics, FCFF projections, WACC + DCF foundations, unified Financial Analysis Summary, and structured Data Room preview ingestion are ready and validated. Ingestion remains preview-only: company records are required for production, backend persistence is pending, and production analysis is not updated.

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
| 4.1 | Interactive Dashboard | **Partial** | Market Watch UI tabs (Market Pulse, Rates & Liquidity, FX & GBA, Sector Benchmarks, Commodities, Stress Signals) are polished and interactive. Motion system ([MotionReveal.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionReveal.tsx), [MotionStagger.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionStagger.tsx), [motion.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/utils/motion.ts)) is production-quality. Market Watch also shows local workspace context provenance when activated from Data Room. However, **Phase 1 sliders** (HIBOR shock, commodity stress) and **AI CFO chat interface** do not exist. |
| 4.2 | Advisory Blueprint UI | **Done** | [AdvisoryBlueprintPage.tsx](file:///D:/projects/finsight-cfo/src/features/advisory-blueprint/AdvisoryBlueprintPage.tsx) at `/platform/advisory-blueprint` consumes `demo-blueprint`, `demo-precheck`, `demo-risk-score`, `demo-stress-tests`, and `demo-facility-structures` backend endpoints. It displays a local workspace context provenance banner when Data Room preview context is active. Context-only financing readiness brief. Lazy-loaded. |
| 4.3 | Data Room UI Foundation | **Done** | [DataRoomPage.tsx](file:///D:/projects/finsight-cfo/src/features/data-room/DataRoomPage.tsx) at `/platform/data-room` displays financial record readiness with backend integration via [dataRoomApi.ts](file:///D:/projects/finsight-cfo/src/features/data-room/api/dataRoomApi.ts). It supports upload metadata, structured CSV/XLSX parse preview, financial snapshot preview UI, local preview session persistence, and explicit local workspace context activation/reset. Falls back to local seed data when backend unavailable. No OCR/PDF parsing or permanent file storage. Lazy-loaded. |
| 4.4 | Data Room Backend API Integration | **Done** | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) serves `GET /api/data-room/demo-readiness`, `POST /api/data-room/demo-upload-metadata`, `POST /api/data-room/demo-parse-preview`, and `POST /api/data-room/demo-snapshot-preview`. [demo_data_room.py](file:///D:/projects/finsight-cfo/backend/app/services/data_room/demo_data_room.py) provides deterministic demo data. [test_data_room.py](file:///D:/projects/finsight-cfo/backend/tests/test_data_room.py) validates contracts. |
| 4.5 | Platform Workflow Navigation | **Done** | [SidebarNav.tsx](file:///D:/projects/finsight-cfo/src/components/platform/SidebarNav.tsx) connects Data Room → Market Watch → Advisory Blueprint workflow. Cross-page CTAs link between modules. Workflow section groups these routes logically. |
| 4.6 | Route Lazy Loading & Bundle Optimization | **Done** | [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) uses `React.lazy` + `Suspense` for Market Watch, Advisory Blueprint, Data Room, and auth routes. [RouteLoadingFallback.tsx](file:///D:/projects/finsight-cfo/src/components/platform/RouteLoadingFallback.tsx) provides polished loading state. |
| 4.7 | Accessibility Label Fix | **Done** | Fixed disabled search input in [TopCommandBar.tsx](file:///D:/projects/finsight-cfo/src/components/platform/TopCommandBar.tsx) — added `id`, `name`, `aria-label`. Audit confirmed all form controls have proper labels, icon-only buttons have accessible names, and status chips include text labels. |
| 4.8 | Nối luồng Backend E2E | **Partial** | Demo pipeline connects Data Room → Financial Analysis → Market Watch → Advisory (precheck → risk score → stress tests → facility structures → blueprint). Data Room preview ingestion can parse structured CSV/XLSX and preview a snapshot locally. However, Market Watch and Advisory Blueprint still use backend demo analysis; local workspace context only adds provenance banners and does not feed backend analysis. |
| 4.9 | E2E & Edge Case Testing | **Partial** | Backend has 110 passing tests across `test_financials.py`, `test_market_watch.py`, `test_advisory.py`, `test_advisory_blueprint.py`, `test_health.py`, `test_data_room.py`. Frontend has no test infrastructure. Division-by-zero handling exists in ratio engine. |

**Phase 4 verdict**: 🟡 **4.1 Partial, 4.2-4.7 Done, 4.8 Partial, 4.9 Partial.** Platform UI foundation is strong — Market Watch, Advisory Blueprint, Data Room pages exist with workflow navigation, lazy loading, accessibility fixes, Data Room preview ingestion, snapshot preview UI, local preview session persistence, and local workspace context provenance. Still lacks OCR/PDF parsing, permanent storage, backend workspace persistence, production analysis replacement, AI CFO chat, Phase 1 sliders, and frontend test infrastructure.

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
| Phase 1: Business Valuation | 7 | 🟡 6 Partial, 1 Done |
| Phase 2: Market Prediction | 5 | 🟡 1 Partial, 4 Not Started |
| Phase 3: Advisory & Structuring | 5 | 🟡 5 Partial |
| Phase 4: UI/UX & E2E | 9 | 🟢 6 Done, 3 Partial |
| Phase 5: First Round | 3 | 🟡 1 Partial, 2 Not Started |
| Phase 6: Finalist | 2 | 🔴 2 Not Started |
| **Total** | **36** | **8 Done, 23 Partial, 5 Not Started** |

---

## Production Gaps

The following gaps must be addressed before the platform can move from demo context to production-ready:

### Data Ingestion & Storage
- Data Room ingestion is preview-only; production analysis not updated
- No OCR/PDF parsing
- No permanent file storage
- No database persistence for uploaded files, parsed records, or preview snapshots
- No backend workspace persistence yet
- No production financial snapshot replacement; company records required for production
- Market Watch and Advisory Blueprint still use backend demo analysis, with only local preview provenance banners
- No accounting connector ingestion (Xero, QuickBooks API integration)
- No bank/account connector ingestion (Open Banking API)
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

### Priority 1: Backend Workspace Persistence Stub for Preview Analysis Context
Add a server-side persistence stub that can store preview analysis context safely:
- Persist preview context metadata and snapshot references in-memory first
- Keep production analysis not updated
- Return explicit `preview-only` and `backend persistence pending` provenance fields
- Maintain demo/provider data remains active unless preview mode is explicitly requested

### Priority 2: Server-Side Preview Analysis Context Endpoint
Create an endpoint that can feed Market Watch and Advisory Blueprint in preview mode:
- Accept a preview context ID or active workspace context selector
- Return preview financial summary inputs separately from demo analysis
- Keep demo analysis as the default path
- Make downstream pages display whether they are using preview-only or demo/provider context

### Priority 3: Structured Parser Hardening with Template Validation
Strengthen the CSV/XLSX parser prototype:
- Validate required statement templates before normalization
- Add clearer errors for missing periods, missing required fields, and unsupported columns
- Keep parser limited to structured files; no OCR/PDF parsing
- Expand backend test coverage for malformed template edge cases

### Priority 4: CSV/XLSX Sample Templates and Downloadable Examples
Provide user-facing structured upload examples:
- P&L sample template
- Balance Sheet sample template
- Cash Flow sample template
- Guidance copy that says company records required for production

### Priority 5: Document Upload Storage Design, Still Without OCR
Design the storage architecture before implementing permanent file storage:
- Metadata schema and retention rules
- File storage boundaries and security constraints
- Database persistence model
- Explicitly defer OCR/PDF parsing until the structured ingestion path is stable

### Priority 6: Market Watch Provenance Audit
Audit remaining fixture/workspace-derived content:
- Sector benchmarks: identify which can connect to real provider data
- Commodities: evaluate FRED / World Bank integration feasibility
- Stress signals: clarify which scenarios can use financial summary inputs
- Update [MARKET_WATCH_SOURCE_REGISTRY.md](file:///D:/projects/finsight-cfo/docs/product/MARKET_WATCH_SOURCE_REGISTRY.md) with audit findings

---

## Do Not Over-Polish Before Data Foundation

> ⚠️ **Critical engineering discipline note**

Market Watch currently has a **polished prototype frontend** (6 tabs, motion system, source provenance tooltips, executive cards, tab persistence via URL params) sitting on top of a **demo-context data pipeline**.

**Risk**: The team may be tempted to continue UI polish (more animations, card redesigns, layout tweaks) while real data ingestion remains unimplemented. This would produce a beautiful shell with no substance for the judges.

**Rule**: No further Market Watch UI polish passes should be done until:
1. Backend workspace persistence exists for preview analysis context (Priority 1)
2. A server-side preview analysis context endpoint can feed downstream pages in preview mode (Priority 2)
3. Structured parser hardening and templates reduce ingestion ambiguity (Priorities 3-4)
4. Production analysis replacement is designed and implemented safely

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
| Data Room Readiness | ✅ Demo | Demo-context | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) | Data Room |
| Data Room Upload Metadata | ✅ Preview | Preview-only | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) | Data Room |
| Structured CSV/XLSX Parse Preview | ✅ Preview | Preview-only | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) | Data Room |
| Data Room Snapshot Preview | ✅ Preview | Preview-only | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) | Data Room |
| Local Preview Session | ✅ Local | Browser localStorage | [dataRoomPreviewStorage.ts](file:///D:/projects/finsight-cfo/src/features/data-room/utils/dataRoomPreviewStorage.ts) | Data Room |
| Local Workspace Context Provenance | ✅ Local | Browser localStorage | [workspaceAnalysisContext.ts](file:///D:/projects/finsight-cfo/src/features/data-room/utils/workspaceAnalysisContext.ts) | Data Room, Market Watch, Advisory Blueprint |
| Sector Benchmarks | ⚠️ Partial | Workspace-derived fixtures | [sector_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/sector_provider.py) | Sector Benchmarks |
| Commodities | ⚠️ Partial | Workspace-derived fixtures | [commodity_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/commodity_provider.py) | Commodities |
| Stress Signals (Market) | ⚠️ Partial | Workspace-derived with demo analysis inputs | [stress_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/stress_engine.py) | Stress Signals |
| Company Context | ⚠️ Partial | Workspace-derived demo | [company_context.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/company_context.py) | All tabs (profile strip) |
| Production Company Financial Records | ❌ Missing | No permanent storage | — | Data Room preview only |
| Financial Ratio Engine | ✅ Demo + Preview | Demo-context and snapshot preview | [ratio_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/ratio_engine.py) | Data Room preview; internal pipeline |
