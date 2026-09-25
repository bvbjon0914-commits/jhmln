"""
Tests für JurisdictionStagingService (Auftrag Priorität 4: sicherer
Aktualisierungsprozess - Konflikterkennung, Freigabe/Ablehnung, Historie).
"""
from datetime import date

import pytest

from app.models.jurisdiction import Jurisdiction
from app.models.jurisdiction_staging import ConflictType, JurisdictionStagingEntry, StagingStatus
from app.services.jurisdiction_staging import JurisdictionStagingService

from tests.conftest import days_ago, make_authority, make_jurisdiction, make_request_type


def test_new_entry_without_existing_rule_has_no_conflict(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    service = JurisdictionStagingService(db_session)

    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id,
        ags="05911000", proposed_authority_id=authority.authority_id,
        source="Testquelle",
    )
    db_session.commit()

    assert entry.conflict_type == ConflictType.NEW
    assert entry.conflicts_with_jurisdiction_id is None
    assert entry.status == StagingStatus.PENDING


def test_exact_duplicate_is_detected(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    make_jurisdiction(db_session, request_type_id=rt.request_type_id, authority_id=authority.authority_id, ags="05911000")

    service = JurisdictionStagingService(db_session)
    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id,
        ags="05911000", proposed_authority_id=authority.authority_id,
    )
    db_session.commit()

    assert entry.conflict_type == ConflictType.DUPLICATE_EXACT


def test_contradicts_verified_rule_is_detected(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    old_authority = make_authority(db_session, name="Alte Behörde")
    new_authority = make_authority(db_session, name="Neue Behörde")
    old_rule = make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=old_authority.authority_id,
        ags="05911000", verification_status="VERIFIED", last_verified_at=days_ago(10), verified_by="Prüfer A",
    )

    service = JurisdictionStagingService(db_session)
    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id,
        ags="05911000", proposed_authority_id=new_authority.authority_id,
    )
    db_session.commit()

    assert entry.conflict_type == ConflictType.CONTRADICTS_VERIFIED
    assert entry.conflicts_with_jurisdiction_id == old_rule.jurisdiction_id


def test_contradicts_unverified_rule_is_detected(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    old_authority = make_authority(db_session, name="Alte Behörde")
    new_authority = make_authority(db_session, name="Neue Behörde")
    make_jurisdiction(db_session, request_type_id=rt.request_type_id, authority_id=old_authority.authority_id, ags="05911000")

    service = JurisdictionStagingService(db_session)
    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id,
        ags="05911000", proposed_authority_id=new_authority.authority_id,
    )
    db_session.commit()

    assert entry.conflict_type == ConflictType.CONTRADICTS_UNVERIFIED


