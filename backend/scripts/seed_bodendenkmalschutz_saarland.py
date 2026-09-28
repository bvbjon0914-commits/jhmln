# -*- coding: utf-8 -*-
"""
BODENDENKMALSCHUTZ (archaeologische Bodendenkmalpflege) fuer das
SAARLAND. Bislang die einzige verbleibende komplett unbedeckte
Bundeslaender-Luecke bei BODENDENKMALSCHUTZ (weder STATE- noch
Kreis-Ebene vorhanden).

Anders als vermutet ist die Zustaendigkeit NICHT bei den 6 Kreisen/dem
Regionalverband Saarbruecken, sondern ZENTRAL beim Landesdenkmalamt -
seit der Neuordnung durch das Saarlaendische Denkmalschutzgesetz
(SDschG) vom 13. Juni 2018 kennt das saarlaendische Denkmalrecht
ueberhaupt keine "untere Denkmalschutzbehoerde" auf Kreisebene mehr
(weder fuer Bau- noch fuer Bodendenkmale) - nur zweistufig: oberste
Denkmalbehoerde (Ministerium fuer Bildung und Kultur) und
Landesdenkmalamt als Fach- und Vollzugsbehoerde. Die bereits
bestehende DENKMALSCHUTZ-Regel fuer das Saarland in dieser Datenbank
ist konsequenterweise ebenfalls schon korrekt als STATE-Level-Regel
angelegt (verifiziert, keine Korrektur noetig).

Woertliche Belege (SDschG vom 13.06.2018, zuletzt geaendert durch
Art. 260 des Gesetzes vom 8.12.2021, gegen recht.saarland.de
verifiziert):
- § 10 Abs. 1 SDschG: "Die Genehmigung zur Veraenderung von
  Baudenkmaelern und Denkmalbereichen ist schriftlich oder
  elektronisch beim Landesdenkmalamt zu beantragen."
- § 10 Abs. 6 Satz 2 SDschG: "Fuer die Genehmigung zur Ausgrabung von
  Bodendenkmaelern nach § 8 Absatz 1 oder bei Arbeiten in
  Grabungsschutzgebieten nach § 9 sowie fuer die Genehmigung zur
  Veraenderung von Bodendenkmaelern oder Erdarbeiten nach § 8 Absatz 2
  und 3 gelten die Absaetze 1 bis 5 entsprechend."
- § 21 Abs. 2 SDschG: "Das Landesdenkmalamt ist eine dem Ministerium
  nachgeordnete Behoerde ..."
- § 22 Abs. 2 Satz 1 SDschG: "Das Landesdenkmalamt ist als Fach- und
  Vollzugsbehoerde fuer Fragen des Denkmalschutzes und der
  Denkmalpflege zustaendig."
Landkreise/Regionalverband Saarbruecken kommen im gesamten
Behoerden-Abschnitt (§§ 21-26 SDschG) nicht als Denkmalbehoerde vor.

Adresse amtlich bestaetigt (saarland.de/lda): Landesdenkmalamt,
Am Bergwerk Reden 11, 66578 Schiffweiler.

1 neue STATE-Level-Regel.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bodendenkmalschutz Saarland)"
SOURCE_URL = "https://recht.saarland.de/bssl/document/jlr-NNLSL0000A10E"
QUOTE = (
    "§ 10 Abs. 1 SDschG: 'Die Genehmigung zur Veränderung von Baudenkmälern und Denkmalbereichen ist "
    "schriftlich oder elektronisch beim Landesdenkmalamt zu beantragen.' § 10 Abs. 6 Satz 2 SDschG: "
    "'Für die Genehmigung zur Ausgrabung von Bodendenkmälern nach § 8 Absatz 1 ... gelten die Absätze "
    "1 bis 5 entsprechend.' § 22 Abs. 2 Satz 1 SDschG: 'Das Landesdenkmalamt ist als Fach- und "
    "Vollzugsbehörde für Fragen des Denkmalschutzes und der Denkmalpflege zuständig.' Landkreise/"
    "Regionalverband Saarbrücken kommen im Behördenabschnitt (§§ 21-26 SDschG) nicht vor - seit der "
    "Neuordnung 2018 gibt es in Saarland keine untere Denkmalschutzbehörde auf Kreisebene mehr."
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

    db = SessionLocal()
    try:
        authority_name = "Landesdenkmalamt Saarland"
        authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
        if authority is None:
            authority = Authority(
                authority_id=str(uuid.uuid4()), authority_name=authority_name,
                authority_type="Fach- und Vollzugsbehörde für Denkmalschutz (zentral, Land)",
                street="Am Bergwerk Reden 11", house_number=None, postal_code="66578",
                city="Schiffweiler", state="Saarland", phone=None, email="poststelle@denkmal.saarland.de",
                source=f"Amtliche Webseite (saarland.de/lda) + {SOURCE_URL}",
                active=True,
            )
            db.add(authority)
            db.flush()

        staging = JurisdictionStagingService(db)
        batch_id = f"bodendenkmalschutz-saarland-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        entry = staging.stage_entry(
            batch_id=batch_id, batch_label="BODENDENKMALSCHUTZ Saarland - zentral Landesdenkmalamt",
            request_type_id="BODENDENKMALSCHUTZ", state="Saarland", ags=None,
            matching_level=MatchingLevel.STATE, priority=60,
            proposed_authority_id=authority.authority_id,
            source=f"{authority_name} - {QUOTE}", source_url=SOURCE_URL,
            source_license="Amtliche Rechtsgrundlage (SDschG 2018) + amtliche Landesdenkmalamt-Webseite",
            source_retrieved_at=datetime.utcnow(),
        )
        db.commit()

        print(f"\n1 Eintrag gestaged (Batch {batch_id}).")
        print(f"Konflikt-Typ: {entry.conflict_type}")
        if entry.conflict_type != "NEW":
            print(f"  KONFLIKT #{entry.id} - {entry.conflict_reason}")
            print("\n0 Regeln freigegeben (Konflikt, keine automatische Freigabe).")
        else:
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
                resulting_verification_status="VERIFIED",
            )
            db.commit()
            print("\n1 Regel freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
