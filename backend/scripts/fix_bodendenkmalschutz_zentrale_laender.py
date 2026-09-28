"""
BODENDENKMALSCHUTZ (Genehmigung von Nachforschungen/Grabungen mit dem
Ziel, Bodendenkmale zu entdecken) - Ergänzung für 5 Bundesländer, in
denen (anders als in Bayern, siehe seed_bodendenkmalschutz_bayern.py,
wo die Kreisverwaltungsbehörde zuständig ist) die eigentliche
Grabungsgenehmigung bei EINER zentralen Landesbehörde liegt:

- Baden-Württemberg: Landesamt für Denkmalpflege im Regierungspräsidium
  Stuttgart (§ 21 DSchG BW - Nachforschungen).
- Mecklenburg-Vorpommern: Landesamt für Kultur und Denkmalpflege M-V
  (LAKD), Abteilung Landesarchäologie (§ 12 DSchG M-V - Nachforschungen,
  Zuständigkeit der OBERSTEN Denkmalschutzbehörde, fachlich vorbereitet
  vom LAKD als Denkmalfachbehörde).
- Thüringen: Thüringisches Landesamt für Denkmalpflege und Archäologie
  (TLDA) (§ 18 ThürDSchG - Nachforschungen, Zuständigkeit der
  Denkmalfachbehörde).
- Hessen: Landesamt für Denkmalpflege Hessen / hessenARCHÄOLOGIE (§ 22
  HDSchG - Nachforschungsgenehmigung, unabhängig von der Kreisebene).
- Sachsen: Landesamt für Archäologie Sachsen (§ 14 Abs. 2 SächsDSchG -
  Nachforschungen/Grabungen zum Auffinden von Kulturdenkmalen,
  Zuständigkeit der Fachbehörde; DAVON ZU UNTERSCHEIDEN: § 14 Abs. 1
  SächsDSchG regelt Erdarbeiten an BEREITS BEKANNTEN Bodendenkmal-
  Fundstellen, wofür die untere Denkmalschutzbehörde - Landkreis/
  kreisfreie Stadt - im Einvernehmen mit dem Landesamt zuständig ist;
  diese engere/andere Fallgruppe ist hier bewusst NICHT abgedeckt, siehe
  Docstring-Hinweis unten).

Alle Behörden-Namen/Adressen wurden per Recherche-Agent gefunden und
zusätzlich eigenständig nachverifiziert: Hessen per curl direkt gegen
denkmal.hessen.de/impressum (bestätigt: Schloss Biebrich, 65203
Wiesbaden, sowie die URL-Struktur /hessenarchaeologie/nachforschungs-
genehmigungen); die übrigen vier durch einen zweiten, gezielten
Recherche-Agenten direkt gegen die jeweilige Behörden-Kontakt-/
Impressumsseite.

Niedersachsen bewusst NICHT in diesem Skript: dort liegt die
Zuständigkeit auf KREIS-Ebene (wie in Bayern), aber mit einer
zusätzlichen Komplikation (Gemeinden mit eigener unterer
Bauaufsichtsbehörde können eine eigene, von ihrem Landkreis getrennte
Zuständigkeit haben) - erfordert eine eigene, sorgfältiger geprüfte
Kampagne wie in Bayern, nicht eine einzelne Landesregel.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, zentrale Landesbehoerden Bodendenkmalschutz)"

LAENDER = [
    dict(
        state="Baden-Württemberg",
        authority_name="Landesamt für Denkmalpflege im Regierungspräsidium Stuttgart",
        street="Berliner Straße 12", postal_code="73728", city="Esslingen am Neckar",
        email="abteilung8@rps.bwl.de", phone="0711 904-0",
        url="https://rps.baden-wuerttemberg.de/abt8/",
        quote="§ 21 DSchG BW: Nachforschungen/Grabungen bedürfen der Genehmigung des Landesamts für Denkmalpflege - amtlich bestätigt über rps.baden-wuerttemberg.de/abt8/ und denkmalpflege-bw.de/kontakt",
    ),
    dict(
        state="Mecklenburg-Vorpommern",
        authority_name="Landesamt für Kultur und Denkmalpflege Mecklenburg-Vorpommern (LAKD) - Abteilung Landesarchäologie",
        street="Domhof 4/5", postal_code="19055", city="Schwerin",
        email="poststelle@lakd-mv.de", phone="0385 58879111",
        url="https://www.kulturwerte-mv.de/Service/Impressum/",
        quote="§ 12 DSchG M-V: Nachforschungen/Grabungen zum Entdecken von Bodendenkmalen bedürfen der Genehmigung der obersten Denkmalschutzbehörde, fachlich vorbereitet vom LAKD als Denkmalfachbehörde - Adresse amtlich per Impressum bestätigt",
    ),
    dict(
        state="Thüringen",
        authority_name="Thüringisches Landesamt für Denkmalpflege und Archäologie (TLDA)",
        street="Humboldtstraße 11", postal_code="99423", city="Weimar",
        email="post.erfurt@tlda.thueringen.de", phone="0361 57322-3300",
        url="https://bodendenkmale-thueringen.de/impressum",
        quote="§ 18 ThürDSchG: Nachforschungen/Grabungen zum Entdecken von Bodendenkmalen bedürfen der Genehmigung der Denkmalfachbehörde (TLDA) - Adresse amtlich per Impressum des offiziellen TLDA-Bodendenkmal-Portals bestätigt",
    ),
    dict(
        state="Hessen",
        authority_name="Landesamt für Denkmalpflege Hessen - hessenARCHÄOLOGIE",
        street="Schloss Biebrich", postal_code="65203", city="Wiesbaden",
        email=None, phone=None,
        url="https://denkmal.hessen.de/hessenarchaeologie/nachforschungs-genehmigungen",
        quote="§ 22 HDSchG: Die Nachforschungsgenehmigung wird vom Landesamt für Denkmalpflege Hessen, Abteilung hessenARCHÄOLOGIE erteilt - eigenständig per curl gegen denkmal.hessen.de/impressum verifiziert (Schloss Biebrich, 65203 Wiesbaden)",
    ),
    dict(
        state="Sachsen",
        authority_name="Landesamt für Archäologie Sachsen",
        street="Zur Wetterwarte 7", postal_code="01109", city="Dresden",
        email="info@lfa.sachsen.de", phone="0351 8926-199",
        url="https://www.lfa.sachsen.de/kontakt-anschrift-anreise-3970.html",
        quote="§ 14 Abs. 2 SächsDSchG: Nachforschungen/Grabungen zum Auffinden von Kulturdenkmalen bedürfen der Genehmigung der Fachbehörde (Landesamt für Archäologie) - Adresse amtlich per Kontaktseite bestätigt. Betrifft NICHT § 14 Abs. 1 (Erdarbeiten an bereits bekannten Fundstellen - dort ist die untere Denkmalschutzbehörde des Landkreises zuständig, hier nicht abgedeckt)",
    ),
]


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
        batch_id = f"bodendenkmalschutz-zentrale-laender-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for info in LAENDER:
            authority = db.query(Authority).filter(Authority.authority_name == info["authority_name"]).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=info["authority_name"],
                    authority_type="Landesamt für Denkmalpflege/Archäologie (Denkmalfachbehörde)",
                    street=info["street"], house_number=None, postal_code=info["postal_code"],
                    city=info["city"], state=info["state"], phone=info["phone"], email=info["email"],
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {info['authority_name']}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz - zentrale Landesbehoerden",
                request_type_id="BODENDENKMALSCHUTZ", state=info["state"], ags=None,
                matching_level=MatchingLevel.STATE, priority=60,
                proposed_authority_id=authority.authority_id,
                source=f"{info['authority_name']} - {info['quote']}", source_url=info["url"],
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts:
            print(f"  KONFLIKT #{c.id} state={c.state} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, info in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=info["quote"],
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
