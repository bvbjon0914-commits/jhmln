# -*- coding: utf-8 -*-
"""
Bundesweite Version des Saarland-Fixes (fix_saarland_bauaufsicht_kreisweite_
duplikate.py): behebt denselben Bug-Typ ueberall dort, wo er nachweislich in
derselben, bereits verifizierten Form auftritt.

BUG-MUSTER (identisch zum Saarland-Fall): eine kreisweite Untere
Bauaufsichtsbehoerde ("Landkreis X"/"Kreis X"/"Kreisverwaltung X"/
"StaedteRegion X"/"uBAB Landkreis X" o.ae.) ist fuer BAUAKTEN/BAULASTEN
faelschlich auf matching_level=MUNICIPALITY + die AGS der (kreisangehoerigen
oder kreisfreien) Kreisstadt/grossen selbstaendigen Stadt gepinnt, statt auf
matching_level=COUNTY + die eigene Kreis-AGS. Ursache: ein aelterer Bulk-
Import ("Bauaemter Datenbank Deutschland FINAL 20260831" o.ae.) hatte nur
Gemeinde-Level-Zeilen, waehrend ein neuerer amtlicher Import (Anschriften-
verzeichnis der Gemeinde- und Stadtverwaltungen, Stand 31.01.2026, bzw. die
Struktur-Korrektur-Kampagne vom 26.09.2026) die korrekte COUNTY-Zeile fuer
denselben realen Kreis ERGAeNZT hat, OHNE die alte, falsch gescopte Zeile zu
entfernen - daher zwei aktive, gleichrangige (priority=40) MUNICIPALITY-
Regeln am selben Ort, die den Matcher zu MULTIPLE_MATCHES fuehren.

Verifikationsmethode (rein AGS-/Datenbank-basiert, keine externe Recherche
noetig - der Bug ist ein reiner Scope-Fehler, keine Sachfrage): fuer jede
AGS mit >1 aktiver, aktuell gueltiger MUNICIPALITY-Regel desselben
Auskunftstyps wird geprueft, ob (a) genau 2 Zeilen vorliegen (Hamburg mit 7
und Berlin mit 12 Bezirks-Zeilen sind bewusst ausgenommen - das sind
gewollte, bereits einzeln recherchierte Mehrfach-Zeilen, kein Bug), (b) genau
eine der beiden Zeilen "Kreis-artig" benannt ist (Praefix Landkreis/Kreis/
Kreisverwaltung/StaedteRegion/uBAB Landkreis/Regionalverband), und (c) fuer
diese Kreis-Zeile bereits eine korrekt gescopte COUNTY-Regel existiert - in
zwei moeglichen Varianten:
  - Variante A (haeufigster Fall): der Kreis DIESER AGS (ermittelt ueber
    administrative_units.ags_kreis) hat selbst schon eine aktive COUNTY-
    Regel - die Kreis-Zeile ist dann einfach eine falsch auf die Kreisstadt
    gescopte Dublette derselben Behoerde.
  - Variante B (kreisfreie Staedte mit gleichnamigem Nachbar-Landkreis, z.B.
    Stadt Oldenburg vs. Landkreis Oldenburg, Stadt Kassel vs. Landkreis
    Kassel, Stadtverwaltung Koblenz vs. Kreisverwaltung Mayen-Koblenz): die
    Kreis-Zeile gehoert zu einem ANDEREN, eigenstaendigen Landkreis, der
    zufaellig denselben oder aehnlichen Namen traegt wie die kreisfreie
    Stadt - dieser andere Landkreis hat aber BEREITS eine eigene korrekte
    COUNTY-Regel unter seiner eigenen (anderen) AGS. Wird per bundesweiter
    Kernnamen-Suche unter den COUNTY-Zeilen gefunden.
Nur wenn eine passende COUNTY-Regel in einer der beiden Varianten gefunden
wird, gilt die Kreis-Zeile als sicher redundant.

STICHPROBENARTIG MANUELL VERIFIZIERT vor Erstellung dieses Skripts (siehe
Diagnose-Ausgabe der Recherche-Sitzung): u.a. Goslar, Helmstedt (Var. A),
Mayen-Koblenz/Koblenz, Oldenburg/Stadt Oldenburg, Kassel/Landkreis Kassel
(Var. B), StaedteRegion Aachen/Stadt Aachen, Landkreis Barnim/Stadt
Eberswalde, Erzgebirgskreis/Stadt Annaberg-Buchholz - in JEDEM Fall ist die
als "Kreis-Zeile" identifizierte Zeile tatsaechlich entweder dieselbe oder
eine andere, aber real existierende und bereits korrekt erfasste Behoerde.

Wie beim Saarland-Fix: reine Ablösung (valid_to = Vortag), `active` bleibt
True, keine neue Quelle noetig, da die Kreis-Zeile durch die bereits
bestehende COUNTY-Zeile schon korrekt und vollstaendig ersetzt wird und
KEINE der beiden verbleibenden Regeln fuer die Kreisstadt/grosse
selbststaendige Stadt selbst veraendert wird.

Ausdruecklich AUSGENOMMEN (kein automatischer Fix, siehe Ergebnis-Ausdruck
fuer den vollstaendigen Review): Hamburg und Berlin (gewollte Mehrfach-
Bezirks-Zeilen) sowie jede AGS, bei der die automatische Pruefung keine
eindeutige Kreis-Zeile identifizieren kann (wird als "SKIP" ausgegeben und
NICHT veraendert - erfordert manuelle Einzelfallpruefung).
"""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, bundesweite Bauaufsicht-Kreisweite-Duplikate)"
EXCLUDED_AGS = {"02000000", "11000000"}  # Hamburg (7 Bezirke), Berlin (12 Bezirke) - gewollt, kein Bug

