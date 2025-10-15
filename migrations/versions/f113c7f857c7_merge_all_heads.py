"""merge all heads

Revision ID: f113c7f857c7
Revises: add_delete_audit_logs, add_fifo_tables, add_profit_detail_fields
Create Date: 2025-10-15 23:00:42.290412

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f113c7f857c7'
down_revision = ('add_delete_audit_logs', 'add_fifo_tables', 'add_profit_detail_fields')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
