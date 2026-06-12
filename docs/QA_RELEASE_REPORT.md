# QA Release Report

## Executive Summary
This document reports the QA validation and release readiness assessment of the Finsight CFO application before its limited public beta release candidate distribution.

**Release Decision**: `Ready for limited public beta, not formal bank-production underwriting.`

---

## Validation Results

### 1. Full Backend Validation

#### Memory Mode
- **Status**: PASSED
- **Command**: `python -m pytest tests -q` (unconfigured env)
- **Results**: 664 passed, 0 failed, 12 warnings

#### Database Mode
- **Status**: PASSED
- **Command**: `python -m pytest tests -q` (configured for SQLite persistence)
- **Results**: 662 passed, 2 skipped, 0 failed, 12 warnings

---

### 2. Full Frontend Validation

- **Dependencies**: Installed successfully via `npm install --legacy-peer-deps`.
- **Linting**: PASSED via `npm run lint` (0 warnings).
- **Production Build**: PASSED via `npm run build` (compiled in 4.57s).
- **Frontend Tests**: N/A (no frontend test suite configured in `package.json`).

---

### 3. Docker / Deployment Validation

- **Docker Compose Configuration**: PASSED via `docker compose -f docker-compose.production.yml config`.
- **Docker Build Status**: Skipped. The local Docker daemon was offline during validation (npipe not found). This is classified as a local environment limitation rather than a product failure.

---

### 4. Forbidden Wording Audit

- **Audit Query**: Evaluated code and documentation using:
  ```powershell
  Get-ChildItem -Recurse -File src,docs,backend\app | Select-String -Pattern "guaranteed approval|approved loan|guaranteed funding|formal underwriting|certified bank rating|bank-grade approval|Govt Guaranteed"
  ```
- **Audit Findings**:
  - No affirmative claims of credit approval, guaranteed funding, or formal underwriting exist.
  - All occurrences are safety disclaimers specifically warning users that the tool does *not* provide formal credit decisions, bank underwriting, or loan guarantees.
  - Advisory report exports deterministically strip unsafe terminology and enforce RM review requirements.

---

### 5. Source Provenance Audit

- Verified that key data sources and metrics (including Market Watch interbank rates, ChinaData macro indicators, FedWatch expectation signals, IHS Sector benchmarks, and AI CFO briefings) display exact provenance status badges:
  - `live` (for active scraping endpoints/feeds)
  - `provider_configured` (for active paid APIs)
  - `provider_not_configured` (for unauthenticated proxy integrations)
  - `workspace_derived` (for ratios and metrics calculated directly from user files)
  - `fixture` (for local demo seed data)
  - `unavailable` (for offline services)

---

### 6. Smoke Test Coverage

Added a lightweight smoke test suite `backend/tests/test_qa_smoke_hardening.py` covering:
- **Secrets Protection**: Verifies that `/api/runtime/status` does not leak database credentials, passwords, or API keys.
- **Sample Reset Hardening**: Verifies that `/api/workspaces/reset-sample` is blocked with a 403 Forbidden status when in production mode.
- **Advisor Report Structure**: Verifies that report compilation outputs include explicit safety disclaimers, limitations, and citations.
- **Workspace Scoping**: Verifies that AI CFO RAG document chunks are isolated per workspace.
- **Stress Parameters Boundary Validation**: Verifies that `/api/advisory/stress-tests` rejects out-of-bounds parameters with 422 errors.
- **Safety Wording Verification**: Verifies that report outputs contain no forbidden credit approval terminology.

---

## Release Blockers
- **None**: All automated unit and integration tests are passing. All static analysis, linting, and build targets succeed. No regulatory or safety language violations were detected.
