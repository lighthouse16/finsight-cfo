import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.data_room import (
    ALLOWED_UPLOAD_EXTENSIONS,
    ALLOWED_UPLOAD_MIME_PREFIXES,
    DataRoomResponse,
    DataRoomUploadedFile,
    DataRoomUploadResponse,
)
from app.services.data_room.demo_data_room import (
    DEMO_RECORDS,
    get_demo_data_room_readiness,
)

router = APIRouter()


@router.get("/demo-readiness", response_model=DataRoomResponse)
async def get_demo_readiness_endpoint():
    return get_demo_data_room_readiness()


def _classify_upload(file: UploadFile, record_key: str) -> DataRoomUploadedFile:
    """Build the upload metadata response without persisting or parsing the file.

    Only metadata (filename, content type, size) is read from the upload.
    The file body is intentionally not stored or parsed here.
    """
    file_name = file.filename or "unknown"
    content_type = (file.content_type or "").lower()
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    allowed = (
        extension in ALLOWED_UPLOAD_EXTENSIONS
        or content_type in ALLOWED_UPLOAD_MIME_PREFIXES
    )

    validation_messages: list[str] = []
    file_size_bytes: int | None = None
    if file.size is not None:
        try:
            file_size_bytes = int(file.size)
        except (TypeError, ValueError):
            file_size_bytes = None

    if not allowed:
        status = "unsupported_type"
        validation_messages.append(
            f"File type '{extension or content_type or 'unknown'}' is not in the supported list. "
            "Supported: pdf, csv, xlsx, xls, docx."
        )
    else:
        status = "accepted_metadata"
        validation_messages.append(
            "Metadata received. File is not parsed and not persisted; "
            "production ingestion is required before analysis updates."
        )

    return DataRoomUploadedFile(
        fileId=f"upload_{uuid.uuid4().hex[:12]}",
        recordKey=record_key,
        fileName=file_name,
        fileType=content_type or (f".{extension}" if extension else "unknown"),
        fileSizeBytes=file_size_bytes,
        status=status,
        receivedAt=datetime.now(timezone.utc).isoformat(),
        validationMessages=validation_messages,
    )


@router.post(
    "/demo-upload-metadata",
    response_model=DataRoomUploadResponse,
)
async def post_demo_upload_metadata(
    recordKey: str = Form(...),
    file: UploadFile = File(...),
):
    """Accept file metadata only. No file body is stored or parsed."""
    record_key = (recordKey or "").strip()
    if not record_key:
        raise HTTPException(status_code=422, detail="recordKey is required")
    if file is None or not (file.filename or ""):
        raise HTTPException(status_code=422, detail="file is required")

    allowed_keys = {record.id for record in DEMO_RECORDS}
    if record_key not in allowed_keys:
        raise HTTPException(
            status_code=400,
            detail=(
                f"recordKey '{record_key}' is not part of the demo data room scope. "
                "Allowed keys: " + ", ".join(sorted(allowed_keys)) + "."
            ),
        )

    uploaded = _classify_upload(file, record_key)

    warnings: list[str] = []
    if uploaded.status == "unsupported_type":
        warnings.append(
            "This file type is not supported. Analysis will not be updated."
        )

    return DataRoomUploadResponse(
        uploadedFile=uploaded,
        warnings=warnings,
    )
