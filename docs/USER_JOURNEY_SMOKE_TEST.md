# User Journey Smoke Test

Use this checklist to verify the workspace-first SaaS journey end to end.

## Preconditions

- Frontend dependencies are installed.
- Backend API is running and reachable by the Vite app.
- Test user/session can access the platform routes.
- No `.env` files created for validation are staged.

## 1. Open app with no workspace

1. Clear the active workspace ID from localStorage (`localStorage.removeItem('active_workspace_id')`).
2. Open the app.

Expected result:

- The user is automatically redirected to `/create-workspace`.
- The two-card choice screen ("Start from scratch" and "Explore with mock data") is rendered.
- No default workspace is silently created.

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

1. Clear the active workspace ID and open the app to go to `/create-workspace`.
2. Click **Open sample company** under the **Explore with mock data** card.
3. Verify the redirection to `/platform/overview`.

Expected result:

- The active workspace is set to `workspace_sample_novus`.
- A "Synthetic Demo Data" badge is displayed:
  - In the Top Command Bar next to the workspace selector dropdown.
  - In the Overview page header chip.
  - In the AI CFO page header chip and assistant hero card.
  - In the Reports page header chip and reports package hero card.

## 8. Cleanup

- Remove any temporary `.env` or `backend/.env` files copied only for compose validation.
- Confirm `node_modules`, `dist`, `.env`, `backend/.env`, and log files are not staged.
- Run `git status --short` before committing.
