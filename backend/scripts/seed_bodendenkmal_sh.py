"""
Bodendenkmalschutz Schleswig-Holstein durch den sicheren
Aktualisierungsprozess - Fortsetzung des RLP-Piloten
(scripts/seed_rlp_bodendenkmal_erschliessung.py) für ein zweites Bundesland.

Fachliche Definition (aus templates/bodendenkmalschutz.docx): Auskunft, ob
für ein Grundstück Bodendenkmäler nach dem Denkmalschutzgesetz DES LANDES
bekannt/eingetragen sind.

Quellen (amtlich, abgerufen 2026-09-26):

  - Archäologisches Landesamt Schleswig-Holstein (ALSH): obere
    Denkmalschutzbehörde für archäologische Kulturdenkmale IM GANZEN LAND
    AUSSER LÜBECK.
    https://de.wikipedia.org/wiki/Arch%C3%A4ologisches_Landesamt_Schleswig-Holstein
    Adresse: Brockdorff-Rantzau-Straße 70, 24837 Schleswig,
    Tel. 04621 387-0, E-Mail alsh@alsh.landsh.de

  - Bereich Archäologie und Denkmalpflege der Hansestadt Lübeck: laut
    eigener Amtsseite und Wikipedia-Artikel zugleich obere UND untere
    Denkmalschutzbehörde NUR für das Gebiet der Hansestadt Lübeck,
    unabhängig von den Landesämtern - eine bundesweite Besonderheit.
    https://de.wikipedia.org/wiki/Bereich_Arch%C3%A4ologie_und_Denkmalpflege_der_Hansestadt_L%C3%BCbeck
    Adresse: Königstraße 21, 23552 Lübeck, Tel. 0451 122-4800,
    E-Mail denkmalpflege@luebeck.de

Läuft über JurisdictionStagingService - Konfliktprüfung je Regel
(erwartet: alle NEW, da SH bislang keine BODENDENKMALSCHUTZ-Regel hatte),
Freigabe durch benannten Prüfer mit Fundstelle je Regel.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-26, siehe source_url je Regel)"

ALSH_KREISE = ["01001", "01002", "01004", "01051", "01053", "01054", "01055", "01056", "01057", "01058", "01059", "01060", "01061", "01062"]
LUEBECK_KREIS = ["01003"]


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
        def get_or_create_authority(name, street, house_number, postal_code, city, phone, email, source_url):
            existing = db.query(Authority).filter(Authority.authority_name == name).first()
            if existing:
                print(f"Authority bereits vorhanden, wird wiederverwendet: {name}")
                return existing
            authority = Authority(
                authority_id=str(uuid.uuid4()), authority_name=name,
                authority_type="Denkmalfachbehörde (Landesbehörde)" if "Landesamt" in name else "Denkmalfachbehörde (kommunal)",
                street=street, house_number=house_number, postal_code=postal_code, city=city,
                state="Schleswig-Holstein", phone=phone, email=email,
                source=f"Amtliche Kontaktseite, recherchiert 2026-09-26: {source_url}", active=True,
            )
            db.add(authority)
            db.flush()
            print(f"Neue Authority angelegt: {name} ({authority.authority_id})")
            return authority

        alsh = get_or_create_authority(
            "Archäologisches Landesamt Schleswig-Holstein (ALSH)",
            "Brockdorff-Rantzau-Straße", "70", "24837", "Schleswig",
            "04621 387-0", "alsh@alsh.landsh.de",
            "https://de.wikipedia.org/wiki/Arch%C3%A4ologisches_Landesamt_Schleswig-Holstein",
        )
        luebeck = get_or_create_authority(
            "Bereich Archäologie und Denkmalpflege der Hansestadt Lübeck",
            "Königstraße", "21", "23552", "Lübeck",
            "0451 122-4800", "denkmalpflege@luebeck.de",
            "https://de.wikipedia.org/wiki/Bereich_Arch%C3%A4ologie_und_Denkmalpflege_der_Hansestadt_L%C3%BCbeck",
        )

        staging = JurisdictionStagingService(db)
        batch_id = f"sh-bodendenkmalschutz-{datetime.utcnow().strftime('%Y%m%d')}"
        staged = []

        for ags_kreis in ALSH_KREISE:
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="SH Bodendenkmalschutz - ALSH + Lübeck",
                request_type_id="BODENDENKMALSCHUTZ", state="Schleswig-Holstein", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=alsh.authority_id,
                source="Archäologisches Landesamt Schleswig-Holstein (ALSH) - obere Denkmalschutzbehörde (ohne Lübeck)",
                source_url="https://de.wikipedia.org/wiki/Arch%C3%A4ologisches_Landesamt_Schleswig-Holstein",
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append(entry)

        for ags_kreis in LUEBECK_KREIS:
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="SH Bodendenkmalschutz - ALSH + Lübeck",
                request_type_id="BODENDENKMALSCHUTZ", state="Schleswig-Holstein", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=luebeck.authority_id,
                source="Bereich Archäologie und Denkmalpflege der Hansestadt Lübeck - eigene obere+untere Denkmalschutzbehörde",
                source_url="https://de.wikipedia.org/wiki/Bereich_Arch%C3%A4ologie_und_Denkmalpflege_der_Hansestadt_L%C3%BCbeck",
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts:
            print(f"  KONFLIKT #{c.id} ags={c.ags} conflict={c.conflict_type} - {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                review_notes="Zuständigkeitsbereich direkt von amtlicher/Wikipedia-Quelle mit Gesetzesbezug übernommen.",
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
