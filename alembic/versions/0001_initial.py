"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"

down_revision = None

branch_labels = None

depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("last_joke_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "common",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_table(
        "black",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_table(
        "attempt",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_table(
        "rating",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_table("rating")
    op.drop_table("attempt")
    op.drop_table("black")
    op.drop_table("common")
    op.drop_table("users")
