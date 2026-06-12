# BOCHK Challenge 2026 — Project Tracker

> **Source of truth**: `BOCHK Challenge 2026.docx` (team document)
> **Repo**: `D:\projects\finsight-cfo`
> **Last updated**: 2026-06-09

---

## Architecture Principle

The team document defines the following core architecture:

| Principle | Definition | Repo status |
|---|---|---|
| **Unidirectional Data Pipeline** | All data flows in one direction: ingestion → standardization → metrics → prediction → advisory → output. No circular dependencies. | **Partial** — Market Watch frontend implements a unidirectional data pattern: `API → adapters → state → insights (rules) → UI`. Demo pipeline now flows: Data Room readiness → Financial analysis summary → Market Watch context → Advisory precheck → Unified risk score → Stress tests → Facility structures → Advisory blueprint UI. Data Room preview flow now adds: upload/parse → snapshot preview → backend preview context → `/api/financials/preview-analysis` → Market Watch / Advisory Blueprint preview panels. Production analysis is not updated and database persistence is pending. |
| **JSON Contracts Between Phases** | Each phase communicates via well-defined JSON schemas. | **Partial** — Backend has typed JSON response contracts: `MarketWatchSummary`, `FinancialAnalysisSummary`, `AdvisoryPrecheckResponse`, `AdvisoryRiskScoreResponse`, `AdvisoryStressTestResponse`, `AdvisoryFacilityStructureResponse`, `AdvisoryBlueprintResponse`, `DataRoomResponse`, upload metadata responses, parse preview responses, snapshot preview responses, backend workspace preview context responses, and preview financial analysis responses. Contracts are demo/preview-only; no persisted company records flow through production analysis. |
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
Backend workspace preview context (/api/data-room/demo-workspace-preview-context)
  ↓ explicit preview activation; in-memory only, no database persistence
Preview financial analysis (/api/financials/preview-analysis)
  ↓ preview-only financial response derived from the active Data Room snapshot
Market Watch / Advisory Blueprint preview panels
  ↓ downstream pages disclose preview context while demo/provider data remains active where preview data is unavailable
```

### Current backend analysis pipeline

```
Financial demo analysis (/api/financials/demo-analysis)
  ↓ CompanyFinancialSnapshot → integrity checks → ratios → risk diagnostics → projections → WACC/DCF
Financial Analysis Summary (FinancialAnalysisSummary)
  ↓ band classifications, key signals, watch items, strengths, constraints
