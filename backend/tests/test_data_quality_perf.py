"""
Tests für die Performance-Maßnahmen der Datenqualitäts-Übersicht
(backend/app/api/data_quality.py, backend/app/services/dq_cache.py):

- gebundene Levenshtein-Distanz ist exakt gleich der vollen Distanz,
- die optimierten Helfer liefern dasselbe wie die unoptimierten Referenzen,
- Aufteilung der Übersicht (light/heavy) und der serverseitige Cache.

Der Cache ist unter pytest standardmäßig inaktiv (siehe dq_cache.effective_ttl);
die Cache-Tests schalten ihn hier ausdrücklich über TTL_OVERRIDE ein.
"""
import random
import threading
import time
from datetime import datetime, timedelta

import pytest

from app.api import data_quality as dq
from app.models.request_item_progress import RequestItemProgress
from app.services import dq_cache
from app.services.jurisdiction_matcher import JurisdictionMatchingService, MatchingStatus
from tests.conftest import (
    make_authority, make_building, make_jurisdiction, make_request, make_request_item,
    make_request_type, make_user,
)

HEAVY_KEYS = ("coverage_gaps", "fuzzy_duplicate_authorities")


@pytest.fixture()
def cache_on(monkeypatch):
    """Schaltet den (unter pytest sonst inaktiven) Cache ein und leert ihn davor/danach."""
    monkeypatch.setattr(dq_cache, "TTL_OVERRIDE", 60.0)
    dq_cache.clear_data_quality_cache()
    yield
    dq_cache.clear_data_quality_cache()


def _seed_bad_geocoding(db):
    """Behörde ganz ohne Adresse mit gecachtem Kartenpin (-> clear-bad-geocoding hat etwas zu tun)."""
    from app.models.authority_location import AuthorityLocation

    authority = make_authority(db, name="Amt ohne Adresse", city=None, street=None)
    db.add(AuthorityLocation(authority_id=authority.authority_id, latitude=51.0, longitude=10.0))
    db.commit()


def _login_as_main(app_client, db_session):
    make_user(db_session, email="main@example.com", password="geheim123", is_main=True)
    app_client.post("/api/auth/login", json={"email": "main@example.com", "password": "geheim123"})


# ---------------------------------------------------------------------------
# Levenshtein mit Abbruchgrenze
# ---------------------------------------------------------------------------

class TestBoundedLevenshtein:
    @pytest.mark.parametrize("max_distance", [1, 2, 3])
    def test_matches_full_levenshtein_on_random_strings(self, max_distance):
        rng = random.Random(1234)
        alphabet = "abcde "
        for _ in range(3000):
            base = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 14)))
            other = list(base)
            for _ in range(rng.randint(0, 4)):  # 0-4 zufällige Änderungen
                op = rng.choice(["sub", "ins", "del"])
                pos = rng.randint(0, max(len(other) - 1, 0))
                if op == "ins":
                    other.insert(pos, rng.choice(alphabet))
                elif op == "del" and other:
                    other.pop(pos)
                elif other:
                    other[pos] = rng.choice(alphabet)
            other = "".join(other)
            full = dq._levenshtein(base, other)
            bounded = dq._levenshtein_within(base, other, max_distance)
            assert bounded == min(full, max_distance + 1), (base, other, full, bounded)

    def test_completely_different_strings_exceed_limit(self):
        assert dq._levenshtein_within("bauamt koeln", "ordnungsamt", 2) == 3


# ---------------------------------------------------------------------------
# Fuzzy-Duplikate: gleiches Ergebnis wie die ursprüngliche Implementierung
# ---------------------------------------------------------------------------

