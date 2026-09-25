"""
Regressionstest für die Ergebnis-Caching-Optimierung in _coverage_gaps
(Priorität 2 des Auditberichts: "Prüfe, ob die Verarbeitung größerer
Portfolios Hintergrundjobs oder einen Bulk-Endpunkt benötigt").

Belegt zwei Dinge an synthetischen Daten, nicht nur behauptet:
1. Das Ergebnis ist mit und ohne Cache IDENTISCH (Korrektheit hat Vorrang
   vor der Optimierung).
2. Der Cache reduziert die Anzahl tatsächlicher match_authority()-Aufrufe
   drastisch, wenn - wie im Regelfall - viele Gebäude dieselbe Gemeinde
   und identische Straßen-/Bezirksfelder teilen.

Eine vollständige 2.000-Objekte-Messung mit Wanduhrzeit und SQL-Abfrage-
Zählung läuft separat und manuell über
scripts/benchmark_matching_scale.py (siehe dortige Ausgabe/Kommentare im
Abschlussbericht) - das hier ist die schnelle, CI-taugliche Absicherung,
dass die Cache-Logik selbst korrekt bleibt.
"""
from unittest.mock import patch

from app.api.data_quality import _coverage_gaps
from app.services.jurisdiction_matcher import JurisdictionMatchingService
from tests.conftest import make_authority, make_building, make_jurisdiction, make_request_type


def _seed_many_buildings_sharing_municipalities(db, n_buildings=60, n_municipalities=5):
    for m in range(n_municipalities):
        ags = f"0591100{m}"
        auth = make_authority(db, name=f"Amt {m}")
        # Bewusst nur JEDE ZWEITE Gemeinde bekommt eine Regel -> die andere
        # Hälfte erzeugt eine echte, wiederholt auftretende Abdeckungslücke.
        if m % 2 == 0:
            make_jurisdiction(db, "GRUNDBUCH", auth.authority_id, ags=ags, priority=40)
    for i in range(n_buildings):
        ags = f"0591100{i % n_municipalities}"
        make_building(db, ags=ags, street="Musterstraße", house_number="1", district=None)


class TestCoverageGapsCacheCorrectness:
    def test_cached_result_matches_uncached_ground_truth(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        _seed_many_buildings_sharing_municipalities(db_session, n_buildings=40, n_municipalities=4)

        gaps_with_cache = _coverage_gaps(db_session)

        # Referenz: dieselbe Logik, aber ohne jede Wiederverwendung - jede
        # Gebäude/Auskunftsart-Kombination wird einzeln über die echte
        # Matching-Engine geprüft, keine Cache-Kurzschlüsse.
        from app.models.building import Building
        from app.models.request_type import RequestType
        from app.services.jurisdiction_matcher import MatchingStatus

        matcher = JurisdictionMatchingService(db_session)
        buildings = db_session.query(Building).filter(Building.ags.isnot(None), Building.ags != "").all()
        request_types = db_session.query(RequestType).filter(RequestType.active.is_(True)).all()
        names_by_id = {rt.request_type_id: rt.name for rt in request_types}
        reference: dict = {}
        for b in buildings:
            for rt in request_types:
                result = matcher.match_authority(b, rt.request_type_id)
                if result.matching_status != MatchingStatus.NO_MATCH:
                    continue
                key = (b.ags, rt.request_type_id)
                reference.setdefault(key, set()).add(b.building_id)

        reference_sorted = sorted(
            [
                {"ags": ags, "request_type_name": names_by_id[rt_id], "building_count": len(ids)}
                for (ags, rt_id), ids in reference.items()
            ],
            key=lambda g: (g["ags"], g["request_type_name"]),
        )
        cached_sorted = sorted(
            [
                {"ags": g["ags"], "request_type_name": g["request_type_name"], "building_count": g["building_count"]}
                for g in gaps_with_cache
            ],
            key=lambda g: (g["ags"], g["request_type_name"]),
        )

        assert cached_sorted == reference_sorted

    def test_cache_drastically_reduces_matcher_invocations(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        n_buildings, n_municipalities = 60, 5
        _seed_many_buildings_sharing_municipalities(db_session, n_buildings, n_municipalities)

        real_match = JurisdictionMatchingService.match_authority
        call_count = {"n": 0}

        def counting_match(self, building, request_type_id):
            call_count["n"] += 1
            return real_match(self, building, request_type_id)

        with patch.object(JurisdictionMatchingService, "match_authority", counting_match):
            _coverage_gaps(db_session)

        # Ohne Cache wären es n_buildings x 1 Auskunftsart = 60 Aufrufe.
        # Da alle Gebäude je Gemeinde identische Straße/Hausnummer/Bezirk
        # haben, genügt EIN echter Aufruf je (Gemeinde, Auskunftsart) -
        # hier also höchstens n_municipalities = 5 statt 60.
        assert call_count["n"] <= n_municipalities, (
            f"Erwartet höchstens {n_municipalities} tatsächliche Matching-Aufrufe dank "
            f"Ergebnis-Cache, tatsächlich {call_count['n']} - Cache greift nicht wie vorgesehen."
        )
        assert call_count["n"] < n_buildings
