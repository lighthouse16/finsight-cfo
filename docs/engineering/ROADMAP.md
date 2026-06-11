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
9. **Move Analysis Runs Behind Interface** [PLANNED]
   - Redirect analysis diagnostic results storage from filesystem JSON files to run artifact DB payloads.

---

## Phase 3: Authentication & Multi-Tenancy
- Integrate production identity providers (OIDC/OAuth2/SAML).
- Add Role-Based Access Control (RBAC) (e.g., CFO, Analyst, Auditor).
- Implement secure token validation and request context middleware.

## Phase 4: Secure Uploads & Async Analysis
- Build a sandboxed pipeline for document ingestion and malware scanning.
- Offload long-running financial analysis workflows to a distributed task queue (e.g., Celery/Redis).
