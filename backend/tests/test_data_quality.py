"""
Regressionstests für das Datenqualitätsmodul (backend/app/api/data_quality.py).

Testet die Erkennungsfunktionen direkt (nicht über HTTP), da sie die
eigentliche fachliche Logik enthalten. Durchgängiges Prinzip laut den
Code-Kommentaren im Modul selbst: "nie raten" - jede Funktion wird explizit
auch auf ihre "needs_review statt automatisch auflösen"-Fälle getestet,
nicht nur auf den einfachen Erfolgsfall.
"""
from datetime import date, datetime, timedelta

from app.api.data_quality import (
    _find_duplicate_authority_groups,
    _fuzzy_duplicate_authority_pairs,
    _buildings_without_coordinates,
    _coverage_gaps,
    _authorities_unverified,
    _jurisdictions_orphaned,
    _find_duplicate_jurisdiction_groups,
    _find_duplicate_building_groups,
    _levenshtein,
)
from tests.conftest import (
    make_request_type, make_authority, make_jurisdiction, make_building,
)


class TestLevenshtein:
    def test_identical_strings(self):
        assert _levenshtein("bauamt", "bauamt") == 0

    def test_one_substitution(self):
        assert _levenshtein("bauamt", "baurmt") == 1

    def test_empty_string(self):
        assert _levenshtein("", "bauamt") == len("bauamt")


class TestExactDuplicateAuthorities:
    def test_unlocated_stub_plus_located_duplicate_is_resolvable(self, db_session):
        stub = make_authority(db_session, name="Bauamt Musterstadt", city=None, street=None)
        full = make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt", street="Rathausplatz")

        resolvable, needs_review = _find_duplicate_authority_groups(db_session)

        assert len(resolvable) == 1
        assert resolvable[0]["keep"].authority_id == stub.authority_id
        assert [a.authority_id for a in resolvable[0]["remove"]] == [full.authority_id]
        assert needs_review == []

    def test_referenced_duplicate_needs_review_not_silently_merged(self, db_session):
        make_request_type(db_session, "BAUAKTEN")
        stub = make_authority(db_session, name="Bauamt Musterstadt", city=None, street=None)
        full = make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt", street="Rathausplatz")
        # 'full' wird bereits von einer Zuständigkeitsregel referenziert ->
        # darf nicht automatisch gelöscht werden.
        make_jurisdiction(db_session, "BAUAKTEN", full.authority_id, ags="05911000")

        resolvable, needs_review = _find_duplicate_authority_groups(db_session)

        assert resolvable == []
        assert len(needs_review) == 1
        assert needs_review[0].authority_id == stub.authority_id

    def test_two_fully_addressed_authorities_same_name_not_touched(self, db_session):
        """Kein 'unlokalisierter Stub' beteiligt -> Funktion rührt es nicht an
        (das ist der Zuständigkeitsbereich der unscharfen Duplikat-Erkennung
        bzw. schlicht zwei tatsächlich verschiedene Dienststellen)."""
        make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt", street="Rathausplatz")
        make_authority(db_session, name="Bauamt Musterstadt", city="Musterstadt", street="Nebenstelle 2")

        resolvable, needs_review = _find_duplicate_authority_groups(db_session)

        assert resolvable == []
        assert needs_review == []


class TestFuzzyDuplicateAuthorities:
    def test_typo_within_same_city_detected(self, db_session):
        a = make_authority(db_session, name="Bauordnungsamt Musterstadt", city="Musterstadt")
        b = make_authority(db_session, name="Bauordnungsamt Mustersadt", city="Musterstadt")  # Tippfehler

        pairs = _fuzzy_duplicate_authority_pairs(db_session)

        ids = {(p["authority_id_a"], p["authority_id_b"]) for p in pairs}
        assert (a.authority_id, b.authority_id) in ids or (b.authority_id, a.authority_id) in ids

    def test_different_cities_not_compared(self, db_session):
        make_authority(db_session, name="Bauordnungsamt Musterstadt", city="Stadt Eins")
        make_authority(db_session, name="Bauordnungsamt Mustersadt", city="Stadt Zwei")

        pairs = _fuzzy_duplicate_authority_pairs(db_session)

        assert pairs == []

    def test_genuinely_different_authorities_not_flagged(self, db_session):
        """'Kreisverwaltung X' vs. 'Stadtverwaltung X' - laut Code-Kommentar
        das Musterbeispiel dafür, warum ein absoluter statt eines
        prozentualen Schwellenwerts verwendet wird."""
        make_authority(db_session, name="Kreisverwaltung Musterkreis", city="Musterstadt")
        make_authority(db_session, name="Stadtverwaltung Musterkreis", city="Musterstadt")

        pairs = _fuzzy_duplicate_authority_pairs(db_session)

        assert pairs == []

    def test_short_names_excluded(self, db_session):
        make_authority(db_session, name="Amt A", city="Musterstadt")
        make_authority(db_session, name="Amt B", city="Musterstadt")

        pairs = _fuzzy_duplicate_authority_pairs(db_session)

        assert pairs == []


