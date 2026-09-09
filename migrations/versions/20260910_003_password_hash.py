"""Add optional password hash without modifying existing account data."""

import sqlalchemy as sa
from alembic import op

revision = "20260910_003"
down_revision = "20260910_002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("accounts", sa.Column("password_hash", sa.String(256), nullable=True))


def downgrade():
    raise RuntimeError("Credential data must be preserved; destructive downgrade is disabled")
