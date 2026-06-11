import uuid
from datetime import datetime, timezone
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
        from app.storage.file_store import FileStore
        records = FileStore.list_file_records(workspace_id)
        return [r.model_dump(by_alias=True) for r in records]

    def get_file_record(self, file_id: str) -> Optional[Dict[str, Any]]:
        from app.storage.file_store import FileStore
        record = FileStore.get_file_record(file_id)
        return record.model_dump(by_alias=True) if record else None

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
        raise NotImplementedError("LocalFileMetadataRepository.save_file_record is not implemented. Use FileStore directly in local mode.")

    def delete_file_record(self, file_id: str) -> bool:
        from app.storage.file_store import FileStore
        return FileStore.delete_file(file_id)

    def list_file_versions(self, file_id: str) -> List[Dict[str, Any]]:
        return []

    def save_file_version(
        self,
        file_id: str,
        version_number: int,
        storage_uri: str,
        checksum_sha256: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("LocalFileMetadataRepository.save_file_version is not implemented.")

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
        run_id = (metadata or {}).get("run_id") or f"run_{uuid.uuid4().hex[:12]}"
        snapshot_id = (metadata or {}).get("snapshot_id", "") or (input_payload or {}).get("snapshot_id", "")
        warnings = (summary or {}).get("warnings", [])
        errors = (summary or {}).get("errors", [])
        if error_message and error_message not in errors:
            errors = list(errors) + [error_message]

        dto = AnalysisRun(
            id=run_id,
            workspaceId=workspace_id,
            snapshotId=snapshot_id,
            runType=run_type,
            status=status,
            inputs=input_payload or {},
            results=output_payload or {},
            warnings=warnings,
            errors=errors,
            sourceTrace=(metadata or {}).get("source_trace", {}),
            logicVersion=(metadata or {}).get("logic_version", "v1"),
            createdAt=datetime.now(timezone.utc).isoformat(),
            completedAt=datetime.now(timezone.utc).isoformat() if status in ("completed", "failed", "cancelled") else None,
            durationMs=None
        )
        saved = WorkspaceStore.save_analysis_run(dto)
        return saved.model_dump(by_alias=True)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        dto = WorkspaceStore.get_run(run_id)
        return dto.model_dump(by_alias=True) if dto else None

    def list_runs(self, workspace_id: str) -> List[Dict[str, Any]]:
        dtos = WorkspaceStore.list_runs(workspace_id)
        return [d.model_dump(by_alias=True) for d in dtos]

    def list_recent_runs(self, workspace_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        dtos = WorkspaceStore.list_runs(workspace_id)
        return [d.model_dump(by_alias=True) for d in dtos[:limit]]

    def update_run_status(
        self,
        run_id: str,
        status: str,
        output_payload: Optional[Dict[str, Any]] = None,
        summary: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        dto = WorkspaceStore.get_run(run_id)
        if not dto:
            raise ValueError(f"Run {run_id} not found")

        dto.status = status
        if output_payload is not None:
            dto.results = output_payload
        if summary is not None:
            dto.warnings = summary.get("warnings", dto.warnings)
            dto.errors = summary.get("errors", dto.errors)
        if error_message:
            if error_message not in dto.errors:
                dto.errors = list(dto.errors) + [error_message]
        if status in ("completed", "failed", "cancelled"):
            dto.completed_at = datetime.now(timezone.utc).isoformat()

        saved = WorkspaceStore.save_analysis_run(dto)
        return saved.model_dump(by_alias=True)

class LocalAuditEventRepository(AuditEventRepository):
    def append_event(
        self,
        workspace_id: Optional[str],
        event_type: str,
        description: str,
        actor_user_id: Optional[str] = None,
        event_payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not workspace_id:
            raise ValueError("workspace_id is required for LocalAuditEventRepository.")
        saved = WorkspaceStore.log_audit_event(workspace_id, event_type, description)
        return saved.model_dump(by_alias=True)

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        try:
            audits = WorkspaceStore._read_json(WorkspaceStore._audits_file)
            for a in audits:
                if a.get("id") == event_id:
                    return {
                        "id": a["id"],
                        "workspaceId": a["workspaceId"],
                        "eventType": a["eventType"],
                        "description": a["description"],
                        "timestamp": a["timestamp"]
                    }
        except Exception:
            pass
        return None

    def list_events(self, workspace_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if not workspace_id:
            return []
        events = WorkspaceStore.get_audit_events(workspace_id)
        return [e.model_dump(by_alias=True) for e in events[:limit]]

    def list_organization_events(self, organization_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return []

class LocalJobRepository(JobRepository):
    def create_job(
        self,
        job_type: str,
        workspace_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("LocalJobRepository.create_job is not implemented.")

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("LocalJobRepository.get_job is not implemented.")

    def list_jobs(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("LocalJobRepository.list_jobs is not implemented.")

    def update_job_status(
        self,
        job_id: str,
        status: str,
        result_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("LocalJobRepository.update_job_status is not implemented.")

    def mark_job_started(self, job_id: str) -> Dict[str, Any]:
        raise NotImplementedError("LocalJobRepository.mark_job_started is not implemented.")

    def mark_job_completed(self, job_id: str, result_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError("LocalJobRepository.mark_job_completed is not implemented.")

    def mark_job_failed(self, job_id: str, error_message: str) -> Dict[str, Any]:
        raise NotImplementedError("LocalJobRepository.mark_job_failed is not implemented.")

class LocalReportRepository(ReportRepository):
    def __init__(self) -> None:
        from app.storage.workspace_store import STORAGE_DIR
        import os
        self.reports_file = os.path.join(STORAGE_DIR, "reports.json")

    def _read_json(self) -> List[Dict[str, Any]]:
        import json
        import os
        if not os.path.exists(self.reports_file):
            return []
        try:
            with open(self.reports_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []

    def _write_json(self, data: List[Dict[str, Any]]) -> None:
        import json
        with open(self.reports_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_report(
        self,
        workspace_id: str,
        report_type: str,
        title: str,
        report_payload: Optional[Dict[str, Any]] = None,
        storage_uri: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        reports = self._read_json()
        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()
        new_report = {
            "id": report_id,
            "workspaceId": workspace_id,
            "organizationId": "org_default",
            "reportType": report_type,
            "title": title,
            "status": "completed",
            "reportPayload": report_payload or {},
            "storageUri": storage_uri,
            "metadata": metadata or {},
            "createdAt": now_str,
            "updatedAt": now_str,
        }
        reports.append(new_report)
        self._write_json(reports)
        return new_report

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        reports = self._read_json()
        for r in reports:
            if r.get("id") == report_id and r.get("status") != "deleted":
                return r
        return None

    def list_reports(
        self, workspace_id: str, report_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        reports = self._read_json()
        workspace_reports = [
            r for r in reports 
            if r.get("workspaceId") == workspace_id and r.get("status") != "deleted"
        ]
        if report_type:
            workspace_reports = [r for r in workspace_reports if r.get("reportType") == report_type]
        workspace_reports.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        return workspace_reports[:limit]

    def update_report_status(
        self,
        report_id: str,
        status: str,
        storage_uri: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        reports = self._read_json()
        for r in reports:
            if r.get("id") == report_id and r.get("status") != "deleted":
                r["status"] = status
                if storage_uri is not None:
                    r["storageUri"] = storage_uri
                if metadata is not None:
                    r["metadata"] = {**(r.get("metadata") or {}), **metadata}
                r["updatedAt"] = datetime.now(timezone.utc).isoformat()
                self._write_json(reports)
                return r
        raise ValueError(f"Report '{report_id}' does not exist or has been deleted.")

    def delete_report(self, report_id: str) -> bool:
        reports = self._read_json()
        for r in reports:
            if r.get("id") == report_id and r.get("status") != "deleted":
                r["status"] = "deleted"
                r["updatedAt"] = datetime.now(timezone.utc).isoformat()
                self._write_json(reports)
                return True
        return False
