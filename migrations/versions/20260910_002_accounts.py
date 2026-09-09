"""Add only the Account Foundation columns; identity/auth fields remain deferred."""

import sqlalchemy as sa
from alembic import op

revision = "20260910_002"
down_revision = "20260910_001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column(
            "account_status",
            sa.Enum(
                "PENDING",
                "ACTIVE",
                "SUSPENDED",
                "WITHDRAWN",
                "BLOCKED",
                native_enum=False,
                create_constraint=True,
                name="ck_accounts_status",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("account_id", name="pk_accounts"),
        sa.CheckConstraint("updated_at >= created_at", name="ck_accounts_updated_at"),
        sa.CheckConstraint(
            "deleted_at IS NULL OR deleted_at >= created_at", name="ck_accounts_deleted_at"
        ),
    )
    op.create_index("ix_accounts_account_status", "accounts", ["account_status"])


def downgrade():
    raise RuntimeError("Account data must be preserved; use a reviewed forward migration")
