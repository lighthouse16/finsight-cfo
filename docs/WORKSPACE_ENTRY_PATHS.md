# Workspace Entry Paths

This document explains the workspace entry flow in FinSight CFO, outlining the two explicit paths available to users upon entering the application: **Start from scratch** and **Explore with mock data**.

---

## The Choice Screen

When a user launches the application and no active workspace is selected, they are directed to the `/create-workspace` page. Here, they must choose between two distinct options:

```
+-----------------------------------------------------------------------------------+
|                               Welcome to FinSight CFO                             |
|                                                                                   |
|        +----------------------------------+ +----------------------------------+  |
|        |       Start from scratch         | |     Explore with mock data       |  |
|        |                                  | |                                  |  |
|        | Create a clean workspace and     | | Use synthetic sample data to     |  |
|        | upload your own company records. | | review the full product flow.    |  |
|        |                                  | |                                  |  |
|        | [ Create company workspace ]     | | [ Open sample company ]          |  |
|        +----------------------------------+ +----------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 1. Start from Scratch

The **Start from scratch** flow is designed for real customers and financial advisors who wish to analyze a new, clean company workspace.

### Key Characteristics:
- **Zero Sample Data:** The workspace is initialized completely empty.
- **Manual Document Ingestion:** The user must navigate to the **Data Room** to upload their own financial statements (Balance Sheet, Profit & Loss, Cash Flow Statement, Debt Schedule, and Receivables Aging).
- **Clean Compilation:** After files are uploaded, the application parses them, compiles an active financial snapshot, and triggers the required analysis pipelines.

### How to use this path:
1. Click **Create company workspace**.
2. Complete the workspace form (Company Name, Industry, Region, Currency, and Reporting Period).
3. Click **Create company workspace** to submit.
4. Navigate to the **Data Room** to upload company CSV/PDF records.

---

## 2. Explore with Mock Data

The **Explore with mock data** flow is designed for judges, stakeholders, and reviewers to evaluate the entire product journey in a single click.

### Key Characteristics:
- **Canonical Workspace:** Loads a pre-configured, read-only demo workspace named `workspace_sample_novus`.
- **Sample Company:** Represents the fictional entity **Novus Retail Solutions Ltd**.
- **Instant Readiness:** Calls the `/api/workspaces/reset-sample` API, which automatically copies 5 core CSV statements into the workspace, builds the snapshot, and triggers the background analysis queue.
- **Zero-Wait Evaluation:** Pre-computes all financial health indicators, credit scores, macro flags, and channel comparisons, meaning reviewers do not need to manually upload records or wait for run queues.

### How to use this path:
1. Click **Open sample company**.
2. The system resets the workspace and redirects you directly to the **Overview** dashboard.

---

## Synthetic Data Framing & Terminology

To maintain professional framing and manage expectations, the application adheres to strict nomenclature rules:

- **Lobbying Labels:** Always label demo data as **"Synthetic Demo Data"** or **"Sample company: Novus Retail Solutions Ltd"**.
- **Avoiding Ambiguity:** Never imply that demo data is real customer data or real bank-approved data.
- **Diagnostic Boundaries:** Terminology refers to "assessing readiness" and "advisory diagnostics". We explicitly avoid terms like "fake data", "bank approved", or "underwriting decision".
- **Disclaimers:** Highly visible badges and chips appear on the **Top Command Bar**, **Overview Page**, **AI CFO**, and **Reports** when the demo workspace is active to reinforce that the results are synthetic.
