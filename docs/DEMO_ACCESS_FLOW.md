# Demo and Development Access Flow

This document details the authentication and onboarding access flow for local development and demonstration environments, as well as how it integrates with production identity systems.

## Local / Demo Mode

In local and development environments, FinSight CFO is configured to remove all landing, login, and signup friction:

1. **Direct Entry**: When you open the application (visiting the root `/` URL), it automatically redirects you to the product workspace (`/platform`).
2. **Auto-Login**: If the backend is running in `local` authentication mode and no authentication session is detected in the browser, the frontend automatically logs the user in as `admin` (or `analyst`).
3. **Workspace First**: 
   - If no workspace has been created, the user is presented with the **Create Workspace** onboarding page as the first screen.
   - A **Load Sample Company** secondary CTA is available to quickly populate the workspace with synthetic seed data.
   - If a workspace already exists, the user is directed straight to the **Overview / CFO Command Center**.

No email or password input is required for local/demo mode.

---

## Production / OIDC Mode

For production environments, the authentication architecture remains fully active and secured:

1. **Route Guards**: When the backend is configured in `production` or `oidc` authentication modes, the frontend platform shell checks for a valid JWT token (`access_token` in `localStorage`).
2. **Redirection to Sign-In**: If the token is missing or expired, the shell redirects the user to the secure `/login` route.
3. **Standard Login & Sign-Up**: The standard login and registration components (`LoginPage.tsx`, `SignupPage.tsx`) are retained in the route tree and are fully functional for identity provider (IdP) integrations.

---

## Backend Environment Configuration

Authentication and AI provider integration are configured in the backend environment file.

### Environment File
Create or update `backend/.env` with the following variables:

```bash
# Authentication Mode
# Options: 'local' (demo/development bypass), 'production' (standard JWT), or 'oidc' (OpenID Connect / OAuth2)
AUTH_MODE=local

# Allow HTTP header overrides for testing roles in local/demo mode
AUTH_ALLOW_HEADER_OVERRIDES=true

# Google Gemini API Provider Configuration
# Set the Google API key to enable AI CFO conversational diagnostics
GOOGLE_API_KEY=your-gemini-api-key-here
```

> [!WARNING]
> Never commit `.env` files or hardcoded credentials to version control.
