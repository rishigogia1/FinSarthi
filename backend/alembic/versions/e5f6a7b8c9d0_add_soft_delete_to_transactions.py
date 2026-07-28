"""add_soft_delete_to_transactions

Revision ID: e5f6a7b8c9d0
Revises: d47822111249
Create Date: 2026-07-25 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd47822111249'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'transactions',
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False)
    )
    op.add_column(
        'transactions',
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True)
    )
    op.create_index('ix_transactions_is_deleted', 'transactions', ['is_deleted'])


def downgrade() -> None:
    op.drop_index('ix_transactions_is_deleted', table_name='transactions')
    op.drop_column('transactions', 'deleted_at')
    op.drop_column('transactions', 'is_deleted')
