# -*- coding: utf-8 -*-
"""
NRW: Kontaktdaten-Vervollständigung für ERSCHLIESSUNG und BODENDENKMALSCHUTZ.

Ausgangslage (Datenqualitäts-Analyse 2026-10-07): In NRW ist jede Gemeinde bei
jeder Auskunftsart zugeordnet (4.356/4.356 Kombinationen MATCHED), aber bei
64 ERSCHLIESSUNG-Regeln und ~28 BODENDENKMALSCHUTZ-Behörden fehlen Anschrift,
E-Mail, Telefon und Webseite der zuständigen Stelle; 16 ERSCHLIESSUNG- und
3 BODENDENKMALSCHUTZ-Regeln sind nur AUTO_IMPORTED.

Die Daten stammen aus einer Web-Recherche (nur amtliche Seiten, jede Angabe
mit URL), siehe `erschliessung_nrw_kontakte.json` / `bodendenkmal_nrw_kontakte.json`.
Je Eintrag steht eine `action`:

  VERIFY     (nur ERSCHLIESSUNG) Amtliche Seite benennt die Stelle ausdrücklich:
             Authority-Kontaktdaten ergänzen; war die Regel AUTO_IMPORTED oder
             die gespeicherte Stelle weicht ab, wird die Authority umbenannt und
             die Regel auf VERIFIED gesetzt (Quelle = amtliche URL).
  UPGRADE    (nur BODENDENKMALSCHUTZ) wie VERIFY, aber ohne Umbenennung.
  FILL       Nur leere Kontaktfelder ergänzen; Name und Status bleiben.
  GENERIC    (nur ERSCHLIESSUNG, AUTO_IMPORTED) keine amtliche Seite stützt die
             gespeicherte Abteilung -> zurück auf die allgemeine Stadt-/
             Gemeindeverwaltung (Gemeinde ist nach § 127 BauGB zuständig), mit
             Anschrift der Verwaltung. Status bleibt AUTO_IMPORTED.
  ADDR_ONLY  Zuständigkeit der Abteilung nicht bestätigt; nur die amtliche
             Anschrift der Verwaltung in leere Felder ergänzen.
  NONE       Nichts ändern (nicht belegbar).

Sicherheitsprinzipien (Mandat):
  * Nur leere Felder werden gefüllt - vorhandene Werte werden NIE überschrieben
    (Abweichungen werden als KONFLIKT gemeldet).
  * Allgemeine Verwaltungs-E-Mails stehen nie als Abteilungs-Kontakt in einem
    Datensatz einer bestätigten Abteilung; nur bei GENERIC (Authority ist die
    Verwaltung selbst).
  * Jeder Eintrag trägt den erwarteten Authority-Namen; passt der Name in der
    Ziel-DB nicht, wird der Eintrag übersprungen (schützt vor ID-/Stand-
    Abweichungen zwischen lokaler und produktiver DB).
  * Standard ist ein DRY-RUN; geschrieben wird nur mit --apply.
  * Idempotent: ein zweiter Lauf ändert nichts mehr.

Aufruf (DATABASE_URL zeigt auf die Ziel-DB):
  python scripts/complete_nrw_kontakte.py                 # Trockenlauf, beide Auskunftsarten
  python scripts/complete_nrw_kontakte.py --apply         # schreiben
  python scripts/complete_nrw_kontakte.py --only erschliessung|bodendenkmal
"""
import argparse
import difflib
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

REVIEWER = (
    "Claude (Recherche-Sitzung 2026-10-07, NRW Kontaktdaten-Vervollständigung "
    "Erschließung/Bodendenkmalschutz, nur amtliche Quellen)"
)
STAMP = "2026-10-07"
CONTACT_FIELDS = ("street", "house_number", "postal_code", "city", "email", "phone", "website")


def _fold(text):
    text = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _short_city(gemeinde):
    name = (gemeinde or "").split(",")[0].strip()
    return re.sub(r"\s*\(.*?\)\s*$", "", name).strip()


def _append_note(current, line):
    current = current or ""
    if line in current:
        return current
    return (current + "\n" + line).strip()


def _fill(authority, field, value, changes, conflicts):
    if not value:
        return
    existing = getattr(authority, field)
    if not existing:
        setattr(authority, field, value)
        changes.append(f"{field}={value}")
    elif _fold(str(existing)) != _fold(str(value)):
        conflicts.append(f"{field}: DB '{existing}' <> Recherche '{value}' (nicht überschrieben)")


