"""add optional ingredient and instruction sections

Revision ID: 20261121_10
Revises: 20261120_09
"""
from alembic import op
import sqlalchemy as sa

revision = '20261121_10'
down_revision = '20261120_09'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'recipe_sections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('recipe_id', sa.String(length=36), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('heading', sa.String(length=120), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recipe_id', 'kind', 'position', name='uq_recipe_section_position'),
    )
    op.create_index(op.f('ix_recipe_sections_recipe_id'), 'recipe_sections', ['recipe_id'], unique=False)
    with op.batch_alter_table('recipe_ingredients') as batch:
        batch.add_column(sa.Column('section_id', sa.String(length=36), nullable=True))
        batch.create_index(batch.f('ix_recipe_ingredients_section_id'), ['section_id'], unique=False)
        batch.create_foreign_key('fk_recipe_ingredients_section_id', 'recipe_sections', ['section_id'], ['id'], ondelete='SET NULL')
    with op.batch_alter_table('recipe_steps') as batch:
        batch.add_column(sa.Column('section_id', sa.String(length=36), nullable=True))
        batch.create_index(batch.f('ix_recipe_steps_section_id'), ['section_id'], unique=False)
        batch.create_foreign_key('fk_recipe_steps_section_id', 'recipe_sections', ['section_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('recipe_steps') as batch:
        batch.drop_constraint('fk_recipe_steps_section_id', type_='foreignkey')
        batch.drop_index(batch.f('ix_recipe_steps_section_id'))
        batch.drop_column('section_id')
    with op.batch_alter_table('recipe_ingredients') as batch:
        batch.drop_constraint('fk_recipe_ingredients_section_id', type_='foreignkey')
        batch.drop_index(batch.f('ix_recipe_ingredients_section_id'))
        batch.drop_column('section_id')
    op.drop_index(op.f('ix_recipe_sections_recipe_id'), table_name='recipe_sections')
    op.drop_table('recipe_sections')
