"""add retry fields to steps and step_executions

Revision ID: d9f14ccfc165
Revises: 9d0260e0e9b3
Create Date: 2026-01-31 11:29:49.624488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f14ccfc165'
down_revision: Union[str, None] = '9d0260e0e9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add retry_config to steps (nullable)
    op.add_column('steps', sa.Column('retry_config', sa.JSON(), nullable=True))
    
    # Add retry tracking fields to step_executions
    # Use server_default for existing rows, then remove it
    op.add_column('step_executions', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('step_executions', sa.Column('is_retry', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('step_executions', sa.Column('parent_step_execution_id', sa.UUID(), nullable=True))
    
    # Remove server_default after backfilling
    op.alter_column('step_executions', 'retry_count', server_default=None)
    op.alter_column('step_executions', 'is_retry', server_default=None)


def downgrade() -> None:
    op.drop_column('step_executions', 'parent_step_execution_id')
    op.drop_column('step_executions', 'is_retry')
    op.drop_column('step_executions', 'retry_count')
    op.drop_column('steps', 'retry_config')
