"""
SQLAlchemy ORM Model: AppSettings

Singleton-Tabelle (genau eine Zeile, id=1) für app-weite Einstellungen,
die zur Laufzeit über die Verwaltung geändert werden können.
"""

from sqlalchemy import Column, Integer, Boolean
from app.database.base import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, default=1)
    login_required = Column(Boolean, default=True, nullable=False)

    @staticmethod
    def get_or_create(db) -> "AppSettings":
        settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
        if not settings:
            settings = AppSettings(id=1, login_required=True)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
