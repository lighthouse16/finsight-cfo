# Workspace Entry Paths

FinSight CFO separates onboarding into two explicit entry paths so users and judges can clearly distinguish clean company workspaces from the synthetic sample company.

## Start from scratch

- Label: **Start from scratch**
- Helper text: **Create a clean workspace and upload your own company records.**
- Route: `/platform/create-workspace`
- Creates a new company workspace through `POST /api/workspaces`.
- Does not load or seed demo/sample data.
- The user is expected to upload company financial documents in the Data Room before building a snapshot and running analyses.

## Explore with mock data

- Label: **Explore with mock data**
- Helper text: **Use synthetic sample data to review the full product flow quickly.**
- Canonical sample workspace ID: `workspace_sample_novus`
- Sample company label: **Sample company: Novus Retail Solutions Ltd**
- Uses `POST /api/workspaces/reset-sample` via the shared frontend workspace context helper.
- Selects the sample workspace after reset and routes users into the platform experience.
- Judges should use this mode to quickly evaluate the dashboard, sample snapshot, AI CFO context, and report path without uploading documents.
- What remains synthetic: sample company records, financial snapshot, analysis outputs, AI CFO context, and generated report content.

## Workspace selector behavior

The command bar workspace selector keeps the product paths distinct:

- Shows the active workspace summary at the top.
- Provides explicit action buttons for **Start from scratch** and **Explore with mock data**.
- Groups regular workspaces under **Company workspaces**.
- Groups sample workspaces under **Demo workspace**.
- Deduplicates workspaces by stable ID before rendering.
- Disambiguates duplicate display names using a short workspace ID suffix.

## Demo data labeling

When the sample workspace is active, key product headers surface the badge:

> **Synthetic Demo Data**

This badge appears in the command bar and product surfaces such as Overview, Workspace Journey, AI CFO, and Reports. Copy should avoid terms like "fake" or "test data" and must not imply that demo outputs are real customer data, real approvals, or bank-approved decisions.

## Implementation notes

Shared constants and helpers live in `src/features/data-room/api/dataRoomApi.ts`:

- `SAMPLE_WORKSPACE_ID`
- `SAMPLE_WORKSPACE_NAME`
- `SYNTHETIC_DEMO_BADGE`
- `isDemoWorkspace`
- `dedupeWorkspaces`
- `getWorkspaceDisplayName`
- `resetSampleWorkspace`

Workspace state orchestration lives in `src/context/workspaceContext.tsx`, including `exploreWithMockData()` for the mock-data path.