KREIS_PREFIXES = [
    "landkreis ", "kreis ", "kreisverwaltung ", "städteregion ", "staedteregion ",
    "ubab landkreis ", "regionalverband ",
]
STADT_PREFIXES = [
    "stadt ", "stadtverwaltung ", "hansestadt ", "landeshauptstadt ",
    "universitätsstadt ", "universitaetsstadt ", "hanse- und universitätsstadt ",
    "untere bauaufsichtsbehörde ", "untere bauaufsichtsbehoerde ",
]
# Saechsische Landkreise, deren amtlicher Name das Wort "-kreis" bereits
# enthaelt (kein separates "Landkreis "-Praefix) - manuell verifiziert
# (siehe COUNTY-Zeilen "Landkreis Erzgebirgskreis/Vogtlandkreis/
# Burgenlandkreis - Bauaufsichtsbehoerde", bereits vor diesem Skript
# bestehend), keine automatische Heuristik fuer beliebige "-kreis"-Namen.
BARE_KREIS_NAMES = {"erzgebirgskreis", "vogtlandkreis", "burgenlandkreis"}


def strip_prefix(name, prefixes):
    low = name.lower()
    for p in prefixes:
        if low.startswith(p):
            return name[len(p):]
    return None


def core_name(authority_name, prefixes):
    """Strip a known prefix (if any) and cut off the trailing ' - .../ – ...'
    descriptor, returning just the bare organisation name for comparison,
    e.g. 'Landkreis Goslar - Bauaufsichtsbehörde' -> 'goslar'."""
    rest = strip_prefix(authority_name, prefixes)
    if rest is None:
        rest = authority_name
    for sep in [" - ", " – "]:
        idx = rest.find(sep)
        if idx != -1:
            rest = rest[:idx]
            break
    return rest.strip().lower()


def is_kreis_prefixed(name):
    low = name.lower()
    if any(low.startswith(p) for p in KREIS_PREFIXES):
        return True
    return any(low.startswith(n) for n in BARE_KREIS_NAMES)


def is_stadt_prefixed(name):
    low = name.lower()
    return any(low.startswith(p) for p in STADT_PREFIXES)


