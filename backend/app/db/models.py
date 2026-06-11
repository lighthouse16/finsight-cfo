import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, BigInteger, TEXT, JSON, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin

class Organization(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    memberships: Mapped[List["OrganizationMembership"]] = relationship(
        "OrganizationMembership", back_populates="organization", cascade="all, delete-orphan"
    )
    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace", back_populates="organization", cascade="all, delete-orphan"
    )

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    memberships: Mapped[List["OrganizationMembership"]] = relationship(
        "OrganizationMembership", back_populates="user", cascade="all, delete-orphan"
    )

class OrganizationMembership(Base, TimestampMixin):
    __tablename__ = "organization_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="analyst", nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    __table_args__ = (
        Index("uq_org_user_membership", "organization_id", "user_id", unique=True),
    )

class Workspace(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    workspace_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="workspaces")
    files: Mapped[List["WorkspaceFile"]] = relationship(
        "WorkspaceFile", back_populates="workspace", cascade="all, delete-orphan"
    )
    snapshots: Mapped[List["FinancialSnapshot"]] = relationship(
        "FinancialSnapshot", back_populates="workspace", cascade="all, delete-orphan"
    )
    runs: Mapped[List["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="workspace", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="workspace", cascade="all, delete-orphan"
    )
    ai_sessions: Mapped[List["AiCfoSession"]] = relationship(
        "AiCfoSession", back_populates="workspace", cascade="all, delete-orphan"
    )

class WorkspaceFile(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "workspace_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    record_key: Mapped[str] = mapped_column(String(100), nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    file_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict, nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="files")
    versions: Mapped[List["WorkspaceFileVersion"]] = relationship(
        "WorkspaceFileVersion", back_populates="workspace_file", cascade="all, delete-orphan"
    )

class WorkspaceFileVersion(Base, TimestampMixin):
    __tablename__ = "workspace_file_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_file_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspace_files.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    workspace_file: Mapped["WorkspaceFile"] = relationship("WorkspaceFile", back_populates="versions")

    __table_args__ = (
        Index("uq_file_version_num", "workspace_file_id", "version_number", unique=True),
    )

class FinancialSnapshot(Base, TimestampMixin):
    __tablename__ = "financial_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    active_version_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="snapshots")
    versions: Mapped[List["FinancialSnapshotVersion"]] = relationship(
        "FinancialSnapshotVersion", back_populates="financial_snapshot", cascade="all, delete-orphan"
    )

class FinancialSnapshotVersion(Base, TimestampMixin):
    __tablename__ = "financial_snapshot_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    financial_snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    statement_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    projections_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    financial_snapshot: Mapped["FinancialSnapshot"] = relationship("FinancialSnapshot", back_populates="versions")

    __table_args__ = (
        Index("uq_snapshot_version_num", "financial_snapshot_id", "version_number", unique=True),
    )

class AnalysisRun(Base, TimestampMixin):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    run_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    snapshot_version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("financial_snapshot_versions.id", ondelete="SET NULL"), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="runs")
    artifacts: Mapped[List["AnalysisRunArtifact"]] = relationship(
        "AnalysisRunArtifact", back_populates="analysis_run", cascade="all, delete-orphan"
    )

class AnalysisRunArtifact(Base, TimestampMixin):
    __tablename__ = "analysis_run_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Relationships
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="artifacts")

class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    analysis_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    pdf_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="reports")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    context_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    arguments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_log: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)

class AiCfoSession(Base, TimestampMixin):
    __tablename__ = "ai_cfo_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Consultation", nullable=False)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="ai_sessions")
    messages: Mapped[List["AiCfoMessage"]] = relationship(
        "AiCfoMessage", back_populates="session", cascade="all, delete-orphan"
    )

class AiCfoMessage(Base):
    __tablename__ = "ai_cfo_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_cfo_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    session: Mapped["AiCfoSession"] = relationship("AiCfoSession", back_populates="messages")

class ExternalDataConsent(Base, TimestampMixin):
    __tablename__ = "external_data_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

class ConnectorAccount(Base, TimestampMixin):
    __tablename__ = "connector_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(150), nullable=False)
    encrypted_auth_payload: Mapped[str] = mapped_column(TEXT, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="linked", nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
