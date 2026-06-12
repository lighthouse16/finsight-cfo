# User Journey Smoke Test

Use this checklist to verify the workspace-first SaaS journey end to end.

## Preconditions

- Frontend dependencies are installed.
- Backend API is running and reachable by the Vite app.
- Test user/session can access the platform routes.
- No `.env` files created for validation are staged.

## 1. Open app with no workspace

1. Clear or use a test account with no company workspaces.
2. Open the app and sign in if required.
3. Navigate to the platform area.

Expected result:

- The platform shell does not show a blank dashboard.
- The user is routed/gated into the company workspace creation experience.
- No implicit default workspace is auto-created by the top command bar.

## 2. Create company workspace

1. Enter a company name.
2. Select currency and reporting period.
3. Optionally select industry and region.
4. Submit the form.

Expected result:

- The frontend calls `POST /api/workspaces` using `FormData`.
- `companyName`, `currency`, and `reportingPeriod` are sent as form fields.
- Optional industry and region are sent as metadata fields.
- The new workspace becomes the active workspace.
- The user lands on the workspace overview.

## 3. Verify workspace dashboard checklist

1. Open the Overview page for the new workspace.
2. Inspect the Workspace Journey checklist.

Expected result:

- The checklist is visible near the top of the overview.
- Upload documents is the first clear next step.
- Snapshot and analysis steps are blocked or ready based on actual workspace state.
- Blocked steps explain the prerequisite instead of failing silently.

## 4. Verify Data Room CTA

1. From the Workspace Journey checklist, select the Data Room CTA.

Expected result:

- The CTA navigates to the Data Room route.
- The active workspace remains selected.
- The user can proceed to upload workspace documents.

## 5. Verify valuation blocked state before active snapshot

1. Use a workspace with no active financial snapshot.
2. Return to Overview.
3. Inspect the valuation step in the checklist.
4. Navigate directly to the Valuation route if needed.

Expected result:

- Valuation is not presented as ready when no active snapshot exists.
- The checklist explains that a financial snapshot is required first.
- The route should show an insufficient-data/empty state rather than invented valuation output.

## 6. Verify AI CFO/provider-not-configured messaging

1. Use an environment where AI/provider configuration is unavailable or disabled.
2. Navigate to AI CFO.

Expected result:

- The UI communicates provider/configuration unavailability clearly.
- The product does not imply AI analysis is available when provider keys are missing.
- Messaging uses user-facing language such as provider not configured, source pending, or company records required.

## 7. Verify demo sample workspace labeling

1. Return to the no-workspace onboarding flow or use the Load Sample Company action.
2. Load the sample/demo workspace.
3. Open Overview.

Expected result:

- The active workspace is the sample workspace, `workspace_sample_novus`.
- Overview displays a visible Demo Workspace badge.
- Demo/sample data is labeled synthetic/demo and distinguishable from real company data.

## 8. Cleanup

- Remove any temporary `.env` or `backend/.env` files copied only for compose validation.
- Confirm `node_modules`, `dist`, `.env`, `backend/.env`, and log files are not staged.
- Run `git status --short` before committing.
