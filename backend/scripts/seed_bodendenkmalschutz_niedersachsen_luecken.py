# -*- coding: utf-8 -*-
"""
BODENDENKMALSCHUTZ fuer 4 niedersaechsische Kreise, die trotz sonst
fast vollstaendiger Abdeckung (41 von 45 Kreisen) bisher fehlten:
Region Hannover, Harburg, Heidekreis, Grafschaft Bentheim.

Keine neue Rechtsgrundlage noetig - die niedersaechsische Struktur
(§ 19 Abs. 1 NDSchG: Landkreis/kreisfreie Stadt/grosse selbstaendige
Stadt als untere Denkmalschutzbehoerde) ist in dieser Datenbank
bereits fuer 41 andere niedersaechsische Kreise etabliert.

Bekannte Einschraenkung Region Hannover (bewusst nicht einzeln
modelliert, siehe Kreis-Ebene-Konvention dieser Kampagne): die Region
uebt die Bauaufsicht/Denkmalschutzaufgaben nur fuer 8 Mitgliedskommunen
direkt aus (Burgwedel, Gehrden, Hemmingen, Isernhagen, Pattensen,
Sehnde, Uetze, Wennigsen); die Landeshauptstadt Hannover sowie 12
weitere grosse selbstaendige Staedte der Region (Barsinghausen,
Burgdorf, Garbsen, Laatzen, Langenhagen, Lehrte, Neustadt a. Rbge.,
Ronnenberg, Seelze, Springe, Wedemark, Wunstorf) haben eigene untere
Denkmalschutzbehoerden. Diese Regel gilt als COUNTY-Level-Fallback
(Prioritaet 50); bereits bestehende oder kuenftige MUNICIPALITY-Level-
Regeln fuer die genannten selbstaendigen Staedte (Prioritaet 40)
nehmen automatisch Vorrang - konsistent mit dem in dieser gesamten
Kampagne etablierten Kreis+Ausnahme-Muster.

Ebenfalls hinweishalber: Grafschaft Bentheim hat mit der Stadt
Nordhorn (grosse selbstaendige Stadt) eine aehnliche Teil-Ausnahme -
auch hier gilt: bestehende MUNICIPALITY-Regeln fuer Nordhorn haben
Vorrang vor dieser COUNTY-Regel.

4 neue COUNTY-Regeln.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bodendenkmalschutz-Lücken Niedersachsen)"
AUTHORITY_TYPE = "Untere Denkmalschutzbehörde (Kreisverwaltungsbehörde)"

# ags_kreis -> (Amtsname, Strasse, PLZ, Ort, Quelle-URL)
KREISE = {
    "03241": ("Region Hannover - Fachbereich Bauen, Untere Denkmalschutzbehörde", "Hildesheimer Straße 20",
              "30169", "Hannover", "https://www.hannover.de"),
    "03353": ("Landkreis Harburg - Fachbereich Bauen, Untere Denkmalschutzbehörde", "Schloßplatz 6", "21423",
              "Winsen (Luhe)", "https://www.landkreis-harburg.de/buergerservice/dienstleistungen/bodendenkmalpflege-1573-0.html"),
    "03358": ("Landkreis Heidekreis - Untere Denkmalschutzbehörde", "Harburger Str. 2", "29614", "Soltau",
              "https://www.heidekreis.de/bauen-planen/denkmalpflege.html"),
    "03456": ("Landkreis Grafschaft Bentheim - Untere Denkmalschutzbehörde", "Stadtring 22", "48529",
              "Nordhorn", "https://www.grafschaft-bentheim.de/grafschaft/buergerservice/"),
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
        batch_id = f"bodendenkmalschutz-niedersachsen-luecken-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, (name, strasse, plz, ort, url) in KREISE.items():
            authority = db.query(Authority).filter(Authority.authority_name == name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=name,
                    authority_type=AUTHORITY_TYPE,
                    street=strasse, house_number=None, postal_code=plz, city=ort,
                    state="Niedersachsen", phone=None, email=None,
                    source=f"Amtliche Webseite, {url}",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"BODENDENKMALSCHUTZ Niedersachsen - {name}",
                request_type_id="BODENDENKMALSCHUTZ", state="Niedersachsen", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{name} - § 19 Abs. 1 NDSchG (Landkreis als untere Denkmalschutzbehörde, "
                       "bereits für 41 andere niedersächsische Kreise etabliert)",
                source_url=url,
                source_license="Amtliche Rechtsgrundlage (NDSchG) + amtliche Webseite",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

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
