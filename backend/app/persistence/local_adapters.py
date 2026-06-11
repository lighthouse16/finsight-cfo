from typing import Any, Dict, List, Optional
from app.models.workspace import CompanyWorkspace, FinancialSnapshot, AnalysisRun, AuditEvent
from app.storage.workspace_store import WorkspaceStore
from app.persistence.interfaces import (
    WorkspaceRepository,
    FileMetadataRepository,
    FinancialSnapshotRepository,
    AnalysisRunRepository,
    AuditEventRepository,
    JobRepository,
    ReportRepository,
)

class LocalWorkspaceRepository(WorkspaceRepository):
    def list_workspaces(self) -> List[CompanyWorkspace]:
        return WorkspaceStore.list_workspaces()

    def get_workspace(self, workspace_id: str) -> Optional[CompanyWorkspace]:
        return WorkspaceStore.get_workspace(workspace_id)

    def create_workspace(self, workspace_id: str, company_name: str, metadata: Optional[Dict[str, Any]] = None) -> CompanyWorkspace:
        return WorkspaceStore.create_workspace(workspace_id, company_name, metadata)

    def delete_workspace(self, workspace_id: str) -> bool:
        return WorkspaceStore.delete_workspace(workspace_id)

    def get_active_workspace(self) -> Optional[CompanyWorkspace]:
        workspaces = self.list_workspaces()
        return workspaces[0] if workspaces else None

class LocalFileMetadataRepository(FileMetadataRepository):
    def list_file_records(self, workspace_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("LocalFileMetadataRepository.list_file_records is not implemented.")

    def get_file_record(self, file_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("LocalFileMetadataRepository.get_file_record is not implemented.")

    def save_file_record(self, file_record: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("LocalFileMetadataRepository.save_file_record is not implemented.")

    def delete_file_record(self, file_id: str) -> bool:
        raise NotImplementedError("LocalFileMetadataRepository.delete_file_record is not implemented.")

class LocalFinancialSnapshotRepository(FinancialSnapshotRepository):
    def get_active_snapshot(self, workspace_id: str) -> Optional[FinancialSnapshot]:
        return WorkspaceStore.get_active_snapshot(workspace_id)

    def save_snapshot(self, snapshot: Any) -> Any:
        return WorkspaceStore.save_snapshot(snapshot)

    def list_snapshots(self, workspace_id: str) -> List[FinancialSnapshot]:
        # Local JSON has snapshots file but not a list_snapshots helper.
        # We can implement it or default to NotImplementedError. Let's return active if present or minimal.
        active = self.get_active_snapshot(workspace_id)
        return [active] if active else []

class LocalAnalysisRunRepository(AnalysisRunRepository):
    def save_run(self, run: Any) -> Any:
        return WorkspaceStore.save_analysis_run(run)

    def get_run(self, run_id: str) -> Optional[AnalysisRun]:
        return WorkspaceStore.get_run(run_id)

    def list_runs(self, workspace_id: str) -> List[AnalysisRun]:
        return WorkspaceStore.list_runs(workspace_id)

    def list_recent_runs(self, workspace_id: str, limit: int = 20) -> List[AnalysisRun]:
        runs = self.list_runs(workspace_id)
        return runs[:limit]

class LocalAuditEventRepository(AuditEventRepository):
    def append_event(self, workspace_id: str, event_type: str, description: str) -> AuditEvent:
        return WorkspaceStore.log_audit_event(workspace_id, event_type, description)

    def list_events(self, workspace_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        if not workspace_id:
            return []
        events = WorkspaceStore.get_audit_events(workspace_id)
        return events[:limit]

class LocalJobRepository(JobRepository):
    def create_job(self, task_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        raise NotImplementedError("LocalJobRepository.create_job is not implemented.")

    def get_job(self, job_id: str) -> Optional[Any]:
        raise NotImplementedError("LocalJobRepository.get_job is not implemented.")

    def update_job_status(self, job_id: str, status: str, error_log: Optional[str] = None) -> Any:
        raise NotImplementedError("LocalJobRepository.update_job_status is not implemented.")

class LocalReportRepository(ReportRepository):
    def save_report(self, report: Any) -> Any:
        raise NotImplementedError("LocalReportRepository.save_report is not implemented.")

    def get_report(self, report_id: str) -> Optional[Any]:
        raise NotImplementedError("LocalReportRepository.get_report is not implemented.")

    def list_reports(self, workspace_id: str) -> List[Any]:
        raise NotImplementedError("LocalReportRepository.list_reports is not implemented.")
