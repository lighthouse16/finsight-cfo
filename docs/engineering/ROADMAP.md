# FinSight CFO Engineering Roadmap

This document outlines the high-level roadmap for transitioning FinSight CFO from an intelligence MVP to a production-ready enterprise platform.

## Phase 1: Configuration & CI Foundation (Current)
- Establish externalized environment variables and config verification.
- Automate pull request and push checks via GitHub Actions CI.
- Define initial production-hardening documentation.

## Phase 2: Database & Storage Persistence
- Migrate from temporary filesystem-based storage to a relational database (e.g., PostgreSQL).
- Implement enterprise-grade tenant isolation for all stored financials and models.
- Set up secure, S3-compatible object storage for uploaded files in the Data Room.

---

## Sprint 1 Detailed Plan — Database Persistence Design and Foundation

1. **Design Docs (Design-Only)** [COMPLETED]
   - Establish table proposals, migration plans, and repository specifications.
2. **Add DB Dependencies and Migration Tooling** [COMPLETED]
   - Add SQLAlchemy, SQLModel, Alembic, and database drivers to python dependencies.
3. **Add Schema Models** [COMPLETED]
   - Write declarative SQLAlchemy/SQLModel models representing all entities (Workspaces, Snapshots, AnalysisRuns).
4. **Add Repository Interfaces** [COMPLETED]
   - Create abstract class signatures specifying CRUD actions.
5. **Add Local Adapter Compatibility Tests** [PLANNED]
   - Write test contract suites checking existing file storage logic against repository interface constraints.
6. **Add Database Workspace Adapter & Tests** [COMPLETED]
   - Verify DB repositories pass the exact same unit test assertions using an in-memory SQLite backend.
7. **Move Workspace Persistence Behind Interface** [PLANNED]
   - Refactor workspaces endpoints to fetch and save using the new interface contract.
8. **Add Database File Metadata Adapter & Migration Alignment** [COMPLETED]
   - Store file metadata and version pointers in database, keeping physical bytes in local storage / object storage. Ensure ORM schemas and Alembic migrations remain aligned.
9. **Move Analysis Runs Behind Interface** [COMPLETED]
   - Redirect analysis diagnostic results storage from filesystem JSON files to run artifact DB payloads.
10. **Add Database Audit Event Adapter & Migration Alignment** [COMPLETED]
    - Store system and workspace audit trails in the database, with support for organization-level auditing.
11. **Add Database Job Adapter & Migration Alignment** [COMPLETED]
    - Store background job executions and statuses in the database to support async tasks and status querying.
12. **Add Database Report Adapter & Migration Alignment** [COMPLETED]
    - Store compiled corporate report metadata and payloads securely in the database, with soft delete capability.
13. **Runtime Database Cutover Plan** [COMPLETED]
    - Establish a concrete cutover roadmap, rollback plan, and test matrix before route integrations.
14. **Workspace Route Database Integration** [COMPLETED]
    - Route workspace CRUD requests through persistence repository factory with backward-compatible local mode default.
15. **File Metadata Route Database Integration** [COMPLETED]
    - Route file metadata requests through persistence repository factory with backward-compatible local mode default.
16. **Other Route Database Integrations** (Analysis Runs: [COMPLETED], Reports: [COMPLETED], Audit Events: [COMPLETED], etc.: [PLANNED])
    - Sequentially integrate analysis runs, reports, and audit event endpoints with database persistence.
17. **Runtime Integration Health Check** [COMPLETED]
    - Add health check validation and guardrails suite checking all active persistence routes.
18. **Workspace Route Service Extraction Plan** [COMPLETED]
    - Plan and document the service extraction boundaries to clean up workspaces.py before further refactoring.
19. **Extract Audit Helper Service (Phase 1)** [COMPLETED]
    - Extract best-effort audit event logging helper from workspaces router into a dedicated audit service.

---

## Phase 3: Authentication & Multi-Tenancy
- Integrate production identity providers (OIDC/OAuth2/SAML).
- Add Role-Based Access Control (RBAC) (e.g., CFO, Analyst, Auditor).
- Implement secure token validation and request context middleware.

## Phase 4: Secure Uploads & Async Analysis
- Build a sandboxed pipeline for document ingestion and malware scanning.
- Offload long-running financial analysis workflows to a distributed task queue (e.g., Celery/Redis).
