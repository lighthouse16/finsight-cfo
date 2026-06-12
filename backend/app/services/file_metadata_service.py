import os
import shutil
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from app.models.workspace import UploadedFileRecord
from app.storage.file_store import FileStore
from app.services.audit_service import record_audit_event_best_effort
from app.services.data_room.structured_parser import PARSEABLE_RECORD_KEYS, parse_csv_bytes, parse_xlsx_bytes

async def upload_workspace_file(
    *,
    workspace_id: str,
    record_key: str,
    filename: str,
    file_bytes: bytes,
    content_type: str,
    workspace_repo: Any,
    file_repo: Any,
    audit_repo: Any,
    settings: Any,
) -> UploadedFileRecord:
    """
    Orchestrates file upload and metadata registry.
    Saves file bytes to disk and metadata to the repository (in DB mode) or delegates to FileStore (in local mode).
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    record_key = record_key.strip()
    if not record_key:
        raise HTTPException(status_code=422, detail="recordKey is required")
    if not (filename or "").strip():
        raise HTTPException(status_code=422, detail="file is required")

    # Run parsing & classification
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if not ext:
        if "csv" in content_type.lower():
            ext = "csv"
        elif "spreadsheet" in content_type.lower() or "excel" in content_type.lower():
            ext = "xlsx"
        elif "pdf" in content_type.lower():
            ext = "pdf"
        elif "word" in content_type.lower():
            ext = "docx"

    parser_status = "unknown"
    record_count = 0
    warnings = []
    
    if record_key in PARSEABLE_RECORD_KEYS:
        if ext == "csv":
            try:
                preview = parse_csv_bytes(record_key, file_bytes)
                parser_status = "parsed" if preview.parsedRecords else "failed"
                record_count = preview.rowCount
                warnings = [w for w in preview.warnings if "Preview only" not in w]
            except Exception as e:
                parser_status = "failed"
                warnings = [f"Failed to parse CSV: {str(e)}"]
        elif ext == "xlsx":
            try:
                preview = parse_xlsx_bytes(record_key, file_bytes)
                parser_status = "parsed" if preview.parsedRecords else "failed"
                record_count = preview.rowCount
                warnings = [w for w in preview.warnings if "Preview only" not in w]
            except Exception as e:
                parser_status = "failed"
                warnings = [f"Failed to parse XLSX: {str(e)}"]
        elif ext in ("pdf", "docx"):
            parser_status = "unsupported_without_ocr"
            record_count = 0
            warnings = ["OCR/PDF parsing is not enabled. Please run standard OCR processing or upload structured CSV/XLSX instead."]
        else:
            parser_status = "unsupported_type"
            record_count = 0
            warnings = [f"File type '{ext}' is not supported for structured parsing. Please upload CSV/XLSX."]
    else:
        # metadata-only record key
        parser_status = "metadata_only"
        record_count = 0
        warnings = ["Metadata-only record key."]

    metadata = {
        "parser_status": parser_status,
        "record_count": record_count,
        "warnings": warnings,
        "source_type": record_key,
    }

    if settings.normalized_persistence_backend == "database":
        from app.storage.workspace_store import STORAGE_DIR
        upload_root = os.path.join(STORAGE_DIR, "uploads")
        workspace_dir = os.path.join(upload_root, workspace_id)
        os.makedirs(workspace_dir, exist_ok=True)
        dest_filename = f"{record_key}.{ext or 'bin'}"
        file_path = os.path.join(workspace_dir, dest_filename)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        try:
            with open(file_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write file to disk: {str(e)}")
            
        res_dict = file_repo.save_file_record(
            workspace_id=workspace_id,
            record_key=record_key,
            filename=filename,
            content_type=content_type,
            file_size_bytes=len(file_bytes),
            storage_uri=file_path,
            metadata=metadata,
        )
        await record_audit_event_best_effort(
            audit_repo=audit_repo,
            settings=settings,
            workspace_id=workspace_id,
            action="file.uploaded",
            description=f"File '{filename}' uploaded to key '{record_key}'."
        )
        return UploadedFileRecord.model_validate(res_dict)
    else:
        record = FileStore.save_file(
            workspace_id=workspace_id,
            record_key=record_key,
            file_name=filename,
            file_bytes=file_bytes,
            content_type=content_type,
            metadata=metadata,
        )
        return record

async def list_workspace_files(
    *,
    workspace_id: str,
    workspace_repo: Any,
    file_repo: Any,
    settings: Any,
) -> List[UploadedFileRecord]:
    """
    Lists uploaded files in a workspace.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if settings.normalized_persistence_backend == "database":
        records = file_repo.list_file_records(workspace_id)
        return [UploadedFileRecord.model_validate(r) for r in records]
    else:
        return FileStore.list_file_records(workspace_id)

async def delete_workspace_file(
    *,
    workspace_id: str,
    file_id: str,
    workspace_repo: Any,
    file_repo: Any,
    audit_repo: Any,
    settings: Any,
) -> Dict[str, str]:
    """
    Deletes a file from a workspace.
    """
    workspace = workspace_repo.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if settings.normalized_persistence_backend == "database":
        file_record = file_repo.get_file_record(file_id)
        if not file_record or file_record.get("workspaceId") != workspace_id:
            raise HTTPException(status_code=404, detail="File not found in this workspace")
            
        file_path = file_record.get("filePath")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
        success = file_repo.delete_file_record(file_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        await record_audit_event_best_effort(
            audit_repo=audit_repo,
            settings=settings,
            workspace_id=workspace_id,
            action="file.deleted",
            description=f"File '{file_id}' deleted."
        )
    else:
        file_record = FileStore.get_file_record(file_id)
        if not file_record or file_record.workspace_id != workspace_id:
            raise HTTPException(status_code=404, detail="File not found in this workspace")
            
        success = FileStore.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")
            
    return {"status": "success", "message": f"File {file_id} deleted successfully"}

def get_workspace_file_bytes(
    *,
    file_id: str,
    file_repo: Any,
    settings: Any,
) -> Optional[bytes]:
    """
    Reads physical file bytes for snapshot compilation.
    """
    if settings.normalized_persistence_backend == "database":
        file_rec_dict = file_repo.get_file_record(file_id)
        file_bytes = None
        if file_rec_dict and file_rec_dict.get("filePath"):
            file_path = file_rec_dict["filePath"]
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                except Exception:
                    pass
        return file_bytes
    else:
        return FileStore.get_file_content(file_id)

def cascade_delete_workspace_files(
    *,
    workspace_id: str,
    file_repo: Any,
    settings: Any,
) -> None:
    """
    Cascades file deletions and workspace directory removal.
    """
    if settings.normalized_persistence_backend == "database":
        db_records = file_repo.list_file_records(workspace_id)
        for r in db_records:
            fid = r.get("id")
            fpath = r.get("filePath")
            if fpath and os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass
            file_repo.delete_file_record(fid)
            
        ws_dir = os.path.join(FileStore._upload_root, workspace_id)
        if os.path.exists(ws_dir):
            try:
                shutil.rmtree(ws_dir)
            except Exception:
                pass
    else:
        FileStore.delete_workspace_files(workspace_id)
