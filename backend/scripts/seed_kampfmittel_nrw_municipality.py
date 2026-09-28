"""
KAMPFMITTEL Nordrhein-Westfalen: die letzten 19 fehlerhaften MUNICIPALITY-
Zeilen (ags=NULL) korrigieren.

WICHTIGER KORREKTUR-HINWEIS ZUR AUSGANGSANNAHME DIESER KAMPAGNE: der
Auftrag ("NRW hat gar keine KAMPFMITTEL-Regel") war ein durch denselben
NULL-Feld-Bug verursachter Fehlalarm wie in feedback-ags-level-coverage-
check/feedback-staging-dedup-null-fields dokumentiert - diesmal am
`state`-Feld: 377 von 396 NRW-Gemeinden hatten BEREITS eine korrekt
AGS-gescopte, aktive MUNICIPALITY-Regel (Quelle "Kampfmittelbehoerden
FINAL 20260831 - NRW_Ordnungsbehoerden + Gemeinde-Anschriften
31.01.2026"), nur mit `state=NULL` statt 'Nordrhein-Westfalen' - die
Ausgangsabfrage `WHERE state='Nordrhein-Westfalen'` hat diese 377
korrekten Zeilen komplett uebersehen und nur die uebrigen 19 kaputten
Zeilen (state korrekt gesetzt, aber ags=NULL, dadurch fuer den
AGS-basierten Matcher nie auffindbar) gefunden - daher der scheinbare
"Totalausfall". Nur diese 19 sind eine echte Luecke.

Rechtsgrundlage der Zustaendigkeit (MUNICIPALITY-Ebene, "oertliche
Ordnungsbehoerde" je Gemeinde) unabhaengig direkt an der Primaerquelle
nachgeprueft, nicht nur aus der Importdatei-Referenz uebernommen:
  https://recht.nrw.de/mblnrw/2006-s288/
  "Kampfmittelbeseitigung ist eine Aufgabe der Gefahrenabwehr und gemaess
  § 1 Abs. 1 Ordnungsbehoerdengesetz (OBG) Aufgabe der oertlichen
  Ordnungsbehoerden. Zur Unterstuetzung der oertlichen Ordnungsbehoerden
  unterhaelt das Land NRW einen Kampfmittelbeseitigungsdienst [...], der
  auf Anforderung der oertlichen Ordnungsbehoerde [...] untersucht,
  bewertet und raeumt."
  Zusaetzlich bestaetigt ueber die offizielle Seite der Bezirksregierung
  Arnsberg (https://www.bra.nrw.de/recht-ordnung/gefahrenabwehr/
  kampfmittelbeseitigungsdienst-westfalen-lippe-kbd-wl): "Der Schutz der
  Bevoelkerung vor den von Kampfmitteln ausgehenden Gefahren obliegt den
  oertlichen Ordnungsbehoerden, also den Staedten und Gemeinden."
  Damit ist MUNICIPALITY-Ebene (nicht eine STATE-Regel auf eine der 5
  Bezirksregierungen, die laut Primaerquelle nur unterstuetzend auf
  Ersuchen der Gemeinde taetig werden) die fachlich richtige Modellierung
  - konsistent mit den bereits bestehenden 377 korrekten Zeilen.

Die 19 betroffenen Gemeinden (Authority-Zuordnung und Adresse waren immer
schon korrekt, nur ags fehlte): Borgentreich, Brüggen, Enger, Erkrath,
Gescher, Grefrath, Halle (Westfalen), Harsewinkel, Hövelhof, Hückeswagen,
Kerpen, Langenfeld (Rhld.), Leichlingen (Rhld.), Meschede, Roetgen,
Saerbeck, Siegen, Solingen, Stolberg (Rhld.).
"""
import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, KAMPFMITTEL NRW - 19 ags=NULL-Zeilen korrigiert)"
SOURCE_URL = "https://recht.nrw.de/mblnrw/2006-s288/"
QUOTE = (
    "MBl. NRW. 2006 S. 288: 'Kampfmittelbeseitigung ist eine Aufgabe der Gefahrenabwehr und "
    "gemaess § 1 Abs. 1 Ordnungsbehoerdengesetz (OBG) Aufgabe der oertlichen Ordnungsbehoerden. "
    "Zur Unterstuetzung der oertlichen Ordnungsbehoerden unterhaelt das Land NRW einen "
    "Kampfmittelbeseitigungsdienst [...], der auf Anforderung der oertlichen Ordnungsbehoerde [...] "
    "untersucht, bewertet und raeumt.' Eigenstaendig direkt an der Primaerquelle (recht.nrw.de) "
    "gelesen und zusaetzlich ueber die offizielle Bezirksregierung-Arnsberg-Seite bestaetigt "
    "(bra.nrw.de: 'Der Schutz der Bevoelkerung ... obliegt den oertlichen Ordnungsbehoerden, "
    "also den Staedten und Gemeinden.'). Ersetzt eine fehlerhafte Altzeile mit ags=NULL aus "
    "demselben Import (Quelle: Kampfmittelbehoerden FINAL 20260831 - NRW_Ordnungsbehoerden + "
    "Gemeinde-Anschriften 31.01.2026); Authority-Zuordnung und Adresse waren dort bereits korrekt."
)

