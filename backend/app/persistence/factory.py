from app.core.config import settings, Settings
from app.persistence.errors import PersistenceConfigurationError, PersistenceAdapterNotImplementedError
from app.persistence.interfaces import WorkspaceRepository
from app.persistence.local_adapters import LocalWorkspaceRepository

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

def get_workspace_repository(app_settings: Settings = settings) -> WorkspaceRepository:
    """
    Factory function returning the active WorkspaceRepository adapter.
    Raises PersistenceAdapterNotImplementedError if database backend is selected but not implemented.
    """
    backend = get_persistence_backend_name(app_settings)
    if backend == "local":
        return LocalWorkspaceRepository()
    elif backend == "database":
        raise PersistenceAdapterNotImplementedError(
            "Database persistence adapter is not implemented yet."
        )
    else:
        # Fallback safeguard
        raise PersistenceConfigurationError(f"Unsupported persistence backend: '{backend}'")
