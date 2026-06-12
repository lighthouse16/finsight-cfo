# Workspace-First User Journey

This branch moves FinSight CFO toward a workspace-first SaaS journey:

```text
Landing / login
→ Create company workspace
→ Workspace dashboard
→ Upload documents
→ Build / review snapshot
→ Run analysis
→ Market and funding views
→ AI CFO
→ Export advisor report
```

## Workspace creation

The private platform shell now loads workspace state before rendering the main app chrome.

- If the user has no workspaces, the shell renders the workspace creation screen.
- The creation screen posts to the existing backend workspace API via `FormData`.
- Required workspace fields are sent as:
  - `companyName`
  - `currency`
  - `reportingPeriod`
- Optional onboarding details are sent as metadata fields:
  - `metadata[industry]`
  - `metadata[region]`

## Active workspace state

Workspace state is centralized in `src/context/workspaceContext.tsx`.

The context owns:

- workspace list loading
- active workspace selection
- workspace creation
- workspace refresh
- backend config loading

The active workspace ID remains persisted in `localStorage.active_workspace_id` for compatibility with existing route modules.

For legacy components, the provider dispatches the existing `workspaceChanged` browser event when the active workspace changes.

## Dashboard journey checklist

The overview page now includes a workspace journey checklist that gives users clear next steps.

The checklist reflects whether the current workspace has:

- uploaded financial files
- an active financial snapshot
- completed analysis runs

Blocked steps explain the dependency, such as uploading files before building a snapshot.

## Demo workspace behavior

The onboarding page includes a demo loader that calls:

```http
POST /api/workspaces/reset-sample
```

After loading the sample data, the UI selects `workspace_sample_novus` and navigates to the overview.

The overview header labels this sample workspace as **Demo Workspace** so users can distinguish it from their real company workspace.

## Scope boundaries

This work intentionally does not add or change:

- finance calculations
- provider models
- risk rules
- eligibility logic
- lending decisions
- external market assumptions
