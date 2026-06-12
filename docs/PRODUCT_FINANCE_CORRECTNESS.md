# FinSight CFO Product Finance Correctness Review

This document provides a banking-grade audit of the financial logic, formulas, risk engines, and valuation methods implemented in the **FinSight CFO** platform. 

---

## Executive Verdict

Following a comprehensive code and system audit of the active FinSight CFO codebase, the following categories have been established for the financial rules:

### Correctly Implemented Finance Rules
The following calculations conform to standard corporate finance and accounting principles and match their intended formulas exactly:
- **Total Debt & Net Debt** (Excludes accounts payable and accrued liabilities as per standard practices).
- **Liquidity Metrics** (Current Ratio, Quick Ratio).
- **Coverage Metrics** (Interest Coverage, DSCR with CADS adjustments).
- **Receivables Analysis** (DSO, Working Capital Gap, Receivables Risk Bands, and Expected Credit Loss AR).
- **Altman Z'' Distress Check** (Tailored for non-manufacturing/service private firms).
- **Projections** (Driver-based 5-year growth/margin fades and Free Cash Flow to Firm (FCFF)).
- **Valuation Bridge** (WACC CAPM build-up, Hamada beta adjustments, DCF Gordon Growth, EV-to-Equity Bridge, EV/EBITDA multiples, and TV concentration checks).
- **Hard-Gate Precheck** (Deterministic rule-based advisory gates).
- **Unified Risk Score** (Composite, factor-weighted readiness index).

### Assumptions-Based Models
These components are mathematically correct but rely on default assumptions and proxy data rather than verified market transactions:
- **WACC Weights**: Uses book-value weights as a proxy for market-value weights (standard for private SMEs but a simplifying assumption).
- **Beta Obsolescence & Fallbacks**: Observed beta default of 1.10 and size/risk premiums are static baseline fixtures.
- **Valuation Opinions**: These are assumptions-based planning context only and do not constitute formal appraisal or investment banking opinions.

### Partial & Deferred Implementations
The following features are designed but not yet fully backed by live external data or calibrated statistical models:
- **Unified Risk Score Calibration**: This is a rule-based advisory readiness score, NOT a statistically calibrated Probability of Default (PD) or default model.
- **CDI / Alternative Data**: CDI, CCRA, and alternative data structures are stubbed/represented as checklist constraints; there is no live integration with external credit bureaus.
- **Stress-Testing Scenarios**: Scenarios apply deterministic shifts (e.g., +1.5% interest rate shock, +15 days DSO lag, +3% COGS inflation, +2% FX cost) but lack dynamic macro-stress calibration.
- **Facility Structuring Optimization**: Limits and pricing spreads are estimates derived from simple baseline multipliers and debt service headroom, not dynamic multi-tranche loan structuring optimization.

### Safety Warning & Product Positioning
> [!IMPORTANT]
> **Safety Guard**: Under no circumstances should the outputs of this tool be positioned as automated credit approval, underwriting decisions, or guaranteed funding. All reports and insights are context-only advisory briefings designed to support RM (Relationship Manager) or CFO planning.

---

## Finance Rule Audit

### 1. Total Debt
- **Product Purpose**: Measures the firm's total interest-bearing debt obligations.
- **Formula**:
  $$\text{Total Debt} = \text{Short-Term Debt} + \text{Current Portion of LTD} + \text{Long-Term Debt} + \text{Lease Liabilities}$$
  *Note: Accounts payable and accrued liabilities are excluded.*
- **Implementation File/Function**: [ratio_engine.py:calculate_total_debt](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L4-L14)
- **Test Evidence**: [test_financials.py:test_total_debt_excludes_ap_and_accrued](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L35-L43)
- **Correctness Verdict**: **Correct**
- **Limitation**: Depends on correct accounting categorization in the balance sheet inputs.
- **Required Future Improvement**: Implement automated chart of accounts classification to map custom ledger names to standard debt codes.

