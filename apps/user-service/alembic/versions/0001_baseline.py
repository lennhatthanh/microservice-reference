"""baseline schema

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-24
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("full_name", sa.String(255), nullable=False),
            sa.Column("role", sa.String(50), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    if "outbox_events" not in tables:
        op.create_table(
            "outbox_events",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("event_type", sa.String(255), nullable=False),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("status", sa.String(50), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
        op.create_index("ix_outbox_events_status", "outbox_events", ["status"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("users")
