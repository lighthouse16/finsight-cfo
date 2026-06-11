from typing import Any, Dict, List, Optional, Protocol

class WorkspaceRepository(Protocol):
    def list_workspaces(self) -> List[Any]:
        """List all workspaces."""
        ...

    def get_workspace(self, workspace_id: str) -> Optional[Any]:
        """Retrieve a specific workspace by ID."""
        ...

    def create_workspace(self, workspace_id: str, company_name: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Create a new workspace."""
        ...

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace and all its associated data."""
        ...

    def get_active_workspace(self) -> Optional[Any]:
        """Retrieve the active workspace (if any)."""
        ...

class FileMetadataRepository(Protocol):
    def list_file_records(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List all file records within a workspace."""
        ...

    def get_file_record(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific file record by ID."""
        ...

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
        """Save/register a file metadata record."""
        ...

    def delete_file_record(self, file_id: str) -> bool:
        """Delete a file metadata record."""
        ...

    def list_file_versions(self, file_id: str) -> List[Dict[str, Any]]:
        """List all versions of a specific file."""
        ...

    def save_file_version(
        self,
        file_id: str,
        version_number: int,
        storage_uri: str,
        checksum_sha256: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save/register a new version of a file."""
        ...

class FinancialSnapshotRepository(Protocol):
    def get_active_snapshot(self, workspace_id: str) -> Optional[Any]:
        """Get the active financial snapshot for a workspace."""
        ...

    def save_snapshot(self, snapshot: Any) -> Any:
        """Save a financial snapshot (and version it)."""
        ...

    def list_snapshots(self, workspace_id: str) -> List[Any]:
        """List all snapshots for a workspace."""
        ...

class AnalysisRunRepository(Protocol):
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
        """Save an analysis run execution result."""
        ...

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get an analysis run by ID."""
        ...

    def list_runs(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List all analysis runs for a workspace."""
        ...

    def list_recent_runs(self, workspace_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List the most recent analysis runs for a workspace up to a limit."""
        ...

    def update_run_status(
        self,
        run_id: str,
        status: str,
        output_payload: Optional[Dict[str, Any]] = None,
        summary: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update active status of an analysis run."""
        ...

class AuditEventRepository(Protocol):
    def append_event(
        self,
        workspace_id: Optional[str],
        event_type: str,
        description: str,
        actor_user_id: Optional[str] = None,
        event_payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append an audit event log entry."""
        ...

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific audit event by ID."""
        ...

    def list_events(self, workspace_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List audit events under a given workspace (or globally) up to a limit."""
        ...

    def list_organization_events(self, organization_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """List all audit events for a given organization."""
        ...

class JobRepository(Protocol):
    def create_job(
        self,
        job_type: str,
        workspace_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a background job task execution record."""
        ...

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job execution details by ID."""
        ...

    def list_jobs(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List background jobs with optional workspace/status filtering."""
        ...

    def update_job_status(
        self,
        job_id: str,
        status: str,
        result_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update active status of a background job."""
        ...

    def mark_job_started(self, job_id: str) -> Dict[str, Any]:
        """Mark job execution as active/started."""
        ...

    def mark_job_completed(self, job_id: str, result_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mark job execution as successfully completed."""
        ...

    def mark_job_failed(self, job_id: str, error_message: str) -> Dict[str, Any]:
        """Mark job execution as failed with an error message."""
        ...

class ReportRepository(Protocol):
    def save_report(
        self,
        workspace_id: str,
        report_type: str,
        title: str,
        report_payload: Optional[Dict[str, Any]] = None,
        storage_uri: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save generated report details."""
        ...

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report details by ID."""
        ...

    def list_reports(
        self, workspace_id: str, report_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List all generated reports within a workspace."""
        ...

    def update_report_status(
        self,
        report_id: str,
        status: str,
        storage_uri: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update active status of a report."""
        ...

    def delete_report(self, report_id: str) -> bool:
        """Delete/soft-delete a report by ID."""
        ...