### 2. Net Debt
- **Product Purpose**: Represents the net interest-bearing debt after offsetting liquid cash reserves.
- **Formula**:
  $$\text{Net Debt} = \text{Total Debt} - \text{Cash}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_net_debt](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L16-L18)
- **Test Evidence**: [test_financials.py:test_net_debt_calculation](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L45-L46)
- **Correctness Verdict**: **Correct**
- **Limitation**: Treats all cash on the balance sheet as unrestricted and available.
- **Required Future Improvement**: Exclude restricted cash or minimum operating cash requirements from the offset.

### 3. Current Ratio
- **Product Purpose**: Measures the firm's ability to cover short-term obligations with short-term assets.
- **Formula**:
  $$\text{Current Ratio} = \frac{\text{Current Assets}}{\text{Current Liabilities}}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L52-L63)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Division by zero is protected (returns `None` and raises a warning).
- **Required Future Improvement**: None required; standard ratio.

### 4. Quick Ratio
- **Product Purpose**: Provides a stricter measure of liquidity by excluding less liquid current assets (inventory and prepaid expenses).
- **Formula**:
  $$\text{Quick Ratio} = \frac{\text{Current Assets} - \text{Inventory} - \text{Prepaid Expenses}}{\text{Current Liabilities}}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L65-L76)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Assumes prepaid expenses are fully illiquid.
- **Required Future Improvement**: None; standard calculation.

### 5. Interest Coverage
- **Product Purpose**: Measures the headroom of earnings relative to interest obligations.
- **Formula**:
  $$\text{Interest Coverage} = \frac{\text{EBIT}}{\text{Interest Expense}}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L78-L89)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Ignores principal repayments and non-operating interest.
- **Required Future Improvement**: Exclude non-cash adjustments from EBIT to capture true cash interest coverage.

### 6. DSCR (Debt Service Coverage Ratio)
- **Product Purpose**: Assesses the firm's cash availability relative to contractual debt payments.
- **Formula**:
  $$\text{DSCR} = \frac{\text{CADS}}{\text{Total Debt Service}}$$
  $$\text{CADS} = \text{EBITDA} - \text{Taxes} - \text{Unfinanced CapEx} - \text{Distributions}$$
  $$\text{Total Debt Service} = \text{Scheduled Interest} + \text{Scheduled Principal}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L91-L111)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Clamps unfinanced CapEx to a minimum of 0.0 (cannot be negative).
- **Required Future Improvement**: Support granular input distinguishing financed vs. unfinanced CapEx rather than treating total CapEx as the proxy.

### 7. Debt Ratio
- **Product Purpose**: Measures the proportion of the firm's assets financed through debt.
- **Formula**:
  $$\text{Debt Ratio} = \frac{\text{Total Debt}}{\text{Total Assets}}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L113-L124)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Uses book value of assets.
- **Required Future Improvement**: Incorporate market value of assets when available.

### 8. Net Debt / EBITDA
- **Product Purpose**: Estimates the number of years required to pay off net debt using operating cash flows.
- **Formula**:
  $$\text{Net Debt / EBITDA} = \frac{\text{Net Debt}}{\text{EBITDA}}$$
  *Note: Undefined if EBITDA $\le$ 0.*
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L126-L137)
- **Test Evidence**: [test_financials.py:test_negative_ebitda_and_missing_aging_handling](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L140-L161)
- **Correctness Verdict**: **Correct**
- **Limitation**: Highly sensitive to short-term EBITDA fluctuations.
- **Required Future Improvement**: Support trailing twelve months (TTM) EBITDA to smooth seasonality.

### 9. DSO (Days Sales Outstanding)
- **Product Purpose**: Measures the average time (in days) the firm takes to collect accounts receivable.
- **Formula**:
  $$\text{DSO} = \frac{\text{Accounts Receivable}}{\text{Revenue}} \times \text{Period Days}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L139-L151)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Uses a keyword search heuristic in the `reporting_period` string (e.g., "q" $\rightarrow$ 90 days, "month" $\rightarrow$ 30 days, "6m" $\rightarrow$ 180 days, default $\rightarrow$ 365 days) to determine `Period Days`.
