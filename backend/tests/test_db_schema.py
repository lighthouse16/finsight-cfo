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

def test_alembic_migrations_upgrade_downgrade(tmp_path):
    """
    Verifies that Alembic migrations run successfully from scratch to head,
    and then downgrade back to base.
    """
    from alembic.config import Config
    from alembic import command
    from app.core.config import settings
    from sqlalchemy import inspect
    import os
    
    db_file = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_file}"
    
    # Save original DB URL
    original_db_url = settings.DATABASE_URL
    settings.DATABASE_URL = db_url
    
    # Read original alembic.ini and strip duplicate sections for strict parser
    with open("alembic.ini", "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.splitlines()
    seen_sections = set()
    cleaned_lines = []
    skip_mode = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
            if section in seen_sections:
                skip_mode = True
                continue
            else:
                seen_sections.add(section)
                skip_mode = False
        elif skip_mode:
            # Skip keys / settings inside duplicate sections
            if stripped == "" or "=" in stripped or ":" in stripped:
                continue
                
        if stripped.startswith("script_location"):
            abs_migrations = os.path.abspath("migrations")
            # Replace backslashes with forward slashes for safer config parsing
            abs_migrations_path = abs_migrations.replace("\\", "/")
            cleaned_lines.append(f"script_location = {abs_migrations_path}")
        else:
            cleaned_lines.append(line)
            
    temp_ini = tmp_path / "alembic.ini"
    with open(temp_ini, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_lines))
    
    try:
        # Load sanitized Alembic configuration
        alembic_cfg = Config(str(temp_ini))
        
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        
        # Verify the database has the expected tables and columns
        engine = create_engine(db_url)
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check workspaces
            workspaces_cols = {c["name"]: c for c in inspector.get_columns("workspaces")}
            assert "metadata" in workspaces_cols
            
            # Check workspace_files
            files_cols = {c["name"]: c for c in inspector.get_columns("workspace_files")}
            assert "record_key" in files_cols
            assert "status" in files_cols
            assert "metadata" in files_cols
            
            # Check workspace_file_versions
            versions_cols = {c["name"]: c for c in inspector.get_columns("workspace_file_versions")}
            assert "sha256_hash" in versions_cols
            assert versions_cols["sha256_hash"]["nullable"] is True
            
        # Run downgrade back to base
        command.downgrade(alembic_cfg, "base")
        
    finally:
        # Restore settings DATABASE_URL
        settings.DATABASE_URL = original_db_url
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass
