"""add the identifier some tags need

Revision ID: 004_source_tag_identifier
Revises: 003_source_tags
Create Date: 2026-11-20 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "004_source_tag_identifier"
down_revision: Union[str, None] = "003_source_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("source_tags", sa.Column("identifier", sa.Text()))


def downgrade() -> None:
    op.drop_column("source_tags", "identifier")
