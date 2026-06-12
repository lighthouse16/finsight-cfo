import json
import os
import shutil
import threading
from datetime import datetime, timezone
from typing import List, Optional
from app.models.workspace import UploadedFileRecord
from app.storage.workspace_store import STORAGE_DIR

class FileStore:
    _lock = threading.Lock()
    _files_file = os.path.join(STORAGE_DIR, "files.json")
    _upload_root = os.path.join(STORAGE_DIR, "uploads")

    @classmethod
    def _read_json(cls) -> List[dict]:
        if not os.path.exists(cls._files_file):
            return []
        try:
            with open(cls._files_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []

    @classmethod
    def _write_json(cls, data: List[dict]):
        with open(cls._files_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def save_file(
        cls, 
        workspace_id: str, 
        record_key: str, 
        file_name: str, 
        file_bytes: bytes,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> UploadedFileRecord:
        with cls._lock:
            files_meta = cls._read_json()
            
            # Determine extension
            ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "bin"
            
            # Workspace upload directory
            workspace_dir = os.path.join(cls._upload_root, workspace_id)
            os.makedirs(workspace_dir, exist_ok=True)
            
            # Physical file path
            dest_filename = f"{record_key}.{ext}"
            file_path = os.path.join(workspace_dir, dest_filename)
            
            # If an existing file for this record key exists in the workspace, we remove/replace it
            existing_record = None
            for meta in files_meta:
                if meta.get("workspaceId") == workspace_id and meta.get("recordKey") == record_key:
                    existing_record = meta
                    break
            
            if existing_record:
                # Remove old physical file if path differs or is overwritten
                old_path = existing_record.get("filePath")
                if old_path and os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass
                files_meta.remove(existing_record)

            # Write physical file content bytes
            with open(file_path, "wb") as f:
                f.write(file_bytes)
                
            # Create metadata record
            file_id = f"file_{workspace_id}_{record_key}_{int(datetime.now(timezone.utc).timestamp())}"
            new_file_record = {
                "id": file_id,
                "workspaceId": workspace_id,
                "recordKey": record_key,
                "fileName": file_name,
                "fileType": content_type,
                "fileSizeBytes": len(file_bytes),
                "status": "uploaded",
                "uploadedAt": datetime.now(timezone.utc).isoformat(),
                "filePath": file_path,
                "metadata": metadata or {}
            }
            
            files_meta.append(new_file_record)
            cls._write_json(files_meta)
            
            from app.storage.workspace_store import WorkspaceStore
            WorkspaceStore.log_audit_event(
                workspace_id, 
                "file_uploaded", 
                f"Uploaded file '{file_name}' for record type '{record_key}'"
            )
            
            return UploadedFileRecord.model_validate(new_file_record)

    @classmethod
    def get_file_record(cls, file_id: str) -> Optional[UploadedFileRecord]:
        with cls._lock:
            files_meta = cls._read_json()
            for f in files_meta:
                if f.get("id") == file_id:
                    return UploadedFileRecord.model_validate(f)
            return None

    @classmethod
    def list_file_records(cls, workspace_id: str) -> List[UploadedFileRecord]:
        with cls._lock:
            files_meta = cls._read_json()
            workspace_files = [f for f in files_meta if f.get("workspaceId") == workspace_id]
            return [UploadedFileRecord.model_validate(f) for f in workspace_files]

    @classmethod
    def get_file_content(cls, file_id: str) -> Optional[bytes]:
        record = cls.get_file_record(file_id)
        if not record or not record.file_path:
            return None
        if not os.path.exists(record.file_path):
            return None
        try:
            with open(record.file_path, "rb") as f:
                return f.read()
        except Exception:
            return None

    @classmethod
    def delete_file(cls, file_id: str) -> bool:
        with cls._lock:
            files_meta = cls._read_json()
            record_to_delete = None
            for f in files_meta:
                if f.get("id") == file_id:
                    record_to_delete = f
                    break
            if not record_to_delete:
                return False
                
            old_path = record_to_delete.get("filePath")
            if old_path and os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
            files_meta.remove(record_to_delete)
            cls._write_json(files_meta)
            
            from app.storage.workspace_store import WorkspaceStore
            WorkspaceStore.log_audit_event(
                record_to_delete.get("workspaceId"), 
                "file_deleted", 
                f"Deleted record file '{record_to_delete.get('fileName')}'"
            )
            return True

    @classmethod
    def delete_workspace_files(cls, workspace_id: str):
        with cls._lock:
            files_meta = cls._read_json()
            remaining = []
            deleted_paths = []
            for f in files_meta:
                if f.get("workspaceId") == workspace_id:
                    path = f.get("filePath")
                    if path:
                        deleted_paths.append(path)
                else:
                    remaining.append(f)
            
            for path in deleted_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            
            # Clean up workspace directory
            ws_dir = os.path.join(cls._upload_root, workspace_id)
            if os.path.exists(ws_dir):
                try:
                    shutil.rmtree(ws_dir)
                except Exception:
                    pass

            cls._write_json(remaining)
