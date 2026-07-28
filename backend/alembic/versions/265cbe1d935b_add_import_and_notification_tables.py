"""add_import_and_notification_tables

Revision ID: 265cbe1d935b
Revises: c6b4254afc25
Create Date: 2026-07-16 12:49:16.299904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '265cbe1d935b'
down_revision: Union[str, None] = 'c6b4254afc25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create import_jobs table
    op.create_table(
        'import_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='uploaded', nullable=False),
        sa.Column('total_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('accepted_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('duplicate_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('rejected_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_summary', sa.String(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_import_jobs_user_id', 'import_jobs', ['user_id'], unique=False)

    # 2. Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=False), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('archived', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('delivery_channel', sa.String(), server_default='in_app', nullable=False),
        sa.Column('delivered_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_import_jobs_user_id', table_name='import_jobs')
    op.drop_table('import_jobs')
