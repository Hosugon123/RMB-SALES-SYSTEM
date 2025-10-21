"""Add transfer columns to ledger_entries

Revision ID: add_transfer_columns
Revises: add_fifo_tables
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_transfer_columns'
down_revision = 'add_fifo_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 添加轉帳相關欄位
    op.add_column('ledger_entries', sa.Column('from_account_id', sa.Integer(), nullable=True))
    op.add_column('ledger_entries', sa.Column('to_account_id', sa.Integer(), nullable=True))
    
    # 添加外鍵約束
    op.create_foreign_key('fk_ledger_entries_from_account', 'ledger_entries', 'cash_accounts', ['from_account_id'], ['id'])
    op.create_foreign_key('fk_ledger_entries_to_account', 'ledger_entries', 'cash_accounts', ['to_account_id'], ['id'])


def downgrade():
    # 移除外鍵約束
    op.drop_constraint('fk_ledger_entries_to_account', 'ledger_entries', type_='foreignkey')
    op.drop_constraint('fk_ledger_entries_from_account', 'ledger_entries', type_='foreignkey')
    
    # 移除欄位
    op.drop_column('ledger_entries', 'to_account_id')
    op.drop_column('ledger_entries', 'from_account_id')