def test_stage_entry_requires_authority_reference(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    service = JurisdictionStagingService(db_session)

    with pytest.raises(ValueError):
        service.stage_entry(batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000")


def test_approve_new_entry_creates_verified_jurisdiction(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    service = JurisdictionStagingService(db_session)

    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id,
        ags="05911000", matching_level="MUNICIPALITY",
        proposed_authority_id=authority.authority_id,
        source="BKG VG250", source_url="https://gdz.bkg.bund.de/...", source_license="DL-DE-BY-2.0",
    )
    db_session.commit()

    new_rule = service.approve_entry(entry.id, reviewer="Testperson", review_notes="ok")
    db_session.commit()

    assert new_rule.verification_status == "VERIFIED"
    assert new_rule.verified_by == "Testperson"
    assert new_rule.authority_id == authority.authority_id
    assert new_rule.source == "BKG VG250"

    db_session.refresh(entry)
    assert entry.status == StagingStatus.APPROVED
    assert entry.resulting_jurisdiction_id == new_rule.jurisdiction_id
    assert entry.reviewed_by == "Testperson"


def test_approve_contradicting_entry_expires_old_rule_without_deleting_it(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    old_authority = make_authority(db_session, name="Alte Behörde")
    new_authority = make_authority(db_session, name="Neue Behörde")
    old_rule = make_jurisdiction(
        db_session, request_type_id=rt.request_type_id, authority_id=old_authority.authority_id, ags="05911000",
    )
    old_jurisdiction_id = old_rule.jurisdiction_id

    service = JurisdictionStagingService(db_session)
    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000",
        proposed_authority_id=new_authority.authority_id,
        valid_from=date(2026, 6, 1),
    )
    db_session.commit()
    assert entry.conflict_type == ConflictType.CONTRADICTS_UNVERIFIED

    new_rule = service.approve_entry(entry.id, reviewer="Testperson")
    db_session.commit()

    # Alte Regel bleibt als Zeile bestehen (Historie), ist aber jetzt abgelaufen.
    refreshed_old = db_session.query(Jurisdiction).filter(
        Jurisdiction.jurisdiction_id == old_jurisdiction_id
    ).first()
    assert refreshed_old is not None
    assert refreshed_old.valid_to == date(2026, 5, 31)
    assert refreshed_old.active is True  # nicht gelöscht/deaktiviert, nur zeitlich ausgelaufen

    # Neue Regel gilt ab dem angegebenen Datum.
    assert new_rule.valid_from == date(2026, 6, 1)
    assert new_rule.authority_id == new_authority.authority_id

    # Keine Überlappung: die beiden Gültigkeitszeiträume berühren sich nicht.
    assert refreshed_old.valid_to < new_rule.valid_from


def test_approve_exact_duplicate_is_rejected_with_error(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    make_jurisdiction(db_session, request_type_id=rt.request_type_id, authority_id=authority.authority_id, ags="05911000")

    service = JurisdictionStagingService(db_session)
    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000",
        proposed_authority_id=authority.authority_id,
    )
    db_session.commit()

    with pytest.raises(ValueError):
        service.approve_entry(entry.id, reviewer="Testperson")


def test_approve_without_resolved_authority_is_rejected_with_error(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    service = JurisdictionStagingService(db_session)

    entry = JurisdictionStagingEntry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000",
        proposed_authority_name="Noch zu recherchierende Behörde",
        status=StagingStatus.PENDING, conflict_type=ConflictType.NEW,
    )
    db_session.add(entry)
    db_session.commit()

    with pytest.raises(ValueError):
        service.approve_entry(entry.id, reviewer="Testperson")


def test_cannot_approve_or_reject_twice(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    service = JurisdictionStagingService(db_session)

    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000",
        proposed_authority_id=authority.authority_id,
    )
    db_session.commit()

    service.approve_entry(entry.id, reviewer="Testperson")
    db_session.commit()

    with pytest.raises(ValueError):
        service.approve_entry(entry.id, reviewer="Testperson")
    with pytest.raises(ValueError):
        service.reject_entry(entry.id, reviewer="Testperson", reason="zu spät")


def test_reject_entry_records_reviewer_and_reason(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    service = JurisdictionStagingService(db_session)

    entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000",
        proposed_authority_id=authority.authority_id,
    )
    db_session.commit()

    rejected = service.reject_entry(entry.id, reviewer="Testperson", reason="Quelle nicht verlässlich")
    db_session.commit()

    assert rejected.status == StagingStatus.REJECTED
    assert rejected.reviewed_by == "Testperson"
    assert rejected.review_notes == "Quelle nicht verlässlich"


def test_pending_conflicts_excludes_conflict_free_new_entries(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    other_authority = make_authority(db_session, name="Andere Behörde")
    make_jurisdiction(db_session, request_type_id=rt.request_type_id, authority_id=authority.authority_id, ags="05911000")

    service = JurisdictionStagingService(db_session)
    new_entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="09162000",
        proposed_authority_id=authority.authority_id,
    )
    conflict_entry = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000",
        proposed_authority_id=other_authority.authority_id,
    )
    db_session.commit()

    pending = service.pending_conflicts(batch_id="batch-1")
    pending_ids = {e.id for e in pending}
    assert conflict_entry.id in pending_ids
    assert new_entry.id not in pending_ids


def test_batch_summary_counts_by_status_and_conflict_type(db_session):
    rt = make_request_type(db_session, code="GRUNDBUCH")
    authority = make_authority(db_session)
    service = JurisdictionStagingService(db_session)

    e1 = service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05911000",
        proposed_authority_id=authority.authority_id,
    )
    service.stage_entry(
        batch_id="batch-1", request_type_id=rt.request_type_id, ags="05913000",
        proposed_authority_id=authority.authority_id,
    )
    db_session.commit()
    service.approve_entry(e1.id, reviewer="Testperson")
    db_session.commit()

    summary = service.batch_summary("batch-1")
    assert summary["total"] == 2
    assert summary["by_status"]["APPROVED"] == 1
    assert summary["by_status"]["PENDING"] == 1
    assert summary["by_conflict_type"]["NEW"] == 2
