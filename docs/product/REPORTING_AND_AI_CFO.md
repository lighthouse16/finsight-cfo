# Reporting and AI CFO Export

This document explains the unified workflow for generating advisor-ready reports and AI CFO context.

## Report Generation Flow

The system supports two parallel patterns for generating reports:

1. **Background Report Jobs (Legacy)**
   - Triggered via `POST /api/workspaces/{workspace_id}/jobs/report-generation`
   - Uses an async worker approach to compile and persist reports
   - Results are available asynchronously when the `report-worker` ticks

2. **Synchronous Advisor-Ready Report Compile (New)**
   - Triggered via `POST /api/advisory/report`
   - Immediately compiles a typed `AdvisorReadyReportPayload` incorporating financial health, valuation, market context, stress testing, and the advisory blueprint.
   - Saves the report to the same backend persistence layer used by jobs
   - Available directly in the Reports UI under the "Generate Advisor-Ready Report" action

## AI CFO Citation Behavior

AI CFO generates contextual insights using a "bounded RAG" approach:
- Retrieves structured workspace data (ratios, health score, valuation).
- Retrieves unstructured document excerpts from the workspace document index.
- Excerpts are formatted into a prompt and submitted to the language model.
- Includes backward-compatible metadata (`chunk_index`, `relevance_score`, `source_mode`) for granular traceability.
- Citations are explicitly mapped and returned in `AdvisoryChatResponse.sources`.

## Workspace-Scoped Retrieval

Both the AI CFO and the advisor report rely strictly on the active workspace:
- Financial context is derived strictly from `FinancialAnalysisResponse`.
- RAG excerpts are strictly scoped to `workspace_id`.
- The `ai_provider.py` enforces safety guidelines via a `SAFETY_SYSTEM_PROMPT` to restrict knowledge external to the provided workspace context.

## Export Path

Advisor-ready reports are rendered in a dedicated UI view within the Reports page. This view includes:
- A prominent summary of the sections and data quality.
- The compiled AI CFO notes, fully cited with chunk-level metadata.
- A "Save as PDF" browser print-friendly style.

## Limitations & Release Notes

**These reports are planning/advisory artifacts only.**
- They **do not** constitute a formal credit approval.
- They **do not** represent a lending commitment.
- They **do not** perform formal underwriting.
- All outputs require Relationship Manager (RM) and BOCHK credit officer review.
- The AI modes range from `deterministic_fallback` (no provider configured) to active LLM inference (`openai`, `google_ai`, etc.). The UI indicates the active mode to ensure transparency.