def main(apply_changes=False):
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")
    print(f"Modus: {'APPLY' if apply_changes else 'DRY-RUN (keine Aenderungen werden gespeichert)'}")

    from app.database.engine import SessionLocal
    from app.models.jurisdiction import Jurisdiction
    from app.models.authority import Authority
    from sqlalchemy import func, text

    db = SessionLocal()
    try:
        today = date.today()
        total_expired = 0
        total_skipped = 0

        for rt in ["BAUAKTEN", "BAULASTEN"]:
            print(f"\n{'='*20} {rt} {'='*20}")

            dup_ags_rows = (
                db.query(Jurisdiction.ags)
                .filter(
                    Jurisdiction.active.is_(True),
                    Jurisdiction.request_type_id == rt,
                    Jurisdiction.matching_level == "MUNICIPALITY",
                    Jurisdiction.ags.isnot(None),
                    (Jurisdiction.valid_to.is_(None)) | (Jurisdiction.valid_to >= today),
                )
                .group_by(Jurisdiction.ags)
                .having(func.count() > 1)
                .all()
            )
            dup_ags = [r[0] for r in dup_ags_rows if r[0] not in EXCLUDED_AGS]

            for ags in dup_ags:
                rows = (
                    db.query(Jurisdiction)
                    .filter(
                        Jurisdiction.active.is_(True),
                        Jurisdiction.request_type_id == rt,
                        Jurisdiction.matching_level == "MUNICIPALITY",
                        Jurisdiction.ags == ags,
                        (Jurisdiction.valid_to.is_(None)) | (Jurisdiction.valid_to >= today),
                    )
                    .all()
                )
                if len(rows) != 2:
                    print(f"  SKIP {ags}: {len(rows)} Zeilen (kein einfaches 2er-Paar) - manuelle Pruefung noetig")
                    total_skipped += 1
                    continue

                ags_kreis_row = db.execute(
                    text("SELECT DISTINCT ags_kreis FROM administrative_units WHERE ags = :ags"), {"ags": ags}
                ).fetchone()
                if not ags_kreis_row:
                    print(f"  SKIP {ags}: kein ags_kreis gefunden")
                    total_skipped += 1
                    continue
                ags_kreis = ags_kreis_row[0]

                # Zuerst nach Präfix klassifizieren: genau eine Zeile muss "Kreis-artig"
                # benannt sein (Landkreis/Kreis/Kreisverwaltung/StädteRegion/...), die
                # andere nicht - sonst ist die Lage nicht eindeutig genug für einen
                # automatischen Fix.
                labelled = []
                for row in rows:
                    auth = db.query(Authority).filter(Authority.authority_id == row.authority_id).first()
                    labelled.append((row, auth, is_kreis_prefixed(auth.authority_name)))
                kreis_rows = [t for t in labelled if t[2]]
                other_rows = [t for t in labelled if not t[2]]

                if len(kreis_rows) != 1 or len(other_rows) != 1:
                    names = [a.authority_name for _, a, _ in labelled]
                    print(f"  SKIP {ags} (Kreis {ags_kreis}): kein eindeutiges Kreis+Nicht-Kreis-Paar "
                          f"({names}) - manuelle Pruefung noetig")
                    total_skipped += 1
                    continue

                best, best_auth, _ = kreis_rows[0]
                second, second_auth, _ = other_rows[0]
                candidate_core = core_name(best_auth.authority_name, KREIS_PREFIXES)

                # Variante A: dieselbe AGS-Kreis hat bereits eine korrekte COUNTY-Zeile
                # (der Normalfall - die Kreis-Zeile ist einfach falsch gescopt).
                county_same_kreis = (
                    db.query(Jurisdiction)
                    .filter(
                        Jurisdiction.active.is_(True),
                        Jurisdiction.request_type_id == rt,
                        Jurisdiction.matching_level == "COUNTY",
                        Jurisdiction.ags == ags_kreis,
                        (Jurisdiction.valid_to.is_(None)) | (Jurisdiction.valid_to >= today),
                    )
                    .first()
                )

                county_match = None
                match_reason = None
                if county_same_kreis:
                    county_match = county_same_kreis
                    match_reason = "gleicher Kreis"
                else:
                    # Variante B: die Kreis-Zeile gehoert zu einem ANDEREN, gleichnamigen
                    # Landkreis (haeufig bei kreisfreien Staedten, deren Name mit dem
                    # eines benachbarten Landkreises uebereinstimmt, z.B. Stadt Oldenburg
                    # vs. Landkreis Oldenburg) - suche bundesweit nach einer COUNTY-Zeile
                    # mit demselben Kernnamen an einer ANDEREN AGS.
                    candidates_elsewhere = (
                        db.query(Jurisdiction, Authority)
                        .join(Authority, Authority.authority_id == Jurisdiction.authority_id)
                        .filter(
                            Jurisdiction.active.is_(True),
                            Jurisdiction.request_type_id == rt,
                            Jurisdiction.matching_level == "COUNTY",
                            Jurisdiction.ags != ags_kreis,
                            (Jurisdiction.valid_to.is_(None)) | (Jurisdiction.valid_to >= today),
                        )
                        .all()
                    )
                    for j, a in candidates_elsewhere:
                        if core_name(a.authority_name, KREIS_PREFIXES) == candidate_core:
                            county_match = j
                            match_reason = f"anderer, gleichnamiger Kreis (ags={j.ags})"
                            break

                if county_match is None:
                    print(f"  SKIP {ags} (Kreis {ags_kreis}): keine passende COUNTY-Regel fuer "
                          f"[{best_auth.authority_name}] gefunden (weder gleicher noch gleichnamiger "
                          f"anderer Kreis) - manuelle Pruefung noetig")
                    total_skipped += 1
                    continue

                county_authority = db.query(Authority).filter(Authority.authority_id == county_match.authority_id).first()

                print(f"  {ags} (Kreis {ags_kreis}): EXPIRE [{best_auth.authority_name}] "
                      f"(ueberdeckt durch COUNTY [{county_authority.authority_name}], {match_reason}) "
                      f"-- KEEP [{second_auth.authority_name}]")

                if apply_changes:
                    best.valid_to = today - timedelta(days=1)
                    best.notes = (
                        (best.notes + " | " if best.notes else "")
                        + f"Abgelöst am {today.isoformat()} durch bundesweiten Bauaufsicht-Kreisweite-Duplikate-Fix "
                        f"({REVIEWER}): redundant zur bereits bestehenden COUNTY-Regel "
                        f"{county_match.jurisdiction_id} ({county_authority.authority_name}, {match_reason})."
                    )
                    total_expired += 1
                else:
                    total_expired += 1

        if apply_changes:
            db.commit()
            print(f"\n{total_expired} Regel(n) abgeloest (valid_to gesetzt). {total_skipped} uebersprungen (manuelle Pruefung noetig).")
        else:
            print(f"\nDRY-RUN: {total_expired} Regel(n) waeren abgeloest worden. {total_skipped} uebersprungen. Keine Aenderung gespeichert.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
