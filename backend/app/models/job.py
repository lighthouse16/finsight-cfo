from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class JobResponse(BaseModel):
    id: str
    workspace_id: str = Field(..., alias="workspaceId")
    organization_id: Optional[str] = Field(None, alias="organizationId")
    job_type: str = Field(..., alias="jobType")
    status: str
    input_payload: Optional[Dict[str, Any]] = Field(None, alias="inputPayload")
    result_payload: Optional[Dict[str, Any]] = Field(None, alias="resultPayload")
    error_message: Optional[str] = Field(None, alias="errorMessage")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[str] = Field(None, alias="createdAt")
    started_at: Optional[str] = Field(None, alias="startedAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")

    class Config:
        populate_by_name = True

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            workspaceId=data.get("workspaceId") or data.get("workspace_id") or "",
            organizationId=data.get("organizationId") or data.get("organization_id"),
            jobType=data.get("jobType") or data.get("job_type") or "",
            status=data.get("status") or "",
            inputPayload=data.get("payload") or data.get("inputPayload"),
            resultPayload=data.get("result") or data.get("resultPayload"),
            errorMessage=data.get("errorMessage") or data.get("error_message"),
            metadata=data.get("metadata") or {},
            createdAt=data.get("queuedAt") or data.get("createdAt") or data.get("created_at"),
            startedAt=data.get("startedAt") or data.get("started_at"),
            completedAt=data.get("completedAt") or data.get("completed_at"),
        )

class ReportGenerationJobCreateRequest(BaseModel):
    report_type: str = Field(..., alias="reportType")
    report_payload: Dict[str, Any] = Field(default_factory=dict, alias="reportPayload")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    storage_uri: Optional[str] = Field(None, alias="storageUri")
    max_attempts: Optional[int] = Field(None, alias="maxAttempts")

    class Config:
        populate_by_name = True

    from pydantic import model_validator

    @model_validator(mode="after")
    def check_bytes(self):
        from app.services.job_service import _check_no_file_bytes
        if self.report_payload:
            _check_no_file_bytes(self.report_payload)
        if self.metadata:
            _check_no_file_bytes(self.metadata)
        return self

