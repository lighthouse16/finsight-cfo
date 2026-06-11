from app.core.config import settings, Settings
from app.persistence.errors import PersistenceConfigurationError, PersistenceAdapterNotImplementedError
from app.persistence.interfaces import WorkspaceRepository, FileMetadataRepository, AnalysisRunRepository, AuditEventRepository, JobRepository, ReportRepository
from app.persistence.local_adapters import LocalWorkspaceRepository, LocalFileMetadataRepository, LocalAnalysisRunRepository, LocalAuditEventRepository, LocalJobRepository, LocalReportRepository
from app.persistence.database_adapters import DatabaseWorkspaceRepository, DatabaseFileMetadataRepository, DatabaseAnalysisRunRepository, DatabaseAuditEventRepository, DatabaseJobRepository, DatabaseReportRepository

def get_persistence_backend_name(app_settings: Settings = settings) -> str:
    """
    Normalizes and returns the persistence backend name from application settings.
    Raises PersistenceConfigurationError if the backend is unknown.
    """
    backend = app_settings.normalized_persistence_backend
    if backend not in ("local", "database"):
        raise PersistenceConfigurationError(
            f"Unknown persistence backend configured: '{backend}'. "
            f"Supported backends are 'local' and 'database'."
        )
    return backend

def get_workspace_repository(app_settings: Settings = settings, db_session=None) -> WorkspaceRepository:
    """
    Factory function returning the active WorkspaceRepository adapter.
    Raises PersistenceConfigurationError if database backend is selected but session is missing.
    """
    backend = get_persistence_backend_name(app_settings)
    if backend == "local":
        return LocalWorkspaceRepository()
    elif backend == "database":
        if db_session is None:
            raise PersistenceConfigurationError(
                "Database session is required when database persistence backend is active."
            )
        return DatabaseWorkspaceRepository(db_session)
    else:
        # Fallback safeguard
        raise PersistenceConfigurationError(f"Unsupported persistence backend: '{backend}'")

def get_file_metadata_repository(app_settings: Settings = settings, db_session=None) -> FileMetadataRepository:
    """
    Factory function returning the active FileMetadataRepository adapter.
    Raises PersistenceConfigurationError if database backend is selected but session is missing.
    """
    backend = get_persistence_backend_name(app_settings)
    if backend == "local":
        if 'LocalFileMetadataRepository' not in globals():
            raise PersistenceAdapterNotImplementedError("Local file metadata repository adapter does not exist.")
        return LocalFileMetadataRepository()
    elif backend == "database":
        if db_session is None:
            raise PersistenceConfigurationError(
                "Database session is required when database persistence backend is active."
            )
        return DatabaseFileMetadataRepository(db_session)
    else:
        raise PersistenceConfigurationError(f"Unsupported persistence backend: '{backend}'")

def get_analysis_run_repository(app_settings: Settings = settings, db_session=None) -> AnalysisRunRepository:
    """
    Factory function returning the active AnalysisRunRepository adapter.
    Raises PersistenceConfigurationError if database backend is selected but session is missing.
    """
    backend = get_persistence_backend_name(app_settings)
    if backend == "local":
        if 'LocalAnalysisRunRepository' not in globals():
            raise PersistenceAdapterNotImplementedError("Local analysis run repository adapter does not exist.")
        return LocalAnalysisRunRepository()
    elif backend == "database":
        if db_session is None:
            raise PersistenceConfigurationError(
                "Database session is required when database persistence backend is active."
            )
        return DatabaseAnalysisRunRepository(db_session)
    else:
        raise PersistenceConfigurationError(f"Unsupported persistence backend: '{backend}'")

def get_audit_event_repository(app_settings: Settings = settings, db_session=None) -> AuditEventRepository:
    """
    Factory function returning the active AuditEventRepository adapter.
    Raises PersistenceConfigurationError if database backend is selected but session is missing.
    """
    backend = get_persistence_backend_name(app_settings)
    if backend == "local":
        if 'LocalAuditEventRepository' not in globals():
            raise PersistenceAdapterNotImplementedError("Local audit event repository adapter does not exist.")
        return LocalAuditEventRepository()
    elif backend == "database":
        if db_session is None:
            raise PersistenceConfigurationError(
                "Database session is required when database persistence backend is active."
            )
        return DatabaseAuditEventRepository(db_session)
    else:
        raise PersistenceConfigurationError(f"Unsupported persistence backend: '{backend}'")

def get_job_repository(app_settings: Settings = settings, db_session=None) -> JobRepository:
    """
    Factory function returning the active JobRepository adapter.
    Raises PersistenceConfigurationError if database backend is selected but session is missing.
    """
    backend = get_persistence_backend_name(app_settings)
    if backend == "local":
        if 'LocalJobRepository' not in globals():
            raise PersistenceAdapterNotImplementedError("Local job repository adapter does not exist.")
        return LocalJobRepository()
    elif backend == "database":
        if db_session is None:
            raise PersistenceConfigurationError(
                "Database session is required when database persistence backend is active."
            )
        return DatabaseJobRepository(db_session)
    else:
        raise PersistenceConfigurationError(f"Unsupported persistence backend: '{backend}'")


def get_report_repository(app_settings: Settings = settings, db_session=None) -> ReportRepository:
    """
    Factory function returning the active ReportRepository adapter.
    Raises PersistenceConfigurationError if database backend is selected but session is missing.
    """
    backend = get_persistence_backend_name(app_settings)
    if backend == "local":
        if 'LocalReportRepository' not in globals():
            raise PersistenceAdapterNotImplementedError("Local report repository adapter does not exist.")
        return LocalReportRepository()
    elif backend == "database":
        if db_session is None:
            raise PersistenceConfigurationError(
                "Database session is required when database persistence backend is active."
            )
        return DatabaseReportRepository(db_session)
    else:
        raise PersistenceConfigurationError(f"Unsupported persistence backend: '{backend}'")

