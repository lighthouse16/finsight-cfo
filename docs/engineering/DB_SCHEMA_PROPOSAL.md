# Database Schema Proposal

This document outlines the detailed relational schema proposal for the commercialized database storage engine of FinSight CFO.

---

## 1. Entity Relationship Overview

The schema is divided into three logical domains:
1. **Core IAM & Multi-Tenancy**: `organizations`, `users`, `organization_memberships`
2. **Workspaces & Data Room Ingestion**: `workspaces`, `workspace_files`, `workspace_file_versions`, `financial_snapshots`, `financial_snapshot_versions`
3. **Analysis & Operations**: `analysis_runs`, `analysis_run_artifacts`, `reports`, `audit_events`, `jobs`, `ai_cfo_sessions`, `ai_cfo_messages`, `external_data_consents`, `connector_accounts`

---

## 2. Table-by-Table Schema Specifications

### 2.1 Table: `organizations`
- **Purpose**: Defines the primary tenant boundary.
- **Soft Delete**: Yes (`deleted_at` timestamp).

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique organization identifier |
| `name` | VARCHAR(255) | NOT NULL | Name of the corporate entity |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | NULL | For soft deletes |

- **Indexes**:
  - `idx_organizations_deleted` ON (`deleted_at`) WHERE `deleted_at` IS NULL

---

### 2.2 Table: `users`
- **Purpose**: Tracks system users.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Primary login identifier |
| `full_name` | VARCHAR(255) | NOT NULL | User's full name |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | User status |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |

- **Indexes**:
  - `idx_users_email` ON (`email`)

---

### 2.3 Table: `organization_memberships`
- **Purpose**: Maps users to organizations with roles (RBAC).

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Membership record ID |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Owner tenant |
| `user_id` | UUID | FK -> `users(id)`, NOT NULL | Associated user |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'analyst' | Role name (e.g. 'cfo', 'analyst', 'auditor') |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |

- **Indexes / Constraints**:
  - UNIQUE constraint on (`organization_id`, `user_id`)
  - `idx_membership_user` ON (`user_id`)

---

### 2.4 Table: `workspaces`
- **Purpose**: Defines corporate workspaces owned by an organization.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique workspace identifier |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Owner tenant |
| `name` | VARCHAR(255) | NOT NULL | Name of workspace (e.g. 'Novus Retail') |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'active' | Workspace state |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | Auditor field |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | NULL | Soft delete |

- **Indexes / Constraints**:
  - `idx_workspaces_tenant` ON (`organization_id`, `deleted_at`) WHERE `deleted_at` IS NULL

---

### 2.5 Table: `workspace_files`
- **Purpose**: Tracks logical file metadata uploaded to the Data Room.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | File logical ID |
| `workspace_id` | UUID | FK -> `workspaces(id)`, NOT NULL | Parent workspace |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Owner tenant |
| `file_name` | VARCHAR(255) | NOT NULL | Logical file name (e.g. 'balance_sheet.csv') |
| `file_type` | VARCHAR(100) | NOT NULL | MIME type / format identifier |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | Audit field |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | NULL | Soft delete |

- **Indexes**:
  - `idx_files_workspace` ON (`workspace_id`, `deleted_at`)
  - `idx_files_tenant` ON (`organization_id`)

---

### 2.6 Table: `workspace_file_versions`
- **Purpose**: Manages file history, supporting future object storage versions.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Version ID |
| `workspace_file_id` | UUID | FK -> `workspace_files(id)`, NOT NULL | Parent file |
| `storage_key` | VARCHAR(512) | NOT NULL | Path in S3 / FileStore |
| `file_size_bytes` | BIGINT | NOT NULL | Size in bytes |
| `sha256_hash` | CHAR(64) | NOT NULL | Integrity checksum |
| `version_number` | INT | NOT NULL | Incremental version number |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | Audit field |

- **Indexes / Constraints**:
  - UNIQUE constraint on (`workspace_file_id`, `version_number`)
  - `idx_file_version_hash` ON (`sha256_hash`)

---

### 2.7 Table: `financial_snapshots`
- **Purpose**: Tracks normalized company statements and active projection data.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Snapshot ID |
| `workspace_id` | UUID | FK -> `workspaces(id)`, NOT NULL | Parent workspace |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Owner tenant |
| `active_version_id` | UUID | NULL | Pointer to active `financial_snapshot_versions(id)` |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |

- **Indexes**:
  - `idx_snapshots_workspace` ON (`workspace_id`)
  - `idx_snapshots_tenant` ON (`organization_id`)

---

### 2.8 Table: `financial_snapshot_versions`
- **Purpose**: Immutable versions of financial statement snapshots (Income, Balance, Projections).

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Version ID |
| `financial_snapshot_id` | UUID | FK -> `financial_snapshots(id)`, NOT NULL | Parent snapshot |
| `version_number` | INT | NOT NULL | Incremental version number |
| `statement_data` | JSONB | NOT NULL | Canonical statements payload (JSON) |
| `projections_data` | JSONB | NULL | Projection parameters / calculated runs (JSON) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | Audit field |

- **Indexes**:
  - UNIQUE constraint on (`financial_snapshot_id`, `version_number`)

---

