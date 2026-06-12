# FinSight CFO Web Deployment Runbook - Data Providers & Provenance

This runbook documents the configuration, deployment, and validation steps for the Market Watch data providers, credentials, and source provenance settings.

---

## 1. Environment Configurations

Configure the following environment variables on the production host or within Docker `.env` files to control data provider adapter behaviors:

### A. Public / Scraping Feeds (Auto-failover)
- `HKAB_ENABLED` (default: `true`): Enable primary HKAB HIBOR scraping.
- `HKMA_ENABLED` (default: `true`): Enable secondary HKMA API for HIBOR fallback and HONIA/Liquidity indicators.
- `FRANKFURTER_ENABLED` (default: `true`): Enable Frankfurter API for GBA trade currency pair rate tracking.

### B. Paid / Credential-Backed Feeds (Honesty-Hardeded)
If these keys are missing or invalid, the backend dynamically resolves the provider status as `provider_not_configured`, returning descriptive warnings/hints to the frontend instead of silently presenting sandbox data as live:
- `ALPHA_VANTAGE_API_KEY`: API credential for Commodities tracking.
- `CHINADATA_API_KEY` / `IHS_API_KEY`: API credential for Sector Benchmarks and industrial metrics.
- `CME_FEDWATCH_API_KEY`: API credential for timing and monetary policy indicators.

---

## 2. Lender Product Catalog Setup

FinSight CFO resolves lender products and indicative rates via a config-driven JSON catalog.

### Production Catalog Path
- Set `LENDER_CATALOG_PATH` in the backend environment to point to the directory containing `provider_catalog.json`.
- A sample template is provided at: `demo_data/provider_catalog.sample.json`.
- For production, copy this to a secure volume, edit the indicative pricing terms, and update the environment variable:
  ```bash
  LENDER_CATALOG_PATH=/var/lib/finsight/provider_catalog.json
  ```

---

## 3. Post-Deployment Verification

1. Verify backend status endpoints return correct provenance mode mappings:
   ```bash
   curl -X GET http://localhost:8000/api/market-watch/sources
   ```
2. Verify that missing keys cause the endpoints to report `provider_not_configured` honestly:
   - Check response fields in `/api/market-watch/commodities` for `provenance.source_mode == "provider_not_configured"`.
