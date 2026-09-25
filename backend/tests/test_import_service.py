"""
Regressionstests für ImportService (Gebäude-, Behörden-, Zuständigkeits-Import).

Der letzte Testfall (TestFillGapsRaceCondition) belegt gezielt den in
Priorität 2 des Auftrags geforderten Fix der im Auditbericht dokumentierten
Race Condition: der fill_gaps-Import darf ein Feld nur füllen, wenn es zum
tatsächlichen Schreibzeitpunkt noch leer ist - nicht nach dem Stand eines
zu Beginn des Imports geladenen Schnappschusses.
"""
import uuid

import pandas as pd
import pytest
from sqlalchemy import bindparam, func, update

from app.models.authority import Authority
from app.services.import_service import ImportService
from tests.conftest import make_authority, make_request_type


def df_from_rows(rows):
    return pd.DataFrame(rows)


class TestImportBuildings:
    def test_valid_row_imported(self, db_session):
        svc = ImportService(db_session)
        df = df_from_rows([{"str": "Musterstraße", "hnr": "12", "ort": "Bochum"}])
        mapping = {"street": "str", "house_number": "hnr", "city": "ort"}

        summary = svc.import_buildings(df, mapping)

        assert summary.imported == 1
        assert summary.needs_review == 0
        assert summary.errors == 0

    def test_missing_required_field_needs_review_not_guessed(self, db_session):
        svc = ImportService(db_session)
        df = df_from_rows([{"str": "Musterstraße", "hnr": "", "ort": "Bochum"}])
        mapping = {"street": "str", "house_number": "hnr", "city": "ort"}

        summary = svc.import_buildings(df, mapping)

        assert summary.needs_review == 1
        assert summary.imported == 0

    def test_duplicate_internal_reference_skipped(self, db_session):
        svc = ImportService(db_session)
        df = df_from_rows([
            {"str": "Musterstraße", "hnr": "12", "ort": "Bochum", "ref": "OBJ-1"},
            {"str": "Andere Straße", "hnr": "3", "ort": "Essen", "ref": "OBJ-1"},
        ])
        mapping = {"street": "str", "house_number": "hnr", "city": "ort", "internal_reference": "ref"}

        summary = svc.import_buildings(df, mapping)

        assert summary.imported == 1
        assert summary.duplicates == 1

    def test_duplicate_check_within_same_file_not_only_against_db(self, db_session):
        """Zwei Zeilen derselben Datei mit identischer Referenz - die zweite
        muss als Duplikat erkannt werden, obwohl die erste zum Zeitpunkt des
        Zeilen-Lesens noch nicht in der DB stand (existing_refs wird beim
        Import live nachgeführt, siehe import_service.py)."""
        svc = ImportService(db_session)
        df = df_from_rows([
            {"str": "A-Straße", "hnr": "1", "ort": "X", "ref": "DUP"},
            {"str": "B-Straße", "hnr": "2", "ort": "Y", "ref": "DUP"},
        ])
        mapping = {"street": "str", "house_number": "hnr", "city": "ort", "internal_reference": "ref"}

        summary = svc.import_buildings(df, mapping)

        assert summary.imported == 1
        assert summary.duplicates == 1


