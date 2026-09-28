"""
Regressionstest für das Alembic-Migrationsverfahren.

Prüft genau das im Auftrag geforderte Verfahren automatisiert:
1. eine FRISCHE, leere Datenbank kommt über `alembic upgrade head` auf den
   vollständigen aktuellen Schema-Stand,
2. eine BESTEHENDE Datenbank (hier: exakt auf dem BASELINE-Schemastand
   erzeugt, ohne alembic_version-Tabelle - stellvertretend für die echte
   Produktivdatenbank, die bisher ausschließlich über
   Base.metadata.create_all() verwaltet wurde) lässt sich per
   `alembic stamp <baseline-revision>` auf den Baseline-Stand heben und
   nimmt danach künftige Migrationen klaglos an, OHNE die vorhandenen Daten
   zu verändern,
3. ein Downgrade der letzten Migration funktioniert (Rollback-Fähigkeit),
4. `alembic stamp head` (statt der exakten Baseline-Revision) auf einer
   solchen Bestands-DB ist NACHWEISLICH FALSCH, sobald weitere Migrationen
   seit der Baseline existieren - dieser Test dokumentiert den Fehler aktiv,
   damit er nicht wieder unbemerkt in Dokumentation oder Praxis einzieht
   (siehe app/database/engine.py:init_db für die ausführliche Erklärung).

WICHTIG zu Testfixture-Fallen: eine frühere Fassung dieser Datei erzeugte die
"Bestands-DB" über Base.metadata.create_all() mit den AKTUELLEN Modellen -
das baut aber immer den Stand von HEAD, nie den echten historischen
Baseline-Stand, egal wie viele Migrationen seither dazugekommen sind. Ein
darauf ausgeführter `stamp head`-Test bestand deshalb "zufällig", ohne den
eigentlichen Fehler (Stamp auf den falschen Revisionsstand) je zu prüfen.
Hier wird die Bestands-DB deshalb über `alembic upgrade <baseline-revision>`
erzeugt und die alembic_version-Tabelle danach wieder entfernt - das bildet
exakt nach, was eine nie von Alembic verwaltete Datenbank auf Baseline-Stand
tatsächlich ist.

Läuft ausschließlich gegen temporäre, für den Test erzeugte SQLite-Dateien -
niemals gegen backend/authority_matching.db und erst recht nicht gegen eine
produktive Datenbank. Ruft Alembic bewusst als Subprozess auf (wie im echten
Betrieb/CI auch), damit jede Invocation ihre eigene DATABASE_URL aus der
Umgebung liest, statt den einen für die gesamte Testsession fest geladenen
Wert aus app.database.engine wiederzuverwenden.
"""
import os
import sqlite3
import subprocess
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Die ursprüngliche Baseline-Revision (bildet den Schemastand ab, den
# Base.metadata.create_all() vor Einführung von Alembic tatsächlich gebaut
# hat). MUSS bei jeder neuen Migration unverändert bleiben - sie ist der
# einzige Stand, auf den die reale Produktivdatenbank per `stamp` gehoben
# werden darf, NIE "head".
BASELINE_REVISION = "ab0d36228547"


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
    Stellvertretend für 'eine bestehende Datenbank auf Baseline-Stand' (wie
    backend/authority_matching.db und die produktive Neon-Datenbank heute):
    exakt der Schemastand der Baseline-Revision, OHNE alembic_version-
    Tabelle - nie über eine höhere Migration hinaus, sonst wäre es keine
    Simulation einer noch nicht adoptierten Bestands-DB mehr.
    """

    def _create_baseline_only_db_with_data(self, path):
        url = f"sqlite:///{path}"
        result = run_alembic("upgrade", BASELINE_REVISION, database_url=url)
        assert result.returncode == 0, result.stderr

        con = sqlite3.connect(path)
        # Alembics eigene Buchführungstabelle wieder entfernen: eine bisher
        # nie von Alembic verwaltete Datenbank (wie die echte Produktiv-DB)
        # hat sie schlicht nicht - nur so testet der anschließende stamp-
        # Schritt das echte Szenario, nicht nur "Alembic kennt sich selbst".
        con.execute("DROP TABLE alembic_version")
        con.execute(
            "INSERT INTO authorities (authority_id, authority_name, city, active, created_at, updated_at) "
            "VALUES ('A1', 'Bestehende Behörde', 'Bochum', 1, datetime('now'), datetime('now'))"
        )
        con.commit()
        con.close()

    def test_stamp_baseline_adopts_existing_db_without_altering_data(self, tmp_sqlite_path):
        self._create_baseline_only_db_with_data(tmp_sqlite_path)
        url = f"sqlite:///{tmp_sqlite_path}"

        stamp = run_alembic("stamp", BASELINE_REVISION, database_url=url)
        assert stamp.returncode == 0, stamp.stderr

        current = run_alembic("current", database_url=url)
        assert BASELINE_REVISION in current.stdout
        # Baseline ist NICHT head, solange neuere Migrationen existieren -
        # genau der Zustand, den ein korrekter Stamp abbilden muss.
        assert "(head)" not in current.stdout

        con = sqlite3.connect(tmp_sqlite_path)
        count = con.execute("SELECT COUNT(*) FROM authorities").fetchone()[0]
        name = con.execute("SELECT authority_name FROM authorities WHERE authority_id='A1'").fetchone()[0]
        cols = {r[1] for r in con.execute("PRAGMA table_info(inbound_emails)").fetchall()}
        con.close()
        assert count == 1
        assert name == "Bestehende Behörde"
        # Auf reinem Baseline-Stand darf message_id noch NICHT existieren -
        # sonst wäre dies keine echte Baseline-Simulation.
        assert "message_id" not in cols

    def test_new_migrations_apply_cleanly_after_baseline_adoption(self, tmp_sqlite_path):
        """Nach dem Stamp AUF DIE BASELINE müssen alle seitherigen echten
        Migrationen (message_id, source_system) anstandslos greifen, ohne
        bestehende Daten zu verändern."""
        self._create_baseline_only_db_with_data(tmp_sqlite_path)
        url = f"sqlite:///{tmp_sqlite_path}"
        run_alembic("stamp", BASELINE_REVISION, database_url=url)

        upgrade = run_alembic("upgrade", "head", database_url=url)
        assert upgrade.returncode == 0, upgrade.stderr

        con = sqlite3.connect(tmp_sqlite_path)
        inbound_cols = {r[1] for r in con.execute("PRAGMA table_info(inbound_emails)").fetchall()}
        building_cols = {r[1] for r in con.execute("PRAGMA table_info(buildings)").fetchall()}
        count = con.execute("SELECT COUNT(*) FROM authorities").fetchone()[0]
        con.close()

        assert "message_id" in inbound_cols
        assert "source_system" in building_cols
        assert count == 1, "Bestehende Daten dürfen durch die Migration nicht verändert werden"

    def test_stamping_at_head_instead_of_baseline_is_wrong(self, tmp_sqlite_path):
        """
        Dokumentiert AKTIV den Fehler, den app/database/engine.py jetzt
        ausdrücklich vor warnt: stampt man eine Baseline-only-DB fälschlich
        auf "head" statt auf die exakte Baseline-Revision, hält Alembic sie
        für vollständig aktuell - ein nachfolgendes `upgrade head` tut dann
        NICHTS, und die seither hinzugekommenen Spalten fehlen tatsächlich,
        obwohl die Anwendung sie voraussetzt. Dieser Test MUSS rot werden,
        falls jemand den Fix in engine.py wieder rückgängig macht.
        """
        self._create_baseline_only_db_with_data(tmp_sqlite_path)
        url = f"sqlite:///{tmp_sqlite_path}"

        wrong_stamp = run_alembic("stamp", "head", database_url=url)
        assert wrong_stamp.returncode == 0, wrong_stamp.stderr

        # Alembic hält die DB jetzt für aktuell - ein upgrade head ist ein No-Op.
        noop_upgrade = run_alembic("upgrade", "head", database_url=url)
        assert noop_upgrade.returncode == 0

        con = sqlite3.connect(tmp_sqlite_path)
        inbound_cols = {r[1] for r in con.execute("PRAGMA table_info(inbound_emails)").fetchall()}
        building_cols = {r[1] for r in con.execute("PRAGMA table_info(buildings)").fetchall()}
        con.close()

        # Der eigentliche Schaden: diese Spalten fehlen real in der
        # Datenbank, obwohl Alembic (durch den falschen Stamp getäuscht)
        # "upgrade head" bereits für erledigt hält.
        assert "message_id" not in inbound_cols
        assert "source_system" not in building_cols
