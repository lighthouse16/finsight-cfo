# FinSight CFO: Demo Runbook

This runbook outlines how to reliably present the FinSight CFO product experience to judges, SME users, and bank stakeholders. It provides step-by-step instructions for running the application, following the core demonstration sequence, handling technical fallbacks, and maintaining appropriate product framing.

---

## 1. Setup & Launch

### Local Run Steps
Run the backend and frontend separately in two terminals from the repository root.

**Backend:**
```bash
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
npm run dev
```

### Docker Run Steps
To run the full stack via containers (recommended for clean environments):
```bash
docker compose up --build -d
```
Access the application at `http://localhost:5173`.
To stop and clean up volumes:
```bash
docker compose down -v
```

---

## 2. Exact Demo Sequence & Expected Screens

**Step 1: Choose Entry Path**
- **Action:** Open `http://localhost:5173`. If no active workspace is selected, you land on the choice screen.
- **Expected Screen:** The Two-Card Choice Screen showing "Start from scratch" and "Explore with mock data" options.
- **Talking Point:** "Welcome to FinSight CFO. When opening the app for the first time, users choose between starting with a clean workspace or exploring the system immediately using synthetic mock data."

**Step 2: Initialize Demo Workspace**
- **Action:** Click **Open sample company** under the **Explore with mock data** card.
- **Expected Screen:** The page loads the canonical demo workspace `workspace_sample_novus` and redirects you to the Overview dashboard, showing a "Synthetic Demo Data" badge.
- **Talking Point:** "By selecting mock data, the platform instantly sets up a pre-configured sample company (Novus Retail Solutions Ltd) with pre-loaded, synthetic statements, meaning we can review the analytics suite without manual upload wait times."

**Step 3: Review Financial Data**
- **Action:** Navigate to the **Data Room**.
- **Expected Screen:** Shows statement checklists, connectivity status, and a validated active financial snapshot.
- **Talking Point:** "The system securely parses uploaded statements or accounting integrations into a unified snapshot. Integrity checks confirm the balance sheet aligns before any analysis occurs."

**Step 4: View Financial Health**
- **Action:** Navigate to **Financial Health**.
- **Expected Screen:** Displays distress index, profitability, and health bands.
- **Talking Point:** "Here we instantly translate raw ledger data into a clear diagnostic of the company's financial resilience and distress indicators."

**Step 5: Review Advisory / Credit Readiness**
- **Action:** Navigate to **Credit Readiness** and **Advisory Blueprint**.
- **Expected Screen:** Shows context-only credit drivers, eligible invoice values, and advisory positioning.
- **Talking Point:** "This is where the magic happens for advisors. It provides context-only insights that help an RM structure the optimal facility or understand credit drivers prior to a formal application."

**Step 6: Generate Report Job & Run Worker Tick**
- **Action:** Navigate to **Reports**, click **Generate report job**, then click **Run worker tick** (if in local mode) and **Refresh jobs**.
- **Expected Screen:** A job appears in the queue, progresses, and completes.
- **Talking Point:** "The platform supports asynchronous background jobs to compile heavy compliance or comprehensive reporting packs without blocking the user."

**Step 7: Explain Result and Limitations**
- **Action:** Show the completed report payload or traceability badge.
- **Expected Screen:** A detailed report summary with an explicit disclaimer.
- **Talking Point:** "Every analysis is cryptographically stamped for traceability. Note that this provides advisory support and context-only readiness; it is not a binding credit decision."

---

## 3. Fallback Paths

If technical issues arise during the presentation, remain calm and use the following fallback explanations:

* **Backend not available:** 
  * *UI state:* Network error toasts or frozen loading states. 
  * *Action:* Check if the backend terminal crashed. Restart `uvicorn`.
* **Job API returns 501:** 
  * *UI state:* Shows "Job persistence is not available in current local mode." 
  * *Action:* Explain: "We are currently running in a local, non-persistent mode for this demo, which disables background task queues."
* **Worker disabled:** 
  * *UI state:* Worker tick summary shows "Report worker is disabled in this environment." 
  * *Action:* Explain: "The background processing daemon is intentionally paused in this environment to manually step through the pipeline."
* **Job fails:** 
  * *UI state:* Job status chip turns red with "Failure details" text. 
  * *Action:* Explain: "The asynchronous job encountered an error during report compilation. In production, this triggers an alert to our support team."
* **RBAC blocks action:** 
  * *UI state:* API returns 403 Forbidden, UI shows an access denied message. 
  * *Action:* Explain: "As expected, my current session does not have the elevated privileges to perform this action."
* **Frontend build issue:** 
  * *UI state:* White screen or Vite overlay error. 
  * *Action:* Hard refresh (`Ctrl+Shift+R`). If it persists, restart the `npm run dev` process.

---

## 4. Do Not Claim Boundaries

To protect the integrity of the product and manage stakeholder expectations, **DO NOT CLAIM** any of the following during the presentation:

* **No loan approval:** Do not state that the system "approves" loans. Use terms like "assesses readiness" or "provides context for review".
* **Not a formal credit decision:** Do not imply the system replaces a bank's underwriting process. The system offers "advisory support" and "diagnostic preparation".
* **No calibrated PD model:** Do not claim the credit scores map to a calibrated Probability of Default (PD) model. It is an indicative scoring framework.
* **No production bank integration yet:** Do not imply that the system is currently pulling live data from or submitting live applications to BOCHK or any other specific banking core systems in production.