Market Watch context (/api/market-watch/*)
  ↓ rates, FX, sector benchmarks, commodities, stress signals
  ↓ Timing Signal → Industry Health → Funding Channel Ranking → Cross-border Funding Context → Red Flags Macro Summary
  ↓ Source Registry Hardening: all provenance built from [source_registry.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/source_registry.py) with consistent mode badges rendered via [sourceMeta.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/utils/sourceMeta.ts)
  ↓ Provider Integration Hardening: no-network adapter contracts define provider-ready interfaces for 7 categories (HIBOR/HK rates, HKMA liquidity/HONIA, IHS/sector benchmarks, ChinaData/macro-sector, FedWatch/rate expectations, LPR/RMB benchmarks, FX reference) — adapter metadata exposed in all provenance responses
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
Demo Flow Rail ([DemoFlowRail.tsx](file:///D:/projects/finsight-cfo/src/components/platform/DemoFlowRail.tsx))
  ↓ 4-step pitch rail (Data Room → Financial Preview → Market Watch → Advisory Blueprint) guides judges through the end-to-end demo path
```

**Important**: Data Room ingestion remains preview-only. Production analysis is not replaced, no files are permanently stored, no preview state is written to a database, and demo/provider data remains active where preview data is unavailable. OCR/PDF parsing is not implemented yet.

---

## Phase Tracker

### Phase 0: Infrastructure & Setup

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 0.1 | Khởi tạo Repo & API Gateway | **Done** | Repo initialized with Vite React TypeScript frontend + FastAPI backend. Frontend: [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) with route lazy loading. Backend: FastAPI app with routers for `/api/market-watch`, `/api/financials`, `/api/advisory`, `/api/data-room`. Health check at `/health`. |
| 0.2 | Setup Database & Timeseries | **Not Started** | No PostgreSQL or TimescaleDB setup in repo. Backend uses in-memory `SimpleCache` ([cache.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cache.py)) with no persistent storage. `requirements.txt` has no psycopg2 or timescaledb dependency. |
| 0.3 | Cấu hình Caching Layer | **Partial** | `SimpleCache` in [cache.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cache.py) provides in-memory TTL-based caching for HKMA/HKAB API responses. This is a lightweight local cache — not a dedicated Redis layer. |
| 0.4 | Lập lịch Job Scheduler | **Partial** | Safe manual scheduler foundation added via `run_report_worker_once.py`. Fully decoupled from Redis/Celery for local/demo simplicity. True cron daemon remains pending for production. |
| 0.5 | Route Lazy Loading & Bundle Optimization | **Done** | [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) uses `React.lazy` + `Suspense` with [RouteLoadingFallback.tsx](file:///D:/projects/finsight-cfo/src/components/platform/RouteLoadingFallback.tsx) for all major platform routes (Market Watch, Advisory Blueprint, Data Room) and auth routes. Non-critical chunks split below 500 kB. |

**Phase 0 verdict**: 🟡 **2 Done, 1 Partial, 2 Not Started.** Frontend foundation is solid with lazy loading, backend caching is functional, but persistent storage and scheduling remain unimplemented.

---

### Phase 1: Business Valuation

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 1.1 | Nhập liệu & Bóc tách BCTC | **Partial** | Structured CSV/XLSX parse preview exists via Data Room preview ingestion. `POST /api/data-room/demo-parse-preview` normalizes simple structured records into preview record sets, `POST /api/data-room/demo-snapshot-preview` builds a temporary snapshot preview, and `GET /api/financials/preview-analysis` can return preview-only financial analysis from the active backend preview context. This remains preview-only: no OCR/PDF parsing, no permanent storage, no database persistence, and production analysis is not replaced. |
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
| 2.1 | Golden Timing Index v1 | **Done** | [timing_signal_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/timing_signal_service.py) computes a context-only timing signal using HIBOR/HONIA rate trends, calendar red flags (quarter-end window dressing, CNY public holidays, year-end), and optional sector health context. Band system: `favorable` / `neutral` / `cautious` / `unavailable`. No CME FedWatch integration (pending). No true ML forecast (Prophet/LSTM pending). [test_market_watch.py](file:///D:/projects/finsight-cfo/backend/tests/test_market_watch.py) validates safe wording, band edges, and calendar triggers. |
| 2.2 | Industry Health Context v1 | **Done** | [industry_health_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/industry_health_service.py) builds a context-only industry health signal with PMI proxy, export growth proxy, industrial production proxy, and margin context. Band system: `strong` / `stable` / `caution` / `unavailable`. No real ChinaData.live/IHS integration (pending). Sector references and PMI/IIP/IEX values are workspace-derived fixture proxies initially and must be replaced with licensed provider data before production use. Context-only language, disclaimer, and source/provenance caveats enforced via test scan. [test_industry_health.py](file:///D:/projects/finsight-cfo/backend/tests/test_industry_health.py) validates sector contexts, default fallback, and safe wording. |
| 2.3 | Funding Channel Ranking v1 | **Done** | [funding_channel_ranking_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/funding_channel_ranking_service.py) ranks candidate funding channels (receivables discounting, term loan, trade finance, wc facility, fx hedging) based on workspace-derived company context, timing signal, and industry health. Context-only: each channel is ranked `strong_fit` / `moderate_fit` / `limited_fit` / `not_recommended`. Constraints and company context flags disclose fixture/provider-pending limitations. No real lender product catalog scraping (pending). [test_funding_channel_ranking.py](file:///D:/projects/finsight-cfo/backend/tests/test_funding_channel_ranking.py) validates exactly 5 channels, item fields, safety wording, and forbidden term scan. |
| 2.4 | Cross-border Funding Context v1 | **Done** | [cross_border_funding_context_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cross_border_funding_context_service.py) provides context-only HKD/HIBOR vs RMB/LPR-style funding comparison. Bands: `spreadBand` (hkd_advantage/rmb_advantage/balanced/unavailable), `fxRiskBand` (low/moderate/elevated/unavailable), `crossBorderReviewBand` (worth_reviewing/monitor/not_priority/unavailable). Explanation text, 5 context components, provenance, 2 warnings about fixture/provider-pending data, and disclaimer. LPR reference is a fixture placeholder — no real HIBOR-LPR spread or BOCHK GBA lending advisory integration (pending). No arbitrage instruction or financing recommendation language — strictly context-only. Frontend card in FX & GBA tab with full loading/null/fallback states. [test_cross_border_funding_context.py](file:///D:/projects/finsight-cfo/backend/tests/test_cross_border_funding_context.py) validates shape, bands, warnings, disclaimer, and forbidden terms. |
| 2.5 | Red Flags & Macro Risk Summary v1 | **Done** | [red_flags_macro_summary_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/red_flags_macro_summary_service.py) consolidates all existing Phase 2 signals into a context-only red-flag dashboard. 7 red flag categories (`rates`, `fx`, `sector`, `funding`, `cross_border`, `timing`, `liquidity`) with 5 severity levels (`low`/`moderate`/`elevated`/`stressed`/`unavailable`). Summary band escalation logic (stressed if 2+ stressed or liquidity+fx+rates stack; elevated if 2+ elevated; watch if any moderate/elevated; clear if all low; unavailable if insufficient data). 3+ mitigants. Headline, suggested review actions per flag, supporting signals, component breakdown grid. Graceful degradation: if any underlying service crashes, adds a warning and continues with partial data. Context-only language enforced via forbidden-term scan in [test_red_flags_macro_summary.py](file:///D:/projects/finsight-cfo/backend/tests/test_red_flags_macro_summary.py) (19 tests). Frontend card in Market Pulse tab after Timing Signal, before Funding Channel Ranking. No real CME FedWatch / ChinaData.live integration (pending). No true ML forecast (pending). |
| 2.6 | Source Registry Hardening v1 | **Done** | Centralized source/provenance metadata registry at [source_registry.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/source_registry.py). Defines 9 registered sources with normalized source key, label, mode (`provider-backed`/`workspace-derived`/`fixture-backed`/`unavailable`), freshness, caveat, provider, and confidence. `build_provenance()` helper unifies provenance construction across all 5 Phase 2 services. Frontend mirror at [sourceMeta.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/utils/sourceMeta.ts) with `buildSourceItems()` providing consistent `SourceItem[]` for `SourceInfoTooltip` across Golden Timing, Industry Health, Funding Channel Ranking, Cross-border Funding Context, and Red Flags & Macro Summary cards. Full backend test suite (202 pass), frontend lint/build pass, and manual UI checks across Market Pulse, Rates & Liquidity, FX & GBA, and Sector Benchmarks confirmed. Source registry standardizes provenance only — it does not add new provider integrations, make fixture data provider-backed, or add ML/lender scraping. All signals remain context-only/planning-support only. |
| 2.7 | Provider Integration Hardening v1 | **Done** | Provider-ready adapter contracts at [provider_adapters.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/provider_adapters.py). Defines typed interfaces (`BaseMarketDataAdapter` protocol) and three no-network adapters: `FixtureMarketDataAdapter` (fixture-backed), `WorkspaceDerivedAdapter` (workspace-derived), `MissingProviderAdapter` (unavailable). Each returns structured `ProviderStatus` with `providerName`, `providerKey`, `mode`, `asOf`, `freshness`, `caveat`, `warnings`, and `confidence`. Supports 7 provider categories: HIBOR/HK rates, HKMA liquidity/HONIA, IHS/sector benchmarks, ChinaData/macro-sector, FedWatch/rate expectations, LPR/RMB benchmarks, and FX reference. `build_provenance()` now returns `providerAdapter` and `providerIntegration` metadata in all API responses. No real provider credentials, external API calls, or scraping added — fixture/workspace-derived data remains active. No new dependencies; async adapter tests use stdlib `asyncio.run()`. Full backend suite: 270 passed. No frontend files touched. |

**Phase 2 verdict**: 🟢 **7 Done.** Golden Timing Index, Industry Health Context, Funding Channel Ranking, Cross-border Funding Context, Red Flags & Macro Risk Summary, Source Registry Hardening, and Provider Integration Hardening are all implemented and tested. Provider adapter contracts define ready interfaces for 7 categories — no real CME FedWatch / ChinaData.live / IHS / LPR integrations yet, but integration points are now explicit in the architecture. No true ML forecast yet. All Phase 2 signals remain context-only and planning-support only.

---

### Phase 3: Advisory & Structuring

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 3.1 | Hard-gates & CDI Alternative Data | **Done** | Hard-gate precheck backend foundation implemented in `precheck_engine.py`. CDI alternative data mock gateway added in `cdi_mock_gateway.py` with consent flow. |
| 3.2 | Unified PD (Xác suất vỡ nợ) | **Done** | Unified risk scoring foundation added. Logistic-style deterministic PD engine implemented in `pd_engine.py` using DSCR, Debt Ratio, and Margin. |
| 3.3 | Stress-Testing Engine | **Done** | Deterministic stress testing foundation added. specific BOCHK HIBOR shock +150 bps stress test implemented in `stress_testing_engine.py`. |
| 3.4 | Băm nhỏ Gói vay (Optimization) | **Done** | Candidate structure foundation added. Full multi-tranche loan structuring optimizer implemented in `loan_structuring_engine.py` (SFGS 80, Trade Finance CDI, Working Capital Buffer). |
| 3.5 | RAG & GenAI Output (Blueprint) | **Done** | Deterministic advisory blueprint foundation added. A unified `/api/advisory/funding-blueprint` API brings together all Phase 3 advisory modules into a single response. Frontend "Funding Blueprint Engine" added to `AdvisoryBlueprintPage.tsx`. |

**Phase 3 verdict**: 🟢 **All 5 Tasks Done.** Hard-gate precheck, unified risk scoring, CDI alternative data mock gateway, deterministic PD engine, specific HIBOR stress tests, deterministic multi-tranche loan structuring, and unified blueprint endpoint are implemented.

---

### Phase 4: UI/UX & E2E Testing

| ID | Task | Repo Status | Evidence |
|---|---|---|---|
| 4.1 | Interactive Dashboard | **Partial** | Market Watch UI tabs (Market Pulse, Rates & Liquidity, FX & GBA, Sector Benchmarks, Commodities, Stress Signals) are polished and interactive. Motion system ([MotionReveal.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionReveal.tsx), [MotionStagger.tsx](file:///D:/projects/finsight-cfo/src/features/market-watch/components/MotionStagger.tsx), [motion.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/utils/motion.ts)) is production-quality. Market Watch now shows Data Room preview context panels when backend preview-analysis is active, while provider market data remains unchanged. However, **Phase 1 sliders** (HIBOR shock, commodity stress) and **AI CFO chat interface** do not exist. |
| 4.2 | Advisory Blueprint UI | **Done** | [AdvisoryBlueprintPage.tsx](file:///D:/projects/finsight-cfo/src/features/advisory-blueprint/AdvisoryBlueprintPage.tsx) at `/platform/advisory-blueprint` consumes `demo-blueprint`, `demo-precheck`, `demo-risk-score`, `demo-stress-tests`, and `demo-facility-structures` backend endpoints. It also displays a Data Room preview financial context block when `/api/financials/preview-analysis` is available. The core advisory response remains unchanged and demo-context. Context-only financing readiness brief. Lazy-loaded. |
| 4.3 | Data Room UI Foundation | **Done** | [DataRoomPage.tsx](file:///D:/projects/finsight-cfo/src/features/data-room/DataRoomPage.tsx) at `/platform/data-room` displays financial record readiness with backend integration via [dataRoomApi.ts](file:///D:/projects/finsight-cfo/src/features/data-room/api/dataRoomApi.ts). It supports upload metadata, structured CSV/XLSX parse preview, financial snapshot preview UI, local preview session persistence, and explicit local workspace context activation/reset. Falls back to local seed data when backend unavailable. No OCR/PDF parsing or permanent file storage. Lazy-loaded. |
| 4.4 | Data Room Backend API Integration | **Done** | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) serves `GET /api/data-room/demo-readiness`, `POST /api/data-room/demo-upload-metadata`, `POST /api/data-room/demo-parse-preview`, and `POST /api/data-room/demo-snapshot-preview`. [demo_data_room.py](file:///D:/projects/finsight-cfo/backend/app/services/data_room/demo_data_room.py) provides deterministic demo data. [test_data_room.py](file:///D:/projects/finsight-cfo/backend/tests/test_data_room.py) validates contracts. |
| 4.5 | Platform Workflow Navigation | **Done** | [SidebarNav.tsx](file:///D:/projects/finsight-cfo/src/components/platform/SidebarNav.tsx) connects Data Room → Market Watch → Advisory Blueprint workflow. Cross-page CTAs link between modules. Workflow section groups these routes logically. |
| 4.6 | Route Lazy Loading & Bundle Optimization | **Done** | [AppRouter.tsx](file:///D:/projects/finsight-cfo/src/routes/AppRouter.tsx) uses `React.lazy` + `Suspense` for Market Watch, Advisory Blueprint, Data Room, and auth routes. [RouteLoadingFallback.tsx](file:///D:/projects/finsight-cfo/src/components/platform/RouteLoadingFallback.tsx) provides polished loading state. |
| 4.7 | Accessibility Label Fix | **Done** | Fixed disabled search input in [TopCommandBar.tsx](file:///D:/projects/finsight-cfo/src/components/platform/TopCommandBar.tsx) — added `id`, `name`, `aria-label`. Audit confirmed all form controls have proper labels, icon-only buttons have accessible names, and status chips include text labels. |
| 4.8 | Nối luồng Backend E2E | **Partial** | Current preview E2E flow is connected: Data Room upload/parse → snapshot preview → backend preview context → `/api/financials/preview-analysis` → Market Watch / Advisory Blueprint preview panels. This is still preview-only: no DB persistence, no production analysis replacement, demo/provider data remains active where preview data is unavailable, and OCR/PDF parsing is not implemented yet. |
| 4.9 | E2E & Edge Case Testing | **Partial** | Backend has 110 passing tests across `test_financials.py`, `test_market_watch.py`, `test_advisory.py`, `test_advisory_blueprint.py`, `test_health.py`, `test_data_room.py`. Frontend has no test infrastructure. Division-by-zero handling exists in ratio engine. |
| 4.10 | Demo / Pitch Polish v1 | **Done** | Reusable [DemoFlowRail.tsx](file:///D:/projects/finsight-cfo/src/components/platform/DemoFlowRail.tsx) guides judges through 4 demo steps (Data Room → Financial Preview → Market Watch → Advisory Blueprint) with icons, descriptions, route links, and status chips (Preview-only / Source-aware / Context-only). Rendered on Data Room, Market Watch, and Advisory Blueprint pages below headings. CTA wording improved across the demo path. Frontend lint/build passes. Manual checks passed on `/platform/data-room`, `/platform/market-watch`, `/platform/advisory-blueprint` — 0 console errors. Backend not touched. UI/pitch polish only — no backend features, provider integrations, or production decision logic added. |

**Phase 4 verdict**: 🟡 **4.1 Partial, 4.2-4.7 Done, 4.8 Partial, 4.9 Partial, 4.10 Done.** Platform UI foundation is strong — Market Watch, Advisory Blueprint, Data Room pages exist with workflow navigation, lazy loading, accessibility fixes, Data Room preview ingestion, snapshot preview UI, local preview session persistence, backend preview context, `/api/financials/preview-analysis`, downstream preview panels, and DemoFlowRail pitch polish. Still lacks OCR/PDF parsing, permanent storage, production analysis replacement, AI CFO chat, Phase 1 sliders, and frontend test infrastructure.

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
| Phase 2: Market Prediction | 7 | 🟢 7 Done |
| Phase 3: Advisory & Structuring | 5 | 🟡 5 Partial |
| Phase 4: UI/UX & E2E | 10 | 🟢 7 Done, 3 Partial |
| Phase 5: First Round | 3 | 🟡 1 Partial, 2 Not Started |
| Phase 6: Finalist | 2 | 🔴 2 Not Started |
| **Total** | **39** | **16 Done, 17 Partial, 6 Not Started** |

---

## Production Gaps

The following gaps must be addressed before the platform can move from demo context to production-ready:

### Data Ingestion & Storage
- Data Room ingestion is preview-only; production analysis not updated
- No OCR/PDF parsing
- No permanent file storage
- No database persistence for uploaded files, parsed records, or preview snapshots
- Backend workspace preview context is in-memory only
- No production financial snapshot replacement; company records required for production
- Market Watch and Advisory Blueprint can display preview-analysis panels, but core demo/provider data remains active where preview data is unavailable
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
- Timing signal calendar flags cover basic quarters and public holidays; true ML forecast (Prophet/LSTM) pending
- Funding channel ranking uses workspace-derived company context and fixture industry data; no real lender product catalog scraping or APR comparison
- Red Flags & Macro Risk Summary consolidates all Phase 2 signals but remains context-only: no real CME FedWatch, ChinaData.live/IHS, or LPR provider integrations yet; some references remain fixture/workspace-derived
- Source Registry Hardening v1 standardizes provenance metadata across all Phase 2 services and cards. It does not add new provider integrations, does not make fixture data provider-backed, and does not add ML or lender scraping. All signals remain context-only/planning-support only.
- Provider Integration Hardening v1 adds provider-ready adapter contracts defining typed interfaces and three no-network adapters (FixtureMarketDataAdapter, WorkspaceDerivedAdapter, MissingProviderAdapter) across 7 provider categories. `providerAdapter` and `providerIntegration` metadata exposed in all provenance responses. No real provider credentials, external API calls, or scraping added. Fixture/workspace-derived data remains active until provider integrations are implemented. No new dependencies.

### Platform Hardening
- Authentication / authorization hardening (production-grade auth, not mock)
- Frontend test infrastructure (unit, integration, E2E)
- Backend integration tests for full pipeline flow
- Rate limiting, input validation hardening
- Deployment pipeline / Docker configuration

---

> These priorities build on the completed Phase 2 workflow (Timing → Industry Health → Funding Channel Ranking → Cross-border Funding Context → Red Flags Macro Summary), the Source Registry Hardening pass that standardized provenance metadata across all cards, the Provider Integration Hardening pass that defined provider-ready adapter contracts with explicit integration points, and the Demo Flow Rail that guides judges through the end-to-end pitch path.

### Priority 1: Real Provider Integrations (Phase 2 services)
Connect real provider data for Phase 2 signals that still use fixture/workspace-derived data, using the adapter contracts defined in Provider Integration Hardening v1:
- CME FedWatch integration (for Timing Signal & Red Flags macro context)
- ChinaData.live or IHS integration (for Industry Health PMI/IIP/IEX & Red Flags sector context)
- LPR reference provider (for Cross-border Funding Context)
- Lender product catalog research (for Funding Channel Ranking)

### Priority 2: Final Demo Script / Presentation Flow
Polish the judge-facing presentation flow now that the DemoFlowRail is live:
- Draft a walkthrough script that follows the 4-step rail (Data Room → Financial Preview → Market Watch → Advisory Blueprint)
- Ensure each demo step has a clear talking point and expected judge takeaway
- Coordinate with pitch deck content from Phase 5

---

## Do Not Over-Polish Before Data Foundation

> ⚠️ **Critical engineering discipline note**

Market Watch currently has a **polished prototype frontend** (6 tabs, motion system, source provenance tooltips, executive cards, tab persistence via URL params) sitting on top of a **demo-context data pipeline**.

**Risk**: The team may be tempted to continue UI polish (more animations, card redesigns, layout tweaks) while real data ingestion remains unimplemented. This would produce a beautiful shell with no substance for the judges.

**Rule**: No further Market Watch UI polish passes should be done until:
1. Persisted workspace preview context design is complete (Priority 1)
2. Structured parser hardening and templates reduce ingestion ambiguity (Priorities 2-3)
3. Production analysis replacement is designed and implemented safely

Market Watch UI should remain at its current polish level — clean and professional — but no new visual features until the data pipeline catches up.

> **Note**: Phase 2.5 Red Flags & Macro Risk Summary card was added as a consolidated risk dashboard, but the rule still applies: this card reuses existing Phase 2 signals without adding new UI visual features beyond what is needed for the card's display.

---

## Appendix: Current Repo State — Source Integration Map

| Source | Status | Type | Backend | UI Tab |
|---|---|---|---|---|
| HKAB HIBOR (web scrape) | ✅ Live | Provider-backed | [hkab_web_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkab_web_client.py) | Rates & Liquidity |
| HKMA HONIA (API) | ✅ Live | Provider-backed | [hkma_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkma_client.py) | Rates & Liquidity |
| HKMA Interbank Liquidity (API) | ✅ Live | Provider-backed | [hkma_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/hkma_client.py) | Rates & Liquidity |
| Frankfurter FX (API) | ✅ Live | Provider-backed | [fx_client.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/fx_client.py) | FX & GBA |
| Golden Timing Index v1 | ✅ Workspace | Context-only, market-rate-aware | [timing_signal_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/timing_signal_service.py) | Market Pulse, Rates & Liquidity |
| Industry Health Context v1 | ✅ Workspace | Context-only, workspace-derived fixture | [industry_health_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/industry_health_service.py) | Market Pulse, Sector Benchmarks |
| Funding Channel Ranking v1 | ✅ Workspace | Context-only, workspace-derived company context | [funding_channel_ranking_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/funding_channel_ranking_service.py) | Market Pulse |
| Cross-border Funding Context v1 | ✅ Workspace | Context-only, fixture LPR placeholder | [cross_border_funding_context_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/cross_border_funding_context_service.py) | FX & GBA |
| Red Flags & Macro Risk Summary v1 | ✅ Workspace | Context-only, consolidates Phase 2 signals | [red_flags_macro_summary_service.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/red_flags_macro_summary_service.py) | Market Pulse |
| Source Registry Hardening v1 | ✅ Workspace | Provenance metadata standardisation; registry-driven tooltip badges | [source_registry.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/source_registry.py), [sourceMeta.ts](file:///D:/projects/finsight-cfo/src/features/market-watch/utils/sourceMeta.ts) | All Market Watch tabs |
| Provider Integration Hardening v1 | ✅ Adapter | Provider-ready no-network adapter contracts for 7 categories; exposes `providerAdapter`/`providerIntegration` in all provenance | [provider_adapters.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/provider_adapters.py) | Internal architecture; metadata visible in all Market Watch provenance responses |
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
| Backend Workspace Preview Context | ✅ Preview | In-memory backend stub | [data_room.py](file:///D:/projects/finsight-cfo/backend/app/routes/data_room.py) | Data Room activation |
| Preview Financial Analysis | ✅ Preview | Preview-only analysis endpoint | [financials.py](file:///D:/projects/finsight-cfo/backend/app/routes/financials.py) | Market Watch, Advisory Blueprint |
| Sector Benchmarks | ⚠️ Partial | Workspace-derived fixtures | [sector_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/sector_provider.py) | Sector Benchmarks |
| Commodities | ⚠️ Partial | Workspace-derived fixtures | [commodity_provider.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/commodity_provider.py) | Commodities |
| Stress Signals (Market) | ⚠️ Partial | Workspace-derived with demo analysis inputs | [stress_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/stress_engine.py) | Stress Signals |
| Company Context | ⚠️ Partial | Workspace-derived demo | [company_context.py](file:///D:/projects/finsight-cfo/backend/app/services/market_watch/company_context.py) | All tabs (profile strip) |
| Production Company Financial Records | ❌ Missing | No permanent storage | — | Data Room preview only |
| Financial Ratio Engine | ✅ Demo + Preview | Demo-context and snapshot preview | [ratio_engine.py](file:///D:/projects/finsight-cfo/backend/app/services/financials/ratio_engine.py) | Data Room preview; internal pipeline |
