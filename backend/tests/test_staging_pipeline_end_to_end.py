"""
End-to-End-Test des sicheren Aktualisierungsprozesses mit einem realistischen
Fall (Auftrag: "Führe die neuen Daten vollständig durch den gebauten
Prozess ... und teste das Matching mit repräsentativen Adressen").

Nachgebildet: BODENDENKMALSCHUTZ in Rheinland-Pfalz wird über die vier
GDKE-Landesarchäologie-Außenstellen (Koblenz, Mainz, Speyer, Trier) auf
Landkreis-Ebene organisiert (siehe docs/COVERAGE_ANALYSIS_REPORT.md und die
tatsächlich in dieser Sitzung recherchierten Quellen). Dieser Test benutzt
KEINE echten Behörden-IDs aus der Produktions-/Entwicklungsdatenbank,
sondern synthetische Testdaten mit demselben AGS-Schema, um die MECHANIK
(Staging -> Konflikterkennung -> Freigabe -> Matching) unabhängig vom
tatsächlichen DB-Inhalt abzusichern.
"""
from app.services.jurisdiction_matcher import JurisdictionMatchingService, MatchingLevel, MatchingStatus
from app.services.jurisdiction_staging import JurisdictionStagingService
from app.models.jurisdiction_staging import ConflictType

from tests.conftest import make_authority, make_building, make_request_type


def test_new_request_type_gets_staged_approved_and_matches_correctly(db_session):
    """
    Simuliert genau den geforderten Ablauf für eine Auskunftsart, für die
    bislang KEINE Regel existiert: mehrere Landkreise werden auf zwei
    unterschiedliche Fachbehörden (Außenstellen) verteilt, jede Regel läuft
    durch Staging, wird konfliktfrei erkannt (kein Bestand vorhanden) und
    erst nach Freigabe aktiv - anschließend wird für Adressen aus BEIDEN
    Zuständigkeitsbereichen korrekt gematcht.
    """
    rt = make_request_type(db_session, code="BODENDENKMALSCHUTZ")
    aussenstelle_koblenz = make_authority(
        db_session, name="GDKE - Direktion Landesarchäologie, Außenstelle Koblenz",
        street="Niederberger Höhe", house_number="1", postal_code="56077", city="Koblenz",
        email="landesarchaeologie-koblenz@gdke.rlp.de",
    )
    aussenstelle_trier = make_authority(
        db_session, name="GDKE - Direktion Landesarchäologie, Außenstelle Trier",
        street="Weimarer Allee", house_number="1", postal_code="54290", city="Trier",
        email="landesarchaeologie-trier@gdke.rlp.de",
    )

    service = JurisdictionStagingService(db_session)
    batch_id = "test-bodendenkmalschutz-rlp"

    kreise_koblenz = ["07131", "07143"]  # Ahrweiler, Westerwaldkreis
    kreise_trier = ["07232", "07233"]    # Eifelkreis Bitburg-Prüm, Vulkaneifel

    staged_ids = []
    for ags_kreis in kreise_koblenz:
        entry = service.stage_entry(
            batch_id=batch_id, request_type_id=rt.request_type_id,
            state="Rheinland-Pfalz", ags=ags_kreis, matching_level=MatchingLevel.COUNTY, priority=50,
            proposed_authority_id=aussenstelle_koblenz.authority_id,
            source="GDKE RLP - Landesarchäologie, Außenstelle Koblenz (Zuständigkeitsbereich laut Amtsseite)",
            source_url="https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-koblenz",
        )
        staged_ids.append(entry.id)
    for ags_kreis in kreise_trier:
        entry = service.stage_entry(
            batch_id=batch_id, request_type_id=rt.request_type_id,
            state="Rheinland-Pfalz", ags=ags_kreis, matching_level=MatchingLevel.COUNTY, priority=50,
            proposed_authority_id=aussenstelle_trier.authority_id,
            source="GDKE RLP - Landesarchäologie, Außenstelle Trier (Zuständigkeitsbereich laut Amtsseite)",
            source_url="https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-trier",
        )
        staged_ids.append(entry.id)
    db_session.commit()

    # Konflikterkennung: da bislang keine BODENDENKMALSCHUTZ-Regel existierte, muss JEDER Eintrag NEW sein.
    from app.models.jurisdiction_staging import JurisdictionStagingEntry
    entries = db_session.query(JurisdictionStagingEntry).filter(JurisdictionStagingEntry.batch_id == batch_id).all()
    assert len(entries) == 4
    assert all(e.conflict_type == ConflictType.NEW for e in entries)

    # Vor Freigabe: Matching muss noch NO_MATCH liefern (Staging wirkt sich nicht auf das Live-Matching aus).
    matcher = JurisdictionMatchingService(db_session)
    probe_ahrweiler = make_building(db_session, ags="07131000", city="Bad Neuenahr-Ahrweiler", state="Rheinland-Pfalz")
    result_before = matcher.match_authority(probe_ahrweiler, rt.request_type_id)
    assert result_before.matching_status == MatchingStatus.NO_MATCH

    # Freigabe aller vier Einträge durch einen benannten Prüfer.
    for sid in staged_ids:
        service.approve_entry(
            sid, reviewer="Testperson (Recherche-Sitzung)",
            review_notes="Zuständigkeitsbereich direkt von der amtlichen GDKE-Seite übernommen.",
        )
    db_session.commit()

    # Nach Freigabe: Matching muss jetzt für BEIDE Zuständigkeitsbereiche korrekt greifen.
    result_ahrweiler = matcher.match_authority(probe_ahrweiler, rt.request_type_id)
    assert result_ahrweiler.matching_status == MatchingStatus.MATCHED
    assert result_ahrweiler.authority_id == aussenstelle_koblenz.authority_id
    assert result_ahrweiler.matching_level == MatchingLevel.COUNTY

    probe_vulkaneifel = make_building(db_session, ags="07233000", city="Daun", state="Rheinland-Pfalz")
    result_vulkaneifel = matcher.match_authority(probe_vulkaneifel, rt.request_type_id)
    assert result_vulkaneifel.matching_status == MatchingStatus.MATCHED
    assert result_vulkaneifel.authority_id == aussenstelle_trier.authority_id

    # Eine dritte, NICHT zugeordnete Region bleibt weiterhin korrekt NO_MATCH (kein pauschaler Fallback erfunden).
    probe_bayern = make_building(db_session, ags="09162000", city="Nirgendwo", state="Bayern")
    result_bayern = matcher.match_authority(probe_bayern, rt.request_type_id)
    assert result_bayern.matching_status == MatchingStatus.NO_MATCH

    # Die neu übernommenen Regeln sind fachlich bestätigt (VERIFIED), nicht nur automatisch importiert.
    from app.models.jurisdiction import Jurisdiction
    new_rule = db_session.query(Jurisdiction).filter(
        Jurisdiction.jurisdiction_id == result_ahrweiler.jurisdiction_id
    ).first()
    assert new_rule.verification_status == "VERIFIED"
    assert new_rule.verified_by == "Testperson (Recherche-Sitzung)"
    assert new_rule.is_professionally_verified()
    assert new_rule.source_url == "https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-koblenz"


