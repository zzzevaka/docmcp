"""add_user_id_and_visibility_to_templates

Revision ID: 023fef859539
Revises: b2c3d4e5f6a7
Create Date: 2025-11-24 17:19:09.893664

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "023fef859539"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add PRIVATE to templatevisibility enum
    op.execute("ALTER TYPE templatevisibility ADD VALUE IF NOT EXISTS 'PRIVATE'")

    # Add user_id column to templates
    op.add_column("templates", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_templates_user_id", "templates", "users", ["user_id"], ["id"])
    op.create_index(op.f("ix_templates_user_id"), "templates", ["user_id"], unique=False)

    # Add visibility column to templates with default TEAM
    op.add_column("templates",
        sa.Column("visibility",
                  sa.Enum("PRIVATE", "TEAM", "PUBLIC", name="templatevisibility"),
                  nullable=False,
                  server_default="TEAM"))
    op.create_index(op.f("ix_templates_visibility"), "templates", ["visibility"], unique=False)


def downgrade() -> None:
    # Drop indexes and columns
    op.drop_index(op.f("ix_templates_visibility"), table_name="templates")
    op.drop_column("templates", "visibility")
    op.drop_index(op.f("ix_templates_user_id"), table_name="templates")
    op.drop_constraint("fk_templates_user_id", "templates", type_="foreignkey")
    op.drop_column("templates", "user_id")

    # Note: Cannot remove PRIVATE from enum in downgrade as PostgreSQL doesn't support it
    # This would require recreating the enum type entirely
