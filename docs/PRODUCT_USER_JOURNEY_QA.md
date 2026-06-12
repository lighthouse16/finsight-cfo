# FinSight CFO: Product User Journey QA

This document outlines the core product journey, quality assurance standards, UX risks, and polish items for the FinSight CFO product experience. It ensures the application is coherent, reliable, understandable, and presentable end-to-end as a serious fintech MVP.

---

## Core Product Journey Map

### 1. Start App
* **Expected User Action:** User opens the application in their browser (`/`).
* **Expected System Behavior:** Application loads without errors, showing the overview dashboard or a prompt to select a workspace.
* **Evidence Route/Component:** `src/routes/AppRouter.tsx`, `src/features/overview/OverviewPage.tsx`
* **Possible Failure Mode:** Backend not available; API health check fails.
* **Fallback Message:** "Cannot connect to server. Please ensure the backend services are running."
* **Readiness Verdict:** PASS

### 2. Select Workspace
* **Expected User Action:** User selects a target SME workspace from the header/sidebar dropdown.
* **Expected System Behavior:** Application fetches and populates the active context with the chosen workspace data.
* **Evidence Route/Component:** `src/components/platform/SidebarNav.tsx`
* **Possible Failure Mode:** Missing workspace or workspace data fails to load.
* **Fallback Message:** "Select a workspace to begin analysis."
* **Readiness Verdict:** PASS

### 3. Review Financial Data
* **Expected User Action:** User navigates to the Data Room to review financial statements.
* **Expected System Behavior:** Uploaded or synced statements are visible, and financial snapshot status shows as compiled and validated.
* **Evidence Route/Component:** `src/features/data-room/DataRoomPage.tsx`
* **Possible Failure Mode:** Missing statement files or snapshot validation errors.
* **Fallback Message:** "Insufficient data to compile active snapshot."
* **Readiness Verdict:** PASS

### 4. View Financial Health
* **Expected User Action:** User navigates to Financial Health to view business metrics, scores, and distress index.
* **Expected System Behavior:** Detailed metrics and an aggregated health band are displayed based on the active snapshot.
* **Evidence Route/Component:** `src/features/financial-health/FinancialHealthPage.tsx`
* **Possible Failure Mode:** Run incomplete or local mode fallback active.
* **Fallback Message:** "Local/Fallback Mode (Non-Persisted)" tag visible on badge.
* **Readiness Verdict:** PASS

### 5. Review Advisory/Credit Readiness
* **Expected User Action:** User opens Credit Readiness and Advisory Blueprint pages.
* **Expected System Behavior:** Shows credit driver indicators, eligible invoice totals (context-only), and an advisory readiness brief.
* **Evidence Route/Component:** `src/features/credit-readiness/CreditReadinessPage.tsx`, `src/features/advisory-blueprint/AdvisoryBlueprintPage.tsx`
* **Possible Failure Mode:** Synthetic/sample data not clearly identified.
* **Fallback Message:** "Context-only financing readiness brief based on sample financial analysis."
* **Readiness Verdict:** PASS

### 6. Generate Report Job
* **Expected User Action:** User navigates to Reports and clicks "Generate report job".
* **Expected System Behavior:** API triggers a background report generation job and adds it to the job list in a `pending` or `running` state.
* **Evidence Route/Component:** `src/features/reports/ReportsPage.tsx`, `backend/app/routes/jobs.py`
* **Possible Failure Mode:** Job API returns 501 in local persistence mode.
* **Fallback Message:** "Job persistence is not available in current local mode."
* **Readiness Verdict:** PASS

### 7. Run Worker Tick
* **Expected User Action:** User clicks "Run worker tick" to manually advance background job progress.
* **Expected System Behavior:** The backend processes the job queue and returns a tick summary (scanned, processed, succeeded, failed).
* **Evidence Route/Component:** `src/features/reports/api/reportJobsApi.ts`, `backend/app/routes/jobs.py`
* **Possible Failure Mode:** Worker is disabled in the current environment.
* **Fallback Message:** "Report worker is disabled in this environment."
* **Readiness Verdict:** PASS

### 8. Refresh Job List
* **Expected User Action:** User clicks "Refresh jobs".
* **Expected System Behavior:** Application fetches the latest job statuses and updates the list.
* **Evidence Route/Component:** `src/features/reports/ReportsPage.tsx`
* **Possible Failure Mode:** Network timeout or API error.
* **Fallback Message:** "Report jobs are currently unavailable. Please try again."
* **Readiness Verdict:** PASS

### 9. Interpret Job Status/Progress/Failure
* **Expected User Action:** User views the job card.
* **Expected System Behavior:** Job card displays clear status chips (`completed`, `failed`, `running`), progress percentages, and readable timestamps.
* **Evidence Route/Component:** `src/features/reports/ReportsPage.tsx` (StatusChip, normalizeProgressPercent)
* **Possible Failure Mode:** Job fails due to generation error.
* **Fallback Message:** "Failure details: [Error Message]" rendered inline.
* **Readiness Verdict:** PASS

### 10. Explain Result and Limitations
* **Expected User Action:** User reviews the completed workspace report.
* **Expected System Behavior:** Product clearly disclaims that the report is for context and advisory support, requiring bank review.
* **Evidence Route/Component:** `src/features/reports/ReportsPage.tsx`
* **Possible Failure Mode:** User mistakenly treats output as a binding approval.
* **Fallback Message:** "Important Disclaimer: This workspace report is prepared automatically for analysis and diagnostic preparation support only. It does not constitute credit approval..."
* **Readiness Verdict:** PASS

---

## UX Risks

* **Unclear disabled worker:** The worker tick can silently do nothing if disabled, which might confuse the user. *Mitigation:* The worker tick summary explicitly warns "Report worker is disabled in this environment."
* **Job persistence unavailable:** If running in local mode, creating jobs will fail. *Mitigation:* The UI intercepts 501 errors and displays an expected "Job persistence is not available in current local mode" notice rather than a crash or red error toast.
* **Missing workspace:** Attempting actions without selecting a workspace can lead to unpredictable UI states. *Mitigation:* Explicit guardrails "Select a workspace to begin analysis."
* **Failed report job:** If a report fails to generate asynchronously. *Mitigation:* The Reports page natively supports failure detail rendering.
* **Local mode fallback:** Users might think they are operating against production persistence. *Mitigation:* Badges dynamically update to "Local/Fallback Mode (Non-Persisted)".
* **RBAC forbidden action:** Users executing privileged actions. *Mitigation:* The backend returns 403, and the UI gracefully handles the denial.
* **Synthetic data disclaimer:** Demo data might be confused with real data. *Mitigation:* Disclaimers explicitly label the active data as sample or context-only, avoiding terms like "demo" to maintain a serious product tone.

---

## Recommended Polish Items

### Must Fix Now
* Remove any residual "demo" phrasing in user-facing UI labels and tooltips to ensure the product reads as a serious MVP.
* Convert "Demo Mode" to "Local/Fallback Mode".
* Replace "Demo Financial Analysis" with "Sample Financial Analysis".

### Nice to Have Later
* Implement WebSocket/SSE for live job progress updates, removing the need for manual "Refresh jobs" clicks.
* Add an explicit visual banner indicating when local mode is active globally.

### Deferred
* Implement full asynchronous PDF generation in the background job queue (currently PDF export relies on browser printing of the report page).
* Real-time automated worker orchestration for local development without relying on manual ticks.
