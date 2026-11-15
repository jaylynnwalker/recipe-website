"""Persistent Meals on Deck and grocery snapshots."""
from alembic import op
import sqlalchemy as sa

revision = '20261114_03'
down_revision = '20261114_02'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('deck_entries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('servings', sa.Integer(), nullable=False), sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('cooked_at', sa.DateTime(timezone=True), nullable=True), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('household_id', 'recipe_id', name='uq_household_deck_recipe'))
    op.create_index('ix_deck_entries_household_id', 'deck_entries', ['household_id'])
    op.create_index('ix_deck_entries_recipe_id', 'deck_entries', ['recipe_id'])
    op.create_table('grocery_lists',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_grocery_lists_household_id', 'grocery_lists', ['household_id'], unique=True)
    op.create_table('grocery_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('grocery_list_id', sa.String(36), sa.ForeignKey('grocery_lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('label', sa.String(240), nullable=False), sa.Column('normalized_name', sa.String(160), nullable=False),
        sa.Column('quantity', sa.Numeric(12, 4), nullable=True), sa.Column('unit', sa.String(60), nullable=True),
        sa.Column('category', sa.String(80), nullable=False), sa.Column('checked', sa.Boolean(), nullable=False),
        sa.Column('is_manual', sa.Boolean(), nullable=False), sa.Column('source_key', sa.String(260), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('grocery_list_id', 'source_key', name='uq_grocery_generated_source'))
    op.create_index('ix_grocery_items_grocery_list_id', 'grocery_items', ['grocery_list_id'])
    op.create_index('ix_grocery_items_normalized_name', 'grocery_items', ['normalized_name'])
    op.create_table('grocery_excluded_staples',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('grocery_list_id', sa.String(36), sa.ForeignKey('grocery_lists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(160), nullable=False), sa.Column('normalized_name', sa.String(160), nullable=False),
        sa.UniqueConstraint('grocery_list_id', 'normalized_name', name='uq_grocery_excluded_staple'))
    op.create_index('ix_grocery_excluded_staples_grocery_list_id', 'grocery_excluded_staples', ['grocery_list_id'])


def downgrade():
    op.drop_table('grocery_excluded_staples')
    op.drop_table('grocery_items')
    op.drop_table('grocery_lists')
    op.drop_table('deck_entries')
