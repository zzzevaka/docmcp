"""add_library_tables

Revision ID: f970dc25089c
Revises: c842a705500c
Create Date: 2025-11-21 18:09:18.695815

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f970dc25089c"
down_revision = "c842a705500c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create categories table
    op.create_table("categories",
    sa.Column("name", sa.String(length=128), nullable=False),
    sa.Column("visibility", sa.Enum("TEAM", "PUBLIC", name="templatevisibility"), nullable=False),
    sa.Column("id", sa.Uuid(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("name")
    )
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=True)

    # Create templates table
    op.create_table("templates",
    sa.Column("name", sa.String(length=128), nullable=False),
    sa.Column("team_id", sa.UUID(), nullable=False),
    sa.Column("category_id", sa.UUID(), nullable=False),
    sa.Column("type", sa.Enum("MARKDOWN", "WHITEBOARD", name="templatetype"), nullable=False),
    sa.Column("content", sa.Text(), nullable=False),
    sa.Column("id", sa.Uuid(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ),
    sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ),
    sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_templates_category_id"), "templates", ["category_id"], unique=False)
    op.create_index(op.f("ix_templates_name"), "templates", ["name"], unique=False)
    op.create_index(op.f("ix_templates_team_id"), "templates", ["team_id"], unique=False)
    op.create_index(op.f("ix_templates_type"), "templates", ["type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_templates_type"), table_name="templates")
    op.drop_index(op.f("ix_templates_team_id"), table_name="templates")
    op.drop_index(op.f("ix_templates_name"), table_name="templates")
    op.drop_index(op.f("ix_templates_category_id"), table_name="templates")
    op.drop_table("templates")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_table("categories")
