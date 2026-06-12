import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Workspace, Organization, WorkspaceFile, WorkspaceFileVersion
from app.persistence.database_adapters import DatabaseFileMetadataRepository
from app.persistence.factory import get_file_metadata_repository
from app.persistence.errors import PersistenceConfigurationError

@pytest.fixture
def db_session():
    # Set up in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    # Create default test org and workspace to satisfy Foreign Key dependencies
    org = Organization(id="org_test", name="Test Org")
    session.add(org)
    session.flush()
    
    ws = Workspace(id="ws_test", organization_id="org_test", name="Test Workspace", status="active")
    session.add(ws)
    session.commit()
    
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

def test_db_file_repo_save_and_get(db_session):
    """
    1. DatabaseFileMetadataRepository can save and retrieve file metadata.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    record = repo.save_file_record(
        workspace_id="ws_test",
        record_key="pl-statement",
        filename="pl.csv",
        content_type="text/csv",
        file_size_bytes=1024,
        storage_uri="local://workspace/pl.csv",
        checksum_sha256="abc123sha",
        metadata={"foo": "bar"}
    )
    
    assert record["workspaceId"] == "ws_test"
    assert record["recordKey"] == "pl-statement"
    assert record["fileName"] == "pl.csv"
    assert record["fileType"] == "text/csv"
    assert record["fileSizeBytes"] == 1024
    assert record["filePath"] == "local://workspace/pl.csv"
    assert record["status"] == "uploaded"
    assert record["metadata"] == {"foo": "bar", "storageMode": "local_file"}

    retrieved = repo.get_file_record(record["id"])
    assert retrieved is not None
    assert retrieved["id"] == record["id"]
    assert retrieved["recordKey"] == "pl-statement"
    assert retrieved["fileName"] == "pl.csv"
    assert retrieved["fileType"] == "text/csv"
    assert retrieved["fileSizeBytes"] == 1024
    assert retrieved["filePath"] == "local://workspace/pl.csv"
    assert retrieved["status"] == "uploaded"
    assert retrieved["metadata"] == {"foo": "bar", "storageMode": "local_file"}

def test_db_file_repo_list_workspace_only(db_session):
    """
    2. list_file_records returns files for the workspace only.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    
    # Create a secondary workspace
    ws2 = Workspace(id="ws_other", organization_id="org_test", name="Other Workspace", status="active")
    db_session.add(ws2)
    db_session.commit()
    
    # Save file in ws_test
    f1 = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri1")
    # Save file in ws_other
    f2 = repo.save_file_record("ws_other", "balance-sheet", "bs.csv", "text/csv", 200, "uri2")
    
    ws_test_files = repo.list_file_records("ws_test")
    assert len(ws_test_files) == 1
    assert ws_test_files[0]["id"] == f1["id"]
    
    ws_other_files = repo.list_file_records("ws_other")
    assert len(ws_other_files) == 1
    assert ws_other_files[0]["id"] == f2["id"]

def test_db_file_repo_list_excludes_deleted(db_session):
    """
    3. list_file_records excludes deleted files.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    f1 = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri1")
    f2 = repo.save_file_record("ws_test", "balance-sheet", "bs.csv", "text/csv", 200, "uri2")
    
    assert len(repo.list_file_records("ws_test")) == 2
    
    repo.delete_file_record(f1["id"])
    
    active_files = repo.list_file_records("ws_test")
    assert len(active_files) == 1
    assert active_files[0]["id"] == f2["id"]

def test_db_file_repo_delete_soft_delete(db_session):
    """
    4. delete_file_record soft-deletes file metadata.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    f = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri")
    
    assert repo.get_file_record(f["id"]) is not None
    
    # Soft delete the file record
    success = repo.delete_file_record(f["id"])
    assert success is True
    
    # Should not be accessible via get/list
    assert repo.get_file_record(f["id"]) is None
    assert len(repo.list_file_records("ws_test")) == 0
    
    # Verify the row remains in the DB but is soft deleted
    db_file = db_session.query(WorkspaceFile).filter_by(id=f["id"]).first()
    assert db_file is not None
    assert db_file.deleted_at is not None
    assert db_file.status == "deleted"

