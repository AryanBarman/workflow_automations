"""Add step execution metadata

Revision ID: 7d2a1e9d1a3c
Revises: ee442b97a522
Create Date: 2026-02-14 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7d2a1e9d1a3c"
down_revision: Union[str, None] = "ee442b97a522"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("step_executions", sa.Column("step_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("step_executions", "step_metadata")
