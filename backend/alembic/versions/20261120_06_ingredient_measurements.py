"""add alternative ingredient measurements

Revision ID: 20261120_06
Revises: 20261114_05
"""
from alembic import op
import sqlalchemy as sa

revision = '20261120_06'
down_revision = '20261114_05'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('recipe_ingredients') as batch:
        batch.add_column(sa.Column('package_detail', sa.String(length=100), nullable=True))
    op.create_table('ingredient_measurements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recipe_ingredient_id', sa.String(length=36), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(12, 4), nullable=False),
        sa.Column('unit', sa.String(length=60), nullable=True),
        sa.ForeignKeyConstraint(['recipe_ingredient_id'], ['recipe_ingredients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recipe_ingredient_id', 'position', name='uq_ingredient_measurement_position'))
    op.create_index(op.f('ix_ingredient_measurements_recipe_ingredient_id'), 'ingredient_measurements', ['recipe_ingredient_id'])


def downgrade():
    op.drop_index(op.f('ix_ingredient_measurements_recipe_ingredient_id'), table_name='ingredient_measurements')
    op.drop_table('ingredient_measurements')
    with op.batch_alter_table('recipe_ingredients') as batch:
        batch.drop_column('package_detail')
