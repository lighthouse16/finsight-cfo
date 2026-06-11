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

## Phase 3: Authentication & Multi-Tenancy
- Integrate production identity providers (OIDC/OAuth2/SAML).
- Add Role-Based Access Control (RBAC) (e.g., CFO, Analyst, Auditor).
- Implement secure token validation and request context middleware.

## Phase 4: Secure Uploads & Async Analysis
- Build a sandboxed pipeline for document ingestion and malware scanning.
- Offload long-running financial analysis workflows to a distributed task queue (e.g., Celery/Redis).
