"""align audit event metadata

Revision ID: 0004_align_audit_event_metadata
Revises: 0003_align_analysis_run_metadata
Create Date: 2026-06-11 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0004_align_audit_event_metadata'
down_revision: Union[str, None] = '0003_align_analysis_run_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns and foreign keys to audit_events
    with op.batch_alter_table('audit_events') as batch_op:
        batch_op.add_column(sa.Column('workspace_id', sa.String(length=36), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('metadata', sa.JSON(), nullable=True))
        
    op.create_index('ix_audit_events_workspace_id', 'audit_events', ['workspace_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_events_workspace_id', table_name='audit_events')
    with op.batch_alter_table('audit_events') as batch_op:
        batch_op.drop_column('metadata')
        batch_op.drop_column('description')
        batch_op.drop_column('workspace_id')
