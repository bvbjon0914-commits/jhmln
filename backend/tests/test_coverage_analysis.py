"""
Tests für CoverageAnalysisService (Auftrag Priorität 1: Abdeckung "AGS x
Auskunftsart" messbar machen).

Deckt genau die fünf geforderten Kategorien mit je einem eindeutigen
Testfall ab. Jeder Testfall bekommt einen eigenen AGS/Bundesland-Namen, damit
sich die Fälle nicht gegenseitig über Landes-Fallback-Regeln beeinflussen.
"""
from app.services.coverage_analysis import (
    CATEGORY_CONFLICTING,
    CATEGORY_FALLBACK_ONLY,
    CATEGORY_NO_MATCH,
    CATEGORY_UNVERIFIED_OR_STALE,
    CATEGORY_VERIFIED,
    CoverageAnalysisService,
)

from tests.conftest import (
    days_ago,
    make_administrative_unit,
    make_authority,
    make_jurisdiction,
    make_request_type,
)


def _entry_for(entries, ags):
    matches = [e for e in entries if e.ags == ags]
    assert len(matches) == 1, f"Erwartet genau einen Eintrag für AGS {ags}, gefunden: {len(matches)}"
    return matches[0]


def test_classifies_all_five_categories_correctly(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")

    # (a) VERIFIED: eindeutig zugeordnet und fachlich geprüft, nicht abgelaufen
    make_administrative_unit(db_session, ags="05911000", state_name="NRW-A", municipality_name="Bochum")
    authority_a = make_authority(db_session, name="Grundbuchamt Bochum")
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=authority_a.authority_id,
        ags="05911000", matching_level="MUNICIPALITY",
        verification_status="VERIFIED", last_verified_at=days_ago(10), verified_by="Testperson",
    )

    # (b) UNVERIFIED_OR_STALE: eindeutig zugeordnet, aber nie fachlich geprüft
    make_administrative_unit(db_session, ags="05913000", state_name="NRW-B", municipality_name="Herne")
    authority_b = make_authority(db_session, name="Grundbuchamt Herne")
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=authority_b.authority_id,
        ags="05913000", matching_level="MUNICIPALITY",
    )

    # (c) NO_MATCH: keine Regel, kein Landes-Fallback für dieses Bundesland
    make_administrative_unit(db_session, ags="09162000", state_name="BY-NOMATCH", municipality_name="Nirgendwo")

    # (e) FALLBACK_ONLY: nur über eine STATE-Regel zugeordnet
    make_administrative_unit(db_session, ags="14612000", state_name="SN-FALLBACK", municipality_name="Irgendwo")
    authority_state = make_authority(db_session, name="Landesbehörde Sachsen")
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=authority_state.authority_id,
        state="SN-FALLBACK", ags=None, municipality=None, matching_level="STATE",
    )

    # (d) CONFLICTING: zwei widersprüchliche Regeln zu unterschiedlichen Behörden
    make_administrative_unit(db_session, ags="03159000", state_name="NI-CONFLICT", municipality_name="Doppelt")
    authority_c1 = make_authority(db_session, name="Behörde X")
    authority_c2 = make_authority(db_session, name="Behörde Y")
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=authority_c1.authority_id,
        ags="03159000", matching_level="MUNICIPALITY",
    )
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=authority_c2.authority_id,
        ags="03159000", matching_level="MUNICIPALITY",
    )

    service = CoverageAnalysisService(db_session)
    entries = service.analyze()

    assert len(entries) == 5  # 5 Gemeinden x 1 aktive Auskunftsart
    assert _entry_for(entries, "05911000").category == CATEGORY_VERIFIED
    assert _entry_for(entries, "05913000").category == CATEGORY_UNVERIFIED_OR_STALE
    assert _entry_for(entries, "09162000").category == CATEGORY_NO_MATCH
    assert _entry_for(entries, "14612000").category == CATEGORY_FALLBACK_ONLY
    assert _entry_for(entries, "03159000").category == CATEGORY_CONFLICTING


def test_stale_verification_counts_as_unverified(db_session):
    """Eine VERIFIED-Regel mit last_verified_at älter als 365 Tage gilt nicht mehr als belegt."""
    rt = make_request_type(db_session, code="GRUNDBUCH")
    make_administrative_unit(db_session, ags="05911000", state_name="NRW-A", municipality_name="Bochum")
    authority = make_authority(db_session, name="Grundbuchamt Bochum")
    make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=authority.authority_id,
        ags="05911000", matching_level="MUNICIPALITY",
        verification_status="VERIFIED", last_verified_at=days_ago(400), verified_by="Testperson",
    )

    entries = CoverageAnalysisService(db_session).analyze()
    assert _entry_for(entries, "05911000").category == CATEGORY_UNVERIFIED_OR_STALE


def test_existing_authority_address_alone_is_not_counted_as_proven(db_session):
    """
    Auftrag: "Zähle eine vorhandene Behördenadresse nicht automatisch als
    nachgewiesene Zuständigkeit." Eine Authority mit vollständiger Adresse,
    aber OHNE jurisdiction-Regel für diese Auskunftsart, muss NO_MATCH sein.
    """
    make_request_type(db_session, code="GRUNDBUCH")
    make_administrative_unit(db_session, ags="05911000", state_name="NRW-A", municipality_name="Bochum")
    make_authority(
        db_session, name="Grundbuchamt Bochum",
        street="Amtsstraße", house_number="1", postal_code="44787",
    )
    # Bewusst KEINE Jurisdiction-Zeile für diese Gemeinde/Auskunftsart angelegt.

    entries = CoverageAnalysisService(db_session).analyze()
    assert _entry_for(entries, "05911000").category == CATEGORY_NO_MATCH


def test_portfolio_building_count_uses_real_buildings_only(db_session):
    from tests.conftest import make_building

    make_request_type(db_session, code="GRUNDBUCH")
    make_administrative_unit(db_session, ags="05911000", state_name="NRW-A", municipality_name="Bochum")
    make_building(db_session, ags="05911000")
    make_building(db_session, ags="05911000")
    make_administrative_unit(db_session, ags="05913000", state_name="NRW-B", municipality_name="Herne")

    entries = CoverageAnalysisService(db_session).analyze()
    assert _entry_for(entries, "05911000").portfolio_building_count == 2
    assert _entry_for(entries, "05913000").portfolio_building_count == 0


def test_summarize_by_groups_categories_and_affected_buildings(db_session):
    from tests.conftest import make_building

    make_request_type(db_session, code="GRUNDBUCH")
    make_administrative_unit(db_session, ags="09162000", state_name="BY-NOMATCH", municipality_name="Nirgendwo")
    make_building(db_session, ags="09162000")
    make_building(db_session, ags="09162000")
    make_building(db_session, ags="09162000")

    entries = CoverageAnalysisService(db_session).analyze()
    by_state = CoverageAnalysisService.summarize_by(entries, "state_name")
    group = next(g for g in by_state if g["group"] == "BY-NOMATCH")
    assert group["NO_MATCH"] == 1
    assert group["affected_buildings"] == 3

    overall = CoverageAnalysisService.overall_summary(entries)
    assert overall["total"] == 1
    assert overall[CATEGORY_NO_MATCH] == 1


def test_inactive_request_types_are_excluded(db_session):
    make_request_type(db_session, code="GRUNDBUCH", active=False)
    make_administrative_unit(db_session, ags="05911000", state_name="NRW-A", municipality_name="Bochum")

    entries = CoverageAnalysisService(db_session).analyze()
    assert entries == []
