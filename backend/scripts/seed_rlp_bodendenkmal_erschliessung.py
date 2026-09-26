"""
Pilot-Datenübernahme: BODENDENKMALSCHUTZ (ganz Rheinland-Pfalz) und
ERSCHLIESSUNG (Stadt Trier, als Einzelfall) durch den sicheren
Aktualisierungsprozess (JurisdictionStagingService).

Quellen (alle amtlich, in dieser Sitzung einzeln recherchiert - siehe
docs/COVERAGE_ANALYSIS_REPORT.md für den Kontext der Lückenanalyse):

  - GDKE (Generaldirektion Kulturelles Erbe Rheinland-Pfalz), Direktion
    Landesarchäologie: vier Außenstellen mit klar abgegrenzten
    Zuständigkeitsbereichen je Landkreis/kreisfreie Stadt.
      * Koblenz:  https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-koblenz
      * Mainz:    https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-mainz
      * Trier:    https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-trier
      * Speyer:   https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-speyer
        (nennt nur "Gebiet der Pfalz", KEINE explizite Kreisliste - die
        16 zugeordneten Kreise/Städte hier sind durch Ausschluss aus der
        vollständigen amtlichen Liste der 24 Landkreise + 12 kreisfreien
        Städte [https://de.wikipedia.org/wiki/Liste_der_Landkreise_und_kreisfreien_St%C3%A4dte_in_Rheinland-Pfalz]
        abzüglich der explizit den drei anderen Außenstellen zugeordneten
        20 Einheiten ermittelt - NICHT von der Quelle selbst benannt.
        Deshalb eigener, niedrigerer Beleg-Vermerk in `notes`.)
    Rechtsgrundlage: § 25 Abs. 3 Denkmalschutzgesetz (DSchG) Rheinland-Pfalz
    (GDKE als Denkmalfachbehörde); §§ 18, 21 DSchG (Fundmeldung/Anzeigepflicht
    bei der Denkmalfachbehörde).

  - Stadt Trier, StadtRaum Trier (Beitragsabteilung SRT): zuständig für
    Erschließungsbeiträge gemäß § 127 ff. BauGB i.V.m. der städtischen
    Erschließungsbeitragssatzung.
      https://www.trier.de/service/dienstleistungen-a-z/zusatzinformationen-mter/7595.Ausbaubeitraege-und-Erschliessungsbeitraege.html
    HINWEIS: die Quelle bestätigt NICHT ausdrücklich, dass dieselbe Stelle
    auch "Anliegerbescheinigungen" ausstellt (der zweite Teil des
    Auskunftsart-Namens) - deshalb in `notes` als offene Prüffrage vermerkt,
    NICHT als bestätigt dargestellt.

Läuft NUR gegen die lokale Entwicklungsdatenbank. Legt zuerst die
benötigten Authority-Zeilen an (idempotent - prüft vorher auf Duplikate),
staged dann jede Regel einzeln über JurisdictionStagingService (inkl.
Konfliktprüfung) und gibt erst danach - mit explizit benanntem Prüfer -
die Freigabe. Kein Schritt überspringt die Konfliktprüfung.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-26, siehe source_url je Regel)"

# (ags_kreis, name_zur_dokumentation) - direkt aus den amtlichen Außenstellen-Seiten
KOBLENZ_KREISE = ["07111", "07131", "07132", "07135", "07137", "07138", "07140", "07141", "07143"]
MAINZ_KREISE = ["07133", "07315", "07319", "07331", "07339"]
TRIER_KREISE = ["07134", "07211", "07231", "07232", "07233", "07235"]
# Nicht explizit von der Quelle benannt - durch Ausschluss ermittelt, siehe Docstring oben.
SPEYER_KREISE = [
    "07311", "07312", "07313", "07314", "07316", "07317", "07318", "07320",
    "07332", "07333", "07334", "07335", "07336", "07337", "07338", "07340",
]

AUSSENSTELLEN = {
    "Koblenz": dict(
        street="Niederberger Höhe", house_number="1", postal_code="56077", city="Koblenz",
        phone="0261 6675-3000", email="landesarchaeologie-koblenz@gdke.rlp.de",
        source_url="https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-koblenz",
        kreise=KOBLENZ_KREISE, belegt="direkt",
    ),
    "Mainz": dict(
        street="Große Langgasse", house_number="29", postal_code="55116", city="Mainz",
        phone="06131 2016-300", email="landesarchaeologie-mainz@gdke.rlp.de",
        source_url="https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-mainz",
        kreise=MAINZ_KREISE, belegt="direkt",
    ),
    "Trier": dict(
        street="Weimarer Allee", house_number="1", postal_code="54290", city="Trier",
        phone="0651 9774-0", email="landesarchaeologie-trier@gdke.rlp.de",
        source_url="https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-trier",
        kreise=TRIER_KREISE, belegt="direkt",
    ),
    "Speyer": dict(
        street="Kleine Pfaffengasse", house_number="10", postal_code="67346", city="Speyer",
        phone="06232 6757-40", email="landesarchaeologie-speyer@gdke.rlp.de",
        source_url="https://gdke.rlp.de/wer-wir-sind/landesarchaeologie/aussenstelle-speyer",
        kreise=SPEYER_KREISE, belegt="durch Ausschluss ermittelt, siehe Skript-Docstring",
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
        bodendenkmalschutz_authorities = {}
        for name, info in AUSSENSTELLEN.items():
            full_name = f"GDKE - Direktion Landesarchäologie, Außenstelle {name}"
            existing = db.query(Authority).filter(Authority.authority_name == full_name).first()
            if existing:
                print(f"Authority bereits vorhanden, wird wiederverwendet: {full_name}")
                bodendenkmalschutz_authorities[name] = existing
                continue
            authority = Authority(
                authority_id=str(uuid.uuid4()),
                authority_name=full_name,
                authority_type="Denkmalfachbehörde (Landesbehörde)",
                street=info["street"], house_number=info["house_number"],
                postal_code=info["postal_code"], city=info["city"], state="Rheinland-Pfalz",
                phone=info["phone"], email=info["email"],
                source=f"Amtliche Kontaktseite GDKE, recherchiert 2026-09-26: {info['source_url']}",
                active=True,
            )
            db.add(authority)
            db.flush()
            bodendenkmalschutz_authorities[name] = authority
            print(f"Neue Authority angelegt: {full_name} ({authority.authority_id})")

        trier_erschliessung_name = "Stadtverwaltung Trier - StadtRaum Trier (Beitragsabteilung SRT)"
        trier_erschliessung = db.query(Authority).filter(Authority.authority_name == trier_erschliessung_name).first()
        if not trier_erschliessung:
            trier_erschliessung = Authority(
                authority_id=str(uuid.uuid4()),
                authority_name=trier_erschliessung_name,
                authority_type="Kommunale Beitragsstelle",
                street="Am Grüneberg", house_number="90", postal_code="54292", city="Trier",
                state="Rheinland-Pfalz", phone="0651/718-0",
                source=(
                    "Amtliche Seite Stadt Trier, recherchiert 2026-09-26: "
                    "https://www.trier.de/service/dienstleistungen-a-z/zusatzinformationen-mter/"
                    "7595.Ausbaubeitraege-und-Erschliessungsbeitraege.html"
                ),
                active=True,
            )
            db.add(trier_erschliessung)
            db.flush()
            print(f"Neue Authority angelegt: {trier_erschliessung_name} ({trier_erschliessung.authority_id})")
        else:
            print(f"Authority bereits vorhanden, wird wiederverwendet: {trier_erschliessung_name}")

        staging = JurisdictionStagingService(db)
        batch_id = f"rlp-bodendenkmal-erschliessung-{datetime.utcnow().strftime('%Y%m%d')}"
        staged = []

        for name, info in AUSSENSTELLEN.items():
            authority = bodendenkmalschutz_authorities[name]
            for ags_kreis in info["kreise"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label="RLP Bodendenkmalschutz - GDKE Außenstellen (Pilot)",
                    request_type_id="BODENDENKMALSCHUTZ",
                    state="Rheinland-Pfalz", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"GDKE RLP - Landesarchäologie, Außenstelle {name}",
                    source_url=info["source_url"],
                    source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append((entry, info["belegt"]))

        erschliessung_entry = staging.stage_entry(
            batch_id=batch_id, batch_label="Erschließungsbeiträge Trier (Einzelfall-Pilot)",
            request_type_id="ERSCHLIESSUNG",
            state="Rheinland-Pfalz", ags="07211000", matching_level=MatchingLevel.MUNICIPALITY, priority=40,
            proposed_authority_id=trier_erschliessung.authority_id,
            source="Stadt Trier - StadtRaum Trier, Beitragsabteilung SRT",
            source_url=(
                "https://www.trier.de/service/dienstleistungen-a-z/zusatzinformationen-mter/"
                "7595.Ausbaubeitraege-und-Erschliessungsbeitraege.html"
            ),
            source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
            source_retrieved_at=datetime.utcnow(),
        )
        db.commit()

        print(f"\n{len(staged) + 1} Einträge gestaged (Batch {batch_id}).")
        summary = staging.batch_summary(batch_id)
        print("Konflikt-Verteilung:", summary["by_conflict_type"])

        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        if erschliessung_entry.conflict_type != "NEW":
            conflicts.append(erschliessung_entry)
        if conflicts:
            print(f"\nACHTUNG: {len(conflicts)} Einträge sind KEIN einfacher Neuzugang - keine automatische Freigabe:")
            for c in conflicts:
                print(f"  #{c.id} ags={c.ags} conflict={c.conflict_type} reason={c.conflict_reason}")
            print("Diese Einträge bleiben PENDING zur manuellen Entscheidung.")

        approved = 0
        for entry, belegt in staged:
            if entry.conflict_type != "NEW":
                continue
            notes = (
                "Zuständigkeitsbereich direkt von der amtlichen Außenstellen-Seite übernommen."
                if belegt == "direkt" else
                "Zuständigkeitsbereich NICHT explizit von der Quelle genannt, sondern durch Ausschluss "
                "aus der vollständigen Landkreisliste RLP abzüglich der drei anderen, explizit belegten "
                "Außenstellen ermittelt (siehe Skript-Docstring) - geringere Beleglage als die anderen drei."
            )
            staging.approve_entry(entry.id, reviewer=REVIEWER, review_notes=notes)
            approved += 1
        if erschliessung_entry.conflict_type == "NEW":
            staging.approve_entry(
                erschliessung_entry.id, reviewer=REVIEWER,
                review_notes=(
                    "Erschließungsbeiträge-Zuständigkeit bestätigt; ob dieselbe Stelle auch "
                    "Anliegerbescheinigungen ausstellt, ist durch die Quelle NICHT ausdrücklich "
                    "bestätigt - offene Prüffrage, siehe Skript-Docstring."
                ),
            )
            approved += 1
        db.commit()
        print(f"\n{approved} Einträge freigegeben und als VERIFIED in jurisdictions übernommen.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
