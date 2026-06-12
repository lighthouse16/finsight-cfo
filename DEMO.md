# FinSight CFO — End-to-End Product Demo Script

This script guides you through a complete, polished product demonstration of **FinSight CFO** using the real sample data pack. 

The demo covers creating/resetting a workspace, statement parsing validation, active financial snapshot compilation, executing automated runs, report validation/traceability metadata, PDF exporting, and AI CFO context queries.

---

## Prerequisites & Setup

Ensure the backend and frontend are running locally in development mode:

### 1. Launch Backend
Run from the root of the repository:
```powershell
cd backend
# Activate virtual environment
.\.venv\Scripts\activate
# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Verify the backend is live at [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

### 2. Launch Frontend
Run from the root of the repository in a separate terminal:
```powershell
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your web browser.

---

## Guided Demo Script

### Step 1: Initialize the Sample Workspace
1. In the sidebar, navigate to the **Data Room** module.
2. Click the **"Initialize Sample Workspace"** button in the upper-right corner.
   * *Under the hood:* This deletes any existing sample data, creates a clean workspace for **Novus Retail Solutions Ltd**, writes five statement CSVs, compiles the active financial snapshot, and runs the entire 6-stage core analysis pipeline sequentially.
3. Observe the green toast notification confirming that the sample company has been initialized.
4. Note that **Novus Retail Solutions Ltd** is now selected as the active workspace in the top dropdown.

### Step 2: Verify Statement Checklist & Snapshot
1. On the **Data Room** page, inspect the checklist:
   * **Profit & Loss Statement (P&L)**, **Balance Sheet**, **Cash Flow Statement**, **Debt Amortization Schedule**, and **Accounts Receivable (AR) Aging Ledger** are all marked as **Connected** (green).
2. Scroll down to the **Financial Snapshot Calibration** card:
   * Verify that the active snapshot shows the core values (Revenue $5.40M, Gross Profit $3.30M, Total Assets $3.50M, Total Liabilities $2.00M, Equity $1.50M).
   * Confirm that all accounting integrity checks (such as the balance sheet identity) are marked as **Passed** (green).

### Step 3: Run / Rerun Analysis
1. Under the **Analysis Run Status** section, verify that all core runs (`financial_health`, `valuation`, `credit_score`, `funding_strategy`, `advisory_blueprint`, `workflow_run`) are marked as **Ready** (green).
2. Click the **Rerun** circle arrow button on any individual card (e.g., **Financial Health**) to demonstrate the real-time calculation pipeline.

### Step 4: Review Analytical Dashboards
1. Navigate to **Financial Health** in the sidebar:
   * Verify the Altman Z'' Double-Prime distress index, Altman score, EBITDA, interest coverage, and projected Years grid.
   * View the **RunMetadataBadge** showing the unique Run ID, Snapshot ID, warnings count, and logic version.
2. Navigate to **Valuation**:
   * Review the CAPM WACC build-up, Gordon Growth terminal value, and discounted explicit cash flows.
3. Navigate to **Credit Readiness**:
   * Review the unified credit scorecard, composite score, and credit drivers.
4. Navigate to **Funding Strategy**:
   * View the ranked suitable channels (such as Trade Finance or Receivable Purchase) and the detailed facility candidates.

### Step 5: Check Reports Readiness & PDF Export
1. Navigate to the **Reports** page.
2. Observe the green banner: `Report fully verified from workspace runs (100% ready)`.
3. Scroll to the bottom and inspect the **Report Traceability & Compliance Audit** card:
   * Verify it lists the Workspace ID (`workspace_sample_novus`), the active Snapshot ID, the current Timestamp, and the specific cryptographic Run IDs for each sub-analysis.
   * Read the professional banking compliance disclaimer.
4. Click the **"Print / Save PDF"** button in the top header:
   * Confirm in the browser print preview that the navigation sidebar, top bars, buttons, and footers are completely hidden (`no-print` styling applied).
   * Confirm the page breaks are placed cleanly and the layouts adjust to standard A4 printing.

### Step 6: Query the AI CFO Assistant
1. Navigate to the **AI CFO** page.
2. Observe the green context badge at the top of the chat panel:
   * It shows `Context Active: Snapshot snap_workspace_sample_novus...`, `Runs Loaded: 4/4 Core`, and the Freshness timestamp.
3. Click any of the **Suggested Questions** cards (e.g., *"Draft the advisor-ready summary."* or *"Explain valuation and WACC."*):
   * Confirm the assistant generates a deterministic, grounded answer drawing directly from the sample workspace run metadata.
   * Confirm that the sources (e.g., `Reports`, `Advisory Blueprint`, `Valuation`) are tagged below the response.

---

## Known Limitations

1. **Local Filesystem Storage**: Data and run metadata are persisted locally inside the `storage_db` folder. Clearing or deleting files physically will invalidate snapshots.
2. **Deterministic AI CFO**: The AI CFO assistant uses deterministic templates mapping keywords to the active snapshot metrics for demo reliability. It does not hit an external OpenAI/Gemini API key.
3. **Demo Reset Guard**: The sample reset helper button is locked to development/demo environments. If the backend is started with `APP_MODE=production` or `ALLOW_DEMO_FALLBACK=false`, the reset helper is hidden, and the API returns `HTTP 403 Forbidden`.
