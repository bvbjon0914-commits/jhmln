"""
BODENDENKMALSCHUTZ - zweite Runde zentraler Landesbehörden (Fortsetzung
von fix_bodendenkmalschutz_zentrale_laender.py), auf Basis eines
weiteren Recon-Agenten-Durchlaufs zu Berlin, Brandenburg, Bremen,
Hamburg und Nordrhein-Westfalen:

- Brandenburg: Brandenburgisches Landesamt für Denkmalpflege und
  Archäologisches Landesmuseum (BLDAM) (§ 10 Abs. 1 BbgDSchG - die
  Genehmigung für Nachforschungen/Grabungen liegt ausdrücklich bei der
  Denkmalfachbehörde, NICHT bei den unteren Denkmalschutzbehörden der
  Kreise). Adresse eigenständig per curl gegen bldam-brandenburg.de/
  impressum verifiziert.
- Bremen: Landesamt für Denkmalpflege (Landesarchäologie) - gilt laut
  Recherche-Agent AUSDRÜCKLICH für BEIDE Stadtgemeinden (Bremen UND
  Bremerhaven) zentral, anders als die allgemeine (Bau-)Denkmalschutz-
  Zuständigkeit, die zwischen den beiden Städten aufgeteilt ist (siehe
  die bereits bestehende, separate DENKMALSCHUTZ-Regel aus einem
  früheren Durchlauf dieser Sitzung). Deshalb hier STATE-Ebene statt
  zwei einzelner MUNICIPALITY-Regeln. Wiederverwendet dieselbe, bereits
  in der Datenbank vorhandene Authority "Landesamt für Denkmalpflege
  Bremen" (nur für Bremen-Stadt angelegt) NICHT - da diese laut ihrem
  bestehenden Namen ausdrücklich auf die Stadtgemeinde Bremen beschränkt
  ist, wird für die hier abweichende bundeslandweite Bodendenkmalpflege-
  Zuständigkeit eine eigene, korrekt benannte Authority angelegt.
- Hamburg: Archäologisches Museum Hamburg (Helms-Museum) - eigenständig
  per curl gegen amh.de verifiziert (Museumsplatz 2, 21073 Hamburg).
  Anders als bei anderen Auskunftsarten in Hamburg (z.B. Wasserbehörden)
  gibt es hier KEINE bezirkliche Aufteilung.

Saarland (Landesdenkmalamt des Saarlandes) und Berlin (bezirkliche
Zuständigkeit) bewusst NICHT in diesem Skript:
- Saarland: Adresse (Am Bergwerk Reden 11, 66578 Schiffweiler) konnte
  wegen Bot-Schutz (Bunny Shield) auf saarland.de nicht eigenständig
  nachverifiziert werden - wird zurückgestellt, bis eine zweite,
  unabhängige amtliche Quelle geprüft werden kann, statt eine nur
  einfach-belegte Adresse zu übernehmen.
- Berlin: dieselbe strukturelle Einschränkung wie bei den bereits in
  Abschnitt 14 dokumentierten Berlin/Hamburg-Bezirksamt-Fällen (nur 1
  AGS für ganz Berlin in AdministrativeUnit, echte bezirkliche
  Zuständigkeit erfordert Gebäude-district-Daten, die nicht vorliegen).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, zentrale Landesbehoerden Bodendenkmalschutz Runde 2)"

LAENDER = [
    dict(
        state="Brandenburg",
        authority_name="Brandenburgisches Landesamt für Denkmalpflege und Archäologisches Landesmuseum (BLDAM)",
        street="Wünsdorfer Platz 4", postal_code="15806", city="Zossen OT Wünsdorf",
        email=None, phone="033702 211-1200",
        url="https://bldam-brandenburg.de/impressum/",
        quote="§ 10 Abs. 1 BbgDSchG: 'Wer nach Bodendenkmalen zielgerichtet mit technischen Hilfsmitteln suchen, nach Bodendenkmalen graben oder Bodendenkmale aus einem Gewässer bergen will, bedarf der Erlaubnis der Denkmalfachbehörde.' - Adresse eigenständig per curl gegen bldam-brandenburg.de/impressum verifiziert",
    ),
    dict(
        state="Bremen",
        authority_name="Landesamt für Denkmalpflege Bremen - Landesarchäologie (Bodendenkmalpflege, Bremen und Bremerhaven)",
        street=None, postal_code=None, city="Bremen",
        email=None, phone=None,
        url="https://www.landesarchaeologie.bremen.de/aufgaben/ausgrabungen/ausgrabungen-bremerhaven-9851",
        quote="Landesarchäologie ist für Bodendenkmalpflege zentral für BEIDE Stadtgemeinden (Bremen und Bremerhaven) zuständig, anders als die allgemeine Baudenkmalschutz-Zuständigkeit (die zwischen beiden Städten aufgeteilt ist) - eigene Rubrik 'Ausgrabungen Bremerhaven' bestätigt die Zuständigkeit auch für Bremerhaven",
    ),
    dict(
        state="Hamburg",
        authority_name="Archäologisches Museum Hamburg (Helms-Museum)",
        street="Museumsplatz 2", postal_code="21073", city="Hamburg",
        email=None, phone=None,
        url="https://amh.de/museum/archaeologie/bodendenkmalpflege-stadt-hamburg/",
        quote="§ 14 Abs. 5 DSchG HH: der Senat bestimmt per Rechtsverordnung die zuständige Stelle für Bodendenkmalpflege = Archäologisches Museum Hamburg. Keine bezirkliche Aufteilung. Adresse eigenständig per curl gegen amh.de verifiziert",
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
        batch_id = f"bodendenkmalschutz-zentrale-laender-2-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
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
                batch_id=batch_id, batch_label="Bodendenkmalschutz - zentrale Landesbehoerden Runde 2",
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
