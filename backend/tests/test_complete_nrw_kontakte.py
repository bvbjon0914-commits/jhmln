# -*- coding: utf-8 -*-
"""Tests für scripts/complete_nrw_kontakte.py (nur leere Felder füllen, idempotent, Namens-Schutz)."""
import importlib.util
import os
import uuid
from datetime import datetime

from app.models.authority import Authority
from app.models.jurisdiction import Jurisdiction

_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "complete_nrw_kontakte.py")
_spec = importlib.util.spec_from_file_location("complete_nrw_kontakte", _SCRIPT)
script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(script)

NOW = datetime(2026, 10, 7)


def _make_rule(db, name, status="AUTO_IMPORTED", ags="05158016", request_type="ERSCHLIESSUNG", **auth_fields):
    authority = Authority(
        authority_id=str(uuid.uuid4()), authority_name=name, authority_type="Kommune",
        state="Nordrhein-Westfalen", active=True, **auth_fields,
    )
    db.add(authority)
    db.flush()
    rule = Jurisdiction(
        jurisdiction_id=str(uuid.uuid4()), request_type_id=request_type, authority_id=authority.authority_id,
        country="DE", state="Nordrhein-Westfalen", ags=ags, matching_level="MUNICIPALITY", priority=40,
        verification_status=status, active=True,
    )
    db.add(rule)
    db.commit()
    return authority, rule


def _entry(**over):
    entry = {
        "ags": "05158016", "gemeinde": "Hilden, Stadt", "expected_name": "Stadtverwaltung Hilden - Tiefbauamt",
        "verdict": "CONFIRMED_UNIT", "action": "VERIFY", "unit_name": "Bauverwaltungsamt",
        "address": {"street": "Am Rathaus", "house_number": "1", "postal_code": "40721", "city": "Hilden"},
        "email": "bauverwaltung@hilden.de", "phone": "02103 72-601", "website": None,
        "evidence_url": "https://service.hilden.info/?d=2088", "evidence_quote": "Zuständige Stelle: Bauverwaltungsamt",
        "central": None, "review_note": None,
    }
    entry.update(over)
    return entry


def test_verify_fills_renames_and_upgrades_auto_imported(db_session):
    authority, rule = _make_rule(db_session, "Stadtverwaltung Hilden - Tiefbauamt")
    report = script.process_entry(db_session, "erschliessung", _entry(), True, NOW)
    db_session.commit()
    db_session.refresh(authority)
    db_session.refresh(rule)
    assert report["result"] == "geändert"
    assert authority.authority_name == "Stadtverwaltung Hilden - Bauverwaltungsamt"
    assert authority.street == "Am Rathaus" and authority.email == "bauverwaltung@hilden.de"
    assert rule.verification_status == "VERIFIED"
    assert rule.source_url == "https://service.hilden.info/?d=2088"


def test_second_run_changes_nothing(db_session):
    _make_rule(db_session, "Stadtverwaltung Hilden - Tiefbauamt")
    script.process_entry(db_session, "erschliessung", _entry(), True, NOW)
    db_session.commit()
    report = script.process_entry(db_session, "erschliessung", _entry(), True, NOW)
    assert report["result"].startswith("bereits vollständig")
    assert report["changes"] == []


def test_existing_values_never_overwritten(db_session):
    authority, _ = _make_rule(
        db_session, "Stadtverwaltung Hilden - Bauverwaltungsamt", status="VERIFIED",
        street="Alte Straße", house_number="9", email="alt@hilden.de",
    )
    entry = _entry(expected_name="Stadtverwaltung Hilden - Bauverwaltungsamt")
    report = script.process_entry(db_session, "erschliessung", entry, True, NOW)
    db_session.commit()
    db_session.refresh(authority)
    assert authority.street == "Alte Straße" and authority.email == "alt@hilden.de"
    assert any("nicht überschrieben" in c for c in report["conflicts"])


def test_name_mismatch_is_skipped(db_session):
    authority, _ = _make_rule(db_session, "Völlig anderer Name")
    report = script.process_entry(db_session, "erschliessung", _entry(), True, NOW)
    db_session.refresh(authority)
    assert report["result"].startswith("ÜBERSPRUNGEN")
    assert authority.street is None


def test_generic_reverts_to_administration_without_upgrading(db_session):
    authority, rule = _make_rule(db_session, "Stadtverwaltung Wuelfrath - Tiefbauamt (Amt 66)", ags="05158036")
    entry = _entry(
        ags="05158036", gemeinde="Wülfrath, Stadt", expected_name="Stadtverwaltung Wuelfrath - Tiefbauamt (Amt 66)",
        action="GENERIC", verdict="NO_EXPLICIT_UNIT", unit_name=None, address=None, email=None, phone=None,
        evidence_url=None, evidence_quote=None,
        central={"street": "Am Rathaus", "house_number": "1", "postal_code": "42489", "city": "Wülfrath",
                 "email": "verwaltung@stadt.wuelfrath.de", "phone": None, "website": None, "url": "https://www.wuelfrath.net/"},
    )
    script.process_entry(db_session, "erschliessung", entry, True, NOW)
    db_session.commit()
    db_session.refresh(authority)
    db_session.refresh(rule)
    assert authority.authority_name == "Stadtverwaltung Wülfrath - Rathaus (allgemeine Verwaltung)"
    assert authority.email == "verwaltung@stadt.wuelfrath.de"
    assert rule.verification_status == "AUTO_IMPORTED"
    assert "§ 127 BauGB" in rule.source


def test_addr_only_does_not_touch_status_or_email(db_session):
    authority, rule = _make_rule(db_session, "Kreis Herford - Obere Denkmalbehörde", status="VERIFIED",
                                 ags="05758", request_type="BODENDENKMALSCHUTZ")
    entry = {
        "authority_id": authority.authority_id, "expected_name": "Kreis Herford - Obere Denkmalbehörde",
        "action": "ADDR_ONLY", "verdict": "OFFEN", "unit_name": None, "address": None, "email": None,
        "phone": None, "website": None, "evidence_url": None, "evidence_quote": None, "review_note": None,
        "central": {"street": "Amtshausstraße", "house_number": "3", "postal_code": "32051", "city": "Herford",
                    "email": "info@kreis-herford.de", "url": "https://www.kreis-herford.de/"},
    }
    script.process_entry(db_session, "bodendenkmal", entry, True, NOW)
    db_session.commit()
    db_session.refresh(authority)
    assert authority.street == "Amtshausstraße"
    assert authority.email is None
    assert rule.verification_status == "VERIFIED"


def test_data_files_are_consistent():
    import json
    base = os.path.dirname(_SCRIPT)
    for name in ("erschliessung_nrw_kontakte.json", "bodendenkmal_nrw_kontakte.json"):
        with open(os.path.join(base, name), encoding="utf-8") as fh:
            entries = json.load(fh)
        assert entries
        for e in entries:
            assert e["action"] in {"VERIFY", "UPGRADE", "FILL", "GENERIC", "ADDR_ONLY", "NONE"}
            assert e["expected_name"]
            if e["action"] in {"VERIFY", "UPGRADE"}:
                assert e["evidence_url"], e
            for url in (e.get("evidence_url"), (e.get("central") or {}).get("url")):
                assert url is None or url.startswith(("https://", "http://"))
            # allgemeine Verwaltungs-E-Mails dürfen nicht als Abteilungs-E-Mail gespeichert sein
            local = (e.get("email") or "").split("@")[0].lower()
            assert local not in {"info", "poststelle", "rathaus", "post", "kreisverwaltung", "stadtverwaltung"}, e