def _reference_fuzzy_pairs(db):
    """Die ursprüngliche (langsame) Implementierung als Referenz."""
    from app.models.authority import Authority

    active = db.query(Authority).filter(Authority.active.is_(True)).all()
    already_flagged = dq._duplicate_authority_ids(db)
    by_city: dict = {}
    for a in active:
        normalized = dq._normalize_for_similarity(a.authority_name)
        if len(normalized) < dq._FUZZY_MIN_NAME_LENGTH:
            continue
        by_city.setdefault((a.city or "").strip().lower(), []).append((a, normalized))
    pairs = []
    for group in by_city.values():
        for i in range(len(group)):
            a, name_a = group[i]
            for j in range(i + 1, len(group)):
                b, name_b = group[j]
                if a.authority_id in already_flagged and b.authority_id in already_flagged:
                    continue
                if name_a == name_b:
                    continue
                if abs(len(name_a) - len(name_b)) > dq._FUZZY_MAX_EDIT_DISTANCE:
                    continue
                if dq._levenshtein(name_a, name_b) <= dq._FUZZY_MAX_EDIT_DISTANCE:
                    pairs.append({
                        "authority_id_a": a.authority_id, "authority_name_a": a.authority_name,
                        "authority_id_b": b.authority_id, "authority_name_b": b.authority_name,
                        "city": a.city,
                        "similarity": round(dq._name_similarity(name_a, name_b), 2),
                    })
    return sorted(pairs, key=lambda p: -p["similarity"])


class TestFuzzyDuplicatesUnchanged:
    def test_same_pairs_values_and_order_as_reference(self, db_session):
        rng = random.Random(7)
        stems = ["Bauamt", "Ordnungsamt", "Grundbuchamt", "Vermessungsamt", "Stadtverwaltung"]
        for city in ["Bochum", "Köln", "Essen"]:
            for stem in stems:
                name = f"{stem} {city}"
                make_authority(db_session, name=name, city=city, street="Rathausplatz 1")
                if rng.random() < 0.8:  # Tippfehler-/Umlaut-/Whitespace-Varianten
                    variant = rng.choice([
                        name.replace("a", "e", 1), name + "x", name[:-1], name.replace(" ", "  "),
                        name.replace("ö", "oe"), name.replace("amt", "ant"),
                    ])
                    make_authority(db_session, name=variant, city=city, street="Marktplatz 2")
        # unlokalisierter Stub + lokalisierte Variante (exakte Duplikat-Gruppe, soll
        # nicht doppelt als "ähnlich" auftauchen)
        make_authority(db_session, name="Amt für Wohnen Dortmund", city=None, street=None)
        make_authority(db_session, name="Amt für Wohnen Dortmund", city="Dortmund", street="Weg 1")

        expected = _reference_fuzzy_pairs(db_session)
        assert expected, "Testdaten müssen mindestens ein ähnliches Paar enthalten"
        assert dq._fuzzy_duplicate_authority_pairs(db_session) == expected


# ---------------------------------------------------------------------------
# slim-Varianten liefern dieselben Datensätze (Reihenfolge, IDs) wie die vollen
# ---------------------------------------------------------------------------

def _ids(rows, attr):
    return [getattr(r, attr) for r in rows]


