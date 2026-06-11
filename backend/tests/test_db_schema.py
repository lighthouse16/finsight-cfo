import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers
from app.db.base import Base
# Import models so they are registered on Base
from app.db import models

def test_db_models_importable():
    """
    Verifies that all models import successfully and registers to the declarative base metadata.
    """
    assert len(Base.metadata.tables) > 0

def test_metadata_contains_core_tables():
    """
    Verifies that the SQLAlchemy metadata registers all key tables required.
    """
    expected_tables = {
        "organizations",
        "users",
        "organization_memberships",
        "workspaces",
        "workspace_files",
        "workspace_file_versions",
        "financial_snapshots",
        "financial_snapshot_versions",
        "analysis_runs",
        "analysis_run_artifacts",
        "reports",
        "audit_events",
        "jobs",
        "ai_cfo_sessions",
        "ai_cfo_messages",
        "external_data_consents",
        "connector_accounts"
    }
    registered_tables = set(Base.metadata.tables.keys())
    for table in expected_tables:
        assert table in registered_tables, f"Table '{table}' not registered in Base metadata."

def test_relationships_mapper_configuration():
    """
    Verifies that model relationships do not raise mapping configuration errors.
    """
    try:
        configure_mappers()
    except Exception as e:
        pytest.fail(f"SQLAlchemy mapper configuration failed: {e}")

def test_sqlite_in_memory_creation():
    """
    Verifies that all defined tables can be created cleanly in an in-memory SQLite database.
    """
    engine = create_engine("sqlite:///:memory:")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        pytest.fail(f"Failed to create schema tables in-memory: {e}")
    finally:
        engine.dispose()
