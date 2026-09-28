# -*- coding: utf-8 -*-
"""
BODENDENKMALSCHUTZ fuer 6 nordrhein-westfaelische Kreise, die trotz
sonst fast vollstaendiger Abdeckung (47 von 53 Kreisen) bisher
fehlten: Dueren, Rhein-Erft-Kreis, Borken, Herford, Hoexter, Soest.

Keine neue Rechtsgrundlage noetig - die NRW-Struktur ist in dieser
Datenbank bereits fuer 47 andere nordrhein-westfaelische Kreise
etabliert: nach DSchG NRW sind die Gemeinden untere Denkmalbehoerden,
der Kreis fungiert als OBERE Denkmalbehoerde (Landrat als untere
staatliche Verwaltungsbehoerde) - zustaendig u.a. fuer
Grabungserlaubnisse nach § 15 DSchG NRW, Genehmigung von
Denkmalbereichssatzungen und Fundmeldungen. Konsistent mit dem bereits
etablierten Muster (authority_type "Obere Denkmalbehoerde (Landrat als
untere staatliche Verwaltungsbehoerde)") wird der Kreis auch hier als
Fixpunkt fuer BODENDENKMALSCHUTZ-Anfragen verwendet, NICHT als "untere"
Behoerde.

6 neue COUNTY-Regeln.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bodendenkmalschutz-Lücken NRW)"
AUTHORITY_TYPE = "Obere Denkmalbehörde (Landrat als untere staatliche Verwaltungsbehörde)"

# ags_kreis -> (Amtsname, Strasse, PLZ, Ort, Quelle-URL)
KREISE = {
    "05358": ("Kreis Düren - Obere Denkmalbehörde", "Bismarckstraße 16", "52351", "Düren",
              "https://www.kreis-dueren.de"),
    "05362": ("Rhein-Erft-Kreis - Obere Denkmalbehörde", "Willy-Brandt-Platz 1", "50126", "Bergheim",
              "https://www.rhein-erft-kreis.de/kultur/denkmalschutz.php"),
    "05554": ("Kreis Borken - Obere Denkmalbehörde", "Burloer Straße 93", "46325", "Borken",
              "https://www.kreis-borken.de/denkmalpflege"),
    "05758": ("Kreis Herford - Obere Denkmalbehörde", "Amtshausstraße 3", "32051", "Herford",
              "https://www.kreis-herford.de"),
    "05762": ("Kreis Höxter - Obere Denkmalbehörde", "Moltkestraße 12", "37671", "Höxter",
              "https://www.kreis-hoexter.de/buergerservice/ansprechpersonen"),
    "05974": ("Kreis Soest - Obere Denkmalbehörde", "Hoher Weg 1-3", "59494", "Soest",
              "https://www.kreis-soest.de"),
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
        batch_id = f"bodendenkmalschutz-nrw-luecken-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, (name, strasse, plz, ort, url) in KREISE.items():
            authority = db.query(Authority).filter(Authority.authority_name == name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=name,
                    authority_type=AUTHORITY_TYPE,
                    street=strasse, house_number=None, postal_code=plz, city=ort,
                    state="Nordrhein-Westfalen", phone=None, email=None,
                    source=f"Amtliche Webseite, {url}",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label=f"BODENDENKMALSCHUTZ NRW - {name}",
                request_type_id="BODENDENKMALSCHUTZ", state="Nordrhein-Westfalen", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{name} - DSchG NRW (Kreis als Obere Denkmalbehörde, § 15 DSchG NRW "
                       "Grabungserlaubnisse; bereits für 47 andere NRW-Kreise etabliert)",
                source_url=url,
                source_license="Amtliche Rechtsgrundlage (DSchG NRW) + amtliche Webseite",
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
