"""add recipe yield and additional time

Revision ID: 20261120_07
Revises: 20261120_06
"""
from alembic import op
import sqlalchemy as sa

revision = '20261120_07'
down_revision = '20261120_06'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('recipes') as batch:
        batch.add_column(sa.Column('additional_time_minutes', sa.Integer(), nullable=False, server_default='0'))
        batch.add_column(sa.Column('additional_time_label', sa.String(length=60), nullable=False, server_default='Additional'))
        batch.add_column(sa.Column('yield_unit', sa.String(length=60), nullable=False, server_default='servings'))


def downgrade():
    with op.batch_alter_table('recipes') as batch:
        batch.drop_column('yield_unit')
        batch.drop_column('additional_time_label')
        batch.drop_column('additional_time_minutes')
