# Privacy and Data Handling Guardrails

This document outlines the security, privacy, and data isolation practices employed in FinSight CFO to ensure safe multi-tenant operation.

## 1. Authentication
- **Production Mode:** We use JWT (JSON Web Tokens) generated securely using the HS256 algorithm with a strongly typed environment secret (`JWT_SECRET_KEY`).
- **Development/Demo Mode:** `app_mode` configurations are set to bypass strict validation or enable "mock" headers, but this is explicitly barred in production environments.
- **Header Overrides:** The system completely drops debugging headers like `X-Role` when in production to prevent privilege escalation.

## 2. Role-Based Access Control (RBAC)
We enforce clear isolation boundaries via roles:
- **Admin / Owner:** Full access to manage workspace lifecycles (create/delete) and data visibility.
- **Analyst:** Authorized to upload and execute runs, but cannot delete the workspace.
- **Viewer:** Strictly read-only. Uploads, creations, deletions, and mutable data operations will be actively rejected at the route level.

## 3. Workspace Data Isolation
Every API endpoint operating on a workspace validates that the requester's `organization_id` (derived from the JWT `RequestContext`) matches the target workspace's `organization_id`. Cross-tenant data leakage is structurally impossible at the controller level.

## 4. File Upload Security
- **Size Boundaries:** Firm 50MB file size limit enforced globally.
- **File Validation:** Incoming files must be one of the explicitly allowed types (e.g., `text/csv`, `application/pdf`, `.xlsx`).
- **Filename Sanitization:** Uploaded filenames are scrubbed to strip out shell-dangerous paths or characters, safeguarding backend storage operations.

## 5. Denial-of-Service (Rate Limiting)
A lock-protected Token Bucket rate limiter regulates API throughput, enforcing fair usage and mitigating automated spam attacks across public web endpoints.

## 6. Storage Modes and Retention
- **Storage Modes:** The system operates in two distinct persistence modes. In `local` mode, data is kept strictly on ephemeral local files (JSON/CSV) which do not persist reliably across restarts. In `database` mode, data is stored structurally via an external RDBMS.
- **Data Retention & Deletion:** The explicit deletion of a workspace cascades across all structured databases and bucket-based object storage. Physical files and row-level metadata are purged without a trace. No soft-delete ghost records remain in production limits.

## 7. No Sale of Data
Under no circumstances does FinSight CFO aggregate, anonymize, or sell workspace financial data. Your tenant data belongs solely to the authorized tenant owners and is used strictly for fulfilling analysis requests originating from your active session.

## 8. AI Provider Data Caution
Certain analytical capabilities (e.g., Advisory Blueprint generation, AI CFO conversations) route context strings and snapshot figures to externally configured AI inference providers (e.g., OpenAI). By initiating an AI-driven workflow, users accept that their session data will be sent off-network to the provider. We recommend utilizing zero-retention enterprise tier AI provider agreements to guarantee data is not used for model training. 

## 9. User Responsibility
It is the end user’s responsibility to evaluate their data classification rules before uploading financial material. Administrators must strictly assign and revoke roles to maintain operational security. The application acts strictly as a processor and assumes the tenant administrator has the requisite legal authority to process the provided statements.
