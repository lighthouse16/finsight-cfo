# Market Research & Funding Intelligence (Phase 2)

This document maps out the system architecture, requirements, API specifications, and fixture assumptions for the Phase 2 Market Research & Funding Intelligence module.

## 1. Requirement Mapping

The implementation directly aligns with the BOCHK Challenge/research requirements:

| Requirement Area | Feature Details | Implementation |
| :--- | :--- | :--- |
| **WHEN Module** | HKMA/HIBOR liquidity timing, market red flags, and Golden Timing Index | Calculations based on day-of-month, current HIBOR rate, and interest yield curve states. |
| **WHERE Module** | Ranking of funding channels (SFGS 80%, SFGS 90%, BOCHK SME / Trade Finance, Virtual Bank Fast Liquidity, Working Capital Buffer) | Logic dynamic to corporate profile (cash balance, working capital gap, DSO) and market environment (rates). |
| **Cross-border Arbitrage** | Cross-border funding spread: `Spread = HIBOR - LPR` | Computes current cross-border spread and flags favorable, neutral, or unfavorable windows. |
| **GBA Advisory Trigger** | Triggering GBA cross-border/RMB advisory | Advisory disclaimer embedded in responses indicating "context-only, RM review required" and highlighting cross-border opportunity when favorable. |

---

## 2. API Contract

The backend registers three REST endpoints under `/api/market-funding`:

### GET `/api/market-funding/intelligence`
Returns the full market intelligence package (timing signals, red flags, and ranked funding channels).

#### Response Schema
```json
{
  "current_hibor": 4.25,
  "lpr_or_proxy_rate": 3.45,
  "hibor_lpr_spread": 0.80,
  "fx_hedging_cost_proxy": 1.25,
  "spread_signal": "favorable",
  "market_red_flags": {
    "window_dressing": false,
    "mega_ipo_liquidity": false,
    "inverted_curve": true,
    "high_rate_environment": true
  },
  "golden_timing_index": 75,
  "funding_channels": [
    {
      "name": "SFGS 80%",
      "max_amount_hkd": 18000000.0,
      "tenor": "Up to 7 years",
      "estimated_cost_band": "Low",
      "speed_band": "Medium",
      "eligibility_notes": "SMEs registered in HK for at least 1 year with active business operations.",
      "pros": [
        "Government guarantee (80%) reduces collateral requirements",
        "Lower interest rate spread"
      ],
      "cons": [
        "Longer processing time due to HKMC approval",
        "Requires personal guarantee"
      ],
      "recommendation_reason": "Highly recommended for long-term working capital needs with lower financing cost."
    },
    ...
  ],
  "advisory_disclaimer": "Market and funding intelligence is context-only, RM review required. ..."
}
```

### GET `/api/market-funding/timing-signals`
Returns only timing signals, red flags, and the Golden Timing Index.

### GET `/api/market-funding/funding-channels`
Returns the list of ranked funding channels.

---

## 3. Fixture Assumptions

To ensure high-availability and zero external API dependencies for the initial phase, a deterministic `FixtureMarketDataAdapter` is utilized.

- **Market Rates**:
  - HIBOR rate defaults to `4.25%`.
  - LPR (Loan Prime Rate) or proxy defaults to `3.45%`.
  - FX hedging cost proxy defaults to `1.25%`.
- **Cross-Border Spread**:
  - `Spread = HIBOR - LPR` -> `4.25 - 3.45 = 0.80%`.
  - Classified as `favorable` (since `spread > 0.50%`), indicating that borrowing in LPR-linked RMB and hedging to HKD may offer cross-border cost advantages.
- **Red Flags**:
  - **Window Dressing**: Active if the current date is on or after the 25th of March, June, September, or December.
  - **Mega IPO Liquidity**: Defaults to `false` in sandbox fixture mode.
  - **Inverted Curve**: Defaults to `true` (short-term rates exceed long-term rates).
  - **High Rate Environment**: `true` when HIBOR exceeds `3.50%` (currently `true` at `4.25%`).
- **Golden Timing Index Formula**:
  - Starts at `100`.
  - `-15` for window dressing.
  - `-20` for mega IPO liquidity.
  - `-15` for inverted curve.
  - `-20` for high rate environment.
  - `+10` if spread signal is `favorable`, `-10` if `unfavorable`.
  - Bounded between `0` and `100`. (Base fixture value: `100 - 15 - 20 + 10 = 75`).

---

## 4. Future External Integration Plan

The module is decoupled using the `BaseMarketDataAdapter` Protocol. Future production adapters will fetch real-time market indices:

1. **HKMA HIBOR / Liquidity Indicators**:
   - Integrate with the Hong Kong Monetary Authority (HKMA) Open API for daily HIBOR fixings and Exchange Fund Bills/Notes yields.
2. **PBOC LPR / GBA Spread**:
   - Pull from the People's Bank of China (PBOC) official publications or CEIC/Wind datasets for LPR (1-year and 5-year).
3. **FX Hedging Costs / CNH/HKD Swaps**:
   - Query HKEX or commercial FX spot/forward API feeds (e.g., Bloomberg/Refinitiv or partner virtual bank treasuries) to compute dynamic forward FX premiums/discounts.
4. **Commercial Data Interchange (CDI)**:
   - Integrate with Hong Kong's CDI sandbox to feed verified company consent-based commercial profiles into the ranking service dynamically.
