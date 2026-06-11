import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Workspace, Organization, WorkspaceFile, WorkspaceFileVersion, AnalysisRun as DbAnalysisRun
from app.models.workspace import CompanyWorkspace
from app.persistence.interfaces import WorkspaceRepository, FileMetadataRepository, AnalysisRunRepository
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
        
        existing = (
            self.session.query(Workspace)
            .filter_by(id=workspace_id)
            .filter(Workspace.deleted_at.is_(None))
            .filter(Workspace.status != "deleted")
            .first()
        )
        if existing:
            return CompanyWorkspace(
                id=existing.id,
                companyName=existing.name,
                createdAt=existing.created_at.isoformat(),
                metadata=existing.workspace_metadata or {}
            )

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
        run_id = f"run_{workspace_id}_{uuid.uuid4().hex[:8]}"
        snapshot_id = (metadata or {}).get("snapshot_id", "") or (input_payload or {}).get("snapshot_id", "")
        
        completed_at = None
        if status in ("completed", "failed", "cancelled"):
            completed_at = datetime.now(timezone.utc)
            
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
        run = self.session.query(DbAnalysisRun).filter_by(id=run_id).first()
        if not run:
            return None
        return self._to_dict(run)

    def list_runs(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        List all analysis runs for a workspace, sorted newest first.
        """
        runs = (
            self.session.query(DbAnalysisRun)
            .filter_by(workspace_id=workspace_id)
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
            .filter_by(workspace_id=workspace_id)
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
