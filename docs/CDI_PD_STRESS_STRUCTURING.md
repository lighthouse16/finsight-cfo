# BOCHK Challenge Phase 3: Advisory, Alternative Data, PD, Stress Testing & Structuring

This document details the architecture and business logic implemented for Phase 3 of the BOCHK Challenge. FinSight CFO has been upgraded from a static ratio reporting tool to a deterministic financing advisory engine.

## 1. CDI Alternative Data Gateway Mock
Located in `backend/app/services/advisory/cdi_mock_gateway.py`.
- **Purpose**: Simulates a consent-based alternative data pipeline for supply chain / trade data.
- **Data Source**: Mocked CargoX / Tradelink e-invoices.
- **Metric**: Uses "Delivered" invoices as alternative digital collateral, applying an 80% advance rate to lower the risk profile.

## 2. Deterministic Logistic PD Engine
Located in `backend/app/services/advisory/pd_engine.py`.
- **Formula**: `Z = β0 + β1(DSCR) + β2(DebtRatio) + β3(Margin) + β4(CDI_Collateral_Adjustment)`
- **PD Mapping**: `PD = 1 / (1 + e^-Z)`
- **Tiers**: Converts PD probability into Risk Tiers A through E and a 0-100 score.
- **Disclaimer**: This is a context-only deterministic proxy. It is not calibrated with historical default data.

## 3. BOCHK Specific HIBOR Stress Testing
Located in `backend/app/services/advisory/stress_testing_engine.py`.
- **Mechanism**: Shocks the existing debt schedule by `+150 bps` (or any user-defined shock).
- **Thresholds**: 
  - Stressed DSCR < 1.10 triggers a "Fail" red flag with immediate mitigants (SFGS Principal Moratorium, IRS consideration).
  - Stressed DSCR < 1.25 triggers a "Watch" flag with restructuring recommendations.
  
## 4. Multi-Tranche Loan Structuring Optimizer
Located in `backend/app/services/advisory/loan_structuring_engine.py`.
- **Objective**: Minimize blended interest cost across requested funding amount.
- **Facilities**:
  1. SFGS 80% Guarantee Product (Lowest cost, capped at 18M).
  2. Trade Finance (Backed by CDI data, medium cost, capped at 1.5x alternative collateral).
  3. Working Capital Buffer (Standard revolver, highest cost).
- **Constraints Checked**: LTV <= 70% and DSCR >= 1.25.

## 5. Unified Funding Blueprint Endpoint
- **Route**: `POST /api/advisory/funding-blueprint`
- **Frontend Integration**: Implemented as the "Funding Blueprint Engine" panel on the Advisory Blueprint dashboard, providing an interactive interface to manipulate requested amount, consent toggle, and shock severity.
