# Valuation Page Smoke Test

Use these smoke cases to verify direct-route valuation behavior.

## Preconditions

- Frontend dev server is running.
- Backend API is reachable.
- Browser storage can be cleared between cases.

## Cases

1. **No active workspace**
   - Clear `active_workspace_id` and use an account/org with no selected workspace, or remove the saved id.
   - Visit `/platform/valuation` directly.
   - Expected: the page stops loading and shows **Create a company workspace first** with a workspace CTA.

2. **Workspace with no uploaded files**
   - Select or create a workspace with no Data Room files.
   - Visit `/platform/valuation` directly.
   - Expected: the page stops loading and shows **Upload financial documents before valuation** with an Open Data Room CTA.

3. **Files exist but no active snapshot**
   - Upload one or more workspace files without building/activating the snapshot.
   - Visit `/platform/valuation` directly.
   - Expected: the page stops loading and shows **Review and activate a financial snapshot before valuation** with a Data Room CTA.

4. **Active snapshot but no valuation run**
   - Build/activate a workspace snapshot.
   - Ensure no valuation run exists for the workspace.
   - Visit `/platform/valuation` directly.
   - Expected: the page shows **Run valuation analysis** and a Run Valuation CTA.

5. **Run valuation**
   - Click **Run Valuation**.
   - Expected: the button shows progress, the existing valuation run endpoint is called, and the page reloads valuation state.

6. **Valuation results render**
   - With a completed valuation run available, visit `/platform/valuation` directly.
   - Expected: WACC, DCF bridge, valuation years, sensitivity, sanity checks, metadata badge, and rerun CTA render as before.

7. **API error handling**
   - Temporarily stop the backend or force a failed API response.
   - Visit `/platform/valuation` directly.
   - Expected: the page shows a retryable service error, not an indefinite spinner.

## Regression Checks

- Existing valuation result cards and formatting are unchanged after successful load.
- Rerun Analysis still uses the active workspace and active snapshot context.
- No demo/sample valuation is shown when workspace prerequisites are missing.