class TestImportAuthorities:
    def test_new_authority_created(self, db_session):
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt Musterstadt", "ort": "Musterstadt"}])
        mapping = {"authority_name": "name", "city": "ort"}

        summary = svc.import_authorities(df, mapping, fill_gaps=False)

        assert summary.imported == 1
        row = db_session.query(Authority).filter_by(authority_name="Bauamt Musterstadt").first()
        assert row is not None and row.city == "Musterstadt"

    def test_exact_duplicate_skipped_without_fill_gaps(self, db_session):
        make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt")
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt Musterstadt", "ort": "Musterstadt", "mail": "neu@example.com"}])
        mapping = {"authority_name": "name", "city": "ort", "email": "mail"}

        summary = svc.import_authorities(df, mapping, fill_gaps=False)

        assert summary.duplicates == 1
        assert summary.imported == 0
        assert summary.updated == 0

    def test_fill_gaps_fills_empty_field(self, db_session):
        make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt", email=None)
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt Musterstadt", "ort": "Musterstadt", "mail": "neu@example.com"}])
        mapping = {"authority_name": "name", "city": "ort", "email": "mail"}

        summary = svc.import_authorities(df, mapping, fill_gaps=True)

        assert summary.updated == 1
        row = db_session.query(Authority).filter_by(authority_name="Bauamt Musterstadt").first()
        assert row.email == "neu@example.com"

    def test_fill_gaps_never_overwrites_existing_value(self, db_session):
        make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt", email="alt@example.com")
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt Musterstadt", "ort": "Musterstadt", "mail": "neu@example.com"}])
        mapping = {"authority_name": "name", "city": "ort", "email": "mail"}

        summary = svc.import_authorities(df, mapping, fill_gaps=True)

        row = db_session.query(Authority).filter_by(authority_name="Bauamt Musterstadt").first()
        assert row.email == "alt@example.com"
        assert summary.updated == 0
        assert summary.duplicates == 1

    def test_fill_gaps_links_unlocated_stub_by_name(self, db_session):
        """Bestehende Behörde ohne Adresse wird von einem fill_gaps-Import,
        der erstmals einen Ort mitbringt, über den Namen gefunden statt
        dupliziert zu werden."""
        stub = make_authority(db_session, name="Bauamt Einzigartig", city=None, street=None)
        svc = ImportService(db_session)
        df = df_from_rows([{
            "name": "Bauamt Einzigartig", "ort": "Musterstadt", "str": "Rathausplatz",
        }])
        mapping = {"authority_name": "name", "city": "ort", "street": "str"}

        summary = svc.import_authorities(df, mapping, fill_gaps=True)

        assert summary.updated == 1
        assert db_session.query(Authority).count() == 1
        db_session.refresh(stub)
        assert stub.city == "Musterstadt"
        assert stub.street == "Rathausplatz"


