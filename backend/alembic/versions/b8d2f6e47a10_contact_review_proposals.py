"""Belegte Kontaktvorschläge und menschliche Prüfentscheidungen.

Revision ID: b8d2f6e47a10
Revises: a7c3e91d5b24
"""
from alembic import op
import sqlalchemy as sa

revision = "b8d2f6e47a10"
down_revision = "a7c3e91d5b24"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "contact_review_proposals",
        sa.Column("proposal_id", sa.String(64), primary_key=True),
        sa.Column("authority_id", sa.String(50), sa.ForeignKey("authorities.authority_id"), nullable=False),
        sa.Column(
            "request_type_id", sa.String(50), sa.ForeignKey("request_types.request_type_id"), nullable=False
        ),
        sa.Column("channel_type", sa.String(20), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("reasons", sa.Text(), nullable=False),
        sa.Column("ags", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), sa.ForeignKey("authority_contact_channels.id"), nullable=True),
        sa.Column("history", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_contact_review_status_updated", "contact_review_proposals", ["status", "updated_at"])
    op.create_index(
        "ix_contact_review_authority_type", "contact_review_proposals", ["authority_id", "request_type_id"]
    )


def downgrade():
    op.drop_table("contact_review_proposals")
