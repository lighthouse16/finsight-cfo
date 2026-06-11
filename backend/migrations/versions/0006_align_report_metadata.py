"""align report metadata

Revision ID: 0006_align_report_metadata
Revises: 0005_align_job_metadata
Create Date: 2026-06-11 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0006_align_report_metadata'
down_revision: Union[str, None] = '0005_align_job_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('reports') as batch_op:
        batch_op.add_column(sa.Column('report_type', sa.String(length=100), nullable=False, server_default='custom'))
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'))
        batch_op.add_column(sa.Column('report_payload', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('storage_uri', sa.String(length=512), nullable=True))
        batch_op.add_column(sa.Column('metadata', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.alter_column('analysis_run_id', existing_type=sa.String(length=36), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('reports') as batch_op:
        batch_op.alter_column('analysis_run_id', existing_type=sa.String(length=36), nullable=False)
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('metadata')
        batch_op.drop_column('storage_uri')
        batch_op.drop_column('report_payload')
        batch_op.drop_column('status')
        batch_op.drop_column('report_type')