def test_conflicting_source_for_same_kreis_is_flagged_not_silently_overwritten(db_session):
    """
    Zweite, widersprüchliche Quelle für DENSELBEN Landkreis darf die erste
    fachlich bestätigte Regel NICHT automatisch überschreiben - der Auftrag
    verlangt ausdrücklich, dass ein Widerspruch angezeigt wird statt beliebig
    aufgelöst zu werden.
    """
    rt = make_request_type(db_session, code="BODENDENKMALSCHUTZ")
    authority_1 = make_authority(db_session, name="Außenstelle Koblenz")
    authority_2 = make_authority(db_session, name="Fälschlich andere Quelle")

    service = JurisdictionStagingService(db_session)
    first = service.stage_entry(
        batch_id="batch-a", request_type_id=rt.request_type_id,
        ags="07131", matching_level=MatchingLevel.COUNTY,
        proposed_authority_id=authority_1.authority_id, source="GDKE RLP",
    )
    db_session.commit()
    service.approve_entry(first.id, reviewer="Testperson")
    db_session.commit()

    second = service.stage_entry(
        batch_id="batch-b", request_type_id=rt.request_type_id,
        ags="07131", matching_level=MatchingLevel.COUNTY,
        proposed_authority_id=authority_2.authority_id, source="Widersprüchliche Zweitquelle",
    )
    db_session.commit()

    assert second.conflict_type == ConflictType.CONTRADICTS_VERIFIED
    assert second.conflicts_with_jurisdiction_id is not None
