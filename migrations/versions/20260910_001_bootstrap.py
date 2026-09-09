"""Establish migration tracking without business tables."""

revision = "20260910_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    raise RuntimeError("Destructive rollback is disabled; use a reviewed forward migration")
