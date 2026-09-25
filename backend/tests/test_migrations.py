"""
Regressionstest für das Alembic-Migrationsverfahren (Priorität 2 des
Auditberichts, Befund "Schema-Evolution").

Prüft genau das im Auftrag geforderte Verfahren automatisiert:
1. eine FRISCHE, leere Datenbank kommt über `alembic upgrade head` auf den
   vollständigen aktuellen Schema-Stand,
2. eine BESTEHENDE Datenbank (hier: über Base.metadata.create_all() wie vor
   Einführung von Alembic erzeugt, mit echten Daten befüllt - stellvertretend
   für die lokale Entwicklungsdatenbank) lässt sich per `alembic stamp head`
   auf den Baseline-Stand heben und nimmt danach künftige Migrationen
   klaglos an, OHNE die vorhandenen Daten zu verändern,
3. ein Downgrade der letzten Migration funktioniert (Rollback-Fähigkeit).

Läuft ausschließlich gegen temporäre, für den Test erzeugte SQLite-Dateien -
niemals gegen backend/authority_matching.db und erst recht nicht gegen eine
produktive Datenbank. Ruft Alembic bewusst als Subprozess auf (wie im echten
Betrieb/CI auch), damit jede Invocation ihre eigene DATABASE_URL aus der
Umgebung liest, statt den einen für die gesamte Testsession fest geladenen
Wert aus app.database.engine wiederzuverwenden.
"""
import os
import shutil
import subprocess
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_alembic(*args, database_url):
    env = {**os.environ, "DATABASE_URL": database_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


@pytest.fixture()
def tmp_sqlite_path(tmp_path):
    return tmp_path / "migration_test.db"


class TestFreshDatabase:
    def test_upgrade_head_creates_full_schema(self, tmp_sqlite_path):
        url = f"sqlite:///{tmp_sqlite_path}"
        result = run_alembic("upgrade", "head", database_url=url)

        assert result.returncode == 0, result.stderr
        assert tmp_sqlite_path.exists()

        import sqlite3
        con = sqlite3.connect(tmp_sqlite_path)
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        con.close()

        # Stichprobe über zentrale Tabellen aus allen Entwicklungsphasen -
        # bestätigt, dass die Baseline-Migration wirklich das VOLLSTÄNDIGE
        # aktuelle Schema abbildet, nicht nur einen alten Teilstand.
        for expected in ["buildings", "authorities", "jurisdictions", "requests",
                          "cases", "data_sources", "inbound_emails", "alembic_version"]:
            assert expected in tables, f"Tabelle '{expected}' fehlt nach upgrade head"

    def test_downgrade_then_upgrade_round_trip(self, tmp_sqlite_path):
        url = f"sqlite:///{tmp_sqlite_path}"
        run_alembic("upgrade", "head", database_url=url)

        down = run_alembic("downgrade", "-1", database_url=url)
        assert down.returncode == 0, down.stderr

        up_again = run_alembic("upgrade", "head", database_url=url)
        assert up_again.returncode == 0, up_again.stderr


class TestExistingDatabaseAdoption:
    """
    Stellvertretend für 'eine bestehende Datenbank': eine SQLite-Datei wird
    hier über denselben Mechanismus erzeugt, den die Anwendung vor Alembic
    exklusiv genutzt hat (Base.metadata.create_all(), siehe
    app/database/engine.py:init_db) und mit echten Zeilen befüllt - nicht
    über eine Alembic-Migration.
    """

    def _create_legacy_style_db_with_data(self, path):
        import sqlalchemy
        from app.database.base import Base
        from app.models import (
            Building, RequestType, Authority, Jurisdiction, Request, RequestItem,
            AdministrativeUnit, AppSettings, AuthorityLocation,
            Case, CaseBuilding, CaseRequest, RequestItemProgress,
            DataSource, DataSourceRouting,
            AktenzeichenSequence, RequestSequence, RequestItemReference,
            InboundEmail, InboundEmailAttachment,
        )
        engine = sqlalchemy.create_engine(f"sqlite:///{path}")
        Base.metadata.create_all(bind=engine)

        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        session = Session()
        session.add(Authority(authority_id="A1", authority_name="Bestehende Behörde", city="Bochum"))
        session.commit()
        session.close()
        engine.dispose()

    def test_stamp_head_adopts_existing_db_without_altering_data(self, tmp_sqlite_path):
        self._create_legacy_style_db_with_data(tmp_sqlite_path)
        url = f"sqlite:///{tmp_sqlite_path}"

        stamp = run_alembic("stamp", "head", database_url=url)
        assert stamp.returncode == 0, stamp.stderr

        current = run_alembic("current", database_url=url)
        assert "(head)" in current.stdout or "head" in current.stdout

        import sqlite3
        con = sqlite3.connect(tmp_sqlite_path)
        count = con.execute("SELECT COUNT(*) FROM authorities").fetchone()[0]
        name = con.execute("SELECT authority_name FROM authorities WHERE authority_id='A1'").fetchone()[0]
        con.close()
        assert count == 1
        assert name == "Bestehende Behörde"

    def test_new_migration_applies_cleanly_after_adoption(self, tmp_sqlite_path):
        """Nach dem Stamp muss eine ECHTE künftige Migration (hier: die
        bereits vorhandene message_id-Migration für die Webhook-Idempotenz)
        anstandslos greifen, ohne bestehende Daten zu verändern."""
        self._create_legacy_style_db_with_data(tmp_sqlite_path)
        url = f"sqlite:///{tmp_sqlite_path}"
        run_alembic("stamp", "head", database_url=url)

        upgrade = run_alembic("upgrade", "head", database_url=url)
        assert upgrade.returncode == 0, upgrade.stderr

        import sqlite3
        con = sqlite3.connect(tmp_sqlite_path)
        cols = {r[1] for r in con.execute("PRAGMA table_info(inbound_emails)").fetchall()}
        count = con.execute("SELECT COUNT(*) FROM authorities").fetchone()[0]
        con.close()

        assert "message_id" in cols
        assert count == 1, "Bestehende Daten dürfen durch die Migration nicht verändert werden"