class TestBuildingsWithoutCoordinates:
    def test_missing_latitude_flagged(self, db_session):
        b = make_building(db_session, latitude=None, longitude=7.2)
        result = _buildings_without_coordinates(db_session)
        assert b.building_id in [x.building_id for x in result]

    def test_complete_coordinates_not_flagged(self, db_session):
        make_building(db_session, latitude=51.48, longitude=7.22)
        assert _buildings_without_coordinates(db_session) == []


class TestCoverageGaps:
    def test_gap_detected_when_no_rule_exists(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        make_building(db_session, ags="05911000", city="Bochum")

        gaps = _coverage_gaps(db_session)

        assert len(gaps) == 1
        assert gaps[0]["ags"] == "05911000"
        assert gaps[0]["request_type_name"] == "Grundbuch"
        assert gaps[0]["building_count"] == 1

    def test_no_gap_when_rule_exists(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        auth = make_authority(db_session)
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000")
        make_building(db_session, ags="05911000")

        assert _coverage_gaps(db_session) == []

    def test_buildings_without_ags_excluded(self, db_session):
        """Fehlendes AGS ist ein Gebäude-Datenproblem, keine Abdeckungslücke."""
        make_request_type(db_session, "GRUNDBUCH")
        make_building(db_session, ags=None)

        assert _coverage_gaps(db_session) == []

    def test_multiple_buildings_same_gap_grouped_once(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        make_building(db_session, ags="05911000", internal_reference="B1")
        make_building(db_session, ags="05911000", internal_reference="B2")

        gaps = _coverage_gaps(db_session)

        assert len(gaps) == 1
        assert gaps[0]["building_count"] == 2


class TestUnverifiedAuthorities:
    def test_never_verified_flagged(self, db_session):
        a = make_authority(db_session, last_verified_at=None)
        assert a.authority_id in [x.authority_id for x in _authorities_unverified(db_session)]

    def test_verified_over_365_days_ago_flagged(self, db_session):
        a = make_authority(db_session, last_verified_at=datetime.utcnow() - timedelta(days=400))
        assert a.authority_id in [x.authority_id for x in _authorities_unverified(db_session)]

    def test_recently_verified_not_flagged(self, db_session):
        a = make_authority(db_session, last_verified_at=datetime.utcnow() - timedelta(days=10))
        assert a.authority_id not in [x.authority_id for x in _authorities_unverified(db_session)]

    def test_inactive_authority_not_flagged(self, db_session):
        a = make_authority(db_session, last_verified_at=None, active=False)
        assert a.authority_id not in [x.authority_id for x in _authorities_unverified(db_session)]


class TestOrphanedJurisdictions:
    def test_rule_pointing_to_inactive_authority_flagged(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        auth = make_authority(db_session, active=False)
        j = make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000")

        result = _jurisdictions_orphaned(db_session)

        assert j.jurisdiction_id in [x.jurisdiction_id for x in result]

    def test_rule_pointing_to_active_authority_not_flagged(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        auth = make_authority(db_session, active=True)
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000")

        assert _jurisdictions_orphaned(db_session) == []


class TestDuplicateJurisdictions:
    def test_identical_scope_and_metadata_is_resolvable(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        auth = make_authority(db_session)
        j1 = make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000", priority=40)
        j2 = make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000", priority=40)

        resolvable, needs_review = _find_duplicate_jurisdiction_groups(db_session)

        assert len(resolvable) == 1
        kept_and_removed = {resolvable[0]["keep"].jurisdiction_id} | {r.jurisdiction_id for r in resolvable[0]["remove"]}
        assert kept_and_removed == {j1.jurisdiction_id, j2.jurisdiction_id}
        assert needs_review == []

    def test_same_scope_different_priority_needs_review(self, db_session):
        """Gleicher Geltungsbereich, aber unterschiedliche priority - nicht
        eindeutig, welche Zeile korrekt ist -> needs_review, nie raten."""
        make_request_type(db_session, "GRUNDBUCH")
        auth = make_authority(db_session)
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000", priority=40)
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000", priority=10)

        resolvable, needs_review = _find_duplicate_jurisdiction_groups(db_session)

        assert resolvable == []
        assert len(needs_review) == 1


class TestDuplicateBuildings:
    def test_identical_normalized_address_flagged(self, db_session):
        b1 = make_building(db_session, street="Musterstraße", house_number="12",
                            postal_code="44787", city="Bochum")
        b2 = make_building(db_session, street="Musterstraße", house_number="12",
                            postal_code="44787", city="Bochum")

        resolvable, needs_review = _find_duplicate_building_groups(db_session)

        assert len(resolvable) == 1
        ids = {resolvable[0]["keep"].building_id} | {r.building_id for r in resolvable[0]["remove"]}
        assert ids == {b1.building_id, b2.building_id}

    def test_different_address_not_flagged(self, db_session):
        make_building(db_session, street="Musterstraße", house_number="12")
        make_building(db_session, street="Musterstraße", house_number="14")

        resolvable, needs_review = _find_duplicate_building_groups(db_session)

        assert resolvable == []
        assert needs_review == []
