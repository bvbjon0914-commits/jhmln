"""
Tests für die Kreisebenen-Scope-Korrektur (app/services/kreis_scope_fix.py).

Bildet den real gefundenen Fehlerpattern mit synthetischen Daten nach: eine
Kreisverwaltungs-Regel ist auf eine einzelne, willkürliche Gemeinde-AGS
gepinnt, obwohl die Behörde für den ganzen Kreis zuständig ist. Prüft
sowohl, dass der Bug korrekt erkannt/behoben wird, als auch, dass
legitim eng gefasste Regeln (Stadtverwaltung, Verbandsgemeinde) NICHT
angefasst werden.
"""
from app.models.jurisdiction import Jurisdiction
from app.services.jurisdiction_matcher import JurisdictionMatchingService, MatchingLevel, MatchingStatus
from app.services.kreis_scope_fix import apply_kreis_scope_fix, find_kreis_scope_bugs

from tests.conftest import make_administrative_unit, make_authority, make_building, make_jurisdiction, make_request_type

STATE_PREFIXES = {"09": "Testland"}


def _make_kreis(db, ags_kreis, n_gemeinden=30):
    for i in range(1, n_gemeinden + 1):
        make_administrative_unit(
            db, ags=f"{ags_kreis}{i:03d}", state_name="Testland",
            county_name="Testkreis", municipality_name=f"Gemeinde{i}",
        )


def test_detects_and_fixes_kreis_pinned_to_single_municipality(db_session):
    rt = make_request_type(db_session, code="BAUAKTEN")
    _make_kreis(db_session, "09111", n_gemeinden=30)

    kreisverwaltung = make_authority(db_session, name="Kreisverwaltung Testkreis - Untere Bauaufsichtsbehörde")
    # Bug: Regel ist auf EINE Gemeinde gepinnt, meint aber den ganzen Kreis.
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=kreisverwaltung.authority_id,
        ags="09111003", municipality="Testkreis", matching_level="MUNICIPALITY",
    )

    findings = find_kreis_scope_bugs(db_session, ["BAUAKTEN"], STATE_PREFIXES)
    assert len(findings) == 1
    assert findings[0].ags_kreis == "09111"
    assert findings[0].authority_id == kreisverwaltung.authority_id

    result = apply_kreis_scope_fix(db_session, findings, reviewer="Testperson")
    db_session.commit()
    assert len(result["approved"]) == 1
    assert len(result["conflicts"]) == 0

    matcher = JurisdictionMatchingService(db_session)

    # Vorher ungedeckte Gemeinde (nicht die gepinnte AGS) muss jetzt ueber COUNTY matchen.
    probe = make_building(db_session, ags="09111015", city="Gemeinde15", state="Testland")
    result_match = matcher.match_authority(probe, rt.request_type_id)
    assert result_match.matching_status == MatchingStatus.MATCHED
    assert result_match.authority_id == kreisverwaltung.authority_id
    assert result_match.matching_level == MatchingLevel.COUNTY

    # Die urspruengliche, spezifischere Gemeinde-Regel bleibt unveraendert bestehen und matcht weiterhin direkt.
    probe_original = make_building(db_session, ags="09111003", city="Gemeinde3", state="Testland")
    result_original = matcher.match_authority(probe_original, rt.request_type_id)
    assert result_original.matching_status == MatchingStatus.MATCHED
    assert result_original.matching_level == MatchingLevel.MUNICIPALITY
    assert result_original.authority_id == kreisverwaltung.authority_id


def test_does_not_touch_legitimately_narrow_city_or_verbandsgemeinde_rules(db_session):
    """Eine Stadtverwaltung/Verbandsgemeindeverwaltung ist bewusst NUR fuer ihre eigene(n) Gemeinde(n)
    zustaendig - das darf nicht faelschlich als 'Kreis-Scope-Bug' erkannt werden."""
    rt = make_request_type(db_session, code="BAUAKTEN")
    _make_kreis(db_session, "09222", n_gemeinden=30)

    stadtverwaltung = make_authority(db_session, name="Stadtverwaltung Kleinstadt - Untere Bauaufsichtsbehörde")
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=stadtverwaltung.authority_id,
        ags="09222005", municipality="Kleinstadt", matching_level="MUNICIPALITY",
    )

    findings = find_kreis_scope_bugs(db_session, ["BAUAKTEN"], STATE_PREFIXES)
    assert findings == []


def test_is_idempotent_when_county_rule_already_exists(db_session):
    rt = make_request_type(db_session, code="BAUAKTEN")
    _make_kreis(db_session, "09111", n_gemeinden=30)
    kreisverwaltung = make_authority(db_session, name="Kreisverwaltung Testkreis - Untere Bauaufsichtsbehörde")
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=kreisverwaltung.authority_id,
        ags="09111003", municipality="Testkreis", matching_level="MUNICIPALITY",
    )
    # COUNTY-Regel existiert bereits (z.B. aus einem frueheren Lauf dieser Korrektur).
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=kreisverwaltung.authority_id,
        ags="09111", matching_level="COUNTY", priority=50,
    )

    findings = find_kreis_scope_bugs(db_session, ["BAUAKTEN"], STATE_PREFIXES)
    assert findings == []


def test_leaves_existing_verified_status_of_old_rule_untouched(db_session):
    """Die Korrektur ergaenzt nur eine neue Regel - sie darf die alte Regel nicht anfassen."""
    rt = make_request_type(db_session, code="BAUAKTEN")
    _make_kreis(db_session, "09111", n_gemeinden=30)
    kreisverwaltung = make_authority(db_session, name="Kreisverwaltung Testkreis - Untere Bauaufsichtsbehörde")
    old_rule = make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=kreisverwaltung.authority_id,
        ags="09111003", municipality="Testkreis", matching_level="MUNICIPALITY",
        verification_status="AUTO_IMPORTED", source="Bauaemter Datenbank Deutschland FINAL",
    )
    old_id = old_rule.jurisdiction_id

    findings = find_kreis_scope_bugs(db_session, ["BAUAKTEN"], STATE_PREFIXES)
    apply_kreis_scope_fix(db_session, findings, reviewer="Testperson")
    db_session.commit()

    refreshed_old = db_session.query(Jurisdiction).filter(Jurisdiction.jurisdiction_id == old_id).first()
    assert refreshed_old.verification_status == "AUTO_IMPORTED"
    assert refreshed_old.source == "Bauaemter Datenbank Deutschland FINAL"
    assert refreshed_old.ags == "09111003"
    assert refreshed_old.matching_level == "MUNICIPALITY"
