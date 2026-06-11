# Job/Worker Evaluation & Rollout Plan

This document outlines the focused architecture, lifecycle, candidate workloads, and rollout phases for introducing asynchronous background processing in FinSight CFO.

## Current State

* **Job DB Adapter**: The `DatabaseJobRepository` adapter exists and is mapped to the `jobs` database table. It implements standard CRUD status transitions.
* **Local Mode Unimplemented**: `LocalJobRepository` is defined but currently raises `NotImplementedError` for all operations. The default runtime mode remains local.
* **No Background Executor**: No worker process, queue runner, or asynchronous executor (e.g. Celery, Redis, RQ, or FastAPI BackgroundTasks) is currently active or integrated.
* **Wired-only in Tests**: The `get_job_repository` dependency is only invoked inside test suites; no API routes or services currently queue or poll background jobs.

## Non-Goals

The following activities are strictly out of scope for this planning phase:
* **No queue implementation**: We will not install, configure, or spin up message brokers (like Redis or RabbitMQ) in the runtime code.
* **No worker process**: We will not write daemon processes, background loops, or Celery worker scripts.
* **No background task runtime**: We will not defer any workloads to async runners or background threads.
* **No API endpoint changes**: We will not add, modify, or expose any new HTTP routes for background job creation or polling.
* **No DB schema changes**: No database migration files or modifications to schema models are permitted.
* **No frontend changes**: The user interface remains untouched.
* **Do not implement workers in this PR**: This PR is strictly limited to planning, documentation, and architectural guardrails.

## Candidate Async Workloads

The following workloads are candidates for asynchronous offloading, ranked by value-to-risk ratio:

1. **Report Generation** (Safest / Highest Priority)
   * *Value*: Medium (Report compilation is CPU-heavy and generates PDF files).
   * *Risk*: Low (Read-heavy database interactions; self-contained; does not alter financial snapshots or active state).
2. **Analysis Workflow Run** (High Priority)
   * *Value*: High (CFO analysis executes sequentially across multiple financial calculators).
   * *Risk*: Medium (Write-heavy; relies on snapshot data integrity; must be isolated to prevent dirty reads).
3. **File Ingestion / Parsing**
   * *Value*: High (Validating and parsing large Excel/CSV uploads).
   * *Risk*: High (Deals with raw file uploads; must handle malformed data and disk cleanups; potential out-of-memory issues).
4. **External Data Enrichment** (Future)
   * *Value*: Medium (Fetching external market benchmarks and industry health metrics).
   * *Risk*: Medium (Network-dependent; requires handling API rate limits and circuit-breaking).
5. **AI CFO Consultation Sessions** (Future)
   * *Value*: High (Generating multi-turn financial advice via large language model APIs).
   * *Risk*: High (Long-lived connections; streaming requirements; high API token cost management).
6. **Scheduled System Monitoring** (Future)
   * *Value*: Low (Periodic checks on system health, database size, and audit trails).
   * *Risk*: Low (Very low write footprint; can run out-of-band).

### Recommended First Worker Use Case

We recommend **Report Generation** as the safest first worker use case. Report generation is self-contained and read-heavy. Because it compiles static PDFs or summaries from existing data and does not modify the underlying financial snapshots, workspace metadata, or analysis run history, a failure in report compilation cannot corrupt workspace state. This allows testing the job lifecycle from `pending` -> `running` -> `completed`/`failed` with minimal risk.

## Job Lifecycle

The system supports the following job state transitions:
* **Pending**: The job has been created and registered in the database, waiting to be picked up by a worker.
* **Running**: A worker has acquired the job and execution is in progress.
* **Completed**: The job succeeded and results are saved.
* **Failed**: The job encountered an error; the execution attempt failed.
* **Cancelled** (Optional / Future): The user terminated the job before completion.

### Database Schema Model Fields
The job record includes the following fields (mapped from `DbJob`):
* `id`: Unique UUID-based job identifier (String(36)).
* `workspace_id`: Workspace association context (String(36), Nullable, ON DELETE CASCADE).
* `organization_id`: Tenant context for isolation and RBAC billing context (String(36), ON DELETE CASCADE).
* `task_name` / `job_type`: Name of the task workload to execute (String(255)).
* `status`: Current state (`pending`, `running`, `completed`, `failed`, `cancelled`) (String(50)).
* `attempts`: Number of times the job execution has been attempted (Integer).
* `arguments` / `input_payload`: JSON configuration arguments (JSON).
* `result_payload`: JSON results payload on completion (JSON).
* `error_log` / `error_message`: Text traceback or error log on failure (TEXT).
* `metadata`: Dynamic metadata parameters (JSON).
* `queued_at` / `created_at`: Datetime when the job was queued.
* `started_at`: Datetime when the worker changed the status to `running`.
* `completed_at`: Datetime when the status changed to `completed` or `failed`.

## Worker Architecture Options

Three primary architectural choices exist for implementing the background processing loop:

