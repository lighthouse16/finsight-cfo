# Market Watch Content Audit

This document audits current copy blocks and data presentation elements across Market Watch to establish rule-based insight generation.

---

## 1. Executive Signal Cards
* **Classification**: `data_bound` & `rule_generated`
* **Audit**:
  * Currently displays top-level cards for rates, FX, sector health, and funding conditions.
  * Implication copy (e.g., "HIBOR rates affect HKD 6.5M floating-rate facility") is computed dynamically based on company context in `MarketWatchPage.tsx`.
* **Actionable / Hardcoded Copy to Replace**:
  * Default interpretation strings in case of missing context (e.g., "Floating-rate debt is cost-sensitive" or "CNY operations watch").

---

## 2. Market Pulse Priorities ("What Needs Attention Now")
* **Classification**: `rule_generated`
* **Audit**:
  * Displays 3 priority exposure summaries for Harbour & Finch Trading Ltd. (floating-rate, receivables stretch, and FX/input-cost).
* **Actionable / Hardcoded Copy to Replace**:
  * Wording is currently static under the profile branch (e.g., "DSO 52d vs 45d benchmark, creating working-capital pressure"). These must be generated dynamically based on computed thresholds (e.g., if DSO > sector_average + 5 days).

---

## 3. Rates CFO Takeaway
* **Classification**: `rule_generated`
* **Audit**:
  * Summarizes sensitivity of the monthly debt service to base HIBOR shifts.
* **Actionable / Hardcoded Copy to Replace**:
  * Template string: `Your monthly debt service of HKD {monthlyDebtService} is highly sensitive to HIBOR fluctuations...`

---

## 4. FX Watch Signals
* **Classification**: `data_bound`
* **Audit**:
  * GBA Watch Signals represent CNY, USD import exposures, repatriation, and landing-cost variance.
* **Actionable / Hardcoded Copy to Replace**:
  * The categories and descriptions (e.g., "Import: 72% import costs are USD-linked") are currently static arrays inside `FxGbaTab.tsx` when the profile is connected. These should be built dynamically from the profile context.

---

## 5. Sector Benchmark Interpretation
* **Classification**: `data_bound`
* **Audit**:
  * Renders DSO, Inventory, DPO, Gross margin, and Documentation comparisons.
* **Actionable / Hardcoded Copy to Replace**:
  * "Comparative Performance" labels and card descriptions (e.g., "Receivables cycle slightly elevated. Maintain collection discipline") are currently selected via hardcoded switches on IDs. These will be generated using comparison rule templates.

---

## 6. Commodities Watch Signals
* **Classification**: `rule_generated`
* **Audit**:
  * Outlines Metals exposure, Freight/Energy cost sensitivity, and supplier contract reviews.
* **Actionable / Hardcoded Copy to Replace**:
  * Short margin sensitivity messages (e.g., "Copper increases pressure printed component cost base") are currently mapped statically. These will be dynamic based on which commodities cross volatility thresholds.

---

## 7. Stress Scenarios
* **Classification**: `demo_only` & `rule_generated`
* **Audit**:
  * Show cases for HIBOR shock (+150 bps), receivables delay (+15 Days), and currency swings.
* **Actionable / Hardcoded Copy to Replace**:
  * Implication lines (e.g., "HIBOR shock increases interest on the HKD 6.5M floating-rate facility") are selected via regex/string matching. These should be structured objects generated directly from the snapshot parameters.

---

## 8. Source Banners
* **Classification**: `static_explainer`
* **Audit**:
  * Compact horizontal banners showing data source, freshness, and secondary warnings.
* **Actionable / Hardcoded Copy to Replace**:
  * Mostly correct. Requires standardizing warnings to only display when fallback/fixture data is active.

---

## 9. Integration Status
* **Classification**: `static_explainer`
* **Audit**:
  * Renders status of company records (connected, required, partial).
* **Actionable / Hardcoded Copy to Replace**:
  * Status mappings are static. Mappings must match API responses exactly and change labels dynamically depending on the profile.
