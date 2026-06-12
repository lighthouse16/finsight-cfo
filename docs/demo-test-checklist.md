# BOCHK Demo Test Checklist

This checklist maps the BOCHK challenge workflow and known gaps to concrete demo endpoints and talking points.

## 1. Core health check

```bash
curl http://127.0.0.1:8000/health
```

Expected: service returns `status: ok`.

## 2. Stage 0-7 workflow runner

```bash
curl http://127.0.0.1:8000/api/workflow/run
```

Expected:

- `workflowId = bochk-business-valuation-credit-scoring-v1`
- `stages` includes Stage 0 to Stage 7
- `outputs.financialAnalysis`
- `outputs.creditScore`
- `outputs.facilityStructuring`
- `outputs.advisoryBlueprint`
- `outputs.trustBridgeContext`

Demo line:

> This endpoint proves the single JSON pipeline from financial ingestion through valuation, PD proxy, funding readiness, and CDI trust bridge.

## 3. Gap 1 - OCR / PDF / NER ingestion

```bash
curl http://127.0.0.1:8000/api/gap-remediation/ingestion-pipeline
```

Expected:

- document intake
- OCR/PDF extraction
- NER and canonical mapping
- integrity validation

Demo line:

> The current repo has Data Room preview ingestion and a production contract for OCR, PDF extraction, NER line-item mapping, and confidence-based human review.

## 4. Gap 2 - TimescaleDB / Redis / Celery architecture

```bash
curl http://127.0.0.1:8000/api/gap-remediation/target-architecture
```

Expected:

- `postgresTimescale`
- `redis`
- `celery`
- workflow persistence and audit trail criteria

Demo line:

> We separate demo execution from target production architecture: market time series in TimescaleDB, short-lived context in Redis, and long-running parsing or market refresh jobs in Celery.

## 5. Gap 3 - Macro prediction

```bash
curl http://127.0.0.1:8000/api/gap-remediation/macro-prediction
```

Expected:

- base case
- downside liquidity squeeze
- easing case
- provider/model contract

Demo line:

> The demo uses deterministic scenario overlays, while production can swap in Prophet/LSTM once provider history and credentials are available.

## 6. Gap 4 - Logistic PD

```bash
curl "http://127.0.0.1:8000/api/gap-remediation/logistic-pd?score=72&dscr=1.32&bureau_band=clear"
```

Expected:

- formula `P(Default)=1/(1+e^-Z)`
- z-score
- PD percentage
- tier

Demo line:

> The deterministic scorecard is now complemented by an explicit logistic PD formula contract. The coefficients are demo-only and must be calibrated with observed defaults before production underwriting.

## 7. Gap 5 - Facility optimization

```bash
curl "http://127.0.0.1:8000/api/gap-remediation/facility-optimization?requested_amount=3000000&eligible_invoices=1715000&dscr=1.32"
```

Expected:

- recommended stack
- weighted cost bps
- constraints
- feasible flag

Demo line:

> The demo returns a heuristic optimizer contract for Core SFGS, receivables finance, and liquidity buffer. Production should replace the heuristic with PuLP or scipy linprog after bank constraints are finalized.

## 8. CDI consent and trust bridge

Create consent:

```bash
curl -X POST http://127.0.0.1:8000/api/cdi/mock-consent \
  -H "Content-Type: application/json" \
  -d '{"companyId":"demo-company","companyName":"Demo Trading Limited"}'
```

Fetch data:

```bash
curl http://127.0.0.1:8000/api/cdi/mock-data/<consent_id>
```

Expected:

- cashflow signal
- verified invoice pool
- bureau signal
- funding implications
- risk implications

Demo line:

> CDI is represented as consent-first alternative data. It improves lender trust through verified invoices, cash-flow signals, and bureau-style context.

## 9. Frontend screens to open

```text
/platform/overview
/platform/financial-health
/platform/valuation
/platform/credit-readiness
/platform/funding-strategy
/platform/advisory-blueprint
/platform/reports
/platform/ai-cfo
```

Focus screens:

- Overview: workflow coverage
- Credit Readiness: PD proxy + CDI overlay
- Funding Strategy: CDI trust bridge + facility candidates
- Advisory Blueprint: advisor-ready recommendations

## 10. Local build checks

```bash
npm run type-check
npm run build
```

Backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Frontend:

```bash
npm run dev
```
