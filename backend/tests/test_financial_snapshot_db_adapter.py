import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import Settings
from app.db.base import Base
from app.db.models import Workspace, Organization, FinancialSnapshot as DbFinancialSnapshot, FinancialSnapshotVersion as DbFinancialSnapshotVersion
from app.persistence.database_adapters import DatabaseFinancialSnapshotRepository
from app.persistence.factory import get_financial_snapshot_repository
from app.persistence.errors import PersistenceConfigurationError
from app.models.workspace import FinancialSnapshot as PydanticFinancialSnapshot

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

def get_dummy_snapshot_data(workspace_id: str, snapshot_id: str):
    return {
        "id": snapshot_id,
        "workspace_id": workspace_id,
        "reporting_period": "2026-Q1",
        "currency": "HKD",
        "income_statement": {
            "revenue": 1000000.0,
            "cogs": 400000.0,
            "gross_profit": 600000.0,
            "operating_expenses": 300000.0,
            "ebit": 300000.0,
            "depreciation_amortization": 50000.0,
            "ebitda": 350000.0,
            "interest_expense": 0.0,
            "ebt": 300000.0,
            "taxes": 50000.0,
            "net_income": 250000.0
        },
        "balance_sheet": {
            "cash": 500000.0,
            "accounts_receivable": 150000.0,
            "inventory": 200000.0,
            "prepaid": 10000.0,
            "current_assets": 860000.0,
            "ppe_net": 1000000.0,
            "total_assets": 1860000.0,
            "accounts_payable": 100000.0,
            "accrued": 10000.0,
            "short_term_debt": 50000.0,
            "current_portion_long_term_debt": 0.0,
            "long_term_debt": 200000.0,
            "lease_liabilities": 0.0,
            "current_liabilities": 160000.0,
            "total_liabilities": 360000.0,
            "equity": 1500000.0,
            "retained_earnings": 1000000.0
        },
        "cash_flow_statement": {
            "cfo": 280000.0,
            "capex": -100000.0,
            "debt_issued": -50000.0,
            "debt_repaid": 0.0,
            "dividends": 0.0,
            "net_change_cash": 130000.0
        },
        "debt_schedule": {
            "scheduled_interest": 0.0,
            "scheduled_principal": 0.0
        },
        "receivables_aging": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved": True,
        "metadata": {}
    }

def test_db_snapshot_repo_save_and_get(db_session):
    """
    Verifies that DatabaseFinancialSnapshotRepository can save and retrieve snapshots.
    """
    repo = DatabaseFinancialSnapshotRepository(db_session)
    dummy_data = get_dummy_snapshot_data("ws_test", "snap_test_123")
    pydantic_snap = PydanticFinancialSnapshot.model_validate(dummy_data)
    
    saved = repo.save_snapshot(pydantic_snap)
    assert saved.id == "snap_test_123"
    assert saved.workspace_id == "ws_test"
    assert saved.reporting_period == "2026-Q1"
    
    retrieved = repo.get_active_snapshot("ws_test")
    assert retrieved is not None
    assert retrieved.id == "snap_test_123"
    assert retrieved.workspace_id == "ws_test"
    assert retrieved.reporting_period == "2026-Q1"
    assert retrieved.income_statement.revenue == 1000000

def test_db_snapshot_repo_versioning(db_session):
    """
    Verifies that DatabaseFinancialSnapshotRepository supports multiple versions correctly.
    """
    repo = DatabaseFinancialSnapshotRepository(db_session)
    
    # Save version 1
    dummy_data1 = get_dummy_snapshot_data("ws_test", "snap_version_1")
    pydantic_snap1 = PydanticFinancialSnapshot.model_validate(dummy_data1)
    repo.save_snapshot(pydantic_snap1)
    
    # Save version 2
    dummy_data2 = get_dummy_snapshot_data("ws_test", "snap_version_2")
    dummy_data2["income_statement"]["revenue"] = 1500000
    pydantic_snap2 = PydanticFinancialSnapshot.model_validate(dummy_data2)
    repo.save_snapshot(pydantic_snap2)
    
    # The active snapshot should be the newest saved (snap_version_2)
    active = repo.get_active_snapshot("ws_test")
    assert active is not None
    assert active.id == "snap_version_2"
    assert active.income_statement.revenue == 1500000
    
    # Listing snapshots should return both
    snapshots = repo.list_snapshots("ws_test")
    assert len(snapshots) == 2
    assert snapshots[0].id == "snap_version_2"
    assert snapshots[1].id == "snap_version_1"

def test_factory_returns_db_snapshot_repo(db_session):
    """
    Verifies the repository factory yields DatabaseFinancialSnapshotRepository.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    repo = get_financial_snapshot_repository(settings, db_session=db_session)
    assert repo.__class__.__name__ == "DatabaseFinancialSnapshotRepository"
    assert repo.session == db_session

def test_factory_without_session_raises():
    """
    Verifies the repository factory raises an exception without a database session.
    """
    settings = Settings(PERSISTENCE_BACKEND="database")
    with pytest.raises(PersistenceConfigurationError) as exc_info:
        get_financial_snapshot_repository(settings)
    assert "Database session is required" in str(exc_info.value)
