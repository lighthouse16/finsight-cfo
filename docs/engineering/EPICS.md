# Engineering Epics

This document tracks active and upcoming large-scale engineering initiatives (Epics).

## Epic 1: Configuration & CI Hardening
- **Goal**: Clean configuration separation and automatic linting/testing.
- **Status**: Active (Task `commercial/foundation-config-ci`)
- **Key Deliverables**:
  - Environment validation check at startup.
  - Strict linting and build checks in GitHub Actions.

## Epic 2: Production Database Integration
- **Goal**: Replace filesystem JSON store with database persistence.
- **Status**: Backlog
- **Key Deliverables**:
  - Relational database schema for Workspaces and AnalysisRuns.
  - Transaction safety and migrations system (Alembic).

## Epic 3: Secure Multi-Tenant Architecture
- **Goal**: Ensure absolute data boundary separation between clients.
- **Status**: Backlog
- **Key Deliverables**:
  - Tenant ID filtering at database/repository levels.
  - Row-Level Security (RLS) enforcement.
