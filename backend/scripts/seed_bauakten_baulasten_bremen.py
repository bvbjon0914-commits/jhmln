"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer BREMEN. Wie bei anderen
Auskunftsarten in diesem Projekt ist die Zustaendigkeit zwischen den
beiden Staedten des Stadtstaats getrennt: § 82 BremLBO (Bremische
Landesbauordnung) regelt Baulasten/Baulastenverzeichnis; fuer
Bauakten/Bauaufsicht ist in Bremen-Stadt "Die Senatorin fuer Bau,
Mobilitaet und Stadtentwicklung" (Bauordnungsamt) zustaendig, in
Bremerhaven der Magistrat der Stadt Bremerhaven (Bauordnungsamt
Bremerhaven) - jeweils amtlich bestaetigt ueber service.bremen.de bzw.
bremerhaven.de. Beide Staedte fuehren auch das jeweilige
Baulastenverzeichnis fuer ihr Gebiet (Baulastenauskunft wird laut
service.bremen.de "bei der unteren Bauaufsichtsbehoerde" beantragt).

2 neue COUNTY-Regeln je Auskunftsart (Bremen-Stadt, Bremerhaven) = 4
Regeln insgesamt (abzueglich etwaiger bereits bestehender
Alt-Abdeckung, die der Konfliktpruefung korrekt als Duplikat erkannt
und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Bremen)"
QUOTE = ("service.bremen.de: 'Auskunft aus dem Baulastenverzeichnis' wird bei der unteren "
         "Bauaufsichtsbehörde beantragt. Bremerhaven: 'Die Verwaltungsabteilung des "
         "Bauordnungsamtes gewährt Einsicht und gibt Auskunft aus archivierten Bauakten.'")

EINHEITEN = {
    "04011": dict(
        name="Die Senatorin für Bau, Mobilität und Stadtentwicklung - Bauordnungsamt Bremen",
        street="Contrescarpe 72", plz="28195", city="Bremen", email="office@bau.bremen.de",
        url="https://www.service.bremen.de/dienstleistungen/auskunft-aus-dem-baulastenverzeichnis-beantragen-196543",
    ),
    "04012": dict(
        name="Magistrat der Stadt Bremerhaven - Bauordnungsamt",
        street="Fährstraße 20 (Technisches Rathaus)", plz="27568", city="Bremerhaven",
        email="bauordnungsamt@magistrat.bremerhaven.de",
        url="https://www.bremerhaven.de/de/verwaltung-politik-sicherheit/buergerservice/dienstleistungen/"
            "akteneinsicht-und-auskunft-aus-archivierten-bauakten.35307.html",
    ),
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
        batch_id = f"bauakten-baulasten-bremen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, info in EINHEITEN.items():
                authority = db.query(Authority).filter(Authority.authority_name == info["name"]).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=info["name"],
                        authority_type="Untere Bauaufsichtsbehörde (Stadtgemeinde)",
                        street=info["street"], house_number=None, postal_code=info["plz"], city=info["city"],
                        state="Bremen", phone=None, email=info["email"],
                        source=f"Amtliche Quelle, recherchiert 2026-09-28: {info['url']}",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Bremen",
                    request_type_id=request_type_id, state="Bremen", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{info['name']} - {QUOTE}", source_url=info["url"],
                    source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
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
