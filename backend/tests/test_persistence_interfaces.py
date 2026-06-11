import sys

def test_interfaces_importable_without_db():
    """
    Verifies that persistence interfaces and factories are importable cleanly.
    """
    from app.persistence import (
        WorkspaceRepository,
        LocalWorkspaceRepository,
        get_workspace_repository,
        get_persistence_backend_name,
    )
    assert WorkspaceRepository is not None
    assert LocalWorkspaceRepository is not None
    assert get_workspace_repository is not None
    assert get_persistence_backend_name is not None

def test_import_does_not_instantiate_db():
    """
    Verifies that importing persistence components does not instantiate the database engine or session.
    """
    # Clear session/engine module if imported to get a clean check, though it shouldn't be
    if "app.db.session" in sys.modules:
        del sys.modules["app.db.session"]
    if "app.db" in sys.modules:
        del sys.modules["app.db"]

    # Import the interfaces
    from app.persistence import get_workspace_repository  # noqa: F401
    
    # Verify that app.db.session is NOT in sys.modules,
    # OR if it is, the global _engine private variable remains None.
    if "app.db.session" in sys.modules:
        from app.db.session import _engine
        assert _engine is None, "Database engine was instantiated merely by importing persistence factory!"
    else:
        # If the db session module was not even imported, that's even better/safer!
        assert True