# Klammerzusatz-Gemeinden, deren Jurisdiction.municipality-Text nicht
# direkt gegen administrative_units.municipality_name (vor dem ersten
# Komma) matcht.
MANUAL_AGS_OVERRIDES = {
    "Stolberg (Rhld.)": "05334032",
    "Halle (Westfalen)": "05754012",
    "Langenfeld (Rhld.)": "05158020",
    "Leichlingen (Rhld.)": "05378016",
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit
    from app.models.jurisdiction import Jurisdiction
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Nordrhein-Westfalen").all()
        name_to_ags = {}
        for u in units:
            norm_name = u.municipality_name.split(",")[0].strip()
            name_to_ags.setdefault(norm_name, []).append(u.ags)
        dupes = {k: v for k, v in name_to_ags.items() if len(v) > 1}
        if dupes:
            print(f"FEHLER: mehrdeutige Gemeindenamen in NRW gefunden: {dupes}")
            sys.exit(1)

        broken_rows = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == "KAMPFMITTEL",
                Jurisdiction.state == "Nordrhein-Westfalen",
                Jurisdiction.ags.is_(None),
                Jurisdiction.active.is_(True),
            )
            .all()
        )
        if len(broken_rows) != 19:
            print(f"FEHLER: erwartet 19 kaputte ags=NULL-Zeilen, gefunden {len(broken_rows)} - Abbruch, Lage hat sich geaendert, Pruefung noetig.")
            sys.exit(1)
        print(f"{len(broken_rows)} kaputte ags=NULL-Zeilen gefunden.")

        resolved = []
        unresolved = []
        for old_rule in broken_rows:
            gemeinde_name = old_rule.municipality
            ags = MANUAL_AGS_OVERRIDES.get(gemeinde_name)
            if ags is None:
                cands = name_to_ags.get(gemeinde_name)
                if cands and len(cands) == 1:
                    ags = cands[0]
            if ags is None:
                unresolved.append(old_rule)
            else:
                resolved.append((old_rule, ags))

        if unresolved:
            print(f"FEHLER: {len(unresolved)} Zeilen konnten keinem eindeutigen AGS zugeordnet werden - Abbruch, keine Regel wird geraten:")
            for r in unresolved:
                print(f"  {r.jurisdiction_id} municipality={r.municipality!r}")
            sys.exit(1)
        print(f"{len(resolved)} von 19 Zeilen eindeutig einem AGS zugeordnet.")

        # Sicherstellen, dass fuer keinen dieser AGS bereits eine andere
        # aktive KAMPFMITTEL-Regel existiert (die 377 bereits korrekten
        # Zeilen duerfen nicht ueberlappt werden).
        target_ags = {ags for _, ags in resolved}
        existing_for_target = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == "KAMPFMITTEL",
                Jurisdiction.active.is_(True),
                Jurisdiction.ags.in_(target_ags),
            )
            .all()
        )
        if existing_for_target:
            print(f"FEHLER: {len(existing_for_target)} der Ziel-AGS haben bereits eine aktive Regel - Abbruch, Ueberschneidung pruefen:")
            for r in existing_for_target:
                print(f"  {r.jurisdiction_id} ags={r.ags}")
            sys.exit(1)

        staging = JurisdictionStagingService(db)
        batch_id = f"kampfmittel-nrw-fix-nullags-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        staged = []
        for old_rule, ags in resolved:
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="KAMPFMITTEL NRW - 19 ags=NULL-Zeilen korrigiert",
                request_type_id="KAMPFMITTEL", state="Nordrhein-Westfalen", ags=ags,
                municipality=old_rule.municipality, matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=old_rule.authority_id,
                source=f"{old_rule.source} - {QUOTE}", source_url=SOURCE_URL,
                source_license="Amtliche Auskunft (keine Datenlizenz, Rechtsnorm + Anschriftenverzeichnis)",
                source_retrieved_at=datetime.now(),
            )
            staged.append((entry, old_rule, ags))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        by_conflict = {}
        for entry, _, _ in staged:
            by_conflict.setdefault(entry.conflict_type, 0)
            by_conflict[entry.conflict_type] += 1
        print(f"Konflikt-Verteilung: {by_conflict}")
        non_new = [(e, o, ags) for e, o, ags in staged if e.conflict_type != "NEW"]
        for e, o, ags in non_new[:20]:
            print(f"  KONFLIKT #{e.id} ags={ags} - {e.conflict_type}: {e.conflict_reason}")
        if non_new:
            print(f"\nFEHLER: {len(non_new)} unerwartete Konflikte - Abbruch ohne Freigabe, Pruefung noetig.")
            sys.exit(1)

        approved = 0
        yesterday = date.today() - timedelta(days=1)
        for entry, old_rule, ags in staged:
            new_rule = staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=QUOTE,
                resulting_verification_status="AUTO_IMPORTED",
            )
            approved += 1
            old_rule.valid_to = yesterday
            old_rule.notes = (
                (old_rule.notes + " | " if old_rule.notes else "")
                + f"Abgelöst durch korrekt AGS-gescopte Regel {new_rule.jurisdiction_id} (Batch {batch_id}), "
                f"freigegeben von {REVIEWER} am {date.today().isoformat()} - alte Zeile hatte ags=NULL und war "
                "fuer den Matcher nie auffindbar."
            )
        db.commit()
        print(f"\n{approved} Regeln freigegeben, {approved} alte ags=NULL-Zeilen abgelöst (valid_to={yesterday.isoformat()}, active bleibt True).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
