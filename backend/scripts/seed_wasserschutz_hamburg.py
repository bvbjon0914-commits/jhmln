# -*- coding: utf-8 -*-
"""
WASSERSCHUTZ (Wasserschutzgebiete, Grundwasserschutz) fuer HAMBURG.
Bislang die einzige verbleibende echte Luecke bei WASSERSCHUTZ
bundesweit (alle anderen 15 Laender vollstaendig abgedeckt).

Anders als bei den meisten anderen Hamburger Auskunftsarten in dieser
Datenbank (Bauaufsicht: bezirklich, 7 Bezirksaemter) ist WASSERSCHUTZ
in Hamburg ZENTRAL bei der Behoerde fuer Umwelt, Klima, Energie und
Agrarwirtschaft (BUKEA) organisiert, NICHT bezirklich - die 7
bezirklichen "unteren Wasserbehoerden" sind laut ihren eigenen
Webseiten nur fuer Gewaesserbenutzung/-aufsicht an oberirdischen
Gewaessern II. Ordnung zustaendig (Einleitungen, Stege,
Uferbefestigungen), nicht fuer Wasserschutzgebiete/Grundwasserschutz.

Beleg (woertliches Zitat, amtliche hamburg.de-Quelle):
"Fuer die Entnahme von Grundwasser durch Foerderbrunnen ist in der
Regel eine Wasserrechtliche Erlaubnis bei der Behoerde fuer Umwelt,
Klima, Energie und Agrarwirtschaft (W12) zu beantragen." und "In
Wasserschutzgebieten ist zusaetzlich zu der wasserrechtlichen
Erlaubnis oder Anzeige eine Befreiung gemaess Wasserhaushaltsgesetz zu
beantragen." Bestaetigt durch die konkrete Leistungsseite
"Wasserrechtliche Befreiung ... im Wasserschutzgebiet beantragen":
zustaendige Stelle ist die Behoerde fuer Umwelt, Klima, Energie und
Agrarwirtschaft, Abteilung Wasserwirtschaft, Amt Wasser, Abwasser und
Geologie, Referat W12 "Schutz und Bewirtschaftung des Grundwassers /
Wasserschutzgebiete", Neuenfelder Strasse 19, 21109 Hamburg.

HOCHWASSERSCHUTZ (Ueberschwemmungsgebiete) wurde bewusst NICHT in
dieser Sitzung nachgezogen: der Vollzug ist dort tatsaechlich
bezirklich, aber die Zustaendigkeit haengt vom konkret betroffenen
benannten Gewaesser ab (z.B. Bezirksamt Bergedorf fuer Brookwetterung/
Dove-Elbe/Gose-Elbe), nicht von einer gleichmaessigen bezirklichen
Flaechenaufteilung wie bei der Bauaufsicht - eine einzelne Adresse
liegt nicht automatisch "im Bezirk X, also zustaendig fuer HWS", da
die meisten Grundstuecke im Bezirk gar nicht in einem
Ueberschwemmungsgebiet liegen. Dieses Datenmodell (ags/Strasse-
basiertes Dispatch) kann diese Gewaesser-bezogene Differenzierung
nicht abbilden, ohne Grundstuecke faelschlich einem Bezirk pauschal
zuzuordnen. Zudem ist die Bezirks-Zustaendigkeit fuer 5 seit 2017 neu
hinzugekommene Ueberschwemmungsgebiete (Alster, Bille, Wandse u.a.)
nicht amtlich eindeutig belegt. Bewusst als OFFEN dokumentiert statt
geraten.

1 neue MUNICIPALITY-Regel (ags=02000000, zentrale BUKEA-Zustaendigkeit).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Wasserschutz Hamburg)"
HAMBURG_AGS = "02000000"
SOURCE_URL = "https://www.hamburg.de/politik-und-verwaltung/behoerden/bukea/themen/wasser/grundwasser/grundwasserfoerderungen-176062"
QUOTE = (
    "Behörde für Umwelt, Klima, Energie und Agrarwirtschaft (BUKEA), Amt Wasser, Abwasser und "
    "Geologie, Referat W12 'Schutz und Bewirtschaftung des Grundwassers / Wasserschutzgebiete': "
    "'Für die Entnahme von Grundwasser durch Förderbrunnen ist in der Regel eine Wasserrechtliche "
    "Erlaubnis bei der Behörde für Umwelt, Klima, Energie und Agrarwirtschaft (W12) zu beantragen.' "
    "'In Wasserschutzgebieten ist zusätzlich zu der wasserrechtlichen Erlaubnis oder Anzeige eine "
    "Befreiung gemäß Wasserhaushaltsgesetz zu beantragen.' Bestätigt durch die Leistungsseite "
    "'Wasserrechtliche Befreiung ... im Wasserschutzgebiet beantragen' (zuständige Stelle: BUKEA, "
    "Abteilung Wasserwirtschaft, Neuenfelder Straße 19, 21109 Hamburg)."
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
        authority_name = "Behörde für Umwelt, Klima, Energie und Agrarwirtschaft (BUKEA) - Referat W12 Wasserschutzgebiete"
        authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
        if authority is None:
            authority = Authority(
                authority_id=str(uuid.uuid4()), authority_name=authority_name,
                authority_type="Zentrale Wasserbehörde (Land Hamburg)",
                street="Neuenfelder Straße 19", house_number=None, postal_code="21109", city="Hamburg",
                state="Hamburg", phone=None, email=None,
                source=f"Amtliche Webseite (hamburg.de), {SOURCE_URL}",
                active=True,
            )
            db.add(authority)
            db.flush()

        staging = JurisdictionStagingService(db)
        batch_id = f"wasserschutz-hamburg-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        entry = staging.stage_entry(
            batch_id=batch_id, batch_label="WASSERSCHUTZ Hamburg - zentral BUKEA",
            request_type_id="WASSERSCHUTZ", state="Hamburg", ags=HAMBURG_AGS,
            matching_level=MatchingLevel.MUNICIPALITY, priority=40,
            proposed_authority_id=authority.authority_id,
            source=f"{authority_name} - {QUOTE}", source_url=SOURCE_URL,
            source_license="Amtliche Webseite (hamburg.de)",
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