class TestSlimVariantsEquivalent:
    def _seed(self, db):
        make_request_type(db, "GRUNDBUCH")
        a_ok = make_authority(db, name="Amt A", city="Bochum", street="Weg 1", email="a@x.de",
                              last_verified_at=datetime.utcnow())
        make_authority(db, name="Amt B", city="Bochum", street="Weg 2", email="")
        make_authority(db, name="Amt C", city=None, street=None, email=None)
        make_authority(db, name="Amt C", city="Essen", street="Straße 5")
        stale = make_authority(db, name="Amt D", city="Essen", street="Weg 3", email="d@x.de",
                               last_verified_at=datetime.utcnow() - timedelta(days=400))
        inactive = make_authority(db, name="Alt", city="Essen", street="Weg 9", active=False)
        make_jurisdiction(db, "GRUNDBUCH", a_ok.authority_id, ags="05911000", priority=40)
        make_jurisdiction(db, "GRUNDBUCH", stale.authority_id, ags="05911000", priority=40)
        # verwaiste Regel (Behörde deaktiviert)
        make_jurisdiction(db, "GRUNDBUCH", inactive.authority_id, ags="05913000", priority=40)
        # Zuständigkeits-Duplikate: identisch (auflösbar) und abweichend (needs_review)
        for _ in range(2):
            make_jurisdiction(db, "GRUNDBUCH", a_ok.authority_id, ags="05915000", priority=40,
                              municipality=" Witten ")
        make_jurisdiction(db, "GRUNDBUCH", stale.authority_id, ags="05916000", priority=40)
        make_jurisdiction(db, "GRUNDBUCH", stale.authority_id, ags="05916000", priority=50)

    def test_authority_helpers(self, db_session):
        self._seed(db_session)
        for helper in (dq._authorities_without_email, dq._authorities_without_address, dq._authorities_unverified):
            assert _ids(helper(db_session, slim=True), "authority_id") == _ids(helper(db_session), "authority_id")
        assert (
            _ids(dq._authorities_without_jurisdiction(db_session, slim=True), "authority_id")
            == _ids(dq._authorities_without_jurisdiction(db_session), "authority_id")
        )
        full_res, full_review = dq._find_duplicate_authority_groups(db_session)
        slim_res, slim_review = dq._find_duplicate_authority_groups(db_session, slim=True)
        assert [(g["keep"].authority_id, [a.authority_id for a in g["remove"]]) for g in full_res] == [
            (g["keep"].authority_id, [a.authority_id for a in g["remove"]]) for g in slim_res
        ]
        assert _ids(full_review, "authority_id") == _ids(slim_review, "authority_id")

    def test_jurisdiction_helpers(self, db_session):
        self._seed(db_session)
        assert (
            _ids(dq._jurisdictions_orphaned(db_session, slim=True), "jurisdiction_id")
            == _ids(dq._jurisdictions_orphaned(db_session), "jurisdiction_id")
        )
        assert len(dq._jurisdictions_orphaned(db_session)) == 1

        full_res, full_review = dq._find_duplicate_jurisdiction_groups(db_session)
        slim_res, slim_review = dq._find_duplicate_jurisdiction_groups(db_session, slim=True)
        assert len(full_res) == 1 and len(full_review) == 1  # Testdaten decken beide Fälle ab
        assert [(g["keep"].jurisdiction_id, [j.jurisdiction_id for j in g["remove"]]) for g in full_res] == [
            (g["keep"].jurisdiction_id, [j.jurisdiction_id for j in g["remove"]]) for g in slim_res
        ]
        assert _ids(full_review, "jurisdiction_id") == _ids(slim_review, "jurisdiction_id")
        assert dq._duplicate_jurisdiction_ids(db_session) == {
            *[g["keep"].jurisdiction_id for g in full_res],
            *[j.jurisdiction_id for g in full_res for j in g["remove"]],
            *_ids(full_review, "jurisdiction_id"),
        }

    def test_serialize_jurisdictions_accepts_row_objects(self, db_session):
        self._seed(db_session)
        full = dq._serialize_jurisdictions(dq._jurisdictions_orphaned(db_session), db_session, 10)
        slim = dq._serialize_jurisdictions(dq._jurisdictions_orphaned(db_session, slim=True), db_session, 10)
        assert full == slim and full[0]["authority_name"] == "Alt"


# ---------------------------------------------------------------------------
# _buildings_with_real_progress (gebündelt statt je Gebäude)
# ---------------------------------------------------------------------------

