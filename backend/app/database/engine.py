"""
SQLAlchemy Engine und Session Management
Unterstützt SQLite (MVP) und PostgreSQL (Production)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Umgebungsvariablen für Datenbankverbindung
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./authority_matching.db"
)

# SQLite für MVP
if DATABASE_URL.startswith("sqlite://"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
# PostgreSQL für Production
else:
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_size=10,
        max_overflow=20,
    )

# SessionLocal für Dependency Injection
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db_session() -> Session:
    """
    Erzeugt eine neue Datenbankverbindung.
    Wird als FastAPI Dependency verwendet.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialisiert die Datenbank.
    Erstellt alle Tabellen basierend auf den ORM-Modellen.
    """
    from app.models import (
        Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
        AdministrativeUnit, AppSettings,
    )

    # Metadaten aller Models
    Building.metadata.create_all(bind=engine)
    RequestType.metadata.create_all(bind=engine)
    Authority.metadata.create_all(bind=engine)
    Jurisdiction.metadata.create_all(bind=engine)
    Request.metadata.create_all(bind=engine)
    RequestItem.metadata.create_all(bind=engine)
    AdministrativeUnit.metadata.create_all(bind=engine)
    AppSettings.metadata.create_all(bind=engine)

    print("✓ Datenbank initialisiert")


def drop_all_tables():
    """
    Löscht ALLE Tabellen. Nur für Development / Testing!
    """
    from app.models import (
        Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
        AdministrativeUnit, AppSettings,
    )

    Building.metadata.drop_all(bind=engine)
    RequestType.metadata.drop_all(bind=engine)
    Authority.metadata.drop_all(bind=engine)
    Jurisdiction.metadata.drop_all(bind=engine)
    Request.metadata.drop_all(bind=engine)
    RequestItem.metadata.drop_all(bind=engine)
    AdministrativeUnit.metadata.drop_all(bind=engine)
    AppSettings.metadata.drop_all(bind=engine)

    print("⚠ Alle Tabellen gelöscht!")
