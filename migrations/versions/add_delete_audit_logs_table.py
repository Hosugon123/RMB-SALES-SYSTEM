"""add delete audit logs table

Revision ID: add_delete_audit_logs
Revises: 94363e6c3b3c
Create Date: 2025-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_delete_audit_logs'
down_revision = '94363e6c3b3c'
branch_labels = None
depends_on = None


def upgrade():
    """添加刪除記錄審計表"""
    op.create_table('delete_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=50), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('deleted_data', sa.Text(), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=True),
        sa.Column('operator_name', sa.String(length=100), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['operator_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 創建索引以提高查詢效能
    op.create_index('ix_delete_audit_logs_table_name', 'delete_audit_logs', ['table_name'])
    op.create_index('ix_delete_audit_logs_record_id', 'delete_audit_logs', ['record_id'])
    op.create_index('ix_delete_audit_logs_deleted_at', 'delete_audit_logs', ['deleted_at'])
    op.create_index('ix_delete_audit_logs_operator_id', 'delete_audit_logs', ['operator_id'])


def downgrade():
    """移除刪除記錄審計表"""
    op.drop_index('ix_delete_audit_logs_operator_id', table_name='delete_audit_logs')
    op.drop_index('ix_delete_audit_logs_deleted_at', table_name='delete_audit_logs')
    op.drop_index('ix_delete_audit_logs_record_id', table_name='delete_audit_logs')
    op.drop_index('ix_delete_audit_logs_table_name', table_name='delete_audit_logs')
    op.drop_table('delete_audit_logs')

