"""Persistent recipe inbox and original import assets."""
from alembic import op
import sqlalchemy as sa

revision = '20261114_04'
down_revision = '20261114_03'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('import_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_type', sa.String(30), nullable=False), sa.Column('source_url', sa.String(2048), nullable=True),
        sa.Column('status', sa.String(30), nullable=False), sa.Column('title', sa.String(240), nullable=False),
        sa.Column('draft_payload', sa.Text(), nullable=False), sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duplicate_recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('saved_recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_import_jobs_household_id', 'import_jobs', ['household_id'])
    op.create_index('ix_import_jobs_source_url', 'import_jobs', ['source_url'])
    op.create_index('ix_import_jobs_status', 'import_jobs', ['status'])
    op.create_table('import_assets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('import_job_id', sa.String(36), sa.ForeignKey('import_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('storage_name', sa.String(255), nullable=False, unique=True), sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('media_type', sa.String(80), nullable=False), sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('import_job_id', 'position', name='uq_import_asset_position'))
    op.create_index('ix_import_assets_import_job_id', 'import_assets', ['import_job_id'])


def downgrade():
    op.drop_table('import_assets')
    op.drop_table('import_jobs')
