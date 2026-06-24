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
    if "payments" not in tables:
        op.create_table(
            "payments",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("order_id", sa.String(36), nullable=False),
            sa.Column("user_id", sa.String(36), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("status", sa.String(50), nullable=False),
            sa.Column("provider", sa.String(100), nullable=False),
            sa.Column("failure_reason", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_payments_order_id", "payments", ["order_id"])
        op.create_index("ix_payments_user_id", "payments", ["user_id"])
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
    if "inbox_events" not in tables:
        op.create_table(
            "inbox_events",
            sa.Column("event_id", sa.String(36), primary_key=True),
            sa.Column("event_type", sa.String(255), nullable=False),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("status", sa.String(50), nullable=False),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_inbox_events_event_type", "inbox_events", ["event_type"])
        op.create_index("ix_inbox_events_status", "inbox_events", ["status"])


def downgrade() -> None:
    op.drop_table("inbox_events")
    op.drop_table("outbox_events")
    op.drop_table("payments")