class TestFillGapsRaceCondition:
    """
    Belegt den Fix in import_service.py (Pass 3/5 von import_authorities):
    Das eigentliche Schreiben eines Lücken-Updates prüft den AKTUELLEN
    Datenbankwert per COALESCE(NULLIF(spalte,''), :neuer_wert) - nicht einen
    zu Beginn des Imports geladenen Python-Schnappschuss. Eine Zeile, die
    zwischen Klassifizierung und Schreiben durch eine andere Quelle (z.B.
    eine parallele manuelle Bearbeitung) bereits gefüllt wurde, bleibt
    deshalb unangetastet, selbst wenn die Klassifizierung sie ursprünglich
    als "leer, wird gefüllt" eingestuft hatte.
    """

    def test_conditional_update_only_fills_still_empty_column(self, db_session):
        auth = make_authority(db_session, name="Bauamt Race", city="Musterstadt", email=None)

        table = Authority.__table__
        stmt = (
            update(table)
            .where(table.c.authority_id == bindparam("target_id"))
            .values(email=func.coalesce(func.nullif(table.c.email, ""), bindparam("email")))
        )
        db_session.execute(stmt, [{"target_id": auth.authority_id, "email": "import@example.com"}])
        db_session.commit()

        db_session.refresh(auth)
        assert auth.email == "import@example.com"

    def test_conditional_update_preserves_value_written_after_snapshot(self, db_session):
        """Simuliert exakt die im Audit beschriebene Race Condition:
        - Pass 2 hätte die Behörde mit leerer E-Mail geladen (email=None).
        - Danach (aber noch bevor Pass 5 schreibt) füllt eine parallele
          manuelle Bearbeitung die E-Mail mit einem ANDEREN, echten Wert.
        - Pass 5 darf diesen manuellen Wert nicht überschreiben, obwohl der
          zu Beginn geladene Schnappschuss noch "leer" zeigte.
        """
        auth = make_authority(db_session, name="Bauamt Race", city="Musterstadt", email=None)

        # ---- Pass 2/3 (Import) liest hier den (noch leeren) Stand ein ----
        snapshot_was_empty = auth.email is None
        assert snapshot_was_empty

        # ---- "Parallele manuelle Bearbeitung", die zwischen Snapshot und
        #      Schreiben passiert - unabhängig vom Import-Prozess ----
        auth.email = "von-hand-recherchiert@example.com"
        db_session.commit()

        # ---- Pass 5 (Import) schreibt jetzt seinen (veralteten) Importwert,
        #      aber konditional auf den AKTUELLEN Spaltenwert ----
        table = Authority.__table__
        stmt = (
            update(table)
            .where(table.c.authority_id == bindparam("target_id"))
            .values(email=func.coalesce(func.nullif(table.c.email, ""), bindparam("email")))
        )
        db_session.execute(stmt, [{"target_id": auth.authority_id, "email": "import-veraltet@example.com"}])
        db_session.commit()

        db_session.refresh(auth)
        assert auth.email == "von-hand-recherchiert@example.com", (
            "Die zwischenzeitliche manuelle Eingabe darf vom Import nicht "
            "überschrieben werden - das war die im Auditbericht dokumentierte "
            "Race Condition."
        )

    def test_end_to_end_fill_gaps_import_is_idempotent_when_rerun(self, db_session):
        """Ergänzender End-to-End-Test: denselben fill_gaps-Import zweimal
        laufen zu lassen darf beim zweiten Mal nichts mehr überschreiben."""
        make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt", email=None)
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt Musterstadt", "ort": "Musterstadt", "mail": "erste-quelle@example.com"}])
        mapping = {"authority_name": "name", "city": "ort", "email": "mail"}

        first = svc.import_authorities(df, mapping, fill_gaps=True)
        assert first.updated == 1

        df2 = df_from_rows([{"name": "Bauamt Musterstadt", "ort": "Musterstadt", "mail": "zweite-quelle@example.com"}])
        second = svc.import_authorities(df2, mapping, fill_gaps=True)

        assert second.updated == 0
        assert second.duplicates == 1
        row = db_session.query(Authority).filter_by(authority_name="Bauamt Musterstadt").first()
        assert row.email == "erste-quelle@example.com"


class TestImportJurisdictions:
    def test_single_ags_imported(self, db_session):
        make_request_type(db_session, "BAUAKTEN")
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt X", "ags_col": "05911000"}])
        mapping = {"authority_name": "name", "ags": "ags_col"}

        summary = svc.import_jurisdictions(df, mapping, "BAUAKTEN")

        assert summary.imported == 1

    def test_multiple_ags_in_one_cell_split(self, db_session):
        make_request_type(db_session, "BAUAKTEN")
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt X", "ags_col": "05911000, 05913000;05916000"}])
        mapping = {"authority_name": "name", "ags": "ags_col"}

        svc.import_jurisdictions(df, mapping, "BAUAKTEN")

        from app.models.jurisdiction import Jurisdiction
        ags_values = {j.ags for j in db_session.query(Jurisdiction).all()}
        assert ags_values == {"05911000", "05913000", "05916000"}

    def test_duplicate_authority_ags_pair_not_reimported(self, db_session):
        make_request_type(db_session, "BAUAKTEN")
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt X", "ags_col": "05911000"}])
        mapping = {"authority_name": "name", "ags": "ags_col"}

        svc.import_jurisdictions(df, mapping, "BAUAKTEN")
        summary2 = svc.import_jurisdictions(df, mapping, "BAUAKTEN")

        assert summary2.duplicates == 1
        assert summary2.imported == 0

    def test_missing_ags_needs_review(self, db_session):
        make_request_type(db_session, "BAUAKTEN")
        svc = ImportService(db_session)
        df = df_from_rows([{"name": "Bauamt X", "ags_col": ""}])
        mapping = {"authority_name": "name", "ags": "ags_col"}

        summary = svc.import_jurisdictions(df, mapping, "BAUAKTEN")

        assert summary.needs_review == 1
