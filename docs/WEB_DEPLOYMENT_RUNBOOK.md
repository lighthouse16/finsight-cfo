# Web Deployment Runbook - Production DB & S3 Setup

This runbook outlines the required steps, environment settings, and commands to configure, deploy, and verify FinSight CFO with a PostgreSQL relational database and S3-compatible object storage.

---

## 1. Database Provisioning & Schema Setup

For production web deployments, FinSight CFO switches from its default in-memory/JSON-file persistence mode to a relational database backend.

### Required Environment Variables

Set the following runtime environment variables in your deployment environment (Docker, Kubernetes, or server system systemd configurations):

```bash
# Set persistence mode to relational database
PERSISTENCE_BACKEND="database"

# Database URL pointing to a hosted PostgreSQL/MySQL instance (SQLAlchemy format)
DATABASE_URL="postgresql+psycopg2://<db_user>:<db_password>@<db_host>:<db_port>/<db_name>"

# Toggle database SQL logging (Keep false in production to optimize performance/logs)
DATABASE_ECHO=false
```

### Running Schema Migrations (Alembic)

Schema migrations must be run automatically during container startup or deployment pipelines. Do NOT manually create tables in the production database.

Run the following command from the `backend/` directory to upgrade the database schema to the latest version:

```bash
cd backend
# Run alembic migrations
.venv/Scripts/alembic upgrade head
```

Or, in a Docker environment:

```dockerfile
# Dockerfile ENTRYPOINT snippet
ENTRYPOINT ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

---

## 2. Object Storage Configuration (S3 / MinIO)

FinSight CFO supports S3-compatible object storage (such as AWS S3, MinIO, or Google Cloud Storage in S3 interoperability mode) for storing physical file uploads (data room spreadsheets, PDFs, etc.).

### S3 Settings

Set the following variables to route file uploads to object storage. If any of these are missing/empty, the application falls back safely to writing files to the local file system.

```bash
# The endpoint URL for S3 (Leave empty for standard AWS S3, or set for MinIO/LocalStack)
S3_ENDPOINT_URL="http://minio:9000"

# S3 Access credentials
S3_ACCESS_KEY_ID="minio_access_key"
S3_SECRET_ACCESS_KEY="minio_secret_key"

# Target bucket name
S3_BUCKET_NAME="finsight-cfo-assets"

# S3 Region configuration
S3_REGION_NAME="us-east-1"

# Force SSL / HTTPS for connections
S3_SECURE=true
```

---

## 3. Backward Compatibility & Local Verification

* **Local / Development Mode**: If `PERSISTENCE_BACKEND` is set to `"local"` or left unset, FinSight CFO stores all state under local JSON configurations in the `storage_db` directory. This is optimal for developer environments and does not require starting PostgreSQL or S3.
* **Testing locally**: You can verify the production setup locally using Docker Compose or by launching a local SQLite database and mock MinIO:
  ```powershell
  $env:PERSISTENCE_BACKEND="database"
  $env:DATABASE_URL="sqlite:///./storage_db/finsight_production.db"
  $env:S3_BUCKET_NAME="dev-bucket"
  $env:S3_ACCESS_KEY_ID="mock"
  $env:S3_SECRET_ACCESS_KEY="mock"
  ```

---

## 4. Verification and Health Checks

### Startup Verification

Ensure the service starts correctly and the `/health` check endpoint returns `200 OK`:

```bash
curl -f http://localhost:8000/health
```

### Integration Test Matrix Checks

Validate the persistence modes by running the test suite:

```bash
# Run tests under database configuration
$env:PERSISTENCE_BACKEND="database"
$env:DATABASE_URL="sqlite:///./storage_db/finsight_test.db"
$env:PYTHONPATH="."
python -m pytest tests
```
