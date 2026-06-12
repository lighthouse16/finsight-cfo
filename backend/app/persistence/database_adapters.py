import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Workspace, Organization, WorkspaceFile, WorkspaceFileVersion, AnalysisRun as DbAnalysisRun, AuditEvent as DbAuditEvent, Job as DbJob, Report as DbReport, FinancialSnapshot as DbFinancialSnapshot, FinancialSnapshotVersion as DbFinancialSnapshotVersion
from app.models.workspace import CompanyWorkspace, FinancialSnapshot as PydanticFinancialSnapshot
from app.persistence.interfaces import WorkspaceRepository, FileMetadataRepository, AnalysisRunRepository, AuditEventRepository, JobRepository, ReportRepository, FinancialSnapshotRepository
from app.persistence.errors import PersistenceConfigurationError

class DatabaseWorkspaceRepository(WorkspaceRepository):
    """
    SQLAlchemy-backed implementation of the WorkspaceRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session
        self.default_org_id = "org_default"

    def _ensure_default_org(self) -> None:
        """
        Ensure default organization exists in the database to satisfy ForeignKey constraints.
        Comments: Multi-tenant security boundaries will be implemented in a subsequent auth/RBAC PR.
        """
        org = self.session.query(Organization).filter_by(id=self.default_org_id).first()
        if not org:
            org = Organization(id=self.default_org_id, name="Default Organization")
            self.session.add(org)
            self.session.flush()

    def list_workspaces(self) -> List[CompanyWorkspace]:
        """
        List all active non-deleted workspaces.
        """
        workspaces = (
            self.session.query(Workspace)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .all()
        )
        return [
            CompanyWorkspace(
                id=w.id,
                companyName=w.name,
                createdAt=w.created_at.isoformat(),
                metadata=w.workspace_metadata or {}
            )
            for w in workspaces
        ]

    def get_workspace(self, workspace_id: str) -> Optional[CompanyWorkspace]:
        """
        Retrieve workspace by ID if it exists and is not deleted.
        """
        w = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not w:
            return None
        return CompanyWorkspace(
            id=w.id,
            companyName=w.name,
            createdAt=w.created_at.isoformat(),
            metadata=w.workspace_metadata or {}
        )

    def create_workspace(self, workspace_id: str, company_name: str, metadata: Optional[Dict[str, Any]] = None) -> CompanyWorkspace:
        """
        Create a new workspace, ensuring the default organization is present.
        """
        self._ensure_default_org()
        
        existing = self.session.query(Workspace).filter_by(id=workspace_id).first()
        if existing:
            if existing.deleted_at is None and existing.status != "deleted":
                return CompanyWorkspace(
                    id=existing.id,
                    companyName=existing.name,
                    createdAt=existing.created_at.isoformat(),
                    metadata=existing.workspace_metadata or {}
                )
            else:
                self.session.delete(existing)
                self.session.flush()

        new_workspace = Workspace(
            id=workspace_id,
            organization_id=self.default_org_id,
            name=company_name,
            status="active",
            workspace_metadata=metadata or {}
        )
        self.session.add(new_workspace)
        self.session.commit()
        return CompanyWorkspace(
            id=new_workspace.id,
            companyName=new_workspace.name,
            createdAt=new_workspace.created_at.isoformat(),
            metadata=new_workspace.workspace_metadata or {}
        )

    def delete_workspace(self, workspace_id: str) -> bool:
        """
        Soft-delete workspace.
        """
        w = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not w:
            return False
        
        w.deleted_at = datetime.now(timezone.utc)
        w.status = "deleted"
        self.session.commit()
        return True

    def get_active_workspace(self) -> Optional[CompanyWorkspace]:
        """
        Returns the newest non-deleted workspace.
        """
        w = (
            self.session.query(Workspace)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .order_by(Workspace.created_at.desc())
            .first()
        )
        if not w:
            return None
        return CompanyWorkspace(
            id=w.id,
            companyName=w.name,
            createdAt=w.created_at.isoformat(),
            metadata=w.workspace_metadata or {}
        )


class DatabaseFileMetadataRepository(FileMetadataRepository):
    """
    SQLAlchemy-backed implementation of the FileMetadataRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session

    def list_file_records(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all file records within a workspace (excluding deleted ones).
        """
        files = (
            self.session.query(WorkspaceFile)
            .filter_by(workspace_id=workspace_id)
            .filter(WorkspaceFile.deleted_at.is_(None))
            .all()
        )
        records = []
        for file in files:
            latest_version = (
                self.session.query(WorkspaceFileVersion)
                .filter_by(workspace_file_id=file.id)
                .order_by(WorkspaceFileVersion.version_number.desc())
                .first()
            )
            records.append({
                "id": file.id,
                "workspaceId": file.workspace_id,
                "recordKey": file.record_key,
                "fileName": file.file_name,
                "fileType": file.file_type,
                "fileSizeBytes": latest_version.file_size_bytes if latest_version else 0,
                "status": file.status,
                "uploadedAt": file.created_at.isoformat() if file.created_at else None,
                "filePath": latest_version.storage_key if latest_version else "",
                "metadata": file.file_metadata or {}
            })
        return records

    def get_file_record(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific file record by ID if it exists and is not deleted.
        """
        file = (
            self.session.query(WorkspaceFile)
            .filter_by(id=file_id)
            .filter(WorkspaceFile.deleted_at.is_(None))
            .first()
        )
        if not file:
            return None
        
        latest_version = (
            self.session.query(WorkspaceFileVersion)
            .filter_by(workspace_file_id=file_id)
            .order_by(WorkspaceFileVersion.version_number.desc())
            .first()
        )
        
        return {
            "id": file.id,
            "workspaceId": file.workspace_id,
            "recordKey": file.record_key,
            "fileName": file.file_name,
            "fileType": file.file_type,
            "fileSizeBytes": latest_version.file_size_bytes if latest_version else 0,
            "status": file.status,
            "uploadedAt": file.created_at.isoformat() if file.created_at else None,
            "filePath": latest_version.storage_key if latest_version else "",
            "storageMode": (file.file_metadata or {}).get("storageMode", "local_file"),
            "objectKey": (file.file_metadata or {}).get("objectKey"),
            "objectUri": (file.file_metadata or {}).get("objectUri"),
            "providerStatus": (file.file_metadata or {}).get("providerStatus"),
            "warnings": (file.file_metadata or {}).get("warnings", []),
            "metadata": file.file_metadata or {}
        }

    def save_file_record(
        self,
        workspace_id: str,
        record_key: str,
        filename: str,
        content_type: str,
        file_size_bytes: int,
        storage_uri: str,
        checksum_sha256: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        storage_mode: str = "local_file",
        object_key: Optional[str] = None,
        object_uri: Optional[str] = None,
        provider_status: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Save/register a file metadata record and create the first version.
        Raises PersistenceConfigurationError if target workspace does not exist.
        """
        workspace = self.session.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace:
            raise PersistenceConfigurationError(f"Workspace '{workspace_id}' does not exist.")
        
        org_id = workspace.organization_id

        # Find and soft-delete existing active file for the same record_key in this workspace
        existing = (
            self.session.query(WorkspaceFile)
            .filter_by(workspace_id=workspace_id, record_key=record_key)
            .filter(WorkspaceFile.deleted_at.is_(None))
            .first()
        )
        if existing:
            existing.deleted_at = datetime.now(timezone.utc)
            existing.status = "deleted"
            self.session.flush()

        # Create logical file record
        file_id = f"file_{workspace_id}_{record_key}_{uuid.uuid4().hex[:8]}"
        file_rec = WorkspaceFile(
            id=file_id,
            workspace_id=workspace_id,
            organization_id=org_id,
            file_name=filename,
            file_type=content_type,
            record_key=record_key,
            status="uploaded",
            file_metadata=metadata or {}
        )
        if storage_mode:
            file_rec.file_metadata["storageMode"] = storage_mode
        if object_key:
            file_rec.file_metadata["objectKey"] = object_key
        if object_uri:
            file_rec.file_metadata["objectUri"] = object_uri
        if provider_status:
            file_rec.file_metadata["providerStatus"] = provider_status
        if warnings:
            file_rec.file_metadata["warnings"] = warnings

        self.session.add(file_rec)
        self.session.flush()

        # Create first version
        version = WorkspaceFileVersion(
            id=f"version_{uuid.uuid4().hex[:12]}",
            workspace_file_id=file_id,
            storage_key=storage_uri,
            file_size_bytes=file_size_bytes,
            sha256_hash=checksum_sha256 or "",
            version_number=1
        )
        self.session.add(version)
        self.session.commit()

        return {
            "id": file_rec.id,
            "workspaceId": file_rec.workspace_id,
            "recordKey": file_rec.record_key,
            "fileName": file_rec.file_name,
            "fileType": file_rec.file_type,
            "fileSizeBytes": version.file_size_bytes,
            "status": file_rec.status,
            "uploadedAt": file_rec.created_at.isoformat() if file_rec.created_at else None,
            "filePath": version.storage_key,
            "storageMode": storage_mode,
            "objectKey": object_key,
            "objectUri": object_uri,
            "providerStatus": provider_status,
            "warnings": warnings or [],
            "metadata": file_rec.file_metadata or {}
        }

    def delete_file_record(self, file_id: str) -> bool:
        """
        Soft-delete file metadata record.
        """
        file = (
            self.session.query(WorkspaceFile)
            .filter_by(id=file_id)
            .filter(WorkspaceFile.deleted_at.is_(None))
            .first()
        )
        if not file:
            return False
        
        file.deleted_at = datetime.now(timezone.utc)
        file.status = "deleted"
        self.session.commit()
        return True

    def list_file_versions(self, file_id: str) -> List[Dict[str, Any]]:
        """
        List all versions of a specific file ordered by version_number ascending.
        """
        versions = (
            self.session.query(WorkspaceFileVersion)
            .filter_by(workspace_file_id=file_id)
            .order_by(WorkspaceFileVersion.version_number.asc())
            .all()
        )
        return [
            {
                "id": v.id,
                "workspaceFileId": v.workspace_file_id,
                "storageKey": v.storage_key,
                "fileSizeBytes": v.file_size_bytes,
                "sha256Hash": v.sha256_hash,
                "versionNumber": v.version_number,
                "createdAt": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]

    def save_file_version(
        self,
        file_id: str,
        version_number: int,
        storage_uri: str,
        checksum_sha256: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Save/register a new version of a file.
        Raises PersistenceConfigurationError if file record is missing or deleted.
        """
        file_rec = (
            self.session.query(WorkspaceFile)
            .filter_by(id=file_id)
            .filter(WorkspaceFile.deleted_at.is_(None))
            .first()
        )
        if not file_rec:
            raise PersistenceConfigurationError(f"WorkspaceFile '{file_id}' does not exist or has been deleted.")

        file_size_bytes = 0
        if metadata and "file_size_bytes" in metadata:
            try:
                file_size_bytes = int(metadata["file_size_bytes"])
            except (ValueError, TypeError):
                file_size_bytes = 0

        new_version = WorkspaceFileVersion(
            id=f"version_{uuid.uuid4().hex[:12]}",
            workspace_file_id=file_id,
            storage_key=storage_uri,
            file_size_bytes=file_size_bytes,
            sha256_hash=checksum_sha256 or "",
            version_number=version_number
        )
        self.session.add(new_version)
        
        if metadata:
            existing_meta = file_rec.file_metadata or {}
            file_rec.file_metadata = {**existing_meta, **metadata}
            
        self.session.commit()
        
        return {
            "id": new_version.id,
            "workspaceFileId": new_version.workspace_file_id,
            "storageKey": new_version.storage_key,
            "fileSizeBytes": new_version.file_size_bytes,
            "sha256Hash": new_version.sha256_hash,
            "versionNumber": new_version.version_number,
            "createdAt": new_version.created_at.isoformat() if new_version.created_at else None,
        }


class DatabaseAnalysisRunRepository(AnalysisRunRepository):
    """
    SQLAlchemy-backed implementation of the AnalysisRunRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session

    def _to_dict(self, run: DbAnalysisRun) -> Dict[str, Any]:
        return {
            "id": run.id,
            "workspaceId": run.workspace_id,
            "snapshotId": run.snapshot_version_id or "",
            "runType": run.run_type,
            "status": run.status,
            "inputs": run.input_payload or {},
            "results": run.output_payload or {},
            "warnings": (run.summary or {}).get("warnings", []),
            "errors": (run.summary or {}).get("errors", []),
            "sourceTrace": (run.run_metadata or {}).get("source_trace", {}),
            "logicVersion": (run.run_metadata or {}).get("logic_version", "v1"),
            "createdAt": run.created_at.isoformat() if run.created_at else None,
            "completedAt": run.completed_at.isoformat() if run.completed_at else None,
            "durationMs": run.duration_ms
        }

    def save_run(
        self,
        workspace_id: str,
        run_type: str,
        status: str,
        input_payload: Optional[Dict[str, Any]] = None,
        output_payload: Optional[Dict[str, Any]] = None,
        summary: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Save/register a new analysis run execution result.
        Raises PersistenceConfigurationError if target workspace does not exist.
        """
        workspace = self.session.query(Workspace).filter_by(id=workspace_id).first()
        if not workspace:
            raise PersistenceConfigurationError(f"Workspace '{workspace_id}' does not exist.")
            
        org_id = workspace.organization_id
        run_id = (metadata or {}).get("run_id") or f"run_{workspace_id}_{uuid.uuid4().hex[:8]}"
        snapshot_id = (metadata or {}).get("snapshot_id", "") or (input_payload or {}).get("snapshot_id", "")
        
        completed_at = None
        if status in ("completed", "failed", "cancelled"):
            completed_at = datetime.now(timezone.utc)
            
        existing_run = self.session.query(DbAnalysisRun).filter_by(id=run_id).first()
        if existing_run:
            existing_run.status = status
            existing_run.snapshot_version_id = snapshot_id or None
            existing_run.duration_ms = (metadata or {}).get("duration_ms")
            existing_run.error_message = error_message
            existing_run.input_payload = input_payload or {}
            existing_run.output_payload = output_payload or {}
            existing_run.summary = summary or {}
            existing_run.run_metadata = metadata or {}
            if completed_at:
                existing_run.completed_at = completed_at
            self.session.commit()
            return self._to_dict(existing_run)
            
        run = DbAnalysisRun(
            id=run_id,
            workspace_id=workspace_id,
            organization_id=org_id,
            run_type=run_type,
            status=status,
            snapshot_version_id=snapshot_id or None,
            duration_ms=(metadata or {}).get("duration_ms"),
            error_message=error_message,
            input_payload=input_payload or {},
            output_payload=output_payload or {},
            summary=summary or {},
            run_metadata=metadata or {},
            started_at=datetime.now(timezone.utc),
            completed_at=completed_at
        )
        self.session.add(run)
        self.session.commit()
        return self._to_dict(run)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an analysis run by ID.
        """
        run = (
            self.session.query(DbAnalysisRun)
            .join(Workspace, Workspace.id == DbAnalysisRun.workspace_id)
            .filter(DbAnalysisRun.id == run_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not run:
            return None
        return self._to_dict(run)

    def list_runs(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all analysis runs for a workspace, sorted newest first.
        """
        runs = (
            self.session.query(DbAnalysisRun)
            .join(Workspace, Workspace.id == DbAnalysisRun.workspace_id)
            .filter(DbAnalysisRun.workspace_id == workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .order_by(DbAnalysisRun.created_at.desc())
            .all()
        )
        return [self._to_dict(r) for r in runs]

    def list_recent_runs(self, workspace_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List the most recent analysis runs for a workspace, sorted newest first, up to a limit.
        """
        runs = (
            self.session.query(DbAnalysisRun)
            .join(Workspace, Workspace.id == DbAnalysisRun.workspace_id)
            .filter(DbAnalysisRun.workspace_id == workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .order_by(DbAnalysisRun.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_dict(r) for r in runs]

    def update_run_status(
        self,
        run_id: str,
        status: str,
        output_payload: Optional[Dict[str, Any]] = None,
        summary: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update the status/outputs/errors of an analysis run.
        """
        run = self.session.query(DbAnalysisRun).filter_by(id=run_id).first()
        if not run:
            raise PersistenceConfigurationError(f"AnalysisRun '{run_id}' does not exist.")
            
        run.status = status
        if output_payload is not None:
            run.output_payload = output_payload
        if summary is not None:
            run.summary = summary
        if error_message is not None:
            run.error_message = error_message
            
        if status in ("completed", "failed", "cancelled"):
            run.completed_at = datetime.now(timezone.utc)
            if run.started_at:
                started_at = run.started_at
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                completed_at = run.completed_at
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=timezone.utc)
                diff = completed_at - started_at
                run.duration_ms = int(diff.total_seconds() * 1000)
                
        self.session.commit()
        return self._to_dict(run)


class DatabaseAuditEventRepository(AuditEventRepository):
    """
    SQLAlchemy-backed implementation of the AuditEventRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session

    def _to_dict(self, event: DbAuditEvent) -> Dict[str, Any]:
        return {
            "id": event.id,
            "workspaceId": event.workspace_id or "",
            "eventType": event.action,
            "description": event.description or "",
            "timestamp": event.created_at.isoformat() if event.created_at else None
        }

    def append_event(
        self,
        workspace_id: Optional[str],
        event_type: str,
        description: str,
        actor_user_id: Optional[str] = None,
        event_payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Append an audit event log entry.
        """
        if workspace_id:
            workspace = (
                self.session.query(Workspace)
                .filter_by(id=workspace_id)
                .filter(Workspace.deleted_at.is_(None))
                .filter(Workspace.status != "deleted")
                .first()
            )
            if not workspace:
                raise PersistenceConfigurationError(f"Workspace '{workspace_id}' does not exist or has been deleted.")
            org_id = workspace.organization_id
        else:
            # Check metadata or event_payload for organization_id
            org_id = (metadata or {}).get("organization_id") or (event_payload or {}).get("organization_id")
            if not org_id:
                raise PersistenceConfigurationError(
                    "organization_id must be provided in metadata or event_payload for organization-level events."
                )

        event_id = f"audit_{uuid.uuid4().hex[:12]}"
        
        event = DbAuditEvent(
            id=event_id,
            organization_id=org_id,
            workspace_id=workspace_id,
            user_id=actor_user_id,
            action=event_type,
            description=description,
            context_payload=event_payload or {},
            event_metadata=metadata or {},
            created_at=datetime.now(timezone.utc)
        )
        self.session.add(event)
        self.session.commit()
        return self._to_dict(event)

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific audit event by ID.
        """
        event = self.session.query(DbAuditEvent).filter_by(id=event_id).first()
        if not event:
            return None
        return self._to_dict(event)

    def list_events(self, workspace_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List audit events under a given workspace (or globally if None) up to a limit, newest first.
        """
        query = self.session.query(DbAuditEvent)
        if workspace_id is not None:
            query = (
                query.join(Workspace, Workspace.id == DbAuditEvent.workspace_id)
                .filter(DbAuditEvent.workspace_id == workspace_id)
                .filter(Workspace.deleted_at.is_(None))
                .filter(Workspace.status != "deleted")
            )
        
        events = query.order_by(DbAuditEvent.created_at.desc()).limit(limit).all()
        return [self._to_dict(e) for e in events]

    def list_organization_events(self, organization_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all audit events for a given organization up to a limit, newest first.
        """
        events = (
            self.session.query(DbAuditEvent)
            .filter_by(organization_id=organization_id)
            .order_by(DbAuditEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_dict(e) for e in events]


class DatabaseJobRepository(JobRepository):
    """
    SQLAlchemy-backed implementation of the JobRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session

    def _to_dict(self, job: DbJob) -> Dict[str, Any]:
        return {
            "id": job.id,
            "workspaceId": job.workspace_id or "",
            "organizationId": job.organization_id,
            "jobType": job.task_name,
            "status": job.status,
            "payload": job.arguments or {},
            "result": job.result_payload or {},
            "errorMessage": job.error_log or "",
            "metadata": job.job_metadata or {},
            "queuedAt": job.created_at.isoformat() if job.created_at else None,
            "startedAt": job.started_at.isoformat() if job.started_at else None,
            "completedAt": job.completed_at.isoformat() if job.completed_at else None,
        }

    def create_job(
        self,
        job_type: str,
        workspace_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Register a background job task execution record.
        """
        if workspace_id:
            workspace = (
                self.session.query(Workspace)
                .filter_by(id=workspace_id)
                .filter(Workspace.deleted_at.is_(None))
                .filter(Workspace.status != "deleted")
                .first()
            )
            if not workspace:
                raise PersistenceConfigurationError(f"Workspace '{workspace_id}' does not exist or has been deleted.")
            org_id = workspace.organization_id
        else:
            org_id = (metadata or {}).get("organization_id") or (payload or {}).get("organization_id")
            if not org_id:
                # Fallback to org_default only if organization org_default exists
                default_org = self.session.query(Organization).filter_by(id="org_default").first()
                if not default_org:
                    raise PersistenceConfigurationError(
                        "organization_id must be provided for system jobs when default organization does not exist."
                    )
                org_id = "org_default"

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        job = DbJob(
            id=job_id,
            workspace_id=workspace_id,
            organization_id=org_id,
            task_name=job_type,
            status="pending",
            attempts=0,
            arguments=payload or {},
            result_payload={},
            error_log=None,
            job_metadata=metadata or {},
            started_at=None,
            completed_at=None
        )
        self.session.add(job)
        self.session.commit()
        return self._to_dict(job)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job execution details by ID.
        """
        job = self.session.query(DbJob).filter_by(id=job_id).first()
        if not job:
            return None
        return self._to_dict(job)

    def list_jobs(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List background jobs with optional workspace/status filtering, newest first.
        """
        query = self.session.query(DbJob)
        if workspace_id is not None:
            query = query.filter_by(workspace_id=workspace_id)
        if status is not None:
            query = query.filter_by(status=status)
            
        jobs = query.order_by(DbJob.created_at.desc()).limit(limit).all()
        return [self._to_dict(j) for j in jobs]

    def update_job_status(
        self,
        job_id: str,
        status: str,
        result_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update active status of a background job.
        """
        job = self.session.query(DbJob).filter_by(id=job_id).first()
        if not job:
            raise PersistenceConfigurationError(f"Job '{job_id}' does not exist.")
            
        job.status = status
        if result_payload is not None:
            job.result_payload = result_payload
        if error_message is not None:
            job.error_log = error_message
        if metadata is not None:
            job.job_metadata = {**(job.job_metadata or {}), **metadata}
            
        if status == "running" and job.started_at is None:
            job.started_at = datetime.now(timezone.utc)
        elif status in ("completed", "failed", "cancelled"):
            if job.completed_at is None:
                job.completed_at = datetime.now(timezone.utc)
            if job.started_at is None:
                job.started_at = job.created_at or datetime.now(timezone.utc)
                
        self.session.commit()
        return self._to_dict(job)

    def mark_job_started(self, job_id: str) -> Dict[str, Any]:
        """
        Mark job execution as active/started.
        """
        return self.update_job_status(job_id, "running")

    def mark_job_completed(self, job_id: str, result_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Mark job execution as successfully completed.
        """
        return self.update_job_status(job_id, "completed", result_payload=result_payload)

    def mark_job_failed(self, job_id: str, error_message: str) -> Dict[str, Any]:
        """
        Mark job execution as failed with an error message.
        """
        return self.update_job_status(job_id, "failed", error_message=error_message)


class DatabaseReportRepository(ReportRepository):
    """
    SQLAlchemy-backed implementation of the ReportRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session

    def _to_dict(self, report: DbReport) -> Dict[str, Any]:
        return {
            "id": report.id,
            "workspaceId": report.workspace_id,
            "organizationId": report.organization_id,
            "reportType": report.report_type,
            "title": report.report_name,
            "status": report.status,
            "reportPayload": report.report_payload,
            "storageUri": report.storage_uri,
            "metadata": report.report_metadata or {},
            "createdAt": report.created_at.isoformat() if report.created_at else None,
            "updatedAt": report.updated_at.isoformat() if report.updated_at else None,
        }

    def save_report(
        self,
        workspace_id: str,
        report_type: str,
        title: str,
        report_payload: Optional[Dict[str, Any]] = None,
        storage_uri: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        workspace = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not workspace:
            raise PersistenceConfigurationError(f"Workspace '{workspace_id}' does not exist or has been deleted.")

        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        report = DbReport(
            id=report_id,
            workspace_id=workspace_id,
            organization_id=workspace.organization_id,
            report_name=title,
            report_type=report_type,
            status="completed",
            report_payload=report_payload,
            storage_uri=storage_uri,
            report_metadata=metadata or {},
        )
        self.session.add(report)
        self.session.commit()
        return self._to_dict(report)

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        report = (
            self.session.query(DbReport)
            .filter_by(id=report_id)
            .filter(DbReport.deleted_at.is_(None))
            .first()
        )
        if not report:
            return None
        return self._to_dict(report)

    def list_reports(
        self, workspace_id: str, report_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = (
            self.session.query(DbReport)
            .filter_by(workspace_id=workspace_id)
            .filter(DbReport.deleted_at.is_(None))
        )
        if report_type is not None:
            query = query.filter_by(report_type=report_type)

        reports = query.order_by(DbReport.created_at.desc()).limit(limit).all()
        return [self._to_dict(r) for r in reports]

    def update_report_status(
        self,
        report_id: str,
        status: str,
        storage_uri: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        report = (
            self.session.query(DbReport)
            .filter_by(id=report_id)
            .filter(DbReport.deleted_at.is_(None))
            .first()
        )
        if not report:
            raise PersistenceConfigurationError(f"Report '{report_id}' does not exist or has been deleted.")

        report.status = status
        if storage_uri is not None:
            report.storage_uri = storage_uri
        if metadata is not None:
            report.report_metadata = {**(report.report_metadata or {}), **metadata}

        self.session.commit()
        return self._to_dict(report)

    def delete_report(self, report_id: str) -> bool:
        report = (
            self.session.query(DbReport)
            .filter_by(id=report_id)
            .filter(DbReport.deleted_at.is_(None))
            .first()
        )
        if not report:
            return False

        report.deleted_at = datetime.now(timezone.utc)
        report.status = "deleted"
        self.session.commit()
        return True


class DatabaseFinancialSnapshotRepository(FinancialSnapshotRepository):
    """
    SQLAlchemy-backed implementation of the FinancialSnapshotRepository.
    Enforcement of tenant isolation and authorization is deferred to future auth/RBAC tasks.
    """
    def __init__(self, db_session: Session) -> None:
        self.session = db_session

    def get_active_snapshot(self, workspace_id: str) -> Optional[PydanticFinancialSnapshot]:
        """Get the active financial snapshot for a workspace."""
        ws = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not ws:
            return None

        db_snap = (
            self.session.query(DbFinancialSnapshot)
            .filter_by(workspace_id=workspace_id)
            .first()
        )
        if not db_snap:
            return None
        
        # Find the active version
        if db_snap.active_version_id:
            version = (
                self.session.query(DbFinancialSnapshotVersion)
                .filter_by(id=db_snap.active_version_id)
                .first()
            )
        else:
            version = (
                self.session.query(DbFinancialSnapshotVersion)
                .filter_by(financial_snapshot_id=db_snap.id)
                .order_by(DbFinancialSnapshotVersion.version_number.desc())
                .first()
            )
            
        if not version:
            return None
            
        # Deserialize from statement_data
        data = dict(version.statement_data)
        # Ensure ID and workspace ID match correctly
        data["id"] = version.id
        data["workspaceId"] = workspace_id
        return PydanticFinancialSnapshot.model_validate(data)

    def save_snapshot(self, snapshot: PydanticFinancialSnapshot) -> PydanticFinancialSnapshot:
        """Save a financial snapshot (and version it)."""
        # Check if DbFinancialSnapshot exists for the workspace
        db_snap = (
            self.session.query(DbFinancialSnapshot)
            .filter_by(workspace_id=snapshot.workspace_id)
            .first()
        )
        if not db_snap:
            # Query workspace to get organization_id
            ws = self.session.query(Workspace).filter_by(id=snapshot.workspace_id).first()
            org_id = ws.organization_id if ws else "org_default"
            db_snap = DbFinancialSnapshot(
                id=f"snap_ws_{snapshot.workspace_id}",
                workspace_id=snapshot.workspace_id,
                organization_id=org_id,
            )
            self.session.add(db_snap)
            self.session.flush()
        
        # Calculate next version number
        max_ver = (
            self.session.query(DbFinancialSnapshotVersion.version_number)
            .filter_by(financial_snapshot_id=db_snap.id)
            .order_by(DbFinancialSnapshotVersion.version_number.desc())
            .first()
        )
        next_ver = (max_ver[0] + 1) if max_ver else 1

        # Check if version with this id already exists to avoid duplicate inserts
        existing_version = (
            self.session.query(DbFinancialSnapshotVersion)
            .filter_by(id=snapshot.id)
            .first()
        )
        if existing_version:
            # Update statement_data
            existing_version.statement_data = snapshot.model_dump(by_alias=True)
            db_snap.active_version_id = snapshot.id
            self.session.commit()
            return snapshot

        # Create DbFinancialSnapshotVersion
        version = DbFinancialSnapshotVersion(
            id=snapshot.id,
            financial_snapshot_id=db_snap.id,
            version_number=next_ver,
            statement_data=snapshot.model_dump(by_alias=True),
            projections_data={}
        )
        self.session.add(version)
        db_snap.active_version_id = snapshot.id
        self.session.commit()
        return snapshot

    def list_snapshots(self, workspace_id: str) -> List[PydanticFinancialSnapshot]:
        """List all snapshots for a workspace."""
        ws = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if not ws:
            return []

        db_snap = (
            self.session.query(DbFinancialSnapshot)
            .filter_by(workspace_id=workspace_id)
            .first()
        )
        if not db_snap:
            return []
            
        versions = (
            self.session.query(DbFinancialSnapshotVersion)
            .filter_by(financial_snapshot_id=db_snap.id)
            .order_by(DbFinancialSnapshotVersion.version_number.desc())
            .all()
        )
        
        results = []
        for version in versions:
            data = dict(version.statement_data)
            data["id"] = version.id
            data["workspaceId"] = workspace_id
            results.append(PydanticFinancialSnapshot.model_validate(data))
        return results



