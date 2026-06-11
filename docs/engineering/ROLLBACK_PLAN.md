# Rollback Plan — Database Persistence

This document outlines the procedures, constraints, and safety guidelines for rolling back the FinSight CFO persistence layer from Database Mode to Local File Mode in the event of critical runtime issues.

## 1. Rollback Triggers

A rollback must be initiated immediately if any of the following occur in staging or production:
* **Severe Latency Spikes**: Request times increase by more than 150ms upon enabling database persistence.
* **Connection Exhaustion**: Backend API starts throwing 500 errors due to pool exhaustion or DB connection timeouts.
* **Data Corruption**: Mismatched type serialization or write failures resulting in partial or corrupted records.
* **Uncaught Deadlocks**: Multiple concurrent transactions causing unresolved database deadlocks.

## 2. Runtime Flag Rollback

The primary mechanism to revert database integration is changing the application configuration:

1. Locate the environment variables for the application deployment.
2. Modify `PERSISTENCE_BACKEND` from `"database"` to `"local"`.
3. Restart the FastAPI application servers.
4. Verify that no database connection pools are initialized on startup.

## 3. Database Migration Rollback

* **Alembic Downgrade**:
  If migrations need to be reverted, run:
  ```bash
  alembic downgrade -1
  ```
  or downgrade all the way to base:
  ```bash
  alembic downgrade base
  ```
* **When NOT to Downgrade**:
  Do **NOT** run migrations downgrade if the database has successfully written production data. Reverting migrations containing `drop_column` or `drop_table` will permanently destroy client records. In such cases, keep the database schema intact and simply toggle the runtime configuration (`PERSISTENCE_BACKEND="local"`).

## 4. Data Safety Rules

* **Do NOT Purge DB Rows**: During a rollback, the relational database rows must remain untouched. This preserves the transactional history for forensic analysis.
* **Do NOT Revert Object Storage**: Uploaded files and rendered PDF reports in object storage must never be deleted. Reverting the metadata persistence backend does not require physical file removal.

## 5. Emergency Procedure

1. **Notify Team**: Post a warning in the engineering channel: `[EMERGENCY] Reverting PERSISTENCE_BACKEND to local due to [Reason]`.
2. **Apply Configuration change**: Update staging/production environment configs (`PERSISTENCE_BACKEND=local`).
3. **Trigger Restart**: Redeploy or restart backend containers.
4. **Monitor API logs**: Confirm that endpoints are routing to localized file stores (`WorkspaceStore`).
5. **Freeze DB Writes**: Revoke write permissions from the database application user if write attempts persist.

## 6. Smoke Tests After Rollback

After reverting to Local Mode, verify:
- [ ] The API `/health` endpoint returns `200 OK`.
- [ ] Active workspaces can be successfully retrieved.
- [ ] The Data Room is queryable and lists legacy local files.
- [ ] Analysis runs can be executed and saved to the local directory.

## 7. Communication Checklist

* Notify DevOps/DBA about database activity suspension.
* Email Product Management regarding the status of current analyses during the rollback window.
* Issue a status post explaining the mitigation path and next steps for resolution.
