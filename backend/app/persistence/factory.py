from app.core.config import settings, Settings
from app.persistence.errors import PersistenceConfigurationError, PersistenceAdapterNotImplementedError
from app.persistence.interfaces import WorkspaceRepository
from app.persistence.local_adapters import LocalWorkspaceRepository
from app.persistence.database_adapters import DatabaseWorkspaceRepository

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
