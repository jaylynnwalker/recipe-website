"""add multi-select recipe proteins

Revision ID: 20261120_08
Revises: 20261120_07
"""
import uuid

from alembic import op
import sqlalchemy as sa

revision = '20261120_08'
down_revision = '20261120_07'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('proteins',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('name'))
    op.create_table('recipe_proteins',
        sa.Column('recipe_id', sa.String(length=36), nullable=False),
        sa.Column('protein_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['protein_id'], ['proteins.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('recipe_id', 'protein_id'))
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, protein FROM recipes WHERE trim(protein) != ''")).fetchall()
    protein_ids: dict[str, str] = {}
    for recipe_id, raw_name in rows:
        name = ' '.join(raw_name.split())
        key = name.casefold()
        protein_id = protein_ids.get(key)
        if not protein_id:
            protein_id = str(uuid.uuid4()); protein_ids[key] = protein_id
            connection.execute(sa.text('INSERT INTO proteins (id, name) VALUES (:id, :name)'), {'id': protein_id, 'name': name})
        connection.execute(sa.text('INSERT INTO recipe_proteins (recipe_id, protein_id) VALUES (:recipe_id, :protein_id)'), {'recipe_id': recipe_id, 'protein_id': protein_id})


def downgrade():
    op.drop_table('recipe_proteins')
    op.drop_table('proteins')
