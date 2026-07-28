"""add_workflow_metadata_to_conversations

Revision ID: f7e8d9c0b1a2
Revises: e5f6a7b8c9d0
Create Date: 2026-07-25 21:13:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7e8d9c0b1a2'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('workflow_id', sa.String(), nullable=True))
    op.add_column('conversations', sa.Column('workflow_status', sa.String(), nullable=True, server_default='ACTIVE'))
    op.add_column('conversations', sa.Column('primary_agent', sa.String(), nullable=True))
    op.add_column('conversations', sa.Column('supporting_agents', sa.JSON(), nullable=True))
    op.add_column('conversations', sa.Column('icon', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('conversations', 'icon')
    op.drop_column('conversations', 'supporting_agents')
    op.drop_column('conversations', 'primary_agent')
    op.drop_column('conversations', 'workflow_status')
    op.drop_column('conversations', 'workflow_id')
