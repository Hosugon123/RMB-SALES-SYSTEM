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
    # 欄位已存在，完全跳過所有操作以避免 DuplicateColumn 錯誤
    # from_account_id, to_account_id, profit_before, profit_after, profit_change 欄位
    # 已由 fix_postgresql_columns.py 腳本創建
    
    # 外鍵約束也由 fix_postgresql_columns.py 管理
    # 此 Migration 檔案不再執行任何 DDL 操作
    pass


def downgrade():
    # 欄位和約束由 fix_postgresql_columns.py 管理
    # 此 Migration 檔案不執行任何 DDL 操作
    # 避免與其他系統組件產生衝突
    pass