### 2.9 Table: `analysis_runs`
- **Purpose**: Logs execution and results of diagnostics and blueprints.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Run ID |
| `workspace_id` | UUID | FK -> `workspaces(id)`, NOT NULL | Parent workspace |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Owner tenant |
| `run_type` | VARCHAR(100) | NOT NULL | e.g. 'financial_health', 'advisory_blueprint' |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'pending' | 'pending', 'running', 'completed', 'failed' |
| `snapshot_version_id` | UUID | FK -> `financial_snapshot_versions(id)`, NULL | Source snapshot version |
| `duration_ms` | INT | NULL | Calculation run execution time |
| `error_message` | TEXT | NULL | Error description if status is 'failed' |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | Audit field |

- **Indexes**:
  - `idx_analysis_runs_workspace` ON (`workspace_id`, `run_type`)
  - `idx_analysis_runs_tenant` ON (`organization_id`)

---

### 2.10 Table: `analysis_run_artifacts`
- **Purpose**: Stores the actual output data structures generated by the run.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Artifact ID |
| `analysis_run_id` | UUID | FK -> `analysis_runs(id)`, NOT NULL | Parent run |
| `artifact_type` | VARCHAR(100) | NOT NULL | e.g. 'ratios_json', 'stress_test_json' |
| `payload` | JSONB | NOT NULL | The structured calculation output |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |

- **Indexes**:
  - `idx_artifacts_run` ON (`analysis_run_id`)

---

### 2.11 Table: `reports`
- **Purpose**: History of compiled and generated corporate reports.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Report ID |
| `workspace_id` | UUID | FK -> `workspaces(id)`, NOT NULL | Parent workspace |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Owner tenant |
| `report_name` | VARCHAR(255) | NOT NULL | Name (e.g. 'Audit Brief Novus') |
| `analysis_run_id` | UUID | FK -> `analysis_runs(id)`, NOT NULL | Core underlying run |
| `pdf_storage_key` | VARCHAR(512) | NULL | S3 storage key to exported PDF file |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | Audit field |

---

### 2.12 Table: `audit_events`
- **Purpose**: Cryptographic or immutable system trail of sensitive operations.
- **Constraints**: Immutable (Updates / Deletes are blocked via DB triggers).

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Event ID |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Associated tenant |
| `user_id` | UUID | FK -> `users(id)`, NULL | Action actor |
| `action` | VARCHAR(100) | NOT NULL | Action key (e.g., 'workspace_reset', 'data_view') |
| `ip_address` | VARCHAR(45) | NULL | Actor network origin IP |
| `context_payload` | JSONB | NULL | Metadata or changes payload |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Timestamp |

- **Indexes**:
  - `idx_audit_tenant_action` ON (`organization_id`, `action`)

---

### 2.13 Table: `jobs`
- **Purpose**: Tracks async task queue executions (e.g. Celery runs).

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Job ID |
| `task_name` | VARCHAR(255) | NOT NULL | Name of task runner (e.g. 'run_valuation') |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'pending' | 'pending', 'started', 'completed', 'failed', 'retrying' |
| `attempts` | INT | NOT NULL, DEFAULT 0 | Count of executions |
| `arguments` | JSONB | NULL | Invocation parameters |
| `error_log` | TEXT | NULL | Exception trace log |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |

---

### 2.14 Table: `ai_cfo_sessions`
- **Purpose**: Chat session history for the AI CFO assistant.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Session ID |
| `workspace_id` | UUID | FK -> `workspaces(id)`, NOT NULL | Associated workspace context |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Owner tenant |
| `title` | VARCHAR(255) | NOT NULL, DEFAULT 'New Consultation' | Thread title |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | User owner |

---

### 2.15 Table: `ai_cfo_messages`
- **Purpose**: Session thread messages.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Message ID |
| `session_id` | UUID | FK -> `ai_cfo_sessions(id)`, NOT NULL | Thread ID |
| `role` | VARCHAR(50) | NOT NULL | 'user', 'assistant', 'system' |
| `content` | TEXT | NOT NULL | Message body |
| `tokens_used` | INT | NULL | LLM token metrics |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Timestamp |

---

### 2.16 Table: `external_data_consents`
- **Purpose**: Tracks user consents for external integrations (CDI, CCRA, MPF).

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Consent ID |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Tenant ID |
| `data_source` | VARCHAR(100) | NOT NULL | 'cdi', 'ccra', 'mpf', 'open_banking' |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'active' | 'active', 'revoked', 'expired' |
| `expires_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Expiration timestamp |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `created_by_user_id` | UUID | FK -> `users(id)`, NULL | Audit field |

---

### 2.17 Table: `connector_accounts`
- **Purpose**: Stores access definitions for active banking/integration connectors.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Account ID |
| `organization_id` | UUID | FK -> `organizations(id)`, NOT NULL | Tenant ID |
| `provider_name` | VARCHAR(150) | NOT NULL | e.g. 'hsb_commercial', 'za_bank' |
| `encrypted_auth_payload` | TEXT | NOT NULL | Encrypted connection secrets |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'linked' | Connection status |
| `last_synced_at` | TIMESTAMP WITH TIME ZONE | NULL | Last sync timestamp |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Audit field |
