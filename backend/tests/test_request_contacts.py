"""Regression tests for service-specific recipients and shared inbox pollution."""

import csv
import io
from datetime import datetime, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

from app.api.auth import require_main
from app.api.data_quality import _contact_gaps, _find_duplicate_authority_groups
from app.models.authority import Authority
from app.models.aktenzeichen import RequestItemReference
from app.models.authority_contact_channel import AuthorityContactChannel, ChannelType
from app.models.case import Case, CaseBuilding, CaseRequest
from app.models.settings import AppSettings
from app.services.contact_resolver import ContactResolver
from app.services.import_service import ImportService
from tests.conftest import (
    make_authority,
    make_building,
    make_jurisdiction,
    make_request,
    make_request_item,
    make_request_type,
)


def setup_authority(db):
    for code in ("BAUAKTEN", "BAULASTEN"):
        make_request_type(db, code)
    return make_authority(db, email="info@bochum.de")


def channel(
    db, authority, request_type="BAUAKTEN", email="bauakten@example.com", **kwargs
):
    values = dict(
        authority_id=authority.authority_id,
        request_type_id=request_type,
        channel_type=ChannelType.EMAIL,
        value=email,
        active=True,
        preferred=False,
        source_url="https://www.bochum.de/test-leistung",
        last_verified_at=datetime.utcnow(),
    )
    values.update(kwargs)
    row = AuthorityContactChannel(**values)
    db.add(row)
    db.commit()
    return row


def resolve(db, authority, request_type="BAUAKTEN"):
    return ContactResolver(db, [authority.authority_id]).resolve(
        authority, request_type
    )


def test_flat_inbox_is_a_fallback_not_a_verified_service_contact(db_session):
    authority = setup_authority(db_session)
    for request_type in ("BAUAKTEN", "BAULASTEN"):
        result = resolve(db_session, authority, request_type)
        assert result.email is None
        assert result.fallback_email == "info@bochum.de"
        assert result.status == "GENERAL_ONLY"
        assert not result.can_send


def test_two_services_use_different_contacts_without_mutating_authority(db_session):
    authority = setup_authority(db_session)
    channel(db_session, authority)
    channel(db_session, authority, "BAULASTEN", "baulasten@example.com")
    resolver = ContactResolver(db_session, [authority.authority_id])
    assert resolver.resolve(authority, "BAUAKTEN").email == "bauakten@example.com"
    assert resolver.resolve(authority, "BAULASTEN").email == "baulasten@example.com"
    assert authority.email == "info@bochum.de"


def test_contact_for_one_service_does_not_cover_another(db_session):
    authority = setup_authority(db_session)
    channel(db_session, authority)
    assert not resolve(db_session, authority, "BAULASTEN").can_send


@pytest.mark.parametrize(
    "overrides",
    [
        {"last_verified_at": None},
        {"source_url": None},
        {"source_url": "Amtliche Quelle"},
        {"last_verified_at": datetime.utcnow() - timedelta(days=366)},
        {"last_verified_at": datetime.utcnow() + timedelta(days=1)},
    ],
)
def test_missing_or_stale_review_never_authorizes_email(db_session, overrides):
    authority = setup_authority(db_session)
    channel(db_session, authority, **overrides)
    assert not resolve(db_session, authority).can_send


def test_explicitly_reviewed_general_address_is_valid_for_that_service(db_session):
    authority = setup_authority(db_session)
    channel(db_session, authority, email="info@bochum.de")
    assert resolve(db_session, authority).can_send
    assert not resolve(db_session, authority, "BAULASTEN").can_send


def test_inactive_and_unscoped_channels_do_not_cover_a_service(db_session):
    authority = setup_authority(db_session)
    channel(db_session, authority, active=False)
    channel(db_session, authority, request_type=None)
    assert not resolve(db_session, authority).can_send


