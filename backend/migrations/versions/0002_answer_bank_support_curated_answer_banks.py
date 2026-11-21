"""Support curated answer banks.

Revision ID: 0002_answer_bank
Revises: 0001_initial
"""
import sqlalchemy as sa
from alembic import op


revision = "0002_answer_bank"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("accepted_answers", sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("questions", sa.Column("allow_fuzzy", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("questions", sa.Column("case_sensitive", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("questions", sa.Column("scope", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("questions", "scope")
    op.drop_column("questions", "case_sensitive")
    op.drop_column("questions", "allow_fuzzy")
    op.drop_column("accepted_answers", "is_active")
