"""store consolidated grocery components and source recipes

Revision ID: 20261122_11
Revises: 20261121_10
"""
from alembic import op
import sqlalchemy as sa

revision = '20261122_11'
down_revision = '20261121_10'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('grocery_items') as batch:
        batch.add_column(sa.Column('quantity_details', sa.Text(), nullable=False, server_default='[]'))
    op.create_table(
        'grocery_item_sources',
        sa.Column('grocery_item_id', sa.String(length=36), nullable=False),
        sa.Column('recipe_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['grocery_item_id'], ['grocery_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('grocery_item_id', 'recipe_id'),
    )


def downgrade():
    op.drop_table('grocery_item_sources')
    with op.batch_alter_table('grocery_items') as batch:
        batch.drop_column('quantity_details')
