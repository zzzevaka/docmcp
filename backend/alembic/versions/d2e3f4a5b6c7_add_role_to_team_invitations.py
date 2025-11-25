"""add_role_to_team_invitations

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2025-11-25 00:01:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column to team_invitations with default 'member'
    with op.batch_alter_table("team_invitations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.Enum("member", "administrator", name="teamrole"),
                nullable=False,
                server_default="administrator",
            )
        )


def downgrade() -> None:
    # Drop the role column from team_invitations
    with op.batch_alter_table("team_invitations", schema=None) as batch_op:
        batch_op.drop_column("role")
