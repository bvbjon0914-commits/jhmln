"""
Regressionstests für JurisdictionMatchingService.

Deckt die in docs/PHASE2_MATCHING_ENGINE.md ursprünglich geplanten acht
Testfälle ab, die nie automatisiert umgesetzt wurden, sowie drei gezielte
Regressionstests für den Prioritäts-/Spezifitäts-Tiebreak
(_select_best_candidate), der laut Auditbericht nur auf origin/main
existierte und mit der Branch-Zusammenführung jetzt fester Bestandteil
dieses Branches ist.
"""
import pytest

from app.services.jurisdiction_matcher import (
    JurisdictionMatchingService, MatchingStatus, MatchingLevel,
)
from tests.conftest import (
    make_request_type, make_authority, make_jurisdiction, make_building,
)


@pytest.fixture()
def matcher(db_session):
    make_request_type(db_session, "GRUNDBUCH")
    return JurisdictionMatchingService(db_session)


class TestSevenStageHierarchy:
    """Test 1 (PHASE2): eindeutige Gemeinde-Zuständigkeit."""

    def test_municipality_level_match(self, db_session, matcher):
        auth = make_authority(db_session, name="Amtsgericht Bochum")
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id,
                           ags="05911000", priority=40, matching_level=MatchingLevel.MUNICIPALITY)
        building = make_building(db_session, street="Musterstraße", house_number="12",
                                  city="Bochum", ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MATCHED
        assert result.authority_id == auth.authority_id
        assert result.matching_level == MatchingLevel.MUNICIPALITY
        assert result.matching_confidence == 1.0

    def test_no_match_when_no_rule_for_ags(self, db_session, matcher):
        """Test 2 (PHASE2): keine Zuständigkeit vorhanden."""
        building = make_building(db_session, city="Nullstadt", ags="99999999")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.NO_MATCH
        assert result.authority_id is None
        assert "99999999" in result.reason

    def test_no_match_reason_distinguishes_missing_ags(self, db_session, matcher):
        """Test 8 (PHASE2): fehlende Daten führen nie zu einer Exception."""
        building = make_building(db_session, ags=None)

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.NO_MATCH
        assert "kein AGS" in result.reason.lower() or "kein ags" in result.reason.lower()

    def test_street_rule_overrides_municipality_rule(self, db_session, matcher):
        """Test 4 (PHASE2): Sonderregel überschreibt Gemeinde-Regel."""
        special_auth = make_authority(db_session, name="Spezial-Amt")
        normal_auth = make_authority(db_session, name="Standard-Amt")
        make_jurisdiction(db_session, "GRUNDBUCH", special_auth.authority_id,
                           ags="05911000", street="Spezialstraße", priority=10,
                           matching_level=MatchingLevel.STREET)
        make_jurisdiction(db_session, "GRUNDBUCH", normal_auth.authority_id,
                           ags="05911000", priority=40, matching_level=MatchingLevel.MUNICIPALITY)
        building = make_building(db_session, street="Spezialstraße", house_number="5",
                                  city="Bochum", ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MATCHED
        assert result.authority_id == special_auth.authority_id
        assert result.matching_level == MatchingLevel.STREET

    def test_postal_code_fallback_not_used_when_ags_rule_exists(self, db_session, matcher):
        """Test 5 (PHASE2): PLZ stimmt, aber AGS-Regel hat Vorrang vor PLZ-Fallback."""
        correct_auth = make_authority(db_session, name="Richtige Behörde")
        wrong_auth = make_authority(db_session, name="Falsche Fallback-Behörde")
        make_jurisdiction(db_session, "GRUNDBUCH", correct_auth.authority_id,
                           ags="05911000", priority=40, matching_level=MatchingLevel.MUNICIPALITY)
        make_jurisdiction(db_session, "GRUNDBUCH", wrong_auth.authority_id,
                           postal_code="44787", priority=70, matching_level=MatchingLevel.POSTAL_CODE)
        building = make_building(db_session, postal_code="44787", city="Bochum", ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.authority_id == correct_auth.authority_id
        assert result.matching_level == MatchingLevel.MUNICIPALITY

    def test_multiple_request_types_matched_independently(self, db_session):
        """Test 6 (PHASE2): mehrere Auskunftsarten unabhängig voneinander."""
        make_request_type(db_session, "GRUNDBUCH")
        make_request_type(db_session, "BAUAKTEN")
        make_request_type(db_session, "ALTLASTEN")
        auth_grundbuch = make_authority(db_session, name="Amtsgericht")
        auth_bauakten = make_authority(db_session, name="Bauamt")
        make_jurisdiction(db_session, "GRUNDBUCH", auth_grundbuch.authority_id, ags="05911000", priority=40)
        make_jurisdiction(db_session, "BAUAKTEN", auth_bauakten.authority_id, ags="05911000", priority=40)
        building = make_building(db_session, ags="05911000")
        matcher = JurisdictionMatchingService(db_session)

        results = matcher.match_authorities(building, ["GRUNDBUCH", "BAUAKTEN", "ALTLASTEN"])

        by_type = {r.request_type_id: r for r in results}
        assert by_type["GRUNDBUCH"].authority_id == auth_grundbuch.authority_id
        assert by_type["BAUAKTEN"].authority_id == auth_bauakten.authority_id
        assert by_type["ALTLASTEN"].matching_status == MatchingStatus.NO_MATCH

    def test_address_normalization_feeds_into_matching(self, db_session, matcher):
        """Test 7 (PHASE2): unsauber geschriebene Adresse matcht trotzdem."""
        auth = make_authority(db_session, name="Amtsgericht Bochum")
        # Regel ist mit normalisierter Schreibweise hinterlegt ...
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id,
                           ags="05911000", street="Musterstraße", house_number="12",
                           priority=10, matching_level=MatchingLevel.STREET_NUMBER)
        # ... Gebäude-Adresse kommt unsauber/uneinheitlich geschrieben herein.
        building = make_building(db_session, street="Musterstr.  ", house_number="12",
                                  city="BOCHUM", ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MATCHED
        assert result.matching_level == MatchingLevel.STREET_NUMBER

    def test_genuinely_conflicting_authorities_yield_multiple_matches(self, db_session, matcher):
        """Test 3 (PHASE2): zwei ECHT unterschiedliche Behörden derselben Stufe -> Konflikt bleibt."""
        auth1 = make_authority(db_session, name="Behörde A")
        auth2 = make_authority(db_session, name="Behörde B")
        make_jurisdiction(db_session, "GRUNDBUCH", auth1.authority_id, ags="05911000", priority=40)
        make_jurisdiction(db_session, "GRUNDBUCH", auth2.authority_id, ags="05911000", priority=40)
        building = make_building(db_session, ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MULTIPLE_MATCHES
        assert result.authority_id is None
        assert set(result.alternative_authorities) == {auth1.authority_id, auth2.authority_id}


class TestPriorityAndSpecificityTiebreak:
    """
    Regressionstests für _select_best_candidate (git diff HEAD/origin/main,
    Commit 'Fix jurisdiction priority resolution and duplicate matches').

    Vor diesem Fix wurde JEDER Mehrfachtreffer auf derselben Stufe als
    MULTIPLE_MATCHES gemeldet - auch wenn es sich um dieselbe Behörde oder
    um Regeln mit eindeutig unterschiedlicher Priorität handelte.
    """

    def test_duplicate_rules_to_same_authority_are_not_a_conflict(self, db_session, matcher):
        """Zwei Regeln, dieselbe Behörde, gleiche Stufe -> MATCHED, kein Konflikt."""
        auth = make_authority(db_session, name="Amtsgericht Bochum")
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000", priority=40)
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000", priority=40)
        building = make_building(db_session, ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MATCHED
        assert result.authority_id == auth.authority_id

    def test_lower_priority_value_wins_at_same_stage(self, db_session, matcher):
        """Bei unterschiedlicher priority auf derselben Stufe gewinnt der kleinere Wert."""
        high_prio_auth = make_authority(db_session, name="Vorrangige Behörde")
        low_prio_auth = make_authority(db_session, name="Nachrangige Behörde")
        make_jurisdiction(db_session, "GRUNDBUCH", low_prio_auth.authority_id, ags="05911000", priority=100)
        make_jurisdiction(db_session, "GRUNDBUCH", high_prio_auth.authority_id, ags="05911000", priority=10)
        building = make_building(db_session, ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MATCHED
        assert result.authority_id == high_prio_auth.authority_id

    def test_higher_specificity_wins_when_priority_ties(self, db_session, matcher):
        """Bei gleicher priority gewinnt die höhere Spezifität (get_specificity_score)."""
        vague_auth = make_authority(db_session, name="Unspezifische Behörde")
        specific_auth = make_authority(db_session, name="Spezifische Behörde")
        # gleiche priority, aber die zweite Regel trägt zusätzlich municipality
        # und postal_code als beschreibende Zusatzinfo -> höherer Spezifitätsscore
        make_jurisdiction(db_session, "GRUNDBUCH", vague_auth.authority_id,
                           ags="05911000", priority=40)
        make_jurisdiction(db_session, "GRUNDBUCH", specific_auth.authority_id,
                           ags="05911000", priority=40, municipality="Bochum", postal_code="44787")
        building = make_building(db_session, ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MATCHED
        assert result.authority_id == specific_auth.authority_id

    def test_conflict_still_reported_after_tiebreak_exhausted(self, db_session, matcher):
        """Auch nach Priority-/Spezifitäts-Tiebreak bleibt ein echter Konflikt ein Konflikt."""
        auth1 = make_authority(db_session, name="Behörde A")
        auth2 = make_authority(db_session, name="Behörde B")
        make_jurisdiction(db_session, "GRUNDBUCH", auth1.authority_id, ags="05911000", priority=10)
        make_jurisdiction(db_session, "GRUNDBUCH", auth2.authority_id, ags="05911000", priority=10)
        building = make_building(db_session, ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.MULTIPLE_MATCHES
        assert len(result.alternative_authorities) == 2


class TestInactiveAndExpiredRules:
    def test_inactive_rule_is_ignored(self, db_session, matcher):
        auth = make_authority(db_session)
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000",
                           priority=40, active=False)
        building = make_building(db_session, ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.NO_MATCH

    def test_expired_rule_is_ignored(self, db_session, matcher):
        from datetime import date, timedelta
        auth = make_authority(db_session)
        make_jurisdiction(db_session, "GRUNDBUCH", auth.authority_id, ags="05911000", priority=40,
                           valid_to=date.today() - timedelta(days=1))
        building = make_building(db_session, ags="05911000")

        result = matcher.match_authority(building, "GRUNDBUCH")

        assert result.matching_status == MatchingStatus.NO_MATCH
