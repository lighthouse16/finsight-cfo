# Google AI CFO Provider Integration

This document describes how to configure, run, and test the Google AI / Gemini provider integration for the digital CFO workspace.

## Configuration & Environment Variables

To configure the Google AI/Gemini integration, define the following environment variables:

| Variable | Description | Default / Example |
|---|---|---|
| `LLM_PROVIDER` | Determines the active AI provider. Must be set to `google_ai` to use Gemini. | `google_ai` |
| `GOOGLE_API_KEY` | Your Google AI Studio/Gemini API key. | `AIzaSy...` |
| `GOOGLE_AI_MODEL` | The specific Gemini model name to use. | `gemini-1.5-flash` |
| `GOOGLE_AI_BASE_URL` | Optional. Overrides the default base URL for the Gemini API. | `https://generativelanguage.googleapis.com` |

## Safety & Compliance copy

The integration includes a strict system/safety prompt that controls response copy to comply with banking-grade guidelines:
- **No Loan Approval / Underwriting**: Responses never claim to approve, reject, or make lending/underwriting decisions.
- **No Guaranteed Funding**: Responses are indicative, preliminary, and subject to RM verification and bank policy.
- **No Arbitrage Claims**: The assistant does not make claims of guaranteed profit or arbitrage.
- **Wording Filter**: Forbidden terms (like `approved`, `guaranteed`, `no risk`, `final decision`, etc.) are automatically scrubbed and replaced with indicative, review-safe terms prior to client-facing output.

## Local Fallback Behavior

If the Google AI provider is selected but `GOOGLE_API_KEY` is not configured, or if the external API request fails due to network or rate limits:
1. The backend automatically catches the exception or configuration gap.
2. It sets `aiMode = "deterministic_fallback"`.
3. It sets `providerStatus = "provider_not_configured"` (if key is missing) or `providerStatus = "provider_error"` (if request failed).
4. A warning is added detailing the status.
5. The backend returns a high-quality deterministic response matching the theme of the user's question, sourced from current workspace financial context (Financial Health, Valuation, Credit Readiness, Funding Strategy, or Macro Risks).

## Example Config

Add the following to your local `.env` file for testing:

```bash
LLM_PROVIDER=google_ai
GOOGLE_API_KEY=AIzaSyYourKeyHere
GOOGLE_AI_MODEL=gemini-1.5-flash
```

## Testing with Mocked Google AI

The test suite includes a mocked mock client test mapping different states of the Google AI provider integration:
- **Missing API key (Not Configured)**: Returns fallback content and lists the warning badge.
- **API success (Mocked)**: Returns Gemini response and sets status to active.
- **API failure (Mocked 500)**: Gracefully falls back to local deterministic template.
- **Safety Copy Scrubbing**: Validates that output containing forbidden phrases is automatically replaced.
- **Secrets leakage test**: Validates that the `GOOGLE_API_KEY` value is never returned in any response payload or debug log-safe field.

To run the backend test suite:
```bash
python -m pytest tests/test_google_ai_provider.py
```