| Option | Tradeoffs for Local Dev | Tradeoffs for CI | Tradeoffs for Demo Mode | Tradeoffs for Production |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI BackgroundTasks** | **Excellent**: Runs in-process; no extra processes. | **Excellent**: Low overhead; runs inline in tests. | **Excellent**: Highly reliable; single-click. | **Poor**: Lacks persistence; shares request CPU thread; cannot scale workers independently. |
| **In-process Async Loop** | **Good**: Low friction; separate loop thread. | **Good**: Fast tests; simple setup. | **Good**: Clean; self-contained. | **Medium**: Persistent queue but shares main container memory and CPU; risk of memory leaks. |
| **External Queue (Redis + Celery)** | **Medium**: Requires running Redis locally. | **Medium**: Requires docker-compose setup in CI. | **Poor**: Not self-contained; hard to distribute. | **Excellent**: Isolated resources; horizontal scaling; retry management; production-ready. |

*Recommendation*: In local development and demo mode, the **local default remains local** using a simple in-memory queue or sync facade, while production environments should utilize **Redis + Celery** for scalable multi-worker operation.

## Recommended Rollout

We propose the following six-step rollout plan:

* **Phase A: Job Route Contract and Repository Guardrails**
  * Establish API route schemas and contracts for listing and getting job statuses.
  * Implement mock repositories for local mode testing.
* **Phase B: Synchronous Job Facade**
  * Wire the routes to repository adapters but execute workloads *synchronously* inline.
  * Establishes the end-to-end API and DB persistence flow before making execution async.
* **Phase C: Background Worker Prototype**
  * Offload Report Generation to `FastAPI.BackgroundTasks` or an in-process worker thread.
  * Test async status updates (`pending` -> `running` -> `completed`).
* **Phase D: Retry, Idempotency & Progress Semantics**
  * Introduce an exponential backoff retry loop tracking the `attempts` column.
  * Ensure report compilations and snapshots write actions are idempotent.
* **Phase E: Process Supervision & Celery Setup**
  * Integrate Redis and Celery.
  * Separate the web container from the worker container in deployment configurations.
* **Phase F: Observability & Monitoring**
  * Expose Prometheus metrics for job latency, throughput, and error rates.
  * Hook up Slack/PagerDuty alerts for critical task failures.

## Guardrails

To prevent regressions, the future implementation must adhere to these rules:
* **No silent fallback in database mode**: If `PERSISTENCE_BACKEND="database"` is enabled and the DB connection fails during job creation, the endpoint must raise an exception. It must not write to local JSON files silently.
* **Local default remains local**: When `PERSISTENCE_BACKEND="local"`, the system must bypass DB session initialization.
* **Worker failures do not corrupt workspace state**: Worker operations must use database transactions. If a step fails, the transaction must roll back workspace status changes.
* **Retries are idempotent**: Retrying a failed background job must not duplicate output assets or DB rows.
* **No file bytes in job payloads**: Job arguments must only store reference metadata (e.g. `file_id`, `s3_key`). Storing raw CSV/Excel file bytes inside the database or message queue payload is strictly prohibited.
* **Clear error reporting**: Log tracebacks and error details in the `error_log` database field for observability.
* **No route response shape changes**: Any modifications to API responses require a dedicated contract PR.

## Test Strategy

* **JobRepository Local & Database Tests**: Validate `LocalJobRepository` (returning mock empty structures or simple stub checks) and `DatabaseJobRepository` (verifying state updates, sorting, and limits using SQLite in-memory).
* **Worker Unit Tests**: Test worker execution functions in isolation using mock repository layers.
* **Failure & Retry Validation**: Assert that worker failures record details to `error_log` and increment `attempts` correctly.
* **CI Integration Guardrails**: CI pipelines must not require a running external Redis/RabbitMQ instance. Mocks or in-memory queues must be utilized.

## Open Questions

1. **Which workloads are safe to queue first?**
   * *Answer*: Report Generation is the safest starting point due to its read-heavy, low-side-effect profile.
2. **What progress events should be exposed?**
   * *Answer*: Report status flags (e.g. `generating`, `uploading`, `ready`) should be tracked inside the `metadata` column.
3. **How should cancellation work?**
   * *Answer*: If a job is cancelled, we should support database status toggling to `cancelled`, and workers should check this status before executing subsequent steps.
4. **What retention policy should jobs use?**
   * *Answer*: Completed/failed job history should be auto-pruned after 30 days to limit table sizing.
5. **Should audit events be emitted for job lifecycle changes?**
   * *Answer*: Yes, creating and failing/completing a job should append a record to the `audit_events` table in database mode.

## Definition of Done

The first job/worker implementation PR will be ready for merge only when:
* **Single Workload**: Report generation is the only workload migrated to async task queue.
* **No Frontend Changes**: Backend endpoints are integrated; frontend polling changes are deferred.
* **Test Isolation**: Local mode tests bypass database session requirements, and database mode tests run against SQLite.
* **Zero Engine Leaks**: Local default remains local with zero database pool initialization.
* **API Compatibility**: API response shapes match existing contracts exactly.
* **CI Passed**: Github Actions pipelines are fully green.
