"""Single workspace auth, protein, and account-optional cooking history."""
from alembic import op
import sqlalchemy as sa

revision = '20261114_02'
down_revision = '20261114_01'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('recipes') as batch:
        batch.add_column(sa.Column('protein', sa.String(100), nullable=False, server_default=''))
    with op.batch_alter_table('cooking_events') as batch:
        batch.alter_column('user_id', existing_type=sa.String(36), nullable=True)
        batch.add_column(sa.Column('actor_email', sa.String(320), nullable=True))


def downgrade():
    with op.batch_alter_table('cooking_events') as batch:
        batch.drop_column('actor_email')
        batch.alter_column('user_id', existing_type=sa.String(36), nullable=False)
    with op.batch_alter_table('recipes') as batch:
        batch.drop_column('protein')
