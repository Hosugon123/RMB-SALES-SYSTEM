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
    # 檢查欄位是否已存在，避免重複添加
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col['name'] for col in inspector.get_columns('ledger_entries')}
    
    # 添加轉帳相關欄位（僅在不存在時添加）
    if 'from_account_id' not in existing_columns:
        op.add_column('ledger_entries', sa.Column('from_account_id', sa.Integer(), nullable=True))
    if 'to_account_id' not in existing_columns:
        op.add_column('ledger_entries', sa.Column('to_account_id', sa.Integer(), nullable=True))
    
    # 檢查外鍵約束是否已存在
    existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('ledger_entries')}
    
    # 添加外鍵約束（僅在不存在時添加）
    if 'fk_ledger_entries_from_account' not in existing_fks:
        op.create_foreign_key('fk_ledger_entries_from_account', 'ledger_entries', 'cash_accounts', ['from_account_id'], ['id'])
    if 'fk_ledger_entries_to_account' not in existing_fks:
        op.create_foreign_key('fk_ledger_entries_to_account', 'ledger_entries', 'cash_accounts', ['to_account_id'], ['id'])


def downgrade():
    # 檢查外鍵約束是否存在，避免重複刪除
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('ledger_entries')}
    
    # 移除外鍵約束（僅在存在時刪除）
    if 'fk_ledger_entries_to_account' in existing_fks:
        op.drop_constraint('fk_ledger_entries_to_account', 'ledger_entries', type_='foreignkey')
    if 'fk_ledger_entries_from_account' in existing_fks:
        op.drop_constraint('fk_ledger_entries_from_account', 'ledger_entries', type_='foreignkey')
    
    # 檢查欄位是否存在，避免重複刪除
    existing_columns = {col['name'] for col in inspector.get_columns('ledger_entries')}
    
    # 移除欄位（僅在存在時刪除）
    if 'to_account_id' in existing_columns:
        op.drop_column('ledger_entries', 'to_account_id')
    if 'from_account_id' in existing_columns:
        op.drop_column('ledger_entries', 'from_account_id')
