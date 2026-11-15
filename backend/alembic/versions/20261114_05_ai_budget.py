"""AI monthly budgets, reservations, and usage records."""
from alembic import op
import sqlalchemy as sa

revision = '20261114_05'
down_revision = '20261114_04'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ai_monthly_budgets',
        sa.Column('id', sa.String(36), primary_key=True), sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('month', sa.String(7), nullable=False), sa.Column('spent_microusd', sa.Integer(), nullable=False), sa.Column('reserved_microusd', sa.Integer(), nullable=False),
        sa.UniqueConstraint('household_id', 'month', name='uq_ai_household_month'))
    op.create_index('ix_ai_monthly_budgets_household_id', 'ai_monthly_budgets', ['household_id'])
    op.create_index('ix_ai_monthly_budgets_month', 'ai_monthly_budgets', ['month'])
    op.create_table('ai_requests',
        sa.Column('id', sa.String(36), primary_key=True), sa.Column('household_id', sa.String(36), sa.ForeignKey('households.id', ondelete='CASCADE'), nullable=False),
        sa.Column('budget_id', sa.String(36), sa.ForeignKey('ai_monthly_budgets.id', ondelete='CASCADE'), nullable=False), sa.Column('feature', sa.String(60), nullable=False),
        sa.Column('model', sa.String(100), nullable=False), sa.Column('status', sa.String(30), nullable=False), sa.Column('reserved_microusd', sa.Integer(), nullable=False),
        sa.Column('estimated_cost_microusd', sa.Integer(), nullable=True), sa.Column('input_tokens', sa.Integer(), nullable=True), sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_ai_requests_household_id', 'ai_requests', ['household_id'])
    op.create_index('ix_ai_requests_budget_id', 'ai_requests', ['budget_id'])
    op.create_index('ix_ai_requests_feature', 'ai_requests', ['feature'])
    op.create_index('ix_ai_requests_status', 'ai_requests', ['status'])


def downgrade():
    op.drop_table('ai_requests')
    op.drop_table('ai_monthly_budgets')
