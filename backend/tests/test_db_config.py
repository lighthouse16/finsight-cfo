from app.core.config import Settings

def test_default_persistence_backend(monkeypatch):
    """
    Verifies that the default persistence backend is local.
    """
    monkeypatch.delenv("PERSISTENCE_BACKEND", raising=False)
    settings = Settings()
    assert settings.PERSISTENCE_BACKEND == "local"
    assert not settings.is_database_persistence_enabled

def test_database_persistence_activation():
    """
    Verifies that database persistence flag activates correctly.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    assert settings.PERSISTENCE_BACKEND == "database"
    assert settings.is_database_persistence_enabled
