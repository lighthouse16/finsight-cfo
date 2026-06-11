"""align job metadata

Revision ID: 0005_align_job_metadata
Revises: 0004_align_audit_event_metadata
Create Date: 2026-06-11 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0005_align_job_metadata'
down_revision: Union[str, None] = '0004_align_audit_event_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True))
        batch_op.add_column(sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, server_default='org_default'))
        batch_op.add_column(sa.Column('result_payload', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('metadata', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))

    op.create_index('ix_jobs_workspace_id', 'jobs', ['workspace_id'], unique=False)
    op.create_index('ix_jobs_organization_id', 'jobs', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_jobs_organization_id', table_name='jobs')
    op.drop_index('ix_jobs_workspace_id', table_name='jobs')
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('completed_at')
        batch_op.drop_column('started_at')
        batch_op.drop_column('metadata')
        batch_op.drop_column('result_payload')
        batch_op.drop_column('organization_id')
        batch_op.drop_column('workspace_id')
