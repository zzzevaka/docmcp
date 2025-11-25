"""add_hierarchy_to_templates

Revision ID: a1b2c3d4e5f7
Revises: d16d4632fe08
Create Date: 2025-11-24 20:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "d16d4632fe08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite to handle constraints
    with op.batch_alter_table("templates", schema=None) as batch_op:
        # Add parent_id column (self-referential foreign key)
        batch_op.add_column(sa.Column("parent_id", sa.UUID(), nullable=True))
        batch_op.create_foreign_key("fk_templates_parent_id", "templates", ["parent_id"], ["id"])
        batch_op.create_index(batch_op.f("ix_templates_parent_id"), ["parent_id"], unique=False)

        # Add order column
        batch_op.add_column(sa.Column("order", sa.Integer(), server_default="0", nullable=False))
        batch_op.create_index(batch_op.f("ix_templates_order"), ["order"], unique=False)


def downgrade() -> None:
    # Use batch mode for SQLite to handle constraints
    with op.batch_alter_table("templates", schema=None) as batch_op:
        # Drop order column and index
        batch_op.drop_index(batch_op.f("ix_templates_order"))
        batch_op.drop_column("order")

        # Drop parent_id column, foreign key, and index
        batch_op.drop_index(batch_op.f("ix_templates_parent_id"))
        batch_op.drop_constraint("fk_templates_parent_id", type_="foreignkey")
        batch_op.drop_column("parent_id")
