# -*- coding: utf-8 -*-
"""
BODENDENKMALSCHUTZ fuer 6 bayerische Kreise, die trotz sonst fast
vollstaendiger Abdeckung (90 von 96 Kreisen) bisher fehlten:
Pfaffenhofen a.d.Ilm, Straubing-Bogen, Amberg (kreisfreie Stadt),
Neumarkt i.d.OPf., Neustadt a.d.Aisch-Bad Windsheim, Dillingen a.d.Donau.

Keine neue Rechtsgrundlage noetig - die bayerische Struktur (Art. 12/25
BayDSchG: Landratsamt/kreisfreie Stadt als untere Denkmalschutzbehoerde,
zustaendig auch fuer Bodendenkmalpflege) ist in dieser Datenbank bereits
fuer 90 andere bayerische Kreise etabliert. Nur die konkreten Aemter
fuer diese 6 verbleibenden Kreise wurden ergaenzend recherchiert (Amts-
und Kontaktseiten der jeweiligen Landratsaemter/Stadt).

6 neue COUNTY-Regeln.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bodendenkmalschutz-Lücken Bayern)"
AUTHORITY_TYPE = "Untere Denkmalschutzbehörde (Kreisverwaltungsbehörde)"

# ags_kreis -> (Amtsname, Strasse, PLZ, Ort, Quelle-URL)
KREISE = {
    "09186": ("Landratsamt Pfaffenhofen a.d.Ilm - Untere Denkmalschutzbehörde", "Hauptplatz 22", "85276",
              "Pfaffenhofen a.d.Ilm", "https://www.landkreis-pfaffenhofen.de"),
    "09278": ("Landratsamt Straubing-Bogen - Sachgebiet baulicher Denkmalschutz - Denkmalpflege",
              "Leutnerstraße 15", "94315", "Straubing",
              "https://www.landkreis-straubing-bogen.de/politik-verwaltung/organisation-des-landratsamtes/"),
    "09361": ("Stadt Amberg - Untere Denkmalschutzbehörde", "Marktplatz 11", "92224", "Amberg",
              "https://amberg.de/rathaus/lebenslagen/bauverfahren/denkmalschutz-beantragung-einer-erlaubnis-fuer-massnahmen-an-bau-und-bodendenkmaelern"),
    "09373": ("Landratsamt Neumarkt i.d.OPf. - Untere Denkmalschutzbehörde", "Nürnberger Str. 1", "92318",
              "Neumarkt i.d.OPf.", "https://www.landkreis-neumarkt.de/landkreis-neumarkt/landratsamt/wasserrecht/denkmalpflege-6539348/"),
    "09575": ("Landratsamt Neustadt a.d.Aisch-Bad Windsheim - Untere Denkmalschutzbehörde",
              "Konrad-Adenauer-Straße 1/2", "91413", "Neustadt a.d.Aisch",
              "https://www.kreis-nea.de/behoerdenwegweiser-a-z/behoerde/denkmalschutz"),
    "09773": ("Landratsamt Dillingen a.d.Donau - Team 432 Bauamt technisch, Untere Denkmalschutzbehörde",
              "Große Allee 24", "89407", "Dillingen a.d.Donau",
              "https://www.bayernportal.de"),
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
        batch_id = f"bodendenkmalschutz-bayern-luecken-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, (name, strasse, plz, ort, url) in KREISE.items():
            authority = db.query(Authority).filter(Authority.authority_name == name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=name,
                    authority_type=AUTHORITY_TYPE,
                    street=strasse, house_number=None, postal_code=plz, city=ort,
                    state="Bayern", phone=None, email=None,
                    source=f"Amtliche Webseite, {url}",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"BODENDENKMALSCHUTZ Bayern - {name}",
                request_type_id="BODENDENKMALSCHUTZ", state="Bayern", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{name} - Art. 12/25 BayDSchG (Landratsamt/kreisfreie Stadt als untere "
                       "Denkmalschutzbehörde, bereits für 90 andere bayerische Kreise etabliert)",
                source_url=url,
                source_license="Amtliche Rechtsgrundlage (BayDSchG) + amtliche Webseite",
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
