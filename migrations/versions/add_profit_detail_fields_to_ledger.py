"""Add profit detail fields to ledger entries

Revision ID: add_profit_detail_fields
Revises: b5bc6a6c2693
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_profit_detail_fields'
down_revision = 'b5bc6a6c2693'
branch_labels = None
depends_on = None


def upgrade():
    # 若欄位已存在，避免重複新增
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('ledger_entries')}

    if 'profit_before' not in existing_columns:
        op.add_column('ledger_entries', sa.Column('profit_before', sa.Float(), nullable=True))
    if 'profit_after' not in existing_columns:
        op.add_column('ledger_entries', sa.Column('profit_after', sa.Float(), nullable=True))
    if 'profit_change' not in existing_columns:
        op.add_column('ledger_entries', sa.Column('profit_change', sa.Float(), nullable=True))


def downgrade():
    # 僅在欄位存在時才刪除
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('ledger_entries')}

    if 'profit_change' in existing_columns:
        op.drop_column('ledger_entries', 'profit_change')
    if 'profit_after' in existing_columns:
        op.drop_column('ledger_entries', 'profit_after')
    if 'profit_before' in existing_columns:
        op.drop_column('ledger_entries', 'profit_before')


