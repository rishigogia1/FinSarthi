"""add_user_roles_and_onboarding

Revision ID: d47822111249
Revises: 265cbe1d935b
Create Date: 2026-07-16 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd47822111249'
down_revision: Union[str, None] = '265cbe1d935b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to users table
    op.add_column(
        'users',
        sa.Column('role', sa.String(), server_default='user', nullable=False)
    )
    op.add_column(
        'users',
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.add_column(
        'users',
        sa.Column('onboarding_completed', sa.Boolean(), server_default='false', nullable=False)
    )


def downgrade() -> None:
    op.drop_column('users', 'onboarding_completed')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'role')
