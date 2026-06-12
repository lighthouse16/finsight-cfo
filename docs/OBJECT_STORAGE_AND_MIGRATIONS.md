# Object Storage & Database Migrations

This document outlines the foundation for production data persistence: S3-compatible object storage and Alembic-based database migrations.

## 1. Object Storage Adapter

The system supports two primary modes for persisting unstructured files (Data Room artifacts, uploaded PDFs, CSVs):

* **`local_file`**: Files are stored natively on the backend server's file system (default, primarily for development).
* **`s3`**: Files are securely uploaded to an S3-compatible provider (e.g., AWS S3, MinIO) without keeping them locally.

### Object Storage Configuration

Configure S3 behavior via `.env`:

```bash
OBJECT_STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://s3.amazonaws.com  # or http://localhost:9000 for MinIO
S3_BUCKET=my-finsight-bucket
S3_ACCESS_KEY_ID=my-access-key
S3_SECRET_ACCESS_KEY=my-secret-key
S3_REGION=us-east-1
S3_FORCE_PATH_STYLE=true
```

### Local Dev Behavior vs. Production

* **Local Mode (`OBJECT_STORAGE_BACKEND=local_file`)**: Files are stored in the `./storage_db/uploads` directory. Data behaves consistently between container reboots if volumes are persisted.
* **Production Mode (`OBJECT_STORAGE_BACKEND=s3`)**: Files are streamed directly into the S3 bucket. If configuration is incomplete, the system will return a `provider_not_configured` status, alerting operators that persistence isn't configured, restricting fallbacks safely.

## 2. Alembic Migrations

We rely on Alembic to manage database schema updates.

### Configuration & Tooling

The configuration uses `alembic.ini` and `backend/migrations/env.py`.

* **SQLite (Local Dev)**: Alembic connects safely to the local `storage_db/finsight_dev.db`.
* **Postgres (Production)**: The same migrations run against the production database URI provided in `DATABASE_URL`.

### Alembic Commands

To run migrations locally during development or CI:

```bash
cd backend
# Create a new migration revision
alembic revision --autogenerate -m "description of changes"

# Upgrade to the latest schema
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

### Rollback Note

Migrations are tracked and version-controlled. If a production deployment fails, you can safely use the `alembic downgrade <revision_id>` command to revert the schema. Data loss may occur if rolling back drops columns—always test rollbacks in a staging environment.

## 3. Remaining Production Gaps

The current foundation lacks real provider configuration:
- You must supply real S3 credentials via `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY`.
- You must provision an AWS S3 bucket (or MinIO container) for S3 uploads to succeed.
- A production PostgreSQL instance must be stood up and connected via `DATABASE_URL`.
