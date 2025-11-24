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
    # Add parent_id column to templates
    op.add_column("templates", sa.Column("parent_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_templates_parent_id", "templates", "templates", ["parent_id"], ["id"])
    op.create_index(op.f("ix_templates_parent_id"), "templates", ["parent_id"], unique=False)

    # Add order column to templates
    op.add_column("templates", sa.Column("order", sa.Integer(), server_default="0", nullable=False))
    op.create_index(op.f("ix_templates_order"), "templates", ["order"], unique=False)


def downgrade() -> None:
    # Drop order column and index
    op.drop_index(op.f("ix_templates_order"), table_name="templates")
    op.drop_column("templates", "order")

    # Drop parent_id column, foreign key, and index
    op.drop_index(op.f("ix_templates_parent_id"), table_name="templates")
    op.drop_constraint("fk_templates_parent_id", "templates", type_="foreignkey")
    op.drop_column("templates", "parent_id")
