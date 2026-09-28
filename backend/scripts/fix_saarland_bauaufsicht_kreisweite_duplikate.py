"""
Löst drei fälschlich auf eine einzelne Gemeinde-AGS gepinnte
BAUAKTEN/BAULASTEN-Regeln in Saarland ab, die denselben Bug zeigen wie der
zuvor behobene Saarlouis-Fall: eine kreisweite Untere Bauaufsichtsbehörde
war technisch auf matching_level=MUNICIPALITY + die AGS der Kreisstadt
gepinnt, statt auf matching_level=COUNTY + die Kreis-AGS.

Für alle drei Fälle existiert bereits eine korrekt auf COUNTY-Ebene
gescopte Regel für dieselbe reale Behörde (angelegt durch den heutigen
Import aus dem "Amtlichen Anschriftenverzeichnis der Gemeinde- und
Stadtverwaltungen", Stand 31.01.2026) - die Korrektur ist daher reines
Ablösen der alten, falsch gescopten Regel, kein Neuanlegen (dieselbe
"expire-only"-Logik wie beim Saarlouis-Fix, inklusive derselben
Feld-Konvention - siehe unten).

Amtlich geprüft (2026-09-28, WebFetch der jeweiligen offiziellen Seite):

1. Landkreis Neunkirchen (BAUAKTEN-Regel b653bcf0, BAULASTEN-Regel
   424f62ff, authority_id b8479696 "Landkreis Neunkirchen – Untere
   Bauaufsichtsbehörde", faelschlich MUNICIPALITY/10043114 = AGS der
   Kreisstadt, Anschrift "Oberer Markt 16, Neunkirchen" identisch mit der
   Kreisstadt-eigenen Behoerde und derselben E-Mail kreisstadt@neunkirchen.de
   - erkennbar ein Dubletten-/Zuordnungsfehler aus dem urspruenglichen
   Bulk-Import "Bauaemter Datenbank Deutschland FINAL 20260831", keine
   eigenstaendige zweite Adresse).
   Amtliche Quelle https://www.landkreis-neunkirchen.de/bauen-wohnen/untere-bauaufsichtsbehoerde
   bestaetigt woertlich: "Die Untere Bauaufsichtsbehoerde ist oertlich
   zustaendig fuer den gesamten Bereich des Landkreises Neunkirchen mit
   Ausnahme der Kreisstadt Neunkirchen, die eine eigene Untere
   Bauaufsichtsbehoerde unterhaelt" - UND nennt als Anschrift der
   Kreis-Behoerde "Wilhelm-Heinrich-Str. 36, 66564 Ottweiler", was exakt
   der bereits vorhandenen COUNTY-Regel (ags=10043, authority_id
   383adf46) entspricht. Die Kreisstadt-eigene Regel (authority_id
   65ad8038, MUNICIPALITY/10043114) bleibt unveraendert aktiv - sie ist
   die durch dieselbe Quelle bestaetigte, tatsaechlich eigenstaendige
   Behoerde.

2. Landkreis Merzig-Wadern (BAUAKTEN-Regel 48067053, BAULASTEN-Regel
   e039d2d6, authority_id e7b4e021 "Landkreis Merzig-Wadern – Untere
   Bauaufsichtsbehoerde", faelschlich MUNICIPALITY/10042113 = AGS der
   Kreisstadt Merzig). Merzig gehoert NICHT zu den 6 saarlaendischen
   Staedten mit eigener Bauaufsichtsbehoerde nach ZustV-LBO - die
   Zustaendigkeit liegt fuer den gesamten Kreis inkl. Kreisstadt beim
   Landkreis. Amtliche Quelle
   https://www.merzig-wadern.de/Verwaltung-Politik/Bauen/Untere-Bauaufsicht/
   bestaetigt die Anschrift "Bahnhofstrasse 44, 66663 Merzig" - identisch
   mit der Anschrift der bereits vorhandenen COUNTY-Regel (ags=10042,
   authority_id 0fadb002). Dieselbe reale Behoerde, zweimal in der
   Datenbank (einmal korrekt auf COUNTY, einmal faelschlich auf
   MUNICIPALITY gescoped).

3. Landkreis St. Wendel (BAUAKTEN-Regel 14a393c2, BAULASTEN-Regel
   c4d1356d, authority_id a19781ce "Landkreis St. Wendel – Untere
   Bauaufsichtsbehoerde", faelschlich MUNICIPALITY/10046117 = AGS der
   Kreisstadt St. Wendel, mit der veralteten/falschen Anschrift
   "Rathausplatz 1"). St. Wendel gehoert ebenfalls nicht zu den 6
   Staedten mit eigener Bauaufsichtsbehoerde. Amtliche Quelle
   https://service.saarland.de/portaldeeplink?tsa_oe_id=100084009&tsa_sprache=de_DE
   (Leistungsuebersicht "Landkreis Sankt Wendel - Untere Bauaufsicht")
   bestaetigt die Anschrift "Mommstrasse 21-31, 66606 St. Wendel,
   Kreisstadt" - identisch mit der Anschrift der bereits vorhandenen
   COUNTY-Regel (ags=10046, authority_id cd1639b3), NICHT mit
   "Rathausplatz 1".

Abgeloest ueber valid_to=gestern (active bleibt True) statt geloescht oder
active=False gesetzt - dieselbe Konvention wie
JurisdictionStagingService.approve_entry() beim Abloesen einer
widersprochenen Regel (siehe jurisdiction_staging.py Zeile ~240) und wie
beim parallel angewendeten Saarlouis-Fix in einem anderen Worktree: die
Regel war bis gestern korrekt gueltig, wird durch die bereits vorhandene
COUNTY-Regel abgeloest, nicht als von Anfang an falsch zurueckgenommen
(dafuer steht active=False, siehe revert_erschliessung_leiningerland.py -
hier nicht einschlaegig). Die Authority-Zeilen selbst bleiben unveraendert
bestehen. Zielgenau ueber jurisdiction_id statt ueber eine generische
Bedingung, um ausschliesslich die hier einzeln geprueften sechs Regeln zu
treffen.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "claude-data-quality-session"

JURISDICTION_IDS_TO_EXPIRE = {
    "b653bcf0-e485-45cd-863b-d3d476cef385": (
        "Abgeloest: kreisweite Behoerde 'Landkreis Neunkirchen - Untere Bauaufsichtsbehoerde' "
        "war faelschlich auf die Gemeinde-AGS der Kreisstadt (10043114) statt auf die Kreis-AGS "
        "(10043, matching_level=COUNTY) gescoped - identischer Bug wie beim zuvor behobenen "
        "Saarlouis-Fall. Amtlich bestaetigt via "
        "https://www.landkreis-neunkirchen.de/bauen-wohnen/untere-bauaufsichtsbehoerde: "
        "Kreisstadt Neunkirchen hat eine eigene Untere Bauaufsichtsbehoerde (bleibt als "
        "separate Regel aktiv), die Landkreis-Behoerde sitzt in Ottweiler und ist bereits "
        "korrekt als COUNTY-Regel (ags=10043, authority_id 383adf46) vorhanden - diese "
        "MUNICIPALITY-Regel ist redundant/falsch gescoped."
    ),
    "424f62ff-9fd6-489c-b1bd-79f9e64c34c9": (
        "Abgeloest: siehe Begruendung fuer BAUAKTEN-Regel b653bcf0 (identischer Fall, "
        "BAULASTEN statt BAUAKTEN)."
    ),
    "48067053-cc5d-461a-bc33-5c09f5d8bba8": (
        "Abgeloest: kreisweite Behoerde 'Landkreis Merzig-Wadern - Untere Bauaufsichtsbehoerde' "
        "war faelschlich auf die Gemeinde-AGS der Kreisstadt Merzig (10042113) statt auf die "
        "Kreis-AGS (10042, matching_level=COUNTY) gescoped. Merzig gehoert nicht zu den saarlaend. "
        "Staedten mit eigener Bauaufsichtsbehoerde (ZustV-LBO) - amtlich bestaetigt via "
        "https://www.merzig-wadern.de/Verwaltung-Politik/Bauen/Untere-Bauaufsicht/ (Anschrift "
        "Bahnhofstrasse 44, 66663 Merzig, identisch mit der bereits vorhandenen COUNTY-Regel "
        "ags=10042, authority_id 0fadb002). Dieselbe reale Behoerde war doppelt und falsch "
        "gescoped in der Datenbank."
    ),
    "e039d2d6-8548-4e34-bc7c-bba0454785f9": (
        "Abgeloest: siehe Begruendung fuer BAUAKTEN-Regel 48067053 (identischer Fall, "
        "BAULASTEN statt BAUAKTEN)."
    ),
    "14a393c2-6963-4ce7-b6a5-2fde4ca5f8aa": (
        "Abgeloest: kreisweite Behoerde 'Landkreis St. Wendel - Untere Bauaufsichtsbehoerde' "
        "war faelschlich auf die Gemeinde-AGS der Kreisstadt St. Wendel (10046117) statt auf die "
        "Kreis-AGS (10046, matching_level=COUNTY) gescoped, zusaetzlich mit veralteter/falscher "
        "Anschrift 'Rathausplatz 1'. St. Wendel gehoert nicht zu den saarlaend. Staedten mit "
        "eigener Bauaufsichtsbehoerde (ZustV-LBO). Amtlich bestaetigt via "
        "https://service.saarland.de/portaldeeplink?tsa_oe_id=100084009&tsa_sprache=de_DE "
        "(Anschrift Mommstrasse 21-31, 66606 St. Wendel, identisch mit der bereits vorhandenen "
        "COUNTY-Regel ags=10046, authority_id cd1639b3)."
    ),
    "c4d1356d-d94e-4b6b-bbe3-40b0c56fb440": (
        "Abgeloest: siehe Begruendung fuer BAUAKTEN-Regel 14a393c2 (identischer Fall, "
        "BAULASTEN statt BAUAKTEN)."
    ),
}


def main(dry_run: bool = True):
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")
    print(f"Modus: {'DRY-RUN (keine Aenderungen werden gespeichert)' if dry_run else 'APPLY'}")

    from sqlalchemy import text
    from app.database.engine import SessionLocal
    from app.models.jurisdiction import Jurisdiction

    db = SessionLocal()
    # Ziel-DB wird gerade parallel von anderen Sessions beschrieben - statt beim
    # ersten Lock-Konflikt sofort zu scheitern, bis zu 30s auf die Sperre warten.
    db.execute(text("PRAGMA busy_timeout=30000"))
    try:
        # Gleiche Konvention wie JurisdictionStagingService.approve_entry() beim
        # Ablösen einer widersprochenen Regel (siehe jurisdiction_staging.py) und
        # wie beim parallel angewendeten Saarlouis-Fix: nur valid_to setzen,
        # active bleibt True. Die Regel war bis gestern korrekt gültig - sie wird
        # abgelöst (durch die bereits vorhandene COUNTY-Regel), nicht zurückgenommen
        # wie bei revert_erschliessung_leiningerland.py (dort active=False, weil die
        # Regel von Anfang an nie eine gültige Quelle hatte).
        expiry = datetime.utcnow().date() - timedelta(days=1)
        found = 0
        for jurisdiction_id, reason in JURISDICTION_IDS_TO_EXPIRE.items():
            rule = db.query(Jurisdiction).filter(
                Jurisdiction.jurisdiction_id == jurisdiction_id
            ).first()
            if rule is None:
                print(f"WARNUNG: Regel {jurisdiction_id} nicht gefunden - uebersprungen.")
                continue
            if rule.valid_to is not None and rule.valid_to <= expiry:
                print(f"WARNUNG: Regel {jurisdiction_id} ist bereits abgelaufen - uebersprungen.")
                continue
            found += 1
            print(
                f"  {rule.request_type_id:9} ags={rule.ags:10} lvl={rule.matching_level} "
                f"authority_id={rule.authority_id} -> wird abgeloest (valid_to={expiry})"
            )
            rule.valid_to = expiry
            rule.notes = (rule.notes + " " if rule.notes else "") + reason
            rule.verified_by = REVIEWER
            rule.last_verified_at = datetime.utcnow()
            rule.verification_status = "CORRECTED"

        if dry_run:
            db.rollback()
            print(f"\nDRY-RUN: {found} Regel(n) waeren abgeloest worden. Keine Aenderung gespeichert.")
        else:
            db.commit()
            print(f"\n{found} Regel(n) abgeloest und gespeichert.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(dry_run=not apply_changes)