def _fill_address(authority, addr, changes, conflicts):
    if not addr:
        return
    # Nur füllen, wenn die Straße noch leer ist: vermeidet gemischte Adressen.
    if authority.street:
        stored = _fold(f"{authority.street} {authority.house_number or ''}")
        new = _fold(f"{addr.get('street', '')} {addr.get('house_number', '')}")
        if stored and new and stored != new:
            conflicts.append(
                f"Anschrift: DB '{authority.street} {authority.house_number or ''}' <> "
                f"Recherche '{addr.get('street')} {addr.get('house_number')}' (nicht überschrieben)"
            )
        # PLZ/Ort ergänzen, falls dort noch leer
        _fill(authority, "postal_code", addr.get("postal_code"), changes, conflicts)
        _fill(authority, "city", addr.get("city"), changes, conflicts)
        return
    _fill(authority, "street", addr.get("street"), changes, conflicts)
    _fill(authority, "house_number", addr.get("house_number"), changes, conflicts)
    _fill(authority, "postal_code", addr.get("postal_code"), changes, conflicts)
    _fill(authority, "city", addr.get("city"), changes, conflicts)


def _rules_for(db, kind, entry):
    from app.models.jurisdiction import Jurisdiction

    q = db.query(Jurisdiction).filter(Jurisdiction.active.is_(True), Jurisdiction.valid_to.is_(None))
    if kind == "erschliessung":
        return q.filter(Jurisdiction.request_type_id == "ERSCHLIESSUNG", Jurisdiction.ags == entry["ags"]).all()
    return q.filter(
        Jurisdiction.request_type_id == "BODENDENKMALSCHUTZ",
        Jurisdiction.authority_id == entry["authority_id"],
    ).all()


def process_entry(db, kind, entry, apply_changes, now):
    """Plant bzw. wendet einen Eintrag an. Gibt einen Report-Dict zurück."""
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction

    label = entry.get("gemeinde") or entry.get("authority_name")
    report = {"label": label, "action": entry["action"], "result": "", "changes": [], "conflicts": []}
    action = entry["action"]
    if action == "NONE":
        report["result"] = "keine Änderung (nicht belegbar)"
        return report

    rules = _rules_for(db, kind, entry)
    if not rules:
        report["result"] = "ÜBERSPRUNGEN: keine aktive Regel gefunden"
        return report
    authority_ids = {r.authority_id for r in rules}
    if len(authority_ids) != 1:
        report["result"] = f"ÜBERSPRUNGEN: {len(authority_ids)} verschiedene Authorities an den Regeln"
        return report
    authority = db.query(Authority).filter(Authority.authority_id == next(iter(authority_ids))).one()
    already_processed = f"[{STAMP}] Kontaktdaten ergänzt" in (authority.notes or "")
    if not already_processed and _fold(authority.authority_name) != _fold(entry["expected_name"]):
        report["result"] = f"ÜBERSPRUNGEN: Name weicht ab (DB: '{authority.authority_name}')"
        return report

    changes, conflicts = report["changes"], report["conflicts"]
    other_refs = (
        db.query(Jurisdiction)
        .filter(Jurisdiction.authority_id == authority.authority_id, Jurisdiction.active.is_(True))
        .count()
    )
    shared = other_refs > len(rules)
    sources = []
    new_status = None
    rename_to = None

    if action in ("VERIFY", "UPGRADE", "FILL"):
        _fill_address(authority, entry.get("address"), changes, conflicts)
        for f in ("email", "phone", "website"):
            _fill(authority, f, entry.get(f), changes, conflicts)
        if entry.get("evidence_url"):
            sources.append(entry["evidence_url"])
    elif action == "GENERIC":
        central = entry["central"]
        _fill_address(authority, central, changes, conflicts)
        _fill(authority, "email", central.get("email"), changes, conflicts)
        _fill(authority, "phone", central.get("phone"), changes, conflicts)
        _fill(authority, "website", central.get("website"), changes, conflicts)
        sources.append(central.get("url"))
    elif action == "ADDR_ONLY":
        central = entry["central"]
        _fill_address(authority, central, changes, conflicts)
        sources.append(central.get("url"))

    if action == "VERIFY":
        stored_status = rules[0].verification_status
        stored_unit = authority.authority_name.split(" - ", 1)[-1]
        ratio = difflib.SequenceMatcher(None, _fold(stored_unit), _fold(entry["unit_name"])).ratio()
        if stored_status != "VERIFIED" or ratio < 0.35:
            if shared:
                changes.append("(Umbenennung übersprungen: Authority wird von weiteren Regeln genutzt)")
            else:
                prefix = authority.authority_name.split(" - ", 1)[0] if " - " in authority.authority_name else (
                    "Stadtverwaltung " + _short_city(entry["gemeinde"]))
                rename_to = f"{prefix} - {entry['unit_name']}"
                new_status = "VERIFIED"
        if stored_status != "VERIFIED" and new_status is None and not shared:
            new_status = "VERIFIED"
    elif action == "UPGRADE":
        if rules[0].verification_status != "VERIFIED":
            new_status = "VERIFIED"
    elif action == "GENERIC":
        generic_name = f"Stadtverwaltung {_short_city(entry['gemeinde'])} - Rathaus (allgemeine Verwaltung)"
        if "allgemeine verwaltung" not in _fold(authority.authority_name) and not shared:
            rename_to = generic_name

    if rename_to and rename_to != authority.authority_name:
        changes.append(f"authority_name: '{authority.authority_name}' -> '{rename_to}'")
        authority.authority_name = rename_to
        if action == "GENERIC":
            authority.department_name = None

    if changes and sources:
        note = f"[{STAMP}] Kontaktdaten ergänzt aus amtlichen Seiten: " + "; ".join(s for s in sources if s)
        authority.notes = _append_note(authority.notes, note)
        if not authority.source:
            authority.source = f"Amtliche Webseite: {sources[0]}"
        authority.last_verified_at = now
        authority.verified_by = REVIEWER

    # Regel-Update (Quelle/Status) nur bei Statuswechsel bzw. Neubenennung/GENERIC
    for rule in rules:
        rule_changed = False
        if new_status and rule.verification_status != new_status:
            changes.append(f"Regel {rule.ags or ''} Status {rule.verification_status} -> {new_status}")
            rule.verification_status = new_status
            rule_changed = True
        if (rename_to or new_status) and entry.get("evidence_url") and action in ("VERIFY", "UPGRADE"):
            quote = (entry.get("evidence_quote") or "").strip()
            rule.source = f"{authority.authority_name} - {quote}"[:2000]
            rule.source_url = entry["evidence_url"]
            rule_changed = True
        elif action == "GENERIC" and (rename_to or changes):
            central_url = entry["central"].get("url")
            rule.source = (
                f"{authority.authority_name} - keine amtliche Seite benennt eine spezielle Stelle für "
                f"Erschließungsbeiträge; Gemeinde ist nach § 127 BauGB beitragsberechtigt "
                f"(Verwaltungs-Kontakt: {central_url})"
            )[:2000]
            if central_url:
                rule.source_url = central_url
            rule_changed = True
        if rule_changed:
            rule.last_verified_at = now
            rule.verified_by = REVIEWER
            rule.notes = _append_note(
                rule.notes,
                f"[{STAMP}] NRW-Kontaktdaten-Vervollständigung (siehe docs/ABSCHLUSSBERICHT_DATENQUALITAET.md)",
            )

    if entry.get("review_note"):
        report["conflicts"].append("HINWEIS: " + entry["review_note"])
    report["result"] = "geändert" if changes else "bereits vollständig (keine Änderung)"
    return report


