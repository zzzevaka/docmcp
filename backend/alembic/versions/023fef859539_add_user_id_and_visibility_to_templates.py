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
    # Add PRIVATE to templatevisibility enum (PostgreSQL only)
    # SQLite doesn't have ALTER TYPE - it handles enum values via CHECK constraints
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE templatevisibility ADD VALUE IF NOT EXISTS 'PRIVATE'")

    # Use batch mode for SQLite to handle constraints
    with op.batch_alter_table("templates", schema=None) as batch_op:
        # Add user_id column
        batch_op.add_column(sa.Column("user_id", sa.UUID(), nullable=True))
        batch_op.create_foreign_key("fk_templates_user_id", "users", ["user_id"], ["id"])
        batch_op.create_index(batch_op.f("ix_templates_user_id"), ["user_id"], unique=False)

        # Add visibility column with default TEAM
        batch_op.add_column(
            sa.Column("visibility",
                      sa.Enum("PRIVATE", "TEAM", "PUBLIC", name="templatevisibility"),
                      nullable=False,
                      server_default="TEAM"))
        batch_op.create_index(batch_op.f("ix_templates_visibility"), ["visibility"], unique=False)


def downgrade() -> None:
    # Use batch mode for SQLite to handle constraints
    with op.batch_alter_table("templates", schema=None) as batch_op:
        # Drop visibility column and index
        batch_op.drop_index(batch_op.f("ix_templates_visibility"))
        batch_op.drop_column("visibility")

        # Drop user_id column, index, and foreign key
        batch_op.drop_index(batch_op.f("ix_templates_user_id"))
        batch_op.drop_constraint("fk_templates_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")

