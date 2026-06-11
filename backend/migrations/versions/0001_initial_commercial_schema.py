"""initial commercial schema

Revision ID: 0001_initial_commercial_schema
Revises: None
Create Date: 2026-06-11 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_commercial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_organizations')
    )
    op.create_index('idx_organizations_deleted', 'organizations', ['deleted_at'], unique=False)

    # 2. Table: users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 3. Table: organization_memberships
    op.create_table(
        'organization_memberships',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_organization_memberships_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_organization_memberships_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_organization_memberships')
    )
    op.create_index('ix_organization_memberships_organization_id', 'organization_memberships', ['organization_id'], unique=False)
    op.create_index('ix_organization_memberships_user_id', 'organization_memberships', ['user_id'], unique=False)
    op.create_index('uq_org_user_membership', 'organization_memberships', ['organization_id', 'user_id'], unique=True)

    # 4. Table: workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_workspaces_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_workspaces_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_workspaces')
    )
    op.create_index('ix_workspaces_organization_id', 'workspaces', ['organization_id'], unique=False)

    # 5. Table: workspace_files
    op.create_table(
        'workspace_files',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_workspace_files_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name='fk_workspace_files_workspace_id_workspaces', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_workspace_files_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_workspace_files')
    )
    op.create_index('ix_workspace_files_organization_id', 'workspace_files', ['organization_id'], unique=False)
    op.create_index('ix_workspace_files_workspace_id', 'workspace_files', ['workspace_id'], unique=False)

    # 6. Table: workspace_file_versions
    op.create_table(
        'workspace_file_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_file_id', sa.String(length=36), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['workspace_file_id'], ['workspace_files.id'], name='fk_workspace_file_versions_workspace_file_id_workspace_files', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_workspace_file_versions_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_workspace_file_versions')
    )
    op.create_index('ix_workspace_file_versions_workspace_file_id', 'workspace_file_versions', ['workspace_file_id'], unique=False)
    op.create_index('uq_file_version_num', 'workspace_file_versions', ['workspace_file_id', 'version_number'], unique=True)

    # 7. Table: financial_snapshots
    op.create_table(
        'financial_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('active_version_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_financial_snapshots_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name='fk_financial_snapshots_workspace_id_workspaces', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_financial_snapshots')
    )
    op.create_index('ix_financial_snapshots_organization_id', 'financial_snapshots', ['organization_id'], unique=False)
    op.create_index('ix_financial_snapshots_workspace_id', 'financial_snapshots', ['workspace_id'], unique=False)

    # 8. Table: financial_snapshot_versions
    op.create_table(
        'financial_snapshot_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('financial_snapshot_id', sa.String(length=36), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('statement_data', sa.JSON(), nullable=False),
        sa.Column('projections_data', sa.JSON(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['financial_snapshot_id'], ['financial_snapshots.id'], name='fk_financial_snapshot_versions_financial_snapshot_id_financial_snapshots', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_financial_snapshot_versions_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_financial_snapshot_versions')
    )
    op.create_index('ix_financial_snapshot_versions_financial_snapshot_id', 'financial_snapshot_versions', ['financial_snapshot_id'], unique=False)
    op.create_index('uq_snapshot_version_num', 'financial_snapshot_versions', ['financial_snapshot_id', 'version_number'], unique=True)

    # 9. Table: analysis_runs
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('run_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('snapshot_version_id', sa.String(length=36), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.TEXT(), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_analysis_runs_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name='fk_analysis_runs_workspace_id_workspaces', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_version_id'], ['financial_snapshot_versions.id'], name='fk_analysis_runs_snapshot_version_id_financial_snapshot_versions', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_analysis_runs_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_analysis_runs')
    )
    op.create_index('ix_analysis_runs_organization_id', 'analysis_runs', ['organization_id'], unique=False)
    op.create_index('ix_analysis_runs_workspace_id', 'analysis_runs', ['workspace_id'], unique=False)
    op.create_index('ix_analysis_runs_status', 'analysis_runs', ['status'], unique=False)

    # 10. Table: analysis_run_artifacts
    op.create_table(
        'analysis_run_artifacts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('analysis_run_id', sa.String(length=36), nullable=False),
        sa.Column('artifact_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], name='fk_analysis_run_artifacts_analysis_run_id_analysis_runs', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_analysis_run_artifacts')
    )
    op.create_index('ix_analysis_run_artifacts_analysis_run_id', 'analysis_run_artifacts', ['analysis_run_id'], unique=False)

    # 11. Table: reports
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('report_name', sa.String(length=255), nullable=False),
        sa.Column('analysis_run_id', sa.String(length=36), nullable=False),
        sa.Column('pdf_storage_key', sa.String(length=512), nullable=True),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_reports_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name='fk_reports_workspace_id_workspaces', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['analysis_run_id'], ['analysis_runs.id'], name='fk_reports_analysis_run_id_analysis_runs', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_reports_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_reports')
    )
    op.create_index('ix_reports_organization_id', 'reports', ['organization_id'], unique=False)
    op.create_index('ix_reports_workspace_id', 'reports', ['workspace_id'], unique=False)

    # 12. Table: audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('context_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_audit_events_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_audit_events_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_audit_events')
    )
    op.create_index('ix_audit_events_organization_id', 'audit_events', ['organization_id'], unique=False)
    op.create_index('ix_audit_events_action', 'audit_events', ['action'], unique=False)
    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'], unique=False)

    # 13. Table: jobs
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('arguments', sa.JSON(), nullable=True),
        sa.Column('error_log', sa.TEXT(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_jobs')
    )
    op.create_index('ix_jobs_status', 'jobs', ['status'], unique=False)

    # 14. Table: ai_cfo_sessions
    op.create_table(
        'ai_cfo_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_ai_cfo_sessions_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], name='fk_ai_cfo_sessions_workspace_id_workspaces', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_ai_cfo_sessions_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_ai_cfo_sessions')
    )
    op.create_index('ix_ai_cfo_sessions_organization_id', 'ai_cfo_sessions', ['organization_id'], unique=False)
    op.create_index('ix_ai_cfo_sessions_workspace_id', 'ai_cfo_sessions', ['workspace_id'], unique=False)

    # 15. Table: ai_cfo_messages
    op.create_table(
        'ai_cfo_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.TEXT(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['ai_cfo_sessions.id'], name='fk_ai_cfo_messages_session_id_ai_cfo_sessions', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_ai_cfo_messages')
    )
    op.create_index('ix_ai_cfo_messages_session_id', 'ai_cfo_messages', ['session_id'], unique=False)

    # 16. Table: external_data_consents
    op.create_table(
        'external_data_consents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('data_source', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_external_data_consents_organization_id_organizations', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_external_data_consents_created_by_user_id_users', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_external_data_consents')
    )
    op.create_index('ix_external_data_consents_organization_id', 'external_data_consents', ['organization_id'], unique=False)

    # 17. Table: connector_accounts
    op.create_table(
        'connector_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('provider_name', sa.String(length=150), nullable=False),
        sa.Column('encrypted_auth_payload', sa.TEXT(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_connector_accounts_organization_id_organizations', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_connector_accounts')
    )
    op.create_index('ix_connector_accounts_organization_id', 'connector_accounts', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_table('connector_accounts')
    op.drop_table('external_data_consents')
    op.drop_table('ai_cfo_messages')
    op.drop_table('ai_cfo_sessions')
    op.drop_table('jobs')
    op.drop_table('audit_events')
    op.drop_table('reports')
    op.drop_table('analysis_run_artifacts')
    op.drop_table('analysis_runs')
    op.drop_table('financial_snapshot_versions')
    op.drop_table('financial_snapshots')
    op.drop_table('workspace_file_versions')
    op.drop_table('workspace_files')
    op.drop_table('workspaces')
    op.drop_table('organization_memberships')
    op.drop_table('users')
    op.drop_table('organizations')
