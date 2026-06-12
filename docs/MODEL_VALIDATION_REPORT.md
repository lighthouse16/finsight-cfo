# Credit & Valuation Model Validation Report

This report documents the validation tests, statistical checks, parameters, and safety controls implemented in the **FinSight CFO** financial and risk engines.

---

## 1. Credit Risk & Probability of Default (PD) Engine

### Methodology
The PD Engine implements a logistic regression classification framework:
$$Z = \beta_0 + \beta_1(\text{DSCR}) + \beta_2(\text{DebtRatio}) + \beta_3(\text{Margin}) + \beta_4(\text{CDI\_Collateral})$$
$$\text{PD} = \frac{1}{1 + e^{-Z}}$$

### Model Training & Calibration
- **Dynamic Training**: If `historical_default_dataset.csv` is uploaded, the backend runs an inline gradient descent optimizer for 1000 epochs to calibrate parameters $(\beta_0, \beta_1, \beta_2, \beta_3)$ against historical binary default labels.
- **Calibrated Verification Guard**: To prevent convergence errors or noise fitting, calibrated parameters are validated:
  - $\beta_1$ (DSCR) must be negative (higher DSCR reduces default probability).
  - $\beta_2$ (Debt Ratio) must be positive (higher leverage increases default probability).
  - If signs are incorrect, calibration fails and falls back to safe baseline defaults.
- **Fallback Mode**: If no dataset is found, the status is set to `indicative_readiness_index` with a prominent user disclaimer in the UI.

### Safety Guards
- **Strictly Advisory**: Under no circumstances does the engine issue credit decisions (approval or decline). All copy is limited to "funding readiness" and "risk tiering".

---

## 2. Altman Z'' Score (Private Service Firms Model)

### Methodology
Altman Z'' Score is calculated using the established private services model coefficients:
$$Z'' = 6.56 \times X_1 + 3.26 \times X_2 + 6.72 \times X_3 + 1.05 \times X_4$$

### Threshold Bands & Validation
- **Safe Zone ($Z'' > 2.60$)**: Low distress profile.
- **Grey Zone ($1.10 \le Z'' \le 2.60$)**: Moderate risk; triggers balance-sheet warnings.
- **Distress Zone ($Z'' < 1.10$)**: Elevated distress; triggers a high-severity alert.
- **Data Completeness Guard**: If `retained_earnings` is missing, the calculation returns `None` to prevent misleading indicators.

---

## 3. Valuation & Discounted Cash Flow (DCF) Validation

### WACC CAPM Build-Up
- Cost of Equity ($K_e$) is built using the extended Capital Asset Pricing Model.
- observed beta (1.10) is unlevered and relevered using target weights via the Hamada equation:
  $$\beta_L = \beta_U \times [1 + (1 - \tau) \times D_{target}/E_{target}]$$
- Cost of Debt ($K_d$) is derived from historical statement interest expense divided by total book debt (capped at 50% to prevent outliers), falling back to 6.5% if total debt is zero.

### DCF Sanity Checks
1. **WACC vs Terminal Growth ($g$)**: If $WACC \le g$, Gordon Growth is mathematically invalid (infinite value). In this case, terminal value and EV are suppressed, and a warning is printed.
2. **Terminal Value Concentration**: If TV represents $>85\%$ of Enterprise Value, a warning is raised to flag high valuation sensitivity.
3. **Implied EV/EBITDA multiple**: Flagged as warning if outside the standard range of $3\text{x}$ to $15\text{x}$.

---

## 4. Verification Suite Outcome
- **651 Backend Unit Tests**: Cover edge cases including divide-by-zero, negative EBIT/EBITDA, missing accounts receivable aging, WACC parameter overrides, and gradient descent calibration validation.
- **Frontend Build Stability**: TypeScript static checking and ESLint warnings are verified at 0 warnings and successful Vite build outcomes.
