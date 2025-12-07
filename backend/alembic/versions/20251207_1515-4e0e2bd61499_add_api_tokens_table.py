"""add api tokens table

Revision ID: 4e0e2bd61499
Revises: d2e3f4a5b6c7
Create Date: 2025-12-07 15:15:38.512707

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4e0e2bd61499"
down_revision = "42cbd79a56f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("api_tokens",
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(length=256), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_api_tokens_token"), "api_tokens", ["token"], unique=True)
    op.create_index(op.f("ix_api_tokens_user_id"), "api_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_tokens_user_id"), table_name="api_tokens")
    op.drop_index(op.f("ix_api_tokens_token"), table_name="api_tokens")
    op.drop_table("api_tokens")
