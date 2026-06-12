# Release Readiness Report

## Release Decision
`Ready for limited public beta, not formal bank-production underwriting.`

---

## Important Safety Disclaimers

> [!IMPORTANT]
> - **Not a Formal Credit Decision**: Finsight CFO is an indicatively modeled scenario planning tool only. Outputs do not constitute formal bank underwriting, automated credit decisions, or lending recommendations.
> - **No Guaranteed Funding**: Recommendation reports or candidate facility structures generated do not guarantee credit approval, loan offers, or financing.
> - **Relationship Manager Review Required**: All advisor-ready reports, blueprints, and AI CFO suggestions must be reviewed and verified by a qualified Relationship Manager (RM) and bank credit officers before any commercial action.

---

## Production Environment Requirements

To deploy the application in production mode, the following credentials and services must be configured in the host environment:
1. **Hosted PostgreSQL Database**: Set `DATABASE_URL` to a valid database server URL.
2. **S3-Compatible Object Storage**: S3 backend configurations (`S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`) are required for persistent document room storage.
3. **Redis Server**: Redis queue configurations (`QUEUE_REDIS_URL`) are required for executing asynchronous background report-generation jobs.
4. **JWT Security Configs**: Set `JWT_SECRET_KEY` and `JWT_ALGORITHM` to secure authentication tokens.

---

## Known Technical & Environment Limitations

### 1. Document parsing & OCR Limitation
- PDF or DOCX files uploaded to the data room that lack a native copyable text layer (e.g. scanned documents) require an OCR parsing provider.
- If the OCR provider API key is not configured (`ocr_provider_not_configured` status), OCR parsing will be bypassed, and the files will not be ingested into the RAG context.

### 2. External Provider Credentials
- Paid and proprietary integrations (e.g. CME FedWatch, ChinaData, IHS Sector benchmarks, Google Gemini LLM API) require valid API keys.
- If these keys are absent, the adapters default to `provider_not_configured` and fall back to local seed fixtures with clear warnings.

### 3. Browser "Save as PDF" Export
- When exporting compiled advisor reports to PDF via the browser's print interface ("Save as PDF"), layout, styling, and graphics page breaks may vary depending on local browser print setups (e.g. "Background graphics" option must be checked).