class TestBuildingsWithRealProgress:
    def test_batch_matches_single_variant_and_ignores_unsent(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        sent = make_building(db_session, street="A")
        answered = make_building(db_session, street="B")
        untouched = make_building(db_session, street="C")
        no_request = make_building(db_session, street="D")

        for building, field in ((sent, "sent_at"), (answered, "response_received_at"), (untouched, None)):
            req = make_request(db_session, building.building_id)
            item = make_request_item(db_session, req.request_id, "GRUNDBUCH")
            progress = RequestItemProgress(request_item_id=item.request_item_id)
            if field:
                setattr(progress, field, datetime.utcnow())
            db_session.add(progress)
            db_session.commit()

        ids = [sent.building_id, answered.building_id, untouched.building_id, no_request.building_id]
        assert dq._buildings_with_real_progress(db_session, ids) == {sent.building_id, answered.building_id}
        for bid in ids:
            assert dq._building_has_real_progress(db_session, bid) == (bid in {sent.building_id, answered.building_id})
        assert dq._buildings_with_real_progress(db_session, []) == set()


# ---------------------------------------------------------------------------
# _coverage_gaps: gleiches Ergebnis wie Matching je Gebäude/Auskunftsart
# ---------------------------------------------------------------------------

def _reference_coverage_gaps(db):
    from app.models.building import Building
    from app.models.request_type import RequestType

    matcher = JurisdictionMatchingService(db)
    buildings = db.query(Building).filter(Building.ags.isnot(None), Building.ags != "").all()
    request_types = db.query(RequestType).filter(RequestType.active.is_(True)).all()
    gaps: dict = {}
    for b in buildings:
        for rt in request_types:
            if matcher.match_authority(b, rt.request_type_id).matching_status != MatchingStatus.NO_MATCH:
                continue
            entry = gaps.setdefault(
                (b.ags, rt.request_type_id),
                {"ags": b.ags, "municipality": b.city, "request_type_name": rt.name, "building_ids": set()},
            )
            entry["building_ids"].add(b.building_id)
    return sorted(
        (
            {"ags": g["ags"], "municipality": g["municipality"], "request_type_name": g["request_type_name"],
             "building_count": len(g["building_ids"])}
            for g in gaps.values()
        ),
        key=lambda g: (g["municipality"] or "", g["request_type_name"]),
    )


class TestCoverageGapsUnchanged:
    def test_street_specific_rules_state_postal_and_empty_types(self, db_session):
        make_request_type(db_session, "GRUNDBUCH", name="Grundbuch")
        make_request_type(db_session, "BAULAST", name="Baulast")
        make_request_type(db_session, "LEER", name="Ohne Regeln")  # keine einzige Regel
        amt = make_authority(db_session, name="Amt")

        # AGS 1: nur eine Straßen-Sonderregel -> andere Straßen in derselben AGS sind eine Lücke.
        make_jurisdiction(db_session, "GRUNDBUCH", amt.authority_id, ags="05911000",
                          street="Sonderstraße", priority=20)
        # AGS 2: Gemeinde-Regel für beide Typen.
        make_jurisdiction(db_session, "GRUNDBUCH", amt.authority_id, ags="05913000", priority=40)
        make_jurisdiction(db_session, "BAULAST", amt.authority_id, ags="05913000", priority=40)
        # Landesweite Regel (ohne AGS) nur für BAULAST in "Nordrhein-Westfalen".
        make_jurisdiction(db_session, "BAULAST", amt.authority_id, state="Nordrhein-Westfalen", priority=60)
        # PLZ-Fallback für GRUNDBUCH.
        make_jurisdiction(db_session, "GRUNDBUCH", amt.authority_id, postal_code="58000", priority=70)

        make_building(db_session, ags="05911000", street="Sonderstraße", house_number="1", city="Alt")
        make_building(db_session, ags="05911000", street="Andere Straße", house_number="2", city="Alt")
        make_building(db_session, ags="05911000", street="Dritte Straße", house_number="3", city="Alt",
                      state="Nordrhein-Westfalen")
        make_building(db_session, ags="05913000", street="X", house_number="1", city="Neu")
        make_building(db_session, ags="05913000", street="Y", house_number="2", city="Neu", postal_code="58000")
        make_building(db_session, ags="05915000", street="Z", house_number="3", city="Ohne",
                      postal_code="58000", state="Nordrhein-Westfalen")
        make_building(db_session, ags="05915000", street="Z", house_number="4", city="Ohne", postal_code="99999")

        expected = _reference_coverage_gaps(db_session)
        assert expected  # es gibt echte Lücken
        assert any(g["request_type_name"] == "Ohne Regeln" for g in expected)
        assert dq._coverage_gaps(db_session) == expected

    def test_matching_runs_once_per_ags_when_no_street_rules(self, db_session):
        make_request_type(db_session, "GRUNDBUCH")
        amt = make_authority(db_session, name="Amt")
        make_jurisdiction(db_session, "GRUNDBUCH", amt.authority_id, ags="05911000", priority=40)
        for i in range(12):  # alle in derselben Gemeinde, jeweils andere Straße
            make_building(db_session, ags="05911000", street=f"Straße {i}", house_number=str(i))

        real = JurisdictionMatchingService.match_authority
        calls = {"n": 0}

        def counting(self, building, request_type_id):
            calls["n"] += 1
            return real(self, building, request_type_id)

        original = JurisdictionMatchingService.match_authority
        JurisdictionMatchingService.match_authority = counting
        try:
            assert dq._coverage_gaps(db_session) == []
        finally:
            JurisdictionMatchingService.match_authority = original
        assert calls["n"] == 1


# ---------------------------------------------------------------------------
# Endpunkt-Vertrag: light / heavy / refresh
# ---------------------------------------------------------------------------

class TestSummaryEndpoints:
    def _seed(self, db):
        make_request_type(db, "GRUNDBUCH")
        make_authority(db, name="Bauamt Musterstadt", city="Musterstadt", street="Platz 1")
        make_authority(db, name="Bauamt Musterstadt", city="Musterstadt", street="Platz 2")
        make_authority(db, name="Bauamt Musterstedt", city="Musterstadt", street="Platz 3")
        make_building(db, ags="05911000")  # keine Regel -> Abdeckungslücke

    def test_default_has_everything_without_heavy_pending(self, app_client, db_session):
        self._seed(db_session)
        _login_as_main(app_client, db_session)
        body = app_client.get("/api/data-quality/summary").json()
        assert "heavy_pending" not in body
        assert body["coverage_gaps"]["count"] == 1
        assert body["fuzzy_duplicate_authorities"]["count"] >= 1
        assert list(body)[-2:] == list(HEAVY_KEYS)

    def test_light_returns_placeholders_and_flag(self, app_client, db_session):
        self._seed(db_session)
        _login_as_main(app_client, db_session)
        full = app_client.get("/api/data-quality/summary").json()
        light = app_client.get("/api/data-quality/summary?light=true").json()
        assert light["heavy_pending"] is True
        for key in HEAVY_KEYS:
            assert light[key] == {"count": 0, "items": []}
        assert list(light) == list(full) + ["heavy_pending"]
        for key in full:
            if key not in HEAVY_KEYS:
                assert light[key] == full[key]

    def test_heavy_matches_full_summary_groups(self, app_client, db_session):
        self._seed(db_session)
        _login_as_main(app_client, db_session)
        full = app_client.get("/api/data-quality/summary").json()
        heavy = app_client.get("/api/data-quality/heavy").json()
        assert list(heavy) == list(HEAVY_KEYS)
        for key in HEAVY_KEYS:
            assert heavy[key] == full[key]

    def test_refresh_param_accepted(self, app_client, db_session):
        self._seed(db_session)
        _login_as_main(app_client, db_session)
        assert app_client.get("/api/data-quality/summary?light=true&refresh=true").status_code == 200
        assert app_client.get("/api/data-quality/heavy?refresh=true").status_code == 200

    def test_export_xlsx_still_works(self, app_client, db_session):
        self._seed(db_session)
        _login_as_main(app_client, db_session)
        res = app_client.get("/api/data-quality/export-xlsx")
        assert res.status_code == 200 and res.content[:2] == b"PK"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

class TestCacheInactiveUnderPytest:
    def test_default_is_off_under_pytest(self):
        assert dq_cache.TTL_OVERRIDE is None
        assert dq_cache.effective_ttl() == 0.0
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 2

    def test_env_var_is_honoured_outside_pytest(self, monkeypatch):
        monkeypatch.setattr(dq_cache, "_running_under_pytest", lambda: False)
        monkeypatch.delenv(dq_cache.TTL_ENV_VAR, raising=False)
        assert dq_cache.effective_ttl() == dq_cache.DEFAULT_TTL_SECONDS
        monkeypatch.setenv(dq_cache.TTL_ENV_VAR, "12")
        assert dq_cache.effective_ttl() == 12.0
        monkeypatch.setenv(dq_cache.TTL_ENV_VAR, "0")
        assert dq_cache.effective_ttl() == 0.0
        monkeypatch.setenv(dq_cache.TTL_ENV_VAR, "kaputt")
        assert dq_cache.effective_ttl() == dq_cache.DEFAULT_TTL_SECONDS


class TestCacheBehaviour:
    def test_hit_refresh_and_ttl_expiry(self, cache_on, monkeypatch):
        calls = []

        def compute():
            calls.append(1)
            return {"n": len(calls)}

        assert dq_cache.get_or_compute("k", compute) == {"n": 1}
        assert dq_cache.get_or_compute("k", compute) == {"n": 1}  # Treffer
        assert dq_cache.get_or_compute("k", compute, refresh=True) == {"n": 2}  # umgangen + neu abgelegt
        assert dq_cache.get_or_compute("k", compute) == {"n": 2}

        monkeypatch.setattr(dq_cache, "TTL_OVERRIDE", 0.05)
        time.sleep(0.1)
        assert dq_cache.get_or_compute("k", compute) == {"n": 3}  # abgelaufen

    def test_clear_forces_recompute(self, cache_on):
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        dq_cache.clear_data_quality_cache()
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 2

    def test_concurrent_cold_requests_compute_once(self, cache_on):
        calls = []
        start = threading.Barrier(6)

        def slow():
            calls.append(1)
            time.sleep(0.3)
            return "ergebnis"

        results = []

        def worker():
            start.wait()
            results.append(dq_cache.get_or_compute("herd", slow))

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert results == ["ergebnis"] * 6
        assert len(calls) == 1

    def test_result_computed_during_invalidation_is_not_stored(self, cache_on):
        calls = []

        def compute():
            calls.append(1)
            dq_cache.clear_data_quality_cache()  # Schreibzugriff mitten in der Berechnung
            return len(calls)

        assert dq_cache.get_or_compute("k", compute) == 1
        assert dq_cache.get_or_compute("k", compute) == 2  # nicht aus dem Cache

    def test_commit_of_master_data_invalidates_automatically(self, cache_on, db_session):
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        make_authority(db_session, name="Neu")  # commit -> Cache geleert
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 2

    def test_commit_of_unrelated_data_keeps_cache(self, cache_on, db_session):
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        make_user(db_session, email="x@example.com")  # User ist für die Übersicht irrelevant
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 1

    def test_rollback_does_not_invalidate(self, cache_on, db_session):
        from app.models.authority import Authority
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        db_session.add(Authority(authority_id="rb", authority_name="Rollback", active=True))
        db_session.flush()
        db_session.rollback()
        db_session.commit()
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 1

    def test_bulk_delete_invalidates(self, cache_on, db_session):
        from app.models.authority import Authority
        make_authority(db_session, name="Weg")
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        db_session.query(Authority).delete(synchronize_session=False)
        db_session.commit()
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 2


class TestSummaryCacheIntegration:
    def test_summary_is_cached_and_mutating_endpoint_clears_it(self, cache_on, app_client, db_session, monkeypatch):
        make_authority(db_session, name="Amt ohne Mail", city="Bochum", street="Weg 1")
        _seed_bad_geocoding(db_session)
        _login_as_main(app_client, db_session)

        counter = {"light": 0, "heavy": 0}
        real_light, real_heavy = dq._compute_light_summary, dq._compute_heavy_summary

        def light(db):
            counter["light"] += 1
            return real_light(db)

        def heavy(db):
            counter["heavy"] += 1
            return real_heavy(db)

        monkeypatch.setattr(dq, "_compute_light_summary", light)
        monkeypatch.setattr(dq, "_compute_heavy_summary", heavy)
        dq_cache.clear_data_quality_cache()

        first = app_client.get("/api/data-quality/summary?light=true").json()
        app_client.get("/api/data-quality/summary?light=true")
        assert counter == {"light": 1, "heavy": 0}  # light rechnet heavy nie

        app_client.get("/api/data-quality/heavy")
        app_client.get("/api/data-quality/heavy")
        app_client.get("/api/data-quality/summary")  # light aus Cache, heavy aus Cache
        assert counter == {"light": 1, "heavy": 1}

        app_client.get("/api/data-quality/summary?light=true&refresh=true")
        assert counter["light"] == 2

        # schreibender Endpunkt leert beide Einträge
        assert app_client.post("/api/data-quality/clear-bad-geocoding").status_code == 200
        second = app_client.get("/api/data-quality/summary?light=true").json()
        assert counter["light"] == 3
        assert second == first
        app_client.get("/api/data-quality/heavy")
        assert counter["heavy"] == 2

    @pytest.mark.parametrize("path", [
        "merge-duplicate-authorities", "merge-duplicate-jurisdictions", "merge-duplicate-buildings",
        "delete-review-required-buildings", "clear-bad-geocoding",
    ])
    def test_every_mutating_endpoint_invalidates(self, cache_on, app_client, db_session, path):
        _seed_bad_geocoding(db_session)
        _login_as_main(app_client, db_session)
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert app_client.post(f"/api/data-quality/{path}").status_code == 200
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 2

    def test_geocode_endpoint_invalidates(self, cache_on, app_client, db_session, monkeypatch):
        _login_as_main(app_client, db_session)
        monkeypatch.setattr(dq, "_geocode_and_cache_building", lambda building: False)
        calls = []
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert app_client.post("/api/data-quality/geocode-missing-buildings").status_code == 200
        dq_cache.get_or_compute("k", lambda: calls.append(1) or len(calls))
        assert len(calls) == 2
