"""convert_auth_provider_to_string

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-22 21:25:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert auth_provider column from enum to string for PostgreSQL compatibility
    # This uses raw SQL to handle the conversion properly

    # Check if we're using PostgreSQL by attempting enum-specific operations
    connection = op.get_bind()

    # For PostgreSQL: alter column type and drop enum
    if connection.dialect.name == "postgresql":
        # First, drop the default value
        op.execute("""
            ALTER TABLE users
            ALTER COLUMN auth_provider DROP DEFAULT
        """)

        # Then, alter the column to VARCHAR using USING clause to cast the enum
        op.execute("""
            ALTER TABLE users
            ALTER COLUMN auth_provider TYPE VARCHAR(20)
            USING auth_provider::text
        """)

        # Finally, drop the enum type
        op.execute("DROP TYPE IF EXISTS authprovider")

    # For SQLite, the column should already be correct from previous migration
    # No action needed


def downgrade() -> None:
    # This downgrade recreates the enum type for PostgreSQL
    connection = op.get_bind()

    if connection.dialect.name == "postgresql":
        # Recreate enum type
        op.execute("CREATE TYPE authprovider AS ENUM ('local', 'google')")

        # Convert column back to enum
        op.execute("""
            ALTER TABLE users
            ALTER COLUMN auth_provider TYPE authprovider
            USING auth_provider::authprovider
        """)
