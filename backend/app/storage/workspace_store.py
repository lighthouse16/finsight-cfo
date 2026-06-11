import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models.workspace import CompanyWorkspace, FinancialSnapshot, AnalysisRun, AuditEvent

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage_db")

os.makedirs(STORAGE_DIR, exist_ok=True)

class WorkspaceStore:
    _lock = threading.Lock()
    _workspaces_file = os.path.join(STORAGE_DIR, "workspaces.json")
    _snapshots_file = os.path.join(STORAGE_DIR, "snapshots.json")
    _runs_file = os.path.join(STORAGE_DIR, "runs.json")
    _audits_file = os.path.join(STORAGE_DIR, "audits.json")

    @classmethod
    def _read_json(cls, filepath: str) -> List[dict]:
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []

    @classmethod
    def _write_json(cls, filepath: str, data: List[dict]):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def create_workspace(cls, id: str, company_name: str, metadata: Optional[dict] = None) -> CompanyWorkspace:
        with cls._lock:
            workspaces = cls._read_json(cls._workspaces_file)
            for w in workspaces:
                if w.get("id") == id:
                    return CompanyWorkspace.model_validate(w)
            
            new_workspace = {
                "id": id,
                "companyName": company_name,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            }
            workspaces.append(new_workspace)
            cls._write_json(cls._workspaces_file, workspaces)
            
            # Auto log audit event
            cls._log_audit_event_unlocked(id, "workspace_created", f"Created workspace for {company_name}")
            
            return CompanyWorkspace.model_validate(new_workspace)

    @classmethod
    def get_workspace(cls, workspace_id: str) -> Optional[CompanyWorkspace]:
        with cls._lock:
            workspaces = cls._read_json(cls._workspaces_file)
            for w in workspaces:
                if w.get("id") == workspace_id:
                    return CompanyWorkspace.model_validate(w)
            return None

    @classmethod
    def list_workspaces(cls) -> List[CompanyWorkspace]:
        with cls._lock:
            workspaces = cls._read_json(cls._workspaces_file)
            return [CompanyWorkspace.model_validate(w) for w in workspaces]

    @classmethod
    def save_snapshot(cls, snapshot: FinancialSnapshot) -> FinancialSnapshot:
        with cls._lock:
            snapshots = cls._read_json(cls._snapshots_file)
            # Retain only one active approved snapshot per workspace for simplicity, or version them
            # We will version them by ID, but can set active
            snapshots = [s for s in snapshots if s.get("id") != snapshot.id]
            snapshots.append(snapshot.model_dump(by_alias=True))
            cls._write_json(cls._snapshots_file, snapshots)
            
            cls._log_audit_event_unlocked(
                snapshot.workspace_id, 
                "snapshot_built", 
                f"Compiled financial snapshot {snapshot.id} for period {snapshot.reporting_period}"
            )
            return snapshot

    @classmethod
    def get_active_snapshot(cls, workspace_id: str) -> Optional[FinancialSnapshot]:
        with cls._lock:
            snapshots = cls._read_json(cls._snapshots_file)
            # Find the most recently created approved snapshot for this workspace
            workspace_snaps = [s for s in snapshots if s.get("workspaceId") == workspace_id and s.get("approved", True)]
            if not workspace_snaps:
                return None
            # Sort by createdAt
            workspace_snaps.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            return FinancialSnapshot.model_validate(workspace_snaps[0])

    @classmethod
    def get_snapshot(cls, snapshot_id: str) -> Optional[FinancialSnapshot]:
        with cls._lock:
            snapshots = cls._read_json(cls._snapshots_file)
            for s in snapshots:
                if s.get("id") == snapshot_id:
                    return FinancialSnapshot.model_validate(s)
            return None

    @classmethod
    def save_analysis_run(cls, run: AnalysisRun) -> AnalysisRun:
        with cls._lock:
            runs = cls._read_json(cls._runs_file)
            runs = [r for r in runs if r.get("id") != run.id]
            runs.append(run.model_dump(by_alias=True))
            cls._write_json(cls._runs_file, runs)
            return run

    @classmethod
    def get_latest_analysis_run(cls, workspace_id: str) -> Optional[AnalysisRun]:
        with cls._lock:
            runs = cls._read_json(cls._runs_file)
            workspace_runs = [r for r in runs if r.get("workspaceId") == workspace_id]
            if not workspace_runs:
                return None
            workspace_runs.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            return AnalysisRun.model_validate(workspace_runs[0])

    @classmethod
    def get_latest_run_by_type(cls, workspace_id: str, run_type: str) -> Optional[AnalysisRun]:
        with cls._lock:
            runs = cls._read_json(cls._runs_file)
            workspace_runs = [
                r for r in runs 
                if r.get("workspaceId") == workspace_id and r.get("runType") == run_type
            ]
            if not workspace_runs:
                return None
            workspace_runs.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            return AnalysisRun.model_validate(workspace_runs[0])

    @classmethod
    def list_runs(cls, workspace_id: str, run_type: Optional[str] = None) -> List[AnalysisRun]:
        with cls._lock:
            runs = cls._read_json(cls._runs_file)
            workspace_runs = [r for r in runs if r.get("workspaceId") == workspace_id]
            if run_type:
                workspace_runs = [r for r in workspace_runs if r.get("runType") == run_type]
            workspace_runs.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
            return [AnalysisRun.model_validate(r) for r in workspace_runs]

    @classmethod
    def get_run(cls, run_id: str) -> Optional[AnalysisRun]:
        with cls._lock:
            runs = cls._read_json(cls._runs_file)
            for r in runs:
                if r.get("id") == run_id:
                    return AnalysisRun.model_validate(r)
            return None

    @classmethod
    def _log_audit_event_unlocked(cls, workspace_id: str, event_type: str, description: str):
        audits = cls._read_json(cls._audits_file)
        new_audit = {
            "id": f"audit_{datetime.now(timezone.utc).timestamp()}",
            "workspaceId": workspace_id,
            "eventType": event_type,
            "description": description,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        audits.append(new_audit)
        cls._write_json(cls._audits_file, audits)

    @classmethod
    def log_audit_event(cls, workspace_id: str, event_type: str, description: str) -> AuditEvent:
        with cls._lock:
            audits = cls._read_json(cls._audits_file)
            new_audit = {
                "id": f"audit_{datetime.now(timezone.utc).timestamp()}",
                "workspaceId": workspace_id,
                "eventType": event_type,
                "description": description,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            audits.append(new_audit)
            cls._write_json(cls._audits_file, audits)
            return AuditEvent.model_validate(new_audit)

    @classmethod
    def get_audit_events(cls, workspace_id: str) -> List[AuditEvent]:
        with cls._lock:
            audits = cls._read_json(cls._audits_file)
            workspace_audits = [a for a in audits if a.get("workspaceId") == workspace_id]
            workspace_audits.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return [AuditEvent.model_validate(a) for a in workspace_audits]

    @classmethod
    def delete_workspace(cls, workspace_id: str) -> bool:
        with cls._lock:
            # 1. Delete workspace
            workspaces = cls._read_json(cls._workspaces_file)
            found = False
            remaining_workspaces = []
            for w in workspaces:
                if w.get("id") == workspace_id:
                    found = True
                else:
                    remaining_workspaces.append(w)
            
            if not found:
                return False
                
            cls._write_json(cls._workspaces_file, remaining_workspaces)
            
            # 2. Delete snapshots
            snapshots = cls._read_json(cls._snapshots_file)
            remaining_snapshots = [s for s in snapshots if s.get("workspaceId") != workspace_id]
            cls._write_json(cls._snapshots_file, remaining_snapshots)
            
            # 3. Delete runs
            runs = cls._read_json(cls._runs_file)
            remaining_runs = [r for r in runs if r.get("workspaceId") != workspace_id]
            cls._write_json(cls._runs_file, remaining_runs)
            
            # 4. Delete audits
            audits = cls._read_json(cls._audits_file)
            remaining_audits = [a for a in audits if a.get("workspaceId") != workspace_id]
            cls._write_json(cls._audits_file, remaining_audits)
            
            return True
