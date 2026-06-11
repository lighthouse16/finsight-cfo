"""align analysis run metadata

Revision ID: 0003_align_analysis_run_metadata
Revises: 0002_align_workspace_file_metadata
Create Date: 2026-06-11 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0003_align_analysis_run_metadata'
down_revision: Union[str, None] = '0002_align_workspace_file_metadata'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('analysis_runs') as batch_op:
        batch_op.add_column(sa.Column('input_payload', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('output_payload', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('summary', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('metadata', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('analysis_runs') as batch_op:
        batch_op.drop_column('completed_at')
        batch_op.drop_column('started_at')
        batch_op.drop_column('metadata')
        batch_op.drop_column('summary')
        batch_op.drop_column('output_payload')
        batch_op.drop_column('input_payload')
