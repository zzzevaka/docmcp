"""populate_user_id_for_existing_templates

Revision ID: d16d4632fe08
Revises: 023fef859539
Create Date: 2025-11-24 17:50:33.729770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd16d4632fe08'
down_revision = '023fef859539'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For existing templates without user_id, set it to the first user in the template's team
    # This SQL query finds templates with NULL user_id and updates them with the first user from their team
    op.execute("""
        UPDATE templates
        SET user_id = (
            SELECT users.id
            FROM users
            JOIN user_team ON users.id = user_team.user_id
            WHERE user_team.team_id = templates.team_id
            LIMIT 1
        )
        WHERE user_id IS NULL
    """)


def downgrade() -> None:
    # No need to revert this - it's a data migration
    pass
