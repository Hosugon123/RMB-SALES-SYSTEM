"""Add payment_status to purchase_records

Revision ID: add_payment_status_to_purchase_records
Revises: f113c7f857c7
Create Date: 2025-10-15 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_payment_status_to_purchase_records'
down_revision = 'f113c7f857c7'
branch_labels = None
depends_on = None


def upgrade():
    # 新增欄位到 purchase_records，預設 'paid' 不可為空
    op.add_column(
        'purchase_records',
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='paid')
    )
    # 將現有資料填入預設值後，移除 server_default，避免未來隱性預設
    with op.get_context().autocommit_block():
        op.execute("UPDATE purchase_records SET payment_status = 'paid' WHERE payment_status IS NULL")
    op.alter_column('purchase_records', 'payment_status', server_default=None)


def downgrade():
    op.drop_column('purchase_records', 'payment_status')


