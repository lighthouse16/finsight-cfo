# Agent: Financial Model, Credit Risk & Stress Hardening

Worktree:
D:\projects\finsight-cfo-v3-agent-risk

Branch:
release/financial-risk-hardening

Mission:
Make financial analysis and advisory credible, explainable, safe, and parameterized for real public use.

Tasks:
1. Audit financial services:
   - integrity checks
   - ratio engine
   - risk diagnostics
   - projection engine
   - valuation engine
   - PD engine
   - unified risk score
   - stress testing
   - facility structuring

2. Add model metadata to outputs:
   - model_version
   - assumptions
   - data_quality
   - limitations
   - confidence_band

3. Credit score transparency:
   - expose sub-scores:
     - coverage
     - leverage
     - liquidity
     - profitability
     - cash flow
     - receivables quality
   - map to planning tier only.
   - do not call it formal credit rating.

4. PD engine:
   - keep deterministic/logistic-style proxy if there is no training data.
   - label as “indicative PD proxy”.
   - add clear limitation: not calibrated to historical default data.
   - create interface/stub for future calibrated model.

5. Stress testing:
   - add parameterized backend endpoint for:
     - HIBOR shock bps
     - DSO days shock
     - input cost shock %
     - FX shock %
   - keep +150 bps HIBOR as default scenario.
   - validate parameter boundaries.

6. Facility structuring:
   - expose constraints:
     - LTV cap
     - DSCR floor
     - facility max
     - indicative pricing
     - source/provenance
   - call output “candidate structure”, not approval.

7. Valuation:
   - ensure sensitivity grid is exportable as JSON.
   - flag if terminal value dominates enterprise value.
   - flag invalid terminal growth >= WACC.

8. Forbidden wording scan:
   - no guaranteed approval
   - no approved loan
   - no formal underwriting
   - no guaranteed funding

9. Tests:
   - divide-by-zero
   - negative EBITDA
   - missing data
   - DSCR below thresholds
   - terminal growth >= WACC invalid
   - stress parameter boundaries
   - no forbidden wording

10. Docs:
   - create/update docs/product/FINANCIAL_MODEL_GUARDRAILS.md

Validation:
cd D:\projects\finsight-cfo-v3-agent-risk\backend
$env:PYTHONPATH="."
python -m pytest tests -q

cd D:\projects\finsight-cfo-v3-agent-risk
npm install --legacy-peer-deps
npm run lint
npm run build

Commit:
git add .
git commit -m "feat: harden financial risk models and stress scenarios"
git push -u origin release/financial-risk-hardening

PR and merge:
$env:GITHUB_TOKEN=''
gh pr create --base main --head release/financial-risk-hardening --title "Harden financial risk models and stress scenarios" --body "## Summary
Hardens financial model outputs, advisory risk metadata, stress scenarios, and safety wording.

## Validation
- Backend tests passed
- Frontend lint passed
- Frontend build passed

## Release note
This remains indicative planning support, not formal bank underwriting."

$prNumber = gh pr view release/financial-risk-hardening --json number --jq ".number"
gh pr checks $prNumber --watch
gh pr merge $prNumber --auto --squash

If auto-merge is blocked, report the exact blocker. Do not bypass failed checks or required review.
