"""
SQLAlchemy ORM Models: Eingehende Postfach-Antworten

Jeder eingehende Mailgun-Webhook-Aufruf wird hier protokolliert - auch
automatisch zugeordnete -, als Audit-Trail/Debugging-Log. Eigene, neue
Tabellen (kein Bezug zu request_items/requests per ALTER TABLE), analog
zu den übrigen Seitentabellen dieser Anwendung.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class InboundEmail(Base):
    """Eine eingehende E-Mail, wie sie roh vom Mailgun-Webhook empfangen wurde."""

    __tablename__ = "inbound_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    from_address = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    body_text = Column(Text, nullable=True)

    # Nur gesetzt, wenn die Antwort eindeutig einem RequestItem zugeordnet
    # werden konnte (automatisch oder manuell) - solange NULL, wartet die
    # E-Mail in der Zuordnungs-Warteschlange.
    matched_request_item_id = Column(String(100), ForeignKey("request_items.request_item_id"), nullable=True)
    auto_matched = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    attachments = relationship("InboundEmailAttachment", back_populates="email", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "from_address": self.from_address,
            "subject": self.subject,
            "body_text": self.body_text,
            "matched_request_item_id": self.matched_request_item_id,
            "auto_matched": self.auto_matched,
            "attachments": [a.to_dict() for a in self.attachments],
        }


class InboundEmailAttachment(Base):
    """Ein einzelner Datei-Anhang einer eingehenden E-Mail (PDF-Bytes in der DB)."""

    __tablename__ = "inbound_email_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inbound_email_id = Column(Integer, ForeignKey("inbound_emails.id"), nullable=False)
    filename = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=True)
    content = Column(LargeBinary, nullable=False)

    email = relationship("InboundEmail", back_populates="attachments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "inbound_email_id": self.inbound_email_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "size": len(self.content) if self.content else 0,
        }