- **Required Future Improvement**: Expose explicit integer fields for days in the period to avoid string parsing.

### 10. Working Capital Gap
- **Product Purpose**: Quantifies the net short-term funding requirement for operational cycles.
- **Formula**:
  $$\text{Working Capital Gap} = \text{Accounts Receivable} + \text{Inventory} + \text{Prepaid Expenses} - \text{Accounts Payable} - \text{Accrued Liabilities}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L153-L158)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Reflects a static point-in-time calculation.
- **Required Future Improvement**: Analyze seasonal working capital gaps over a rolling 12-month series.

### 11. Expected Credit Loss AR
- **Product Purpose**: Estimates potential credit losses on accounts receivable using age bucket provisions.
- **Formula**:
  $$\text{ECL AR} = 0.5\% \times \text{Current}_{0\text{-}30} + 2\% \times \text{Days}_{31\text{-}60} + 8\% \times \text{Days}_{61\text{-}90} + 25\% \times \text{Days}_{90+}$$
- **Implementation File/Function**: [ratio_engine.py:calculate_ratios](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/ratio_engine.py#L160-L178)
- **Test Evidence**: [test_financials.py:test_ratio_calculations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L59-L98)
- **Correctness Verdict**: **Correct**
- **Limitation**: Uses static generic provisions.
- **Required Future Improvement**: Support client-specific historical default matrices or industry benchmarks.

### 12. Altman Z''
- **Product Purpose**: Predicts distress probability tailored for private service and non-manufacturing firms.
- **Formula**:
  $$Z'' = 6.56 \times X_1 + 3.26 \times X_2 + 6.72 \times X_3 + 1.05 \times X_4$$
  $$X_1 = \frac{\text{Working Capital}}{\text{Total Assets}}$$
  $$X_2 = \frac{\text{Retained Earnings}}{\text{Total Assets}}$$
  $$X_3 = \frac{\text{EBIT}}{\text{Total Assets}}$$
  $$X_4 = \frac{\text{Equity}}{\text{Total Liabilities}}$$
- **Implementation File/Function**: [risk_diagnostics.py:calculate_altman_z_service](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/risk_diagnostics.py#L8-L90)
- **Test Evidence**: [test_financials.py:test_altman_z_service_calculation](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L192-L201)
- **Correctness Verdict**: **Correct**
- **Limitation**: Requires retained earnings input (calculated Z'' returns `None` with warnings if missing).
- **Required Future Improvement**: Provide alternative distress indicators (e.g. springate or ohson O-score) when retained earnings are unavailable.

### 13. Receivables Risk Bands
- **Product Purpose**: Groups collections risk into low, moderate, or elevated bands.
- **Threshold**:
  - **Elevated**: 90+ Day concentration $> 15\%$ OR ECL Ratio $> 5\%$
  - **Moderate**: 90+ Day concentration $> 5\%$ OR ECL Ratio $> 2\%$
  - **Low**: Otherwise
- **Implementation File/Function**: [risk_diagnostics.py:calculate_receivables_risk](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/risk_diagnostics.py#L141-L148)
- **Test Evidence**: [test_financials.py:test_receivables_risk_elevated_zone](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L234-L240)
- **Correctness Verdict**: **Correct**
- **Limitation**: Group boundaries are deterministic advisory rules, not statistically modeled risks.
- **Required Future Improvement**: None required; suitable for risk classification.

### 14. Projection / FCFF
- **Product Purpose**: Generates a 5-year driver-based operating forecast and computes Free Cash Flow to Firm (FCFF).
- **Formula**:
  $$\text{FCFF} = \text{EBIT} \times (1 - \tau) + \text{D\&A} - \text{CapEx} - \Delta\text{NWC}$$
  *Note: Revenue growth fades linearly from start growth rate to terminal growth rate.*
- **Implementation File/Function**: [projection_engine.py:calculate_projection](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/projection_engine.py#L57-L173)
- **Test Evidence**: [test_financials.py:test_fcff_formulas_and_variance](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_financials.py#L274-L298)
- **Correctness Verdict**: **Correct**
- **Limitation**: Uses historical snapshot drivers as defaults.
- **Required Future Improvement**: Expose scenario growth selectors in the UI to let RMs run multi-scenario forecasts.

### 15. WACC (Weighted Average Cost of Capital)
- **Product Purpose**: Estimates the company's blended cost of capital for discounting cash flows.
- **Formula**:
  $$\text{WACC} = W_e \times K_e + W_d \times K_d \times (1 - \tau)$$
- **Implementation File/Function**: [valuation_engine.py:calculate_wacc](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L141-L221)
- **Test Evidence**: Checked as part of WACC & DCF validations.
- **Correctness Verdict**: **Correct**
- **Limitation**: Uses book-value weights as a proxy for market-value weights.
- **Required Future Improvement**: Support market-value weights overrides.

### 16. CAPM / Cost of Equity
- **Product Purpose**: Estimates the equity cost of capital using an extended Capital Asset Pricing Model.
- **Formula**:
  $$K_e = R_f + \beta_L \times \text{ERP} + \text{Size Premium} + \text{Industry Risk Premium} + \text{Company-Specific Premium}$$
  *Note: $\beta_L$ is Hamada relevered beta.*
- **Implementation File/Function**: [valuation_engine.py:calculate_cost_of_equity](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L67-L78)
- **Test Evidence**: Verified in beta tests.
- **Correctness Verdict**: **Correct**
- **Limitation**: Observed beta and premiums are fixed baseline constants (e.g. Rf=4%, observed beta=1.1, ERP=5.5%).
- **Required Future Improvement**: Connect to a live market feed (e.g., Bloomberg, HKMA) to update risk-free rates and beta coefficients.

### 17. After-Tax Cost of Debt
- **Product Purpose**: Measures the net interest cost of borrowing.
- **Formula**:
  $$K_d \times (1 - \tau)$$
  *Note: Pre-tax cost of debt ($K_d$) is derived as $\frac{\text{Interest Expense}}{\text{Total Debt}}$ (capped to 50%) or falls back to $6.5\%$.*
- **Implementation File/Function**: [valuation_engine.py:calculate_after_tax_cost_of_debt](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L80-L82)
- **Test Evidence**: Verified in WACC test calculations.
- **Correctness Verdict**: **Correct**
- **Limitation**: Relies on a static tax rate.
- **Required Future Improvement**: Support progressive/multi-tier tax rates.

### 18. DCF
- **Product Purpose**: Valutes the enterprise value by discounting explicit cash flows.
- **Formula**:
  $$\text{Enterprise Value} = \sum_{t=1}^{n} \frac{\text{FCFF}_t}{(1 + \text{WACC})^t} + \frac{\text{Terminal Value}}{(1 + \text{WACC})^n}$$
- **Implementation File/Function**: [valuation_engine.py:calculate_dcf](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L227-L384)
- **Test Evidence**: Covered under unit tests.
- **Correctness Verdict**: **Correct**
- **Limitation**: High dependency on baseline assumptions.
- **Required Future Improvement**: Expose sensitivity parameter adjustment in the UI.

### 19. Gordon Growth Terminal Value
- **Product Purpose**: Computes the perpetual terminal value of the firm's cash flows.
- **Formula**:
  $$\text{Terminal Value} = \frac{\text{FCFF}_n \times (1 + g)}{\text{WACC} - g}$$
  *Note: Returns `None` with warnings if $\text{WACC} \le g$.*
- **Implementation File/Function**: [valuation_engine.py:calculate_dcf](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L322-L327)
- **Test Evidence**: Covered under unit tests.
- **Correctness Verdict**: **Correct**
- **Limitation**: Assumes a constant long-term growth rate.
- **Required Future Improvement**: Compare with exit multiple methods for terminal value validation.

### 20. EV / Equity Bridge
- **Product Purpose**: Connects enterprise value to equity value.
- **Formula**:
  $$\text{Equity Value} = \text{Enterprise Value} - \text{Net Debt}$$
- **Implementation File/Function**: [valuation_engine.py:calculate_dcf](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L329)
- **Test Evidence**: Covered under unit tests.
- **Correctness Verdict**: **Correct**
- **Limitation**: Negative equity value is handled by printing warnings.
- **Required Future Improvement**: Exclude non-controlling interests if group structures are modeled.

### 21. EV/EBITDA Sanity Checks
- **Product Purpose**: Validates whether the implied EV/EBITDA multiple is reasonable.
- **Threshold**: Standard range is $3\text{x}$ to $15\text{x}$. Returns warning status if outside.
- **Implementation File/Function**: [valuation_engine.py:run_valuation_sanity_checks](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L457-L480)
- **Test Evidence**: Covered under sanity checks tests.
- **Correctness Verdict**: **Correct**
- **Limitation**: Basic thresholds only.
- **Required Future Improvement**: Support sector-specific sanity boundaries.

### 22. Terminal Value Concentration
- **Product Purpose**: Measures the percentage of enterprise value represented by the terminal value.
- **Threshold**: Raises warnings if TV Concentration exceeds $85\%$.
- **Implementation File/Function**: [valuation_engine.py:run_valuation_sanity_checks](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/financials/valuation_engine.py#L414-L437)
- **Test Evidence**: Covered under sanity checks tests.
- **Correctness Verdict**: **Correct**
- **Limitation**: Advisory warning boundary only.
- **Required Future Improvement**: Detail TV concentration clearly in reports.

### 23. Hard-Gate Precheck
- **Product Purpose**: Consolidates balance sheet identity, DSCR, liquidity, leverage, receivables, and distress indicators to determine advisor workflow readiness.
- **Threshold**:
  - **Fail**: Any high-severity check fails (e.g. DSCR $< 1.0$, BS identity failed).
  - **Watch**: Any medium-severity warnings exist.
  - **Pass**: All checks pass.
- **Implementation File/Function**: [hard_gate_engine.py:build_hard_gate_precheck](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/advisory/hard_gate_engine.py#L6-L435)
- **Test Evidence**: [test_advisory.py:test_build_hard_gate_precheck_variations](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_advisory.py#L66-L102)
- **Correctness Verdict**: **Correct**
- **Limitation**: Basic threshold logic; not a bank decision tool.
- **Required Future Improvement**: Expose customizable thresholds for different bank products.

### 24. Unified Risk Score
- **Product Purpose**: Provides a composite readiness indicator (scale of 0–100) using financial and operational factors.
- **Formula**:
  $$\text{Base Score} = 100$$
  Minus penalties:
  - **Debt Service**: Strong (0), Adequate (-8), Watch (-15), Constrained (-30).
  - **Liquidity**: Strong (0), Adequate (-5), Watch (-12), Constrained (-22).
  - **Leverage**: Strong (0), Adequate (-5), Watch (-12), Constrained (-20).
  - **Receivables**: Strong (0), Adequate (-3), Watch (-10), Constrained (-18).
  - **Valuation**: Strong (0), Adequate (0), Watch (-8), Constrained (-15).
  - **Hard-Gate**: Pass (0), Watch (-10), Fail (-20).
  - **Data Integrity**: Pass (0), Fail (-25).
- **Implementation File/Function**: [risk_score_engine.py:build_unified_risk_score](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/app/services/advisory/risk_score_engine.py#L11-L336)
- **Test Evidence**: [test_advisory.py:test_build_unified_risk_score_impact](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/audit-finance-rule-correctness/backend/tests/test_advisory.py#L172-L192)
- **Correctness Verdict**: **Correct**
- **Limitation**: Not a calibrated default model.
- **Required Future Improvement**: Accumulate default statistics to train a machine-learning PD model.
