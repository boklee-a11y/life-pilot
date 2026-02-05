"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-02-06 01:07:25.941832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === users ===
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('profile_image_url', sa.String, nullable=True),
        sa.Column('job_category', sa.String(50), nullable=True),
        sa.Column('years_of_experience', sa.Integer, nullable=True),
        sa.Column('auth_provider', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # === data_sources ===
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(30), nullable=False),
        sa.Column('source_url', sa.Text, nullable=False),
        sa.Column('scraped_html', sa.Text, nullable=True),
        sa.Column('parsed_data', postgresql.JSONB, nullable=True),
        sa.Column('is_confirmed', sa.Boolean, default=False),
        sa.Column('last_scraped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_data_sources_user_id', 'data_sources', ['user_id'])

    # === career_scores ===
    op.create_table(
        'career_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expertise_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('influence_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('consistency_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('marketability_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('potential_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('total_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('estimated_salary_min', sa.BigInteger, nullable=True),
        sa.Column('estimated_salary_max', sa.BigInteger, nullable=True),
        sa.Column('analysis_accuracy', sa.Numeric(5, 2), nullable=True),
        sa.Column('ai_insights', postgresql.JSONB, nullable=True),
        sa.Column('scored_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_career_scores_user_id', 'career_scores', ['user_id'])

    # === action_recommendations ===
    op.create_table(
        'action_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('career_scores.id'), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('impact_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('target_area', sa.String(20), nullable=True),
        sa.Column('difficulty', sa.String(10), nullable=True),
        sa.Column('estimated_duration', sa.String(50), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('cta_label', sa.String(100), nullable=True),
        sa.Column('cta_url', sa.Text, nullable=True),
        sa.Column('is_completed', sa.Boolean, default=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_bookmarked', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_action_recommendations_user_id', 'action_recommendations', ['user_id'])

    # === score_history ===
    op.create_table(
        'score_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('career_scores.id'), nullable=False),
        sa.Column('snapshot', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_score_history_user_id', 'score_history', ['user_id'])

    # === market_data ===
    op.create_table(
        'market_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_category', sa.String(50), nullable=False),
        sa.Column('skill_name', sa.String(100), nullable=True),
        sa.Column('demand_level', sa.Integer, nullable=True),
        sa.Column('avg_salary_min', sa.BigInteger, nullable=True),
        sa.Column('avg_salary_max', sa.BigInteger, nullable=True),
        sa.Column('years_range', sa.String(20), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('demand_level BETWEEN 1 AND 10', name='check_demand_level'),
    )


def downgrade() -> None:
    op.drop_table('market_data')
    op.drop_table('score_history')
    op.drop_table('action_recommendations')
    op.drop_table('career_scores')
    op.drop_table('data_sources')
    op.drop_table('users')
