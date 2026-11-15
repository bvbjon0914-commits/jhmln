"""Recherchevorschläge bleiben bis zur menschlichen Entscheidung getrennt."""
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from app.database.base import Base


class ContactReview(Base):
    __tablename__ = "contact_review_proposals"

    proposal_id = Column(String(64), primary_key=True)
    authority_id = Column(String(50), ForeignKey("authorities.authority_id"), nullable=False)
    request_type_id = Column(String(50), ForeignKey("request_types.request_type_id"), nullable=False)
    channel_type = Column(String(20), nullable=False)
    value = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    source_sha256 = Column(String(64), nullable=False)
    observed_at = Column(DateTime, nullable=False)
    evidence = Column(Text, nullable=False)
    reasons = Column(Text, nullable=False)
    ags = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    version = Column(Integer, nullable=False, default=1)
    channel_id = Column(Integer, ForeignKey("authority_contact_channels.id"), nullable=True)
    history = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_contact_review_status_updated", "status", "updated_at"),
        Index("ix_contact_review_authority_type", "authority_id", "request_type_id"),
    )