def run(db, kinds, apply_changes):
    now = datetime.utcnow()
    all_reports = []
    for kind in kinds:
        path = os.path.join(HERE, f"{kind}_nrw_kontakte.json")
        with open(path, encoding="utf-8") as fh:
            entries = json.load(fh)
        for entry in entries:
            all_reports.append((kind, process_entry(db, kind, entry, apply_changes, now)))
    if apply_changes:
        db.commit()
    else:
        db.rollback()
    return all_reports


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Änderungen schreiben (Standard: Trockenlauf)")
    parser.add_argument("--only", choices=["erschliessung", "bodendenkmal"])
    args = parser.parse_args()

    from app.database.engine import SessionLocal, engine

    target = engine.url.render_as_string(hide_password=True)
    print(f"Ziel-Datenbank: {target}")
    print("Modus:", "APPLY (schreibt)" if args.apply else "DRY-RUN (rollback)")
    kinds = [args.only] if args.only else ["erschliessung", "bodendenkmal"]
    db = SessionLocal()
    try:
        reports = run(db, kinds, args.apply)
    finally:
        db.close()

    counts = {}
    for kind, rep in reports:
        counts[(kind, rep["result"].split(":")[0])] = counts.get((kind, rep["result"].split(":")[0]), 0) + 1
        print(f"\n[{kind}] {rep['label']} ({rep['action']}): {rep['result']}")
        for ch in rep["changes"]:
            print("   +", ch)
        for cf in rep["conflicts"]:
            print("   !", cf)
    print("\nZusammenfassung:")
    for (kind, res), n in sorted(counts.items()):
        print(f"  {kind:14s} {res:45s} {n}")


if __name__ == "__main__":
    main()
