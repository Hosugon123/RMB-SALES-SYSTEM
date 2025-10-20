"""Add profit_balance to cash_accounts

Revision ID: add_profit_balance_to_cash_accounts
Revises: add_payment_status_to_purchase_records
Create Date: 2025-10-20 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_profit_balance_to_cash_accounts'
down_revision = 'add_payment_status_to_purchase_records'
branch_labels = None
depends_on = None


def upgrade():
    # 新增欄位，先以 server_default=0 避免舊資料 NOT NULL 衝突
    op.add_column(
        'cash_accounts',
        sa.Column('profit_balance', sa.Float(), nullable=False, server_default='0')
    )
    # 既有資料填入後，移除隱性預設
    with op.get_context().autocommit_block():
        op.execute("UPDATE cash_accounts SET profit_balance = 0 WHERE profit_balance IS NULL")
    op.alter_column('cash_accounts', 'profit_balance', server_default=None)


def downgrade():
    op.drop_column('cash_accounts', 'profit_balance')


