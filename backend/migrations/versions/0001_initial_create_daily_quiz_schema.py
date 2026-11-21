"""Create daily quiz schema

Revision ID: 0001_initial
Revises: None
Create Date: 2026-11-22 01:52:33.664334

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_table(
        'daily_challenges',
        sa.Column('challenge_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('challenge_date')
    )
    op.create_table(
        'games',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('player_id', sa.String(length=36), nullable=False),
        sa.Column('challenge_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_summary', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['challenge_date'], ['daily_challenges.challenge_date']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id', 'challenge_date', name='uq_player_daily_run')
    )
    op.create_index('ix_games_challenge_date', 'games', ['challenge_date'], unique=False)
    op.create_index('ix_games_player_id', 'games', ['player_id'], unique=False)
    op.create_index('ix_games_run_id', 'games', ['run_id'], unique=True)
    op.create_index('ix_games_status', 'games', ['status'], unique=False)

    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_questions_status', 'questions', ['status'], unique=False)

    op.create_table(
        'accepted_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('canonical', sa.String(length=256), nullable=False),
        sa.Column('normalized', sa.String(length=256), nullable=False),
        sa.Column('rarity_tier', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('license_name', sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('question_id', 'normalized', name='uq_answer_question_normalized')
    )
    op.create_index('ix_accepted_answers_question_id', 'accepted_answers', ['question_id'], unique=False)

    op.create_table(
        'daily_challenge_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenge_date', sa.Date(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['challenge_date'], ['daily_challenges.challenge_date'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('challenge_date', 'position', name='uq_daily_question_position'),
        sa.UniqueConstraint('challenge_date', 'question_id', name='uq_daily_question_id')
    )
    op.create_index('ix_daily_challenge_questions_challenge_date', 'daily_challenge_questions', ['challenge_date'], unique=False)

    op.create_table(
        'game_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'position', name='uq_game_question_position'),
        sa.UniqueConstraint('game_id', 'question_id', name='uq_game_question_id')
    )
    op.create_index('ix_game_questions_game_id', 'game_questions', ['game_id'], unique=False)

    op.create_table(
        'answer_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('answer_id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(length=256), nullable=False),
        sa.Column('normalized', sa.String(length=256), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['accepted_answers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('answer_id', 'normalized', name='uq_alias_answer_normalized')
    )
    op.create_index('ix_answer_aliases_answer_id', 'answer_aliases', ['answer_id'], unique=False)
    op.create_index('ix_answer_aliases_normalized', 'answer_aliases', ['normalized'], unique=False)

    op.create_table(
        'game_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('submitted_answer', sa.String(length=256), nullable=False),
        sa.Column('normalized_answer', sa.String(length=256), nullable=False),
        sa.Column('points_awarded', sa.Integer(), nullable=False),
        sa.Column('accepted_answer_id', sa.Integer(), nullable=False),
        sa.Column('receipt_token', sa.Text(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['accepted_answer_id'], ['accepted_answers.id']),
        sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('game_id', 'question_id', name='uq_submission_game_question'),
        sa.UniqueConstraint('receipt_token')
    )
    op.create_index('ix_game_submissions_game_id', 'game_submissions', ['game_id'], unique=False)


def downgrade():
    op.drop_table('game_submissions')
    op.drop_table('answer_aliases')
    op.drop_table('game_questions')
    op.drop_table('daily_challenge_questions')
    op.drop_table('accepted_answers')
    op.drop_table('questions')
    op.drop_table('games')
    op.drop_table('daily_challenges')
    op.drop_table('categories')
