"""Add FIFO inventory tables

Revision ID: add_fifo_tables
Revises: add_card_purchases_table
Create Date: 2025-01-27 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fifo_tables'
down_revision = 'add_card_purchases_table'
branch_labels = None
depends_on = None


def upgrade():
    # 若表已存在則跳過，避免重複建立
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('fifo_inventory'):
        op.create_table('fifo_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_record_id', sa.Integer(), nullable=False),
        sa.Column('rmb_amount', sa.Float(), nullable=False),
        sa.Column('remaining_rmb', sa.Float(), nullable=False),
        sa.Column('unit_cost_twd', sa.Float(), nullable=False),
        sa.Column('exchange_rate', sa.Float(), nullable=False),
        sa.Column('purchase_date', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['purchase_record_id'], ['purchase_records.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    
    if not inspector.has_table('fifo_sales_allocations'):
        op.create_table('fifo_sales_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fifo_inventory_id', sa.Integer(), nullable=False),
        sa.Column('sales_record_id', sa.Integer(), nullable=False),
        sa.Column('allocated_rmb', sa.Float(), nullable=False),
        sa.Column('allocated_cost_twd', sa.Float(), nullable=False),
        sa.Column('allocation_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['fifo_inventory_id'], ['fifo_inventory.id'], ),
        sa.ForeignKeyConstraint(['sales_record_id'], ['sales_records.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    # ### end Alembic commands ###


def downgrade():
    # 僅在表存在時才刪除
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('fifo_sales_allocations'):
        op.drop_table('fifo_sales_allocations')
    if inspector.has_table('fifo_inventory'):
        op.drop_table('fifo_inventory')
    # ### end Alembic commands ###

