"""align workspace file metadata

Revision ID: 0002_align_workspace_file_metadata
Revises: 0001_initial_commercial_schema
Create Date: 2026-06-11 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_align_workspace_file_metadata'
down_revision: Union[str, None] = '0001_initial_commercial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add metadata column to workspaces
    op.add_column('workspaces', sa.Column('metadata', sa.JSON(), nullable=True))

    # 2. Add columns to workspace_files
    with op.batch_alter_table('workspace_files') as batch_op:
        batch_op.add_column(sa.Column('record_key', sa.String(length=100), nullable=False, server_default='unknown'))
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'))
        batch_op.add_column(sa.Column('metadata', sa.JSON(), nullable=True))

    # 3. Alter sha256_hash to be nullable on workspace_file_versions
    with op.batch_alter_table('workspace_file_versions') as batch_op:
        batch_op.alter_column('sha256_hash',
                              existing_type=sa.String(length=64),
                              nullable=True)


def downgrade() -> None:
    # 1. Revert sha256_hash to be non-nullable
    with op.batch_alter_table('workspace_file_versions') as batch_op:
        batch_op.alter_column('sha256_hash',
                              existing_type=sa.String(length=64),
                              nullable=False)

    # 2. Drop columns from workspace_files
    with op.batch_alter_table('workspace_files') as batch_op:
        batch_op.drop_column('metadata')
        batch_op.drop_column('status')
        batch_op.drop_column('record_key')

    # 3. Drop metadata column from workspaces
    op.drop_column('workspaces', 'metadata')
