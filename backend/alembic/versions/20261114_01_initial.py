"""Initial household recipe schema."""
from alembic import op
import sqlalchemy as sa

revision = '20261114_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('households', sa.Column('id', sa.String(36), primary_key=True), sa.Column('name', sa.String(120), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('users', sa.Column('id', sa.String(36), primary_key=True), sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False), sa.Column('email', sa.String(320), nullable=False), sa.Column('display_name', sa.String(100), nullable=False), sa.Column('password_hash', sa.String(255), nullable=False), sa.Column('is_active', sa.Boolean(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint('email'))
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_household_id', 'users', ['household_id'])
    op.create_table('user_sessions', sa.Column('id', sa.String(36), primary_key=True), sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('token_hash', sa.String(64), nullable=False, unique=True), sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_user_sessions_token_hash', 'user_sessions', ['token_hash'])
    op.create_table('ingredients', sa.Column('id', sa.String(36), primary_key=True), sa.Column('normalized_name', sa.String(160), nullable=False, unique=True), sa.Column('display_name', sa.String(160), nullable=False))
    op.create_table('tags', sa.Column('id', sa.String(36), primary_key=True), sa.Column('name', sa.String(100), nullable=False, unique=True))
    op.create_table('categories', sa.Column('id', sa.String(36), primary_key=True), sa.Column('name', sa.String(100), nullable=False, unique=True))
    op.create_table('recipes', sa.Column('id', sa.String(36), primary_key=True), sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False), sa.Column('title', sa.String(200), nullable=False), sa.Column('description', sa.Text(), nullable=False), sa.Column('status', sa.String(30), nullable=False), sa.Column('cuisine', sa.String(100), nullable=False), sa.Column('prep_minutes', sa.Integer(), nullable=False), sa.Column('cook_minutes', sa.Integer(), nullable=False), sa.Column('base_servings', sa.Integer(), nullable=False), sa.Column('notes', sa.Text(), nullable=False), sa.Column('source_type', sa.String(30)), sa.Column('source_label', sa.String(300), nullable=False), sa.Column('source_url', sa.String(2048)), sa.Column('source_page', sa.String(100)), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint('household_id', 'title', name='uq_household_recipe_title'))
    op.create_index('ix_recipes_household_id', 'recipes', ['household_id'])
    op.create_table('recipe_ingredients', sa.Column('id', sa.String(36), primary_key=True), sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False), sa.Column('ingredient_id', sa.String(36), sa.ForeignKey('ingredients.id'), nullable=False), sa.Column('position', sa.Integer(), nullable=False), sa.Column('quantity', sa.Numeric(12, 4)), sa.Column('unit', sa.String(60)), sa.Column('note', sa.String(300)), sa.Column('optional', sa.Boolean(), nullable=False), sa.UniqueConstraint('recipe_id', 'position', name='uq_recipe_ingredient_position'))
    op.create_table('recipe_steps', sa.Column('id', sa.String(36), primary_key=True), sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False), sa.Column('position', sa.Integer(), nullable=False), sa.Column('instruction', sa.Text(), nullable=False), sa.Column('tip', sa.Text()), sa.UniqueConstraint('recipe_id', 'position', name='uq_recipe_step_position'))
    op.create_table('recipe_tags', sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True), sa.Column('tag_id', sa.String(36), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True))
    op.create_table('recipe_categories', sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True), sa.Column('category_id', sa.String(36), sa.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True))
    op.create_table('recipe_photos', sa.Column('id', sa.String(36), primary_key=True), sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False), sa.Column('storage_name', sa.String(255), nullable=False, unique=True), sa.Column('original_name', sa.String(255), nullable=False), sa.Column('media_type', sa.String(80), nullable=False), sa.Column('alt_text', sa.String(300), nullable=False), sa.Column('position', sa.Integer(), nullable=False), sa.Column('is_cover', sa.Boolean(), nullable=False))
    op.create_table('cooking_events', sa.Column('id', sa.String(36), primary_key=True), sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False), sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('cooked_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('pantry_staples', sa.Column('id', sa.String(36), primary_key=True), sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False), sa.Column('name', sa.String(160), nullable=False), sa.Column('normalized_name', sa.String(160), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint('household_id', 'normalized_name', name='uq_household_pantry_staple'))


def downgrade():
    for table in ['pantry_staples', 'cooking_events', 'recipe_photos', 'recipe_categories', 'recipe_tags', 'recipe_steps', 'recipe_ingredients', 'recipes', 'categories', 'tags', 'ingredients', 'user_sessions', 'users', 'households']:
        op.drop_table(table)
