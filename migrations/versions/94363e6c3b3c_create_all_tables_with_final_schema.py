"""Create all tables with final schema

Revision ID: 94363e6c3b3c
Revises: 
Create Date: 2025-08-12 17:00:27.164031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94363e6c3b3c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 讓此遷移具備冪等性：表已存在則跳過
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_table(name: str) -> bool:
        return inspector.has_table(name)

    if not has_table('channels'):
        op.create_table('channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )

    if not has_table('customers'):
        op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('total_receivables_twd', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )

    if not has_table('holders'):
        op.create_table('holders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )

    if not has_table('user'):
        op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
        )

    if not has_table('cash_accounts'):
        op.create_table('cash_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('holder_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['holder_id'], ['holders.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    if not has_table('ledger_entries'):
        op.create_table('ledger_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_type', sa.String(length=50), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('entry_date', sa.DateTime(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['cash_accounts.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    # index（若表存在且索引不存在時才建立）
    if has_table('ledger_entries'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('ledger_entries')}
        index_name = 'ix_ledger_entries_entry_type'
        if index_name not in existing_indexes:
            with op.batch_alter_table('ledger_entries', schema=None) as batch_op:
                batch_op.create_index(batch_op.f(index_name), ['entry_type'], unique=False)

    if not has_table('purchase_records'):
        op.create_table('purchase_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_account_id', sa.Integer(), nullable=True),
        sa.Column('deposit_account_id', sa.Integer(), nullable=True),
        sa.Column('channel_id', sa.Integer(), nullable=True),
        sa.Column('rmb_amount', sa.Float(), nullable=False),
        sa.Column('exchange_rate', sa.Float(), nullable=False),
        sa.Column('twd_cost', sa.Float(), nullable=False),
        sa.Column('purchase_date', sa.DateTime(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.ForeignKeyConstraint(['deposit_account_id'], ['cash_accounts.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['payment_account_id'], ['cash_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    if not has_table('sales_records'):
        op.create_table('sales_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('rmb_account_id', sa.Integer(), nullable=True),
        sa.Column('rmb_amount', sa.Float(), nullable=False),
        sa.Column('exchange_rate', sa.Float(), nullable=False),
        sa.Column('twd_amount', sa.Float(), nullable=False),
        sa.Column('is_settled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['rmb_account_id'], ['cash_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    if not has_table('transactions'):
        op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sales_record_id', sa.Integer(), nullable=False),
        sa.Column('twd_account_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=True),
        sa.Column('note', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['sales_record_id'], ['sales_records.id'], ),
        sa.ForeignKeyConstraint(['twd_account_id'], ['cash_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    # ### end Alembic commands ###


def downgrade():
    # 僅在存在時才刪除，避免出錯
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    def has_table(name: str) -> bool:
        return inspector.has_table(name)

    if has_table('transactions'):
        op.drop_table('transactions')
    if has_table('sales_records'):
        op.drop_table('sales_records')
    if has_table('purchase_records'):
        op.drop_table('purchase_records')
    if has_table('ledger_entries'):
        # 刪索引（若存在）
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('ledger_entries')}
        index_name = 'ix_ledger_entries_entry_type'
        if index_name in existing_indexes:
            with op.batch_alter_table('ledger_entries', schema=None) as batch_op:
                batch_op.drop_index(batch_op.f(index_name))
        op.drop_table('ledger_entries')
    if has_table('cash_accounts'):
        op.drop_table('cash_accounts')
    if has_table('user'):
        op.drop_table('user')
    if has_table('holders'):
        op.drop_table('holders')
    if has_table('customers'):
        op.drop_table('customers')
    if has_table('channels'):
        op.drop_table('channels')
    # ### end Alembic commands ###
