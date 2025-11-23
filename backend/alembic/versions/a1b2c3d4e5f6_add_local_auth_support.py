"""add_local_auth_support

Revision ID: a1b2c3d4e5f6
Revises: f970dc25089c
Create Date: 2025-11-22 21:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f970dc25089c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_hash column (nullable for existing users and OAuth users)
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))

    # Add auth_provider column with default value 'google' for existing users
    # Using String instead of Enum for compatibility
    op.add_column("users", sa.Column(
        "auth_provider",
        sa.String(length=20),
        nullable=False,
        server_default="google"
    ))


def downgrade() -> None:
    # Remove columns
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "password_hash")
