from enum import Enum

class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class FileStatus(str, Enum):
    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"

class SnapshotStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    SUPERSEDED = "superseded"

class AnalysisRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class ReportStatus(str, Enum):
    DRAFT = "draft"
    FINAL = "final"
    ARCHIVED = "archived"

class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class MembershipRole(str, Enum):
    CFO = "cfo"
    ANALYST = "analyst"
    AUDITOR = "auditor"
