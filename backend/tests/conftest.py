"""Shared test fixtures for backend test execution."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.base import Base
from app.db import models  # noqa: F401  # Ensure SQLAlchemy models register on Base
from app.db import session as db_session
from app.routes.workspaces import get_db_session_optional, set_active_db_session


def _database_mode_enabled() -> bool:
    return settings.normalized_persistence_backend == "database"


def _clear_database(session) -> None:
    from app.db.models import (
        AiCfoMessage,
        AiCfoSession,
        AnalysisRun,
        AuditEvent,
        FinancialSnapshot,
        FinancialSnapshotVersion,
        Job,
        Organization,
        OrganizationMembership,
        Report,
        User,
        Workspace,
        WorkspaceFile,
        WorkspaceFileVersion,
    )

    session.query(AiCfoMessage).delete()
    session.query(AiCfoSession).delete()
    session.query(WorkspaceFileVersion).delete()
    session.query(WorkspaceFile).delete()
    session.query(FinancialSnapshotVersion).delete()
    session.query(FinancialSnapshot).delete()
    session.query(AnalysisRun).delete()
    session.query(AuditEvent).delete()
    session.query(Job).delete()
    session.query(Report).delete()
    session.query(Workspace).delete()
    session.query(OrganizationMembership).delete()
    session.query(User).delete()
    session.query(Organization).delete()
    session.commit()


def _ensure_default_org(session) -> None:
    from app.db.models import Organization

    org = session.query(Organization).filter_by(id="org_default").first()
    if org is None:
        session.add(Organization(id="org_default", name="Default Organization"))
        session.commit()


@pytest.fixture(autouse=True)
def database_test_harness() -> Generator[None, None, None]:
    if not _database_mode_enabled():
        yield
        return

    engine = db_session.get_engine()
    Base.metadata.create_all(bind=engine)

    session_factory = db_session.SessionLocal
    assert session_factory is not None, "Expected SessionLocal to be initialized in database mode"
    session = session_factory()

    def override_get_db_session() -> Generator:
        set_active_db_session(session)
        try:
            yield session
        finally:
            set_active_db_session(None)

    app.dependency_overrides[get_db_session_optional] = override_get_db_session

    try:
        _clear_database(session)
        _ensure_default_org(session)
        set_active_db_session(session)
        yield
    finally:
        set_active_db_session(None)
        app.dependency_overrides.pop(get_db_session_optional, None)
        try:
            _clear_database(session)
        finally:
            session.close()


@pytest.fixture
def test_client_factory():
    """Return a callable that creates a fresh TestClient for the app."""

    def _make_client():
        return TestClient(app)

    return _make_client
