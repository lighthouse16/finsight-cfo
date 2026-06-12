# BOCHK Plan Formula to Code Mapping Reference

This document maps each corporate finance and credit risk formula specified in the BOCHK plan to its corresponding implementation in the **FinSight CFO** codebase.

---

## 1. Accounting Integrity Checks
- **Check 1: Balance Sheet Identity**
  - **Formula**: $\text{Total Assets} = \text{Total Liabilities} + \text{Equity}$
  - **Code Path**: [integrity_checks.py:L14-L34](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/integrity_checks.py#L14-L34)
- **Check 2: Total Debt Definition Confirmation**
  - **Formula**: $\text{Total Debt} \le \text{Total Liabilities}$
  - **Code Path**: [integrity_checks.py:L36-L62](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/integrity_checks.py#L36-L62)
- **Check 3: Current Assets Reconciliation**
  - **Formula**: $\text{Current Assets} = \text{Cash} + \text{Accounts Receivable} + \text{Inventory} + \text{Prepaid}$
  - **Code Path**: [integrity_checks.py:L64-L86](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/integrity_checks.py#L64-L86)
- **Check 4: Total Assets Reconciliation**
  - **Formula**: $\text{Total Assets} = \text{Current Assets} + \text{Net PPE}$
  - **Code Path**: [integrity_checks.py:L88-L108](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/integrity_checks.py#L88-L108)
- **Check 5: Cash Flow Reconciliation**
  - **Formula**: $\text{Net Change in Cash} = \text{CFO} - \text{CapEx} + \text{Debt Issued} - \text{Debt Repaid} - \text{Dividends}$
  - **Code Path**: [integrity_checks.py:L110-L134](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/integrity_checks.py#L110-L134)

---

## 2. Debt Definitions
- **Total Debt**
  - **Formula**: $\text{Total Debt} = \text{Short-Term Debt} + \text{Current Portion of LTD} + \text{Long-Term Debt} + \text{Lease Liabilities}$
  - *Excludes accounts payable and accrued liabilities.*
  - **Code Path**: [ratio_engine.py:calculate_total_debt](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/ratio_engine.py#L4-L14)
- **Net Debt**
  - **Formula**: $\text{Net Debt} = \text{Total Debt} - \text{Cash}$
  - **Code Path**: [ratio_engine.py:calculate_net_debt](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/ratio_engine.py#L16-L18)

---

## 3. Financial Ratios
- **Current Ratio**
  - **Formula**: $\text{Current Ratio} = \frac{\text{Current Assets}}{\text{Current Liabilities}}$
  - **Code Path**: [ratio_engine.py:L52-L63](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/ratio_engine.py#L52-L63)
- **Quick Ratio**
  - **Formula**: $\text{Quick Ratio} = \frac{\text{Current Assets} - \text{Inventory} - \text{Prepaid Expenses}}{\text{Current Liabilities}}$
  - **Code Path**: [ratio_engine.py:L65-L76](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/ratio_engine.py#L65-L76)
- **Interest Coverage**
  - **Formula**: $\text{Interest Coverage} = \frac{\text{EBIT}}{\text{Interest Expense}}$
  - **Code Path**: [ratio_engine.py:L78-L89](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/ratio_engine.py#L78-L89)
- **DSCR (Debt Service Coverage Ratio)**
  - **Formula**: $\text{DSCR} = \frac{\text{CADS}}{\text{Scheduled Interest} + \text{Scheduled Principal}}$
  - **CADS Formula**: $\text{CADS} = \text{EBITDA} - \text{Taxes} - \text{CapEx} - \text{Dividends}$
  - **Code Path**: [ratio_engine.py:L91-L111](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/ratio_engine.py#L91-L111)

---

## 4. Expected Credit Loss (ECL) on Accounts Receivable
- **ECL AR**
  - **Formula**: $\text{ECL AR} = 0.5\% \times \text{Current}_{0\text{-}30} + 2\% \times \text{Days}_{31\text{-}60} + 8\% \times \text{Days}_{61\text{-}90} + 25\% \times \text{Days}_{90+}$
  - **Code Path**: [ratio_engine.py:L160-L178](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/ratio_engine.py#L160-L178)

---

## 5. Altman Z'' Distress Score
- **Z'' Score for Non-Manufacturing / Service Private Firms**
  - **Formula**: $Z'' = 6.56 \times X_1 + 3.26 \times X_2 + 6.72 \times X_3 + 1.05 \times X_4$
  - **Components**:
    - $X_1 = \text{Working Capital} / \text{Total Assets}$
    - $X_2 = \text{Retained Earnings} / \text{Total Assets}$
    - $X_3 = \text{EBIT} / \text{Total Assets}$
    - $X_4 = \text{Book Value of Equity} / \text{Total Liabilities}$
  - **Bands**: Safe ($Z'' > 2.60$), Grey ($1.10 \le Z'' \le 2.60$), Distress ($Z'' < 1.10$).
  - **Code Path**: [risk_diagnostics.py:calculate_altman_z_service](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/risk_diagnostics.py#L8-L90)

---

## 6. Free Cash Flow to Firm (FCFF)
- **Primary FCFF**
  - **Formula**: $\text{FCFF} = \text{EBIT} \times (1 - \tau) + \text{D\&A} - \text{CapEx} - \Delta\text{NWC}$
  - **Code Path**: [projection_engine.py:L140](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/projection_engine.py#L140)
- **FCFF Cross-Check**
  - **Formula**: $\text{FCFF Cross-Check} = \text{CFO Estimate} + \text{Interest} \times (1 - \tau) - \text{CapEx}$
  - **Code Path**: [projection_engine.py:L141](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/projection_engine.py#L141)

---

## 7. Weighted Average Cost of Capital (WACC)
- **WACC**
  - **Formula**: $\text{WACC} = W_e \times K_e + W_d \times K_d \times (1 - \tau)$
  - **Code Path**: [valuation_engine.py:calculate_wacc](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/valuation_engine.py#L141-L221)
- **CAPM Cost of Equity (K_e)**
  - **Formula**: $K_e = R_f + \beta_L \times \text{ERP} + \text{Size Premium} + \text{Industry Risk Premium} + \text{Company-Specific Premium}$
  - **Code Path**: [valuation_engine.py:calculate_cost_of_equity](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/valuation_engine.py#L67-L78)
- **Hamada Beta Unlevering / Relevering**
  - **Unlevered Formula**: $\beta_U = \frac{\beta_{observed}}{1 + (1 - \tau) \times D/E}$
  - **Relevered Formula**: $\beta_L = \beta_U \times [1 + (1 - \tau) \times D_{target}/E_{target}]$
  - **Code Paths**:
    - [calculate_unlevered_beta](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/valuation_engine.py#L34-L47)
    - [calculate_relevered_beta](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/financials/valuation_engine.py#L48-L61)

---

## 8. Calibrated Probability of Default (PD)
- **Logistic Default Probability (PD)**
  - **Formula**:
    $$Z = \beta_0 + \beta_1(\text{DSCR}) + \beta_2(\text{DebtRatio}) + \beta_3(\text{Margin}) + \beta_4(\text{CDI\_Collateral})$$
    $$\text{PD} = \frac{1}{1 + e^{-Z}}$$
  - **Model Training**: Trained dynamically using batch gradient descent optimizer in pure Python if `historical_default_dataset.csv` is uploaded.
  - **Code Path**: [pd_engine.py:calculate_pd](file:///C:/Users/dqmgb/.gemini/antigravity/worktrees/finsight-cfo-v3/bochk-finance-model-completion/backend/app/services/advisory/pd_engine.py#L93-L170)
