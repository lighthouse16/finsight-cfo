from app.persistence.interfaces import (
    WorkspaceRepository,
    FileMetadataRepository,
    FinancialSnapshotRepository,
    AnalysisRunRepository,
    AuditEventRepository,
    JobRepository,
    ReportRepository,
)
from app.persistence.local_adapters import (
    LocalWorkspaceRepository,
    LocalFileMetadataRepository,
    LocalFinancialSnapshotRepository,
    LocalAnalysisRunRepository,
    LocalAuditEventRepository,
    LocalJobRepository,
    LocalReportRepository,
)
from app.persistence.database_adapters import DatabaseWorkspaceRepository, DatabaseFileMetadataRepository, DatabaseAnalysisRunRepository, DatabaseAuditEventRepository
from app.persistence.factory import get_workspace_repository, get_file_metadata_repository, get_analysis_run_repository, get_audit_event_repository, get_persistence_backend_name
from app.persistence.errors import PersistenceConfigurationError, PersistenceAdapterNotImplementedError

__all__ = [
    # Interfaces
    "WorkspaceRepository",
    "FileMetadataRepository",
    "FinancialSnapshotRepository",
    "AnalysisRunRepository",
    "AuditEventRepository",
    "JobRepository",
    "ReportRepository",
    # Local adapters
    "LocalWorkspaceRepository",
    "LocalFileMetadataRepository",
    "LocalFinancialSnapshotRepository",
    "LocalAnalysisRunRepository",
    "LocalAuditEventRepository",
    "LocalJobRepository",
    "LocalReportRepository",
    # Database adapters
    "DatabaseWorkspaceRepository",
    "DatabaseFileMetadataRepository",
    "DatabaseAnalysisRunRepository",
    "DatabaseAuditEventRepository",
    # Factory & helpers
    "get_workspace_repository",
    "get_file_metadata_repository",
    "get_analysis_run_repository",
    "get_audit_event_repository",
    "get_persistence_backend_name",
    # Exceptions
    "PersistenceConfigurationError",
    "PersistenceAdapterNotImplementedError",
]
