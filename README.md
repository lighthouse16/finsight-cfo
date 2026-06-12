# FinSight CFO - BOCHK Challenge 2026

FinSight CFO is a finance-first CFO copilot for Hong Kong SMEs. The product workflow follows the BOCHK project plan: ingest company financial records, standardize statements, compute banking-grade diagnostics, value the business, monitor market conditions, and generate an explainable advisory blueprint for funding readiness.

## Core workflow

1. **Data Room ingestion**
   - Upload financial statement templates or structured records.
   - Parse statement line items into a canonical company snapshot.
   - Validate completeness before downstream analysis.

2. **Financial statement standardization**
   - Normalize income statement, balance sheet, cash flow, debt schedule, and receivables ageing data.
   - Run accounting integrity checks such as balance sheet identity, current asset reconciliation, total asset reconciliation, and cash-flow reconciliation.

3. **Historical metrics and diagnostics**
   - Liquidity: current ratio, quick ratio, working-capital gap.
   - Leverage: debt ratio, net debt / EBITDA.
   - Coverage: interest coverage and DSCR.
   - Receivables: DSO and expected credit loss context.
   - Distress check: Altman-style Z'' diagnostic for private-company context.

4. **Projection and valuation engine**
   - Build forecast assumptions from the normalized company snapshot.
   - Project revenue, EBIT, EBITDA, taxes, capital expenditure, net working capital, CFO estimate, and FCFF.
   - Estimate WACC with CAPM-style cost of equity, after-tax cost of debt, and capital structure weights.
   - Run DCF valuation with Gordon Growth terminal value, EV bridge, and sanity checks.

5. **Market Watch context**
   - Pull macro/rate/liquidity data where available.
   - Provide fallback fixtures for demo reliability.
   - Connect market timing, funding-channel ranking, cross-border context, and red-flag summaries to the advisory workflow.

6. **Advisory Blueprint**
   - Consume the active financial analysis.
   - Run hard-gate precheck, unified risk score foundation, deterministic stress tests, and candidate facility structuring.
   - Produce an explainable, context-only advisory briefing. This is not a formal credit approval or underwriting decision.

## Current implementation status

The repository currently implements the main demo-grade workflow:

- React + Vite frontend platform shell.
- FastAPI backend.
- Data Room preview ingestion for structured CSV/XLSX templates.
- Financial analysis engine with integrity checks, ratios, projections, WACC, and DCF.
- Market Watch endpoints for rates/liquidity, FX/GBA, sector benchmarks, commodities, stress signals, timing signal, funding ranking, cross-border funding context, and macro red flags.
- Advisory endpoints for precheck, risk score, stress testing, facility structuring, and advisory blueprint.
- Advisory now uses the active Data Room preview context when available and falls back to demo analysis when no preview has been activated.

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend health check:

```bash
curl http://127.0.0.1:8000/health
```

### Frontend

```bash
npm install
npm run dev
```

Optional frontend API base URL:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Recommended demo flow

The project is fully packaged for an end-to-end product demonstration:
* **Sample Data Pack**: Sourced under the [`demo_data/`](file:///d:/projects/finsight-cfo-v3/demo_data) folder. It contains realistic CSV templates for **Novus Retail Solutions Ltd** (P&L, Balance Sheet, Cash Flow, Debt Schedule, Receivables Aging).
* **Single-Click Setup**: If the application is in development/demo mode, click the **"Initialize Sample Workspace"** button in the Data Room to instantly create, upload, and run all core analysis pipelines.
* **Traceable Report PDF Export**: Navigate to the Reports page to view and export (Print/Save PDF) the fully compiled audit brief.
* **AI CFO Consultation**: Ask questions of the assistant with live active workspace context badges.

Please refer to the comprehensive [DEMO.md](file:///d:/projects/finsight-cfo-v3/DEMO.md) for the step-by-step walkthrough script and demo guidelines.

> [!WARNING]
> **Safety Guard**: The sample workspace reset helper (`POST /api/workspaces/reset-sample`) is a development/demo utility. It is strictly disabled in production (`APP_MODE=production` or `ALLOW_DEMO_FALLBACK=false`), returning `HTTP 403 Forbidden` for security.

## Commercialization note

This repository is currently a challenge-ready MVP. It demonstrates the end-to-end CFO intelligence workflow but is not yet a bank-production or commercial SaaS deployment. See [docs/COMMERCIALIZATION.md](file:///d:/projects/finsight-cfo-v3/docs/COMMERCIALIZATION.md) for the production hardening roadmap and the [Runtime Database Cutover Plan](file:///d:/projects/finsight-cfo-v3/docs/engineering/RUNTIME_CUTOVER_PLAN.md) for details on the current database transition status.

## Finance guardrails for future development

When adding features, keep the project anchored to the core finance workflow:

- Do not generate recommendations without traceable financial drivers.
- Keep valuation assumptions explicit: growth, margins, tax, CapEx, NWC, WACC, terminal growth, and exit multiple.
- Keep credit/risk scoring explainable through sub-scores rather than opaque labels.
- Separate context-only advisory output from formal banking underwriting decisions.
- Treat CDI/CCRA/MPF/Open API integrations as consent-based, auditable data sources.
- Prefer deterministic calculations first, then layer GenAI explanations on top of structured outputs.

## Next build priorities

1. Persist Data Room preview snapshots outside process memory.
2. Add a dedicated PD / credit-scoring engine with financial sub-scores, stress overlays, and transparent tier mapping.
3. Add mock CDI / CCRA / MPF consent connectors for demo completeness.
4. Add report export for advisor-ready PDF or dashboard summary.
5. Add automated tests for ratio calculations, projection assumptions, DCF, stress tests, and Data Room parsing.
6. Add deployment config and environment templates.