def test_conflicting_recipients_require_explicit_preference(db_session):
    authority = setup_authority(db_session)
    channel(db_session, authority)
    second = channel(db_session, authority, email="other@example.com")
    assert resolve(db_session, authority).status == "CONFLICT"
    second.preferred = True
    db_session.commit()
    assert resolve(db_session, authority).email == "other@example.com"


def test_unreviewed_preference_cannot_displace_reviewed_contact(db_session):
    authority = setup_authority(db_session)
    channel(db_session, authority)
    channel(
        db_session,
        authority,
        email="other@example.com",
        preferred=True,
        last_verified_at=None,
    )
    assert resolve(db_session, authority).email == "bauakten@example.com"


MAPPING = {
    "authority_name": "Behörde",
    "city": "Ort",
    "ags": "AGS",
    "request_type": "Auskunftsart",
    "email": "E-Mail",
    "source": "Quelle",
}


def test_import_keeps_different_emails_per_service_and_never_verifies_them(db_session):
    authority = setup_authority(db_session)
    rows = pd.DataFrame(
        [
            {
                "Behörde": authority.authority_name,
                "Ort": "Bochum",
                "AGS": "05911000",
                "Auskunftsart": rt,
                "E-Mail": email,
                "Quelle": "https://www.bochum.de/test-leistung",
            }
            for rt, email in [
                ("BAUAKTEN", "bauakten@example.com"),
                ("BAULASTEN", "baulasten@example.com"),
            ]
        ]
    )
    service = ImportService(db_session)
    assert service.import_jurisdictions(rows, MAPPING).errors == 0
    assert authority.email == "info@bochum.de"
    contacts = db_session.query(AuthorityContactChannel).all()
    assert {(c.request_type_id, c.value) for c in contacts} == {
        ("BAUAKTEN", "bauakten@example.com"),
        ("BAULASTEN", "baulasten@example.com"),
    }
    assert all(c.last_verified_at is None and c.source_url for c in contacts)
    assert service.import_jurisdictions(rows, MAPPING).duplicates == 2
    assert db_session.query(AuthorityContactChannel).count() == 2


def test_invalid_import_email_does_not_create_an_authority(db_session):
    make_request_type(db_session, "BAUAKTEN")
    rows = pd.DataFrame(
        [
            {
                "Behörde": "Ungültiger Eintrag",
                "Ort": "Bochum",
                "AGS": "05911000",
                "Auskunftsart": "BAUAKTEN",
                "E-Mail": "invalid",
            }
        ]
    )
    result = ImportService(db_session).import_jurisdictions(rows, MAPPING)
    assert result.needs_review == 1
    assert db_session.query(Authority).count() == 0


def test_reimport_existing_rule_reports_new_contact_as_update(db_session):
    authority = setup_authority(db_session)
    make_jurisdiction(db_session, "BAUAKTEN", authority.authority_id, ags="05911000")
    rows = pd.DataFrame(
        [
            {
                "Behörde": authority.authority_name,
                "Ort": "Bochum",
                "AGS": "05911000",
                "Auskunftsart": "BAUAKTEN",
                "E-Mail": "bauakten@example.com",
            }
        ]
    )
    result = ImportService(db_session).import_jurisdictions(rows, MAPPING)
    assert result.updated == 1
    assert result.details[0].status == "UPDATED"


def test_contact_gap_report_groups_areas_but_keeps_services_separate(db_session):
    authority = setup_authority(db_session)
    for request_type in ("BAUAKTEN", "BAULASTEN"):
        for ags in ("05911000", "05913000"):
            make_jurisdiction(db_session, request_type, authority.authority_id, ags=ags)
    channel(db_session, authority)
    gaps = _contact_gaps(db_session)
    assert len(gaps) == 1
    assert gaps[0]["request_type_id"] == "BAULASTEN"
    assert gaps[0]["ags"] == "05911000,05913000"


def test_duplicate_merge_keeps_contact_evidence_for_manual_review(db_session):
    setup_authority(db_session)
    make_authority(db_session, name="Gleiches Amt", city=None)
    duplicate = make_authority(db_session, name="Gleiches Amt", city="Bochum")
    channel(db_session, duplicate)
    resolvable, review = _find_duplicate_authority_groups(db_session)
    assert not resolvable
    assert review


