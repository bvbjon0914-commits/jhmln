# -*- coding: utf-8 -*-
"""
DENKMALSCHUTZ (Baudenkmalschutz) UND BODENDENKMALSCHUTZ (archaeologische
Bodendenkmalpflege) fuer BERLIN - je 12 Bezirksamt-Zeilen. Die letzten
beiden Auskunftsarten, fuer die Berlin in dieser Datenbank noch
komplett fehlte (alle anderen: BAUAKTEN, BAULASTEN, KATASTER,
ERSCHLIESSUNG, ALTLASTEN, HOCHWASSERSCHUTZ, WASSERSCHUTZ, KAMPFMITTEL,
GRUNDBUCH waren bereits abgedeckt).

Beide Auskunftsarten werden von DERSELBEN Behoerde je Bezirk
wahrgenommen: die "Untere Denkmalschutzbehoerde" (Bezirksamt) ist nach
§ 6 Abs. 2/3 DSchG Bln fuer "alle Ordnungsaufgaben nach diesem Gesetz"
zustaendig - das Gesetz definiert "Denkmale" in § 2 Abs. 1 einheitlich
als "Baudenkmale, Denkmalbereiche, Gartendenkmale sowie Bodendenkmale"
und enthaelt KEINE Sonderzuweisung von Bodendenkmalpflege-Genehmigungen
an eine zentrale Landesbehoerde (anders als z.B. in Sachsen oder dem
Saarland). Das Landesdenkmalamt (Denkmalfachbehoerde, § 5 DSchG Bln)
wird lediglich im Einvernehmensverfahren beteiligt (§ 6 Abs. 5 DSchG
Bln), hat aber keine eigene Erstentscheidungskompetenz gegenueber
Buergerinnen und Buergern.

Woertlich bestaetigt durch die amtliche Uebersichtsseite der
Senatsverwaltung fuer Stadtentwicklung (zentrale, fuer alle 12 Bezirke
autoritative Adressquelle):
"Die Unteren Denkmalschutzbehoerden sind bei den zwoelf Berliner
Bezirken angesiedelt und fuer alle Ordnungsaufgaben nach dem Berliner
Denkmalschutzgesetz zustaendig. [...] Ihnen obliegt die Genehmigung
denkmalrechtlich relevanter Massnahmen wie die Erteilung und
Versagung von Genehmigungen fuer Grabungen nach Bodendenkmalen oder
bei denkmalschutzrechtlichen bzw. bauordnungsrechtlichen
Genehmigungsverfahren."
(https://www.berlin.de/sen/stadtentwicklung/denkmal/untere-denkmalschutzbehoerden/)

Diese Seite listet auch die amtlichen Adressen aller 12 Bezirksaemter
und wurde als autoritative Quelle fuer beide Auskunftsarten verwendet
(loest zwei kleinere Adress-Diskrepanzen zwischen einzelnen
Bezirksamt-Unterseiten zugunsten dieser zentralen Senatsseite auf:
Marzahn-Hellersdorf, Neukoelln).

12 Bezirke x 2 Auskunftsarten = 24 neue MUNICIPALITY-Regeln (ags=
11000000, Dispatch ueber Strasse/Adresse wie bei den anderen bereits
bezirklich modellierten Berlin-Auskunftsarten in dieser Datenbank).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Denkmalschutz/Bodendenkmalschutz Berlin je Bezirk)"
BERLIN_AGS = "11000000"
SOURCE_URL = "https://www.berlin.de/sen/stadtentwicklung/denkmal/untere-denkmalschutzbehoerden/"
QUOTE = (
    "Senatsverwaltung für Stadtentwicklung, amtliche Übersichtsseite 'Untere Denkmalschutzbehörden "
    "(UD) der Berliner Bezirke': 'Die Unteren Denkmalschutzbehörden sind bei den zwölf Berliner "
    "Bezirken angesiedelt und für alle Ordnungsaufgaben nach dem Berliner Denkmalschutzgesetz "
    "zuständig. [...] Ihnen obliegt die Genehmigung denkmalrechtlich relevanter Maßnahmen wie die "
    "Erteilung und Versagung von Genehmigungen für Grabungen nach Bodendenkmalen oder bei "
    "denkmalschutzrechtlichen bzw. bauordnungsrechtlichen Genehmigungsverfahren.' § 6 Abs. 2/3 DSchG "
    "Bln: 'Untere Denkmalschutzbehörden sind die Bezirksämter; sie sind für alle Ordnungsaufgaben "
    "nach diesem Gesetz zuständig, soweit nichts anderes bestimmt ist.'"
)

# Bezirk -> (Strasse, PLZ)
BEZIRKE = {
    "Charlottenburg-Wilmersdorf": ("Hohenzollerndamm 174", "10713"),
    "Friedrichshain-Kreuzberg": ("Yorckstraße 4", "10965"),
    "Lichtenberg": ("Alt-Friedrichsfelde 60", "10315"),
    "Marzahn-Hellersdorf": ("Helene-Weigel-Platz 8", "12681"),
    "Mitte": ("Müllerstraße 146", "13353"),
    "Neukölln": ("Karl-Marx-Straße 83", "12043"),
    "Pankow": ("Storkower Straße 97", "10407"),
    "Reinickendorf": ("Eichborndamm 215", "13437"),
    "Spandau": ("Carl-Schurz-Straße 2", "13597"),
    "Steglitz-Zehlendorf": ("Kirchstraße 1", "14163"),
    "Tempelhof-Schöneberg": ("John-F-Kennedy-Platz", "10825"),
    "Treptow-Köpenick": ("Alt-Köpenick 21", "12555"),
}


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
        staging = JurisdictionStagingService(db)
        batch_id = f"denkmalschutz-berlin-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for bezirk, (strasse, plz) in BEZIRKE.items():
            authority_name = f"Untere Denkmalschutzbehörde {bezirk}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Denkmalschutzbehörde (Bezirksamt Berlin)",
                    street=strasse, house_number=None, postal_code=plz, city="Berlin",
                    state="Berlin", phone=None, email=None,
                    source=f"Amtliche Webseite (berlin.de), {SOURCE_URL}",
                    active=True,
                )
                db.add(authority)
                db.flush()

            for request_type_id in ["DENKMALSCHUTZ", "BODENDENKMALSCHUTZ"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Berlin - {bezirk}",
                    request_type_id=request_type_id, state="Berlin", ags=BERLIN_AGS,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE}", source_url=SOURCE_URL,
                    source_license="Amtliche Webseite (berlin.de) + Rechtsgrundlage (DSchG Bln)",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} {c.request_type_id} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
                resulting_verification_status="VERIFIED",
            )
            approved += 1
        db.commit()
        print(f"\n{approved} Regeln freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
