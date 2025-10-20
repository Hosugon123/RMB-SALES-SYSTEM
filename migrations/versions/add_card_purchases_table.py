"""Add card_purchases table

Revision ID: add_card_purchases_table
Revises: 94363e6c3b3c
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_card_purchases_table'
down_revision = '94363e6c3b3c'
branch_labels = None
depends_on = None


def upgrade():
    # 檢查表是否已存在，避免重複建立
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if not inspector.has_table('card_purchases'):
        op.create_table('card_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_date', sa.DateTime(), nullable=False),
        sa.Column('supplier', sa.String(length=200), nullable=False),
        sa.Column('rmb_amount', sa.Float(), nullable=False),
        sa.Column('twd_equivalent', sa.Float(), nullable=False),
        sa.Column('calculated_rate', sa.Float(), nullable=False),
        sa.Column('rmb_with_fee', sa.Float(), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    # ### end Alembic commands ###


def downgrade():
    # 僅在表存在時才刪除
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if inspector.has_table('card_purchases'):
        op.drop_table('card_purchases')
    # ### end Alembic commands ###
