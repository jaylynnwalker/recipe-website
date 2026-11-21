"""distinguish import source pages from cover images

Revision ID: 20261120_09
Revises: 20261120_08
"""
from alembic import op
import sqlalchemy as sa

revision = '20261120_09'
down_revision = '20261120_08'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('import_assets') as batch:
        batch.add_column(sa.Column('role', sa.String(length=30), nullable=False, server_default='source'))


def downgrade():
    with op.batch_alter_table('import_assets') as batch:
        batch.drop_column('role')
