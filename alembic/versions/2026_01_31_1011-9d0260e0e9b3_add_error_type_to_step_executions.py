"""add error_type to step_executions

Revision ID: 9d0260e0e9b3
Revises: 96240941449e
Create Date: 2026-01-31 10:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d0260e0e9b3'
down_revision: Union[str, None] = '96240941449e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add error_type column to step_executions
    op.add_column('step_executions', sa.Column('error_type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove error_type column from step_executions
    op.drop_column('step_executions', 'error_type')
