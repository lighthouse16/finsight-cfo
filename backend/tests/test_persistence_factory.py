import pytest
from unittest.mock import patch
from app.core.config import Settings
from app.persistence.factory import get_persistence_backend_name, get_workspace_repository, get_file_metadata_repository, get_analysis_run_repository, get_audit_event_repository
from app.persistence.local_adapters import LocalWorkspaceRepository, LocalFileMetadataRepository, LocalAnalysisRunRepository, LocalAuditEventRepository
from app.persistence.errors import PersistenceConfigurationError, PersistenceAdapterNotImplementedError

def test_default_backend_name():
    """
    Verifies that the normalized default backend is 'local'.
    """
    settings = Settings()
    assert get_persistence_backend_name(settings) == "local"

def test_backend_normalization():
    """
    Verifies that backend name selection trims whitespace and lowercases.
    """
    settings = Settings(PERSISTENCE_BACKEND="  DATABASE  ")
    assert get_persistence_backend_name(settings) == "database"

def test_default_repository_factory():
    """
    Verifies that get_workspace_repository returns LocalWorkspaceRepository by default.
    """
    settings = Settings()
    repo = get_workspace_repository(settings)
    assert isinstance(repo, LocalWorkspaceRepository)

def test_database_persistence_without_session_raises():
    """
    Verifies that PERSISTENCE_BACKEND="database" raises PersistenceConfigurationError if db_session is missing.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_workspace_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_database_persistence_with_session_returns_adapter():
    """
    Verifies that get_workspace_repository returns DatabaseWorkspaceRepository when session is provided.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    from sqlalchemy.orm import Session
    from unittest.mock import MagicMock
    mock_session = MagicMock(spec=Session)
    
    repo = get_workspace_repository(settings, db_session=mock_session)
    from app.persistence.database_adapters import DatabaseWorkspaceRepository
    assert isinstance(repo, DatabaseWorkspaceRepository)
    assert repo.session == mock_session

def test_unknown_backend_raises_configuration_error():
    """
    Verifies that an unknown PERSISTENCE_BACKEND raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="custom_cloud")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_workspace_repository(settings)
    assert "Unknown persistence backend configured" in str(exc_info.value)

def test_workspace_repository_delegation():
    """
    Verifies that LocalWorkspaceRepository delegates calls to the underlying WorkspaceStore.
    """
    repo = LocalWorkspaceRepository()
    
    with patch("app.persistence.local_adapters.WorkspaceStore") as mock_store:
        # 1. list_workspaces
        repo.list_workspaces()
        mock_store.list_workspaces.assert_called_once()
        
        # 2. get_workspace
        repo.get_workspace("ws_123")
        mock_store.get_workspace.assert_called_once_with("ws_123")
        
        # 3. create_workspace
        repo.create_workspace("ws_123", "Company Ltd", {"meta": "val"})
        mock_store.create_workspace.assert_called_once_with("ws_123", "Company Ltd", {"meta": "val"})
        
        # 4. delete_workspace
        repo.delete_workspace("ws_123")
        mock_store.delete_workspace.assert_called_once_with("ws_123")

def test_file_metadata_repository_factory_default():
    """
    Verifies that get_file_metadata_repository returns LocalFileMetadataRepository by default.
    """
    settings = Settings()
    repo = get_file_metadata_repository(settings)
    assert isinstance(repo, LocalFileMetadataRepository)

def test_file_metadata_repository_factory_database_without_session_raises():
    """
    Verifies that get_file_metadata_repository raises PersistenceConfigurationError if database backend is chosen without a session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_file_metadata_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_file_metadata_repository_factory_database_with_session_returns_adapter():
    """
    Verifies that get_file_metadata_repository returns DatabaseFileMetadataRepository when session is provided.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    from sqlalchemy.orm import Session
    from unittest.mock import MagicMock
    mock_session = MagicMock(spec=Session)
    
    repo = get_file_metadata_repository(settings, db_session=mock_session)
    from app.persistence.database_adapters import DatabaseFileMetadataRepository
    assert isinstance(repo, DatabaseFileMetadataRepository)
    assert repo.session == mock_session

def test_analysis_run_repository_factory_default():
    """
    Verifies that get_analysis_run_repository returns LocalAnalysisRunRepository by default.
    """
    settings = Settings()
    repo = get_analysis_run_repository(settings)
    assert isinstance(repo, LocalAnalysisRunRepository)

def test_analysis_run_repository_factory_database_without_session_raises():
    """
    Verifies that get_analysis_run_repository raises PersistenceConfigurationError if database backend is chosen without a session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_analysis_run_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_analysis_run_repository_factory_database_with_session_returns_adapter():
    """
    Verifies that get_analysis_run_repository returns DatabaseAnalysisRunRepository when session is provided.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    from sqlalchemy.orm import Session
    from unittest.mock import MagicMock
    mock_session = MagicMock(spec=Session)
    
    repo = get_analysis_run_repository(settings, db_session=mock_session)
    from app.persistence.database_adapters import DatabaseAnalysisRunRepository
    assert isinstance(repo, DatabaseAnalysisRunRepository)
    assert repo.session == mock_session

def test_audit_event_repository_factory_default():
    """
    Verifies that get_audit_event_repository returns LocalAuditEventRepository by default.
    """
    settings = Settings()
    repo = get_audit_event_repository(settings)
    assert isinstance(repo, LocalAuditEventRepository)

def test_audit_event_repository_factory_database_without_session_raises():
    """
    Verifies that get_audit_event_repository raises PersistenceConfigurationError if database backend is chosen without a session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_audit_event_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_audit_event_repository_factory_database_with_session_returns_adapter():
    """
    Verifies that get_audit_event_repository returns DatabaseAuditEventRepository when session is provided.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    from sqlalchemy.orm import Session
    from unittest.mock import MagicMock
    mock_session = MagicMock(spec=Session)
    
    repo = get_audit_event_repository(settings, db_session=mock_session)
    from app.persistence.database_adapters import DatabaseAuditEventRepository
    assert isinstance(repo, DatabaseAuditEventRepository)
    assert repo.session == mock_session
