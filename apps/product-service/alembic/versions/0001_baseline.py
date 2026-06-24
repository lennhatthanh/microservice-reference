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
    if "categories" not in tables:
        op.create_table(
            "categories",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
        )
        op.create_index("ix_categories_name", "categories", ["name"], unique=True)
    if "products" not in tables:
        op.create_table(
            "products",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price", sa.Numeric(12, 2), nullable=False),
            sa.Column("stock", sa.Integer(), nullable=False),
            sa.Column("category_id", sa.String(36), sa.ForeignKey("categories.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_products_name", "products", ["name"])
    if "stock_reservations" not in tables:
        op.create_table(
            "stock_reservations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("product_id", sa.String(36), nullable=False),
            sa.Column("order_id", sa.String(36), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(50), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_stock_reservations_product_id", "stock_reservations", ["product_id"])
        op.create_index("ix_stock_reservations_order_id", "stock_reservations", ["order_id"])
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
    op.drop_table("stock_reservations")
    op.drop_table("products")
    op.drop_table("categories")
