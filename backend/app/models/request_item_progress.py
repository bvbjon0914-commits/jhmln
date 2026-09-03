"""
SQLAlchemy ORM Model: RequestItemProgress

Fortschritts-Status pro RequestItem jenseits der reinen Dokumentgenerierung
(wurde es tatsächlich versendet, ist eine Antwort da, wurde sie geprüft).
Eigene 1:1-Seitentabelle statt neuer Spalten auf request_items – analog zu
AuthorityLocation/Authority, damit bestehende Tabellen unangetastet bleiben.

Antwort-PDFs werden als Bytes direkt in der Datenbank gespeichert (nicht auf
Festplatte): Render-Hosting hat flüchtigen Festplattenspeicher, der bei jedem
Redeploy gelöscht wird – eine echte Behörden-Antwort darf dabei nicht
verloren gehen.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, LargeBinary, ForeignKey
from app.database.base import Base


class RequestItemProgress(Base):
    __tablename__ = "request_item_progress"

    request_item_id = Column(
        String(100), ForeignKey("request_items.request_item_id"), primary_key=True
    )

    sent_at = Column(DateTime, nullable=True)

    response_received_at = Column(DateTime, nullable=True)
    response_document = Column(LargeBinary, nullable=True)
    response_document_filename = Column(String(255), nullable=True)

    reviewed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "request_item_id": self.request_item_id,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "response_received_at": self.response_received_at.isoformat() if self.response_received_at else None,
            "response_document_filename": self.response_document_filename,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
