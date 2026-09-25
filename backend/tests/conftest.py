"""
Gemeinsame Test-Fixtures.

WICHTIG: DATABASE_URL wird hier auf eine temporäre SQLite-Datei gesetzt,
BEVOR irgendein app.*-Modul importiert wird - app.database.engine liest
DATABASE_URL beim Modul-Import (nicht lazy). Diese Datei muss deshalb die
erste sein, die pytest lädt (Standardverhalten für conftest.py), und darf
selbst kein app.*-Modul importieren, bevor die Umgebungsvariablen gesetzt
sind.

Tests laufen NIE gegen die lokale Entwicklungsdatenbank
(authority_matching.db) und erst recht nicht gegen eine produktive
Datenbank - jede Testsession bekommt eine eigene, leere temporäre SQLite-
Datei, die am Ende wieder gelöscht wird.
"""
import os
import tempfile

_TMP_DB_FD, _TMP_DB_PATH = tempfile.mkstemp(suffix=".db", prefix="civeloq_test_")
os.close(_TMP_DB_FD)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB_PATH}"
os.environ.setdefault("SHARED_PASSWORD", "test-shared-password")
os.environ.setdefault("MAIN_PASSWORD", "test-main-password")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key-not-for-production-use")
os.environ.setdefault("MAILGUN_DRY_RUN", "true")

import atexit  # noqa: E402


@atexit.register
def _cleanup_tmp_db():
    try:
        os.remove(_TMP_DB_PATH)
    except OSError:
        pass


import pytest  # noqa: E402
import uuid  # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.engine import engine, SessionLocal  # noqa: E402
from app.models.building import Building  # noqa: E402
from app.models.authority import Authority  # noqa: E402
from app.models.jurisdiction import Jurisdiction  # noqa: E402
from app.models.request_type import RequestType, STANDARD_REQUEST_TYPES  # noqa: E402


@pytest.fixture()
def db_session():
    """Frische, leere Schema-Instanz je Testfunktion (drop+create), isolierte Session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def app_client(db_session):
    """FastAPI TestClient mit auf db_session umgeleiteter DB-Abhängigkeit."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database.engine import get_db_session

    def _override():
        yield db_session

    app.dependency_overrides[get_db_session] = _override
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory-Helfer für Testdaten
# ---------------------------------------------------------------------------

def make_request_type(db, code="GRUNDBUCH", name=None, active=True):
    rt = RequestType(
        request_type_id=code,
        code=code,
        name=name or code.title(),
        template_filename=f"{code.lower()}.docx",
        active=active,
    )
    db.add(rt)
    db.commit()
    return rt


def make_all_standard_request_types(db):
    for code in STANDARD_REQUEST_TYPES:
        if not db.query(RequestType).filter_by(request_type_id=code).first():
            db.add(RequestType(
                request_type_id=code, code=code, name=code.title(),
                template_filename=f"{code.lower()}.docx", active=True,
            ))
    db.commit()


def make_authority(db, name="Testbehörde", city="Bochum", **kwargs):
    a = Authority(
        authority_id=kwargs.pop("authority_id", str(uuid.uuid4())),
        authority_name=name,
        city=city,
        active=kwargs.pop("active", True),
        **kwargs,
    )
    db.add(a)
    db.commit()
    return a


def make_jurisdiction(db, request_type_id, authority_id, priority=100,
                       matching_level=None, active=True, **kwargs):
    j = Jurisdiction(
        jurisdiction_id=kwargs.pop("jurisdiction_id", str(uuid.uuid4())),
        request_type_id=request_type_id,
        authority_id=authority_id,
        priority=priority,
        matching_level=matching_level,
        active=active,
        **kwargs,
    )
    db.add(j)
    db.commit()
    return j


def make_building(db, street="Musterstraße", house_number="12",
                   postal_code="44787", city="Bochum", ags="05911000", **kwargs):
    b = Building(
        building_id=kwargs.pop("building_id", str(uuid.uuid4())),
        street=street,
        house_number=house_number,
        postal_code=postal_code,
        city=city,
        ags=ags,
        **kwargs,
    )
    db.add(b)
    db.commit()
    return b


def days_ago(n):
    return datetime.utcnow() - timedelta(days=n)
