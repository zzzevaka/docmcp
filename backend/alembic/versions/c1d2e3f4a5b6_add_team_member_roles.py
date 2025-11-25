"""add_team_member_roles

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f7
Create Date: 2025-11-25 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE TYPE teamrole AS ENUM ('member', 'administrator')")

    with op.batch_alter_table("user_team", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.Enum("member", "administrator", name="teamrole"),
                nullable=False,
                server_default="administrator",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("user_team", schema=None) as batch_op:
        batch_op.drop_column("role")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS teamrole")
