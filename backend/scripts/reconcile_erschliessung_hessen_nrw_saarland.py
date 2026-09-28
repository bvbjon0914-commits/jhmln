# -*- coding: utf-8 -*-
"""
Einmaliger Abgleich (analog zu reconcile_erschliessung_stadtstaaten.py):
ersetzt die generischen ERSCHLIESSUNG-Regeln fuer die AGS, die von einer
parallelen Session bereits einzeln recherchiert wurden, durch die
praeziseren Regeln - fuer HESSEN, NORDRHEIN-WESTFALEN und SAARLAND.

Ausgangslage nach dem Merge von civeloq/authority-data-quality (commit
9ca366b, "Saarlouis/BW-Kataster fixes + per-Gemeinde Erschliessung
Berlin/Bremen/Hamburg/Saarland/Hessen/NRW"): es existieren zwei parallel
entstandene ERSCHLIESSUNG-Regelsaetze (matching_level=MUNICIPALITY) mit
teilweiser AGS-Ueberschneidung.

1. GENERISCH (bereits in der echten DB angewendet, committed VOR dem Merge):
   seed_erschliessung_amtsfrei_{hessen,nrw,saarland}.py - je Gemeinde nur
   "§ 127 Abs. 1 BauGB" zitiert, Authority-Name
   "<Gemeinde> - Gemeindeverwaltung (Erschließungsbeiträge)". Deckt
   VOLLSTAENDIG ab: Hessen 421/421, NRW 396/396, Saarland 52/52 Gemeinden.

2. PRAEZISER, einzeln recherchiert (aus der gemergten Peer-Session, NOCH
   NICHT in der echten DB angewendet - nur als Skript vorhanden):
   seed_erschliessung_{hessen,nrw,saarland}.py - je Gemeinde konkretes
   Bauamt/Bauverwaltung/Eigenbetrieb recherchiert und woertlich zitiert,
   teils mit gestaffeltem verification_status (Saarland/NRW: VERIFIED vs.
   AUTO_IMPORTED je nach Beleglage). Deckt TEILWEISE ab: Hessen 8/421,
   NRW 64/396, Saarland 52/52 (aber mit ehrlicherer Differenzierung).

Fuer jede AGS, die in BEIDEN Regelsaetzen vorkommt (= exakt die AGS-Menge
von Regelsatz 2, siehe Pruefung unten - Regelsatz 1 deckt in allen drei
Laendern 100 % ab, ist also immer eine Obermenge), wird hier die
praezisere Regel freigegeben und loest damit automatisch die generische
Regel ab: approve_entry() erkennt den bestehenden generischen Eintrag als
CONTRADICTS_VERIFIED (er ist VERIFIED und < 365 Tage alt) und setzt bei
Freigabe automatisch dessen valid_to (Historie bleibt erhalten, siehe
app/services/jurisdiction_staging.py Zeile ~228-245). Es wird daher
bewusst JEDER nicht-exakte Konflikt freigegeben (nicht nur NEW) - das ist
der Kern dieses Skripts, anders als die staged-Skripte 2 selbst, die nur
NEW freigeben und einen bestehenden Konflikt unangetastet liegen lassen
wuerden.

Fuer AGS, die NUR in Regelsatz 1 vorkommen (der Grossteil bei Hessen/NRW),
bleibt die generische Regel unveraendert bestehen - keine bessere
Alternative vorhanden, das ist korrekt und wird hier nicht angefasst.

Importiert ENTRIES/GEMEINDEN direkt aus den drei seed_erschliessung_*.py-
Dateien, um keine Daten zu duplizieren; die Authority-Anlage- und
stage_entry()-Aufrufe spiegeln bewusst exakt die Logik der jeweiligen
Original-Skripte (Suchschluessel, Lizenztext, verification_status-Logik),
damit die entstehenden Regeln inhaltlich identisch zu einem direkten Lauf
dieser Skripte waeren - nur eben mit Freigabe auch bei Konflikt.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REVIEWER = (
    "Claude (Recherche-Sitzung 2026-09-28, Abgleich Erschließung Hessen/NRW/Saarland "
    "nach Merge: präzisere Einzelrecherche löst generische §127-BauGB-Sammelregel ab)"
)


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService
    from seed_erschliessung_hessen import ENTRIES as HESSEN_ENTRIES
    from seed_erschliessung_nrw import GEMEINDEN as NRW_GEMEINDEN
    from seed_erschliessung_saarland import GEMEINDEN as SAARLAND_GEMEINDEN

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"reconcile-erschliessung-hessen-nrw-saarland-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []  # (entry, state_label, review_note, resulting_verification_status)

        # -- Hessen: ENTRIES-Liste, alle VERIFIED, Authority-Suchschluessel (name, city) --
        for item in HESSEN_ENTRIES:
            authority = (
                db.query(Authority)
                .filter(Authority.authority_name == item["authority_name"], Authority.city == item["city"])
                .first()
            )
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=item["authority_name"],
                    authority_type="Kommunale Beitragsstelle",
                    department_name=item["department_name"],
                    street=item["street"], house_number=None, postal_code=item["plz"], city=item["city"],
                    state="Hessen", phone=item["phone"], email=item["email"],
                    source="Hessen ERSCHLIESSUNG-Import 2026-09, amtliche Webseite: " + item["source_url"],
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Abgleich Erschließung Hessen - {item['authority_name']}",
                request_type_id="ERSCHLIESSUNG", state="Hessen", ags=item["ags"], municipality=item["muni"],
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{item['authority_name']} - {item['quote']}", source_url=item["source_url"],
                source_license="Amtliche Webseite der jeweiligen Kommune",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, "Hessen", item["quote"], "VERIFIED"))

        # -- NRW: GEMEINDEN-Dict (ags -> info), Authority-Suchschluessel (name, city) --
        for ags, info in NRW_GEMEINDEN.items():
            authority = (
                db.query(Authority)
                .filter(Authority.authority_name == info["authority_name"], Authority.city == info["city"])
                .first()
            )
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=info["authority_name"],
                    authority_type=info["authority_type"],
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Nordrhein-Westfalen", phone=info["phone"], email=info["email"],
                    source="Recherche-Sitzung 2026-09-28 (amtliche Stadt-/Gemeinde-Webseite, "
                           "siehe jurisdictions.source_url der zugehörigen Regel)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            quote = info["quote"]
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Abgleich Erschließung NRW - {info['name']}",
                request_type_id="ERSCHLIESSUNG", state="Nordrhein-Westfalen", ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{info['authority_name']} — {quote}",
                source_url=info["source_url"],
                source_license=(
                    "Kommunale Webseite (amtliche Stadt-/Gemeindeverwaltung, Recherche-Sitzung 2026-09-28)"
                    if info["verification_status"] == "VERIFIED"
                    else "Kommunale Webseite (allgemeiner Bauamt-/Gemeindeverwaltungs-Fallback bzw. "
                         "nur Seitentitel-Bestaetigung, Recherche-Sitzung 2026-09-28)"
                ),
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, "NRW", quote, info["verification_status"]))

        # -- Saarland: GEMEINDEN-Dict (ags -> info), Authority-Suchschluessel (name, city) --
        FALLBACK_NOTE = (
            "Keine amtliche Seite benennt eine speziell fuer Erschliessungsbeitraege "
            "zustaendige Stelle woertlich; als Fallback wird das zustaendige allgemeine "
            "Bauamt/die Gemeindeverwaltung gefuehrt, ausdruecklich ohne vorgetaeuschte "
            "Spezifitaet - siehe source_url."
        )
        for ags, info in SAARLAND_GEMEINDEN.items():
            authority = (
                db.query(Authority)
                .filter(Authority.authority_name == info["authority_name"], Authority.city == info["city"])
                .first()
            )
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=info["authority_name"],
                    authority_type=info["authority_type"],
                    street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                    state="Saarland", phone=info["phone"], email=info["email"],
                    source="Recherche-Sitzung 2026-09-28 (amtliche Gemeinde-Webseite bzw. service.saarland.de, "
                           "siehe jurisdictions.source_url der zugehörigen Regel)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            quote = info["quote"] or FALLBACK_NOTE
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"Abgleich Erschließung Saarland - {info['name']}",
                request_type_id="ERSCHLIESSUNG", state="Saarland", ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{info['authority_name']} — {quote}",
                source_url=info["source_url"],
                source_license=(
                    "Kommunale Webseite (amtliche Gemeinde-/Stadtverwaltung, Recherche-Sitzung 2026-09-28)"
                    if info["verification_status"] == "VERIFIED"
                    else "Kommunale Webseite (allgemeiner Bauamt-/Gemeindeverwaltungs-Fallback, "
                         "Recherche-Sitzung 2026-09-28)"
                ),
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, "Saarland", quote, info["verification_status"]))

        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        by_conflict = {}
        for entry, state_label, _, _ in staged:
            by_conflict[entry.conflict_type] = by_conflict.get(entry.conflict_type, 0) + 1
        print(f"Konflikt-Verteilung: {by_conflict}")
        for entry, state_label, _, _ in staged:
            print(f"  #{entry.id} [{state_label}] ags={entry.ags} - {entry.conflict_type}: {entry.conflict_reason}")

        # Bewusst ALLE Eintraege freigeben (auch CONTRADICTS_VERIFIED) - reviewte
        # Ablösung der generischen §127-BauGB-Sammelregel durch die praeziseren,
        # einzeln recherchierten Regeln. DUPLICATE_EXACT waere ein Fehler hier, da
        # sich die Authority-Namen zwischen generischer und praeziser Regel immer
        # unterscheiden - wird also nicht erwartet, aber defensiv uebersprungen.
        approved = 0
        by_state_status = {}
        for entry, state_label, note, status in staged:
            if entry.conflict_type == "DUPLICATE_EXACT":
                print(f"  ÜBERSPRUNGEN (exaktes Duplikat) #{entry.id}")
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=note,
                resulting_verification_status=status,
            )
            approved += 1
            key = (state_label, status)
            by_state_status[key] = by_state_status.get(key, 0) + 1
        db.commit()
        print(f"\n{approved} Regeln freigegeben (alte widersprochene generische Regeln automatisch "
              f"abgelöst/valid_to gesetzt).")
        for (state_label, status), n in sorted(by_state_status.items()):
            print(f"  {state_label}: {status}={n}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