def test_db_file_repo_save_requires_workspace(db_session):
    """
    5. save_file_record requires existing workspace; missing workspace raises PersistenceConfigurationError.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        repo.save_file_record(
            workspace_id="non_existent_workspace",
            record_key="pl-statement",
            filename="pl.csv",
            content_type="text/csv",
            file_size_bytes=100,
            storage_uri="uri"
        )
    assert "does not exist" in str(exc_info.value)

def test_db_file_repo_uses_workspace_org(db_session):
    """
    6. save_file_record uses workspace organization_id.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    f = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri")
    
    db_file = db_session.query(WorkspaceFile).filter_by(id=f["id"]).first()
    assert db_file is not None
    assert db_file.organization_id == "org_test"

def test_db_file_repo_metadata_round_trip(db_session):
    """
    7. metadata round-trips correctly.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    meta = {
        "encoding": "utf-8",
        "delimiters": ",",
        "tags": ["critical", "q3"]
    }
    f = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri", metadata=meta)
    assert f["metadata"] == meta
    
    retrieved = repo.get_file_record(f["id"])
    assert retrieved is not None
    assert retrieved["metadata"] == meta

def test_db_file_repo_checksum_round_trip(db_session):
    """
    8. checksum_sha256 round-trips correctly.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    f = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri", checksum_sha256=checksum)
    
    versions = repo.list_file_versions(f["id"])
    assert len(versions) == 1
    assert versions[0]["sha256Hash"] == checksum

def test_db_file_repo_save_version_creates_additional(db_session):
    """
    9. save_file_version creates an additional version.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    f = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri1")
    
    versions = repo.list_file_versions(f["id"])
    assert len(versions) == 1
    assert versions[0]["versionNumber"] == 1
    
    new_v = repo.save_file_version(
        file_id=f["id"],
        version_number=2,
        storage_uri="uri2",
        checksum_sha256="sha2",
        metadata={"file_size_bytes": 150}
    )
    
    assert new_v["versionNumber"] == 2
    assert new_v["storageKey"] == "uri2"
    assert new_v["fileSizeBytes"] == 150
    assert new_v["sha256Hash"] == "sha2"
    
    # Retrieval should show the latest version's sizes and paths
    retrieved = repo.get_file_record(f["id"])
    assert retrieved["fileSizeBytes"] == 150
    assert retrieved["filePath"] == "uri2"

def test_db_file_repo_list_versions_ordered(db_session):
    """
    10. list_file_versions returns ordered versions.
    """
    repo = DatabaseFileMetadataRepository(db_session)
    f = repo.save_file_record("ws_test", "pl-statement", "pl.csv", "text/csv", 100, "uri1")
    
    # Add versions out of order
    repo.save_file_version(f["id"], 3, "uri3")
    repo.save_file_version(f["id"], 2, "uri2")
    
    versions = repo.list_file_versions(f["id"])
    assert len(versions) == 3
    assert [v["versionNumber"] for v in versions] == [1, 2, 3]

def test_factory_returns_db_repo(db_session):
    """
    11. factory returns DatabaseFileMetadataRepository for database backend with db_session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    repo = get_file_metadata_repository(settings, db_session=db_session)
    assert repo.__class__.__name__ == "DatabaseFileMetadataRepository"
    assert repo.session == db_session

def test_factory_without_session_raises():
    """
    12. factory database backend without db_session raises PersistenceConfigurationError.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_file_metadata_repository(settings)
    assert "Database session is required" in str(exc_info.value)

def test_factory_local_remains_explicit():
    """
    13. local backend behavior remains explicit and does not accidentally create DB repository.
    """
    settings = Settings(PERSISTENCE_BACKEND="local")
    repo = get_file_metadata_repository(settings)
    assert repo.__class__.__name__ == "LocalFileMetadataRepository"