@pytest.fixture
def main_client(app_client, db_session):
    from app.main import app

    settings = AppSettings.get_or_create(db_session)
    settings.login_required = False
    db_session.commit()
    app.dependency_overrides[require_main] = lambda: None
    return app_client


def test_contact_review_requires_source_and_admin(main_client, db_session):
    from app.main import app

    authority = setup_authority(db_session)
    url = f"/api/authorities/{authority.authority_id}/email-contacts"
    payload = {
        "request_type_id": "BAUAKTEN",
        "value": "bauakten@example.com",
        "verified": True,
    }
    assert main_client.post(url, json=payload).status_code == 422
    payload["source_url"] = "https://www.bochum.de/test-leistung"
    result = main_client.post(url, json=payload)
    assert result.status_code == 201
    assert resolve(db_session, authority).can_send
    app.dependency_overrides.pop(require_main)
    assert main_client.post(url, json=payload).status_code == 403


def test_editing_contact_requires_new_explicit_review(main_client, db_session):
    authority = setup_authority(db_session)
    contact = channel(db_session, authority)
    response = main_client.put(
        f"/api/authorities/{authority.authority_id}/email-contacts/{contact.id}",
        json={
            "request_type_id": "BAUAKTEN",
            "value": "new@example.com",
            "verified": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["last_verified_at"] is None
    assert not resolve(db_session, authority).can_send


def test_review_preserves_long_source_url_separately_from_short_label(
    main_client, db_session
):
    authority = setup_authority(db_session)
    source_url = "https://www.bochum.de/" + "quellenpfad/" * 40
    response = main_client.post(
        f"/api/authorities/{authority.authority_id}/email-contacts",
        json={
            "request_type_id": "BAUAKTEN",
            "value": "bauakten@example.com",
            "source_url": source_url,
            "verified": True,
        },
    )
    assert response.status_code == 201, response.text
    contact = db_session.query(AuthorityContactChannel).one()
    assert contact.source_url == source_url
    assert len(contact.source) <= 255


def test_matching_reports_recipient_quality_separately_from_jurisdiction(
    main_client, db_session
):
    authority = setup_authority(db_session)
    building = make_building(db_session)
    for rt in ("BAUAKTEN", "BAULASTEN"):
        make_jurisdiction(
            db_session,
            rt,
            authority.authority_id,
            ags="05911000",
            matching_level="MUNICIPALITY",
        )
    channel(db_session, authority)
    response = main_client.post(
        "/api/matching",
        json={
            "building_id": building.building_id,
            "request_type_ids": ["BAUAKTEN", "BAULASTEN"],
        },
    )
    assert response.status_code == 200, response.text
    results = {r["request_type_id"]: r for r in response.json()["results"]}
    assert all(r["matching_status"] == "MATCHED" for r in results.values())
    assert results["BAUAKTEN"]["contact"]["can_send"]
    assert results["BAULASTEN"]["contact"]["status"] == "GENERAL_ONLY"


def make_case(db, authority):
    building = make_building(db)
    request = make_request(db, building.building_id)
    db.add(Case(case_id="CONTACT_CASE", name="Kontakt-Test"))
    db.commit()
    db.add_all(
        [
            CaseBuilding(case_id="CONTACT_CASE", building_id=building.building_id),
            CaseRequest(case_id="CONTACT_CASE", request_id=request.request_id),
        ]
    )
    db.commit()
    items = [
        make_request_item(
            db,
            request.request_id,
            rt,
            authority_id=authority.authority_id,
            document_status="GENERATED",
        )
        for rt in ("BAUAKTEN", "BAULASTEN")
    ]
    db.add_all(
        [
            RequestItemReference(
                request_item_id=item.request_item_id, aktenzeichen=f"CONTACT-{index}"
            )
            for index, item in enumerate(items)
        ]
    )
    db.commit()
    return request, items


@pytest.mark.parametrize("different", [False, True])
def test_bundle_refuses_missing_or_different_service_recipients(
    main_client, db_session, monkeypatch, different
):
    authority = setup_authority(db_session)
    _, items = make_case(db_session, authority)
    if different:
        channel(db_session, authority)
        channel(db_session, authority, "BAULASTEN", "baulasten@example.com")
    monkeypatch.setattr(
        "app.api.cases.send_email", lambda **kw: pytest.fail("Email must not be sent")
    )
    response = main_client.post(
        "/api/cases/CONTACT_CASE/send-bundle",
        json={"request_item_ids": [i.request_item_id for i in items]},
    )
    assert response.status_code == 400


def test_bundle_uses_reviewed_shared_service_recipient(
    main_client, db_session, monkeypatch, tmp_path
):
    authority = setup_authority(db_session)
    _, items = make_case(db_session, authority)
    for rt in ("BAUAKTEN", "BAULASTEN"):
        channel(db_session, authority, rt, "fachstelle@example.com")
    path = tmp_path / "test.docx"
    path.write_bytes(b"test attachment")
    document_emails = []

    def generate(*args, **kwargs):
        document_emails.append(kwargs["recipient_email"])
        return SimpleNamespace(filepath=str(path), filename="test.docx")

    sent = []
    monkeypatch.setattr(
        "app.api.cases.DocumentGenerationService.generate_document", generate
    )
    monkeypatch.setattr(
        "app.api.cases.send_email",
        lambda **kw: sent.append(kw)
        or SimpleNamespace(dry_run=True, mailgun_message_id=None),
    )
    response = main_client.post(
        "/api/cases/CONTACT_CASE/send-bundle",
        json={"request_item_ids": [i.request_item_id for i in items]},
    )
    assert response.status_code == 200, response.text
    assert sent[0]["to"] == "fachstelle@example.com"
    assert document_emails == ["fachstelle@example.com"] * 2


def test_case_and_csv_show_only_reviewed_service_email(main_client, db_session):
    authority = setup_authority(db_session)
    request, _ = make_case(db_session, authority)
    channel(db_session, authority)
    detail = main_client.get("/api/cases/CONTACT_CASE").json()
    emails = {i["request_type_id"]: i["authority_email"] for i in detail["items"]}
    assert emails == {"BAUAKTEN": "bauakten@example.com", "BAULASTEN": None}
    response = main_client.get(
        "/api/matching/export-csv", params={"request_ids": request.request_id}
    )
    rows = list(
        csv.DictReader(io.StringIO(response.text.lstrip("\ufeff")), delimiter=";")
    )
    assert {r["Behörde E-Mail"] for r in rows} == {"bauakten@example.com", ""}
    assert {r["Kontaktstatus"] for r in rows} == {"VERIFIED", "GENERAL_ONLY"}


def test_generated_documents_use_service_contact_not_shared_authority_email(
    main_client, db_session, monkeypatch, tmp_path
):
    authority = setup_authority(db_session)
    building = make_building(db_session)
    request = make_request(db_session, building.building_id)
    for rt in ("BAUAKTEN", "BAULASTEN"):
        make_request_item(
            db_session, request.request_id, rt, authority_id=authority.authority_id
        )
    channel(db_session, authority)
    recipients = {}

    def generate(self, building, authority, request_type, aktenzeichen, **kwargs):
        recipients[request_type.request_type_id] = kwargs["recipient_email"]
        return SimpleNamespace(
            filepath=str(tmp_path / "test.docx"), filename="test.docx"
        )

    monkeypatch.setattr(
        "app.api.documents.DocumentGenerationService.generate_document", generate
    )
    response = main_client.post(
        "/api/documents/generate", json={"request_id": request.request_id}
    )
    assert response.status_code == 200, response.text
    assert recipients == {"BAUAKTEN": "bauakten@example.com", "BAULASTEN": ""}
    assert {d["contact"]["status"] for d in response.json()["documents"]} == {
        "VERIFIED",
        "GENERAL_ONLY",
    }
