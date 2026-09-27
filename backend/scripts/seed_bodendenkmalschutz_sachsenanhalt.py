"""
BODENDENKMALSCHUTZ Sachsen-Anhalt. Nach § 9 Abs. 3 DenkmSchG LSA ist die
untere Denkmalschutzbehörde (Landkreis bzw. kreisfreie Stadt) für
Nachforschungen/Ausgrabungen zuständig - das Landesamt für Denkmalpflege
und Archäologie Sachsen-Anhalt (LDA, Halle) ist reine Fachbehörde, keine
Genehmigungsbehörde. 3 parallele Recherche-Agenten deckten dabei 2
kreisangehörige Städte auf, die eine EIGENE, vom Landkreis getrennte
untere Denkmalschutzbehörde führen (bestätigt über die jeweilige Stadt-
Website bzw. eine ausdrückliche Ausnahme-Formulierung des Landkreises):
Stadt Köthen (Anhalt) (innerhalb Landkreis Anhalt-Bitterfeld) und
Hansestadt Stendal (innerhalb Landkreis Stendal, dort sogar mit
ausdrücklichem Hinweis "Das Bauordnungsamt des Landkreises Stendal ist
nicht zuständig für das Gebiet der Einheitsgemeinde Hansestadt Stendal!").

Alle 14 Landkreise/kreisfreien Städte konnten mit amtlicher Quelle belegt
werden (keine offenen Fälle) - meist über die einheitliche Leistungsseite
"Bodendenkmalpflege" des Bürgerservice-Portals Sachsen-Anhalt
(buerger.sachsen-anhalt.de), das für jede Gemeinde die "Zuständige
Stelle" ausweist.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, 3 parallele Recherche-Agenten, Bodendenkmalschutz Sachsen-Anhalt)"

# ags_kreis -> dict(dept, tier, quote, url)
LANDKREISE = {
    "15081": dict(dept="Sachgebiet Bauaufsicht, Denkmalschutz und Planung", tier="stark",
                  quote="'Bodendenkmalpflege ... Zuständige Stelle: Altmarkkreis Salzwedel - Sachgebiet Bauaufsicht, Denkmalschutz und Planung'",
                  url="https://buerger.sachsen-anhalt.de/detail?areaId=303796&pstId=183679&ags=15081135"),
    "15082": dict(dept="Fachdienst Bauplanung/Denkmalschutz", tier="stark",
                  quote="'Bodendenkmalpflege ... Zuständige Stelle: Fachdienst Bauplanung/Denkmalschutz'",
                  url="https://buerger.sachsen-anhalt.de/detail?areaId=300381&pstId=183679"),
    "15084": dict(dept="Bauordnungsamt", tier="stark",
                  quote="Organisationseinheiten-Seite 'Untere Denkmalschutzbehörde'; Bürgerservice-Portal weist 'Burgenlandkreis - Bauordnungsamt' als Zuständige Stelle für Bodendenkmalpflege aus",
                  url="https://www.burgenlandkreis.de/de/untere-denkmalschutzbehoerde/organisationseinheit/154/untere_denkmalschutzbehoerde.html"),
    "15083": dict(dept="Bauordnungsamt - Sachgebiet Bauverwaltung", tier="stark",
                  quote="'Bodendenkmalpflege ... Zuständige Stelle: Landkreis Börde - Bauordnungsamt - Sachgebiet Bauverwaltung'",
                  url="https://buerger.sachsen-anhalt.de/detail?area=Oschersleben+(Bode),+Stadt&areaId=302384&pstId=183679"),
    "15001": dict(dept="Untere Denkmalschutzbehörde (Amt für Wirtschaft und Stadtplanung, Dezernat I)", tier="stark",
                  quote="'Die Untere Denkmalschutzbehörde der Stadt Dessau-Roßlau gehört zum Dezernat I und ist eine Abteilung des Amtes für Wirtschaft und Stadtplanung.'",
                  url="https://verwaltung.dessau-rosslau.de/stadtentwicklung-und-umwelt/baukultur-und-denkmalpflege/denkmalpflege-und-denkmalschutz.html"),
    "15002": dict(dept="Abteilung Denkmalschutz (Fachbereich Bauordnung und Stadtvermessung)", tier="stark",
                  quote="'Bodendenkmalpflege ... Zuständige Stelle ... Abteilung Denkmalschutz'",
                  url="https://halle.de/serviceportal/dienstleistungen/leistung/bodendenkmalpflege/183679"),
    "15085": dict(dept="Sachgebiet Denkmalschutz (Bauordnungsamt)", tier="stark",
                  quote="'Landkreis Harz - Sachgebiet Denkmalschutz ... Zuständigkeiten: Bodendenkmalpflege'",
                  url="https://www.kreis-hz.de/de/behoerden/organisationseinheit/592/sachgebiet_denkmalschutz.html"),
    "15086": dict(dept="Sachgebiet Bauplanung", tier="stark",
                  quote="'Zuständig für Anträge auf Ausgrabungen, Erdarbeiten an Stellen mit Bodendenkmalen ... ist zunächst die untere Denkmalschutzbehörde Ihres Landkreises' - bearbeitende Stelle: Sachgebiet Bauplanung",
                  url="https://www.lkjl.de/de/zustaendigkeit/leistung/123/wohnort/59/zustaendigestellen/190/bodendenkmalpflege.html"),
    "15003": dict(dept="Untere Denkmalschutzbehörde der Landeshauptstadt Magdeburg", tier="stark",
                  quote="'Untere Denkmalschutzbehörde ... Bodendenkmalpflege im gesamten Stadtgebiet'",
                  url="https://www.magdeburg.de/index.php?NavID=37.367&object=tx%7C37.398.1"),
    "15087": dict(dept="Untere Denkmalschutzbehörde beim Bauordnungsamt", tier="stark",
                  quote="'Die Untere Denkmalschutzbehörde beim Landkreis ist hier zuständig' / § 14 Abs. 3 DenkmSchG LSA: Genehmigungspflicht für Nachforschungen",
                  url="https://www.mansfeldsuedharz.de/unser-service-ihr-ansprechpartner/unsere-aemter/bauen-wohnen"),
    "15088": dict(dept="Amt für Bauordnung und Denkmalschutz, Sachgebiet Städtebau, Raumordnung und Denkmalschutz", tier="stark",
                  quote="'Zuständig für Anträge auf Ausgrabungen ... ist zunächst die untere Denkmalschutzbehörde' - Zuständige Stelle: Amt für Bauordnung und Denkmalschutz",
                  url="https://www.saalekreis.de/de/leistungsausgabe/leistung/605/zustaendigestelle/38/bodendenkmalpflege.html"),
    "15089": dict(dept="43 Fachdienst Bauordnung, Sachgebiet 43.3 Vorbeugender Brandschutz und Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Zuständige Stelle: Kreisverwaltung Salzlandkreis - 43 Fachdienst Bauordnung' - 'Vorbeugender Brandschutz und Untere Denkmalschutzbehörde'",
                  url="https://buerger.sachsen-anhalt.de/detail?areaId=15243&pstId=183679&ags=15089030"),
    "15090": dict(dept="Bauordnungsamt / Bereich Untere Denkmalschutzbehörde (übriges Kreisgebiet außer Hansestadt Stendal)", tier="stark",
                  quote="'Untere Denkmalschutzbehörde – Bauordnungsamt' - Verwaltungsleistung 'Bodendenkmalpflege' gelistet",
                  url="https://www.landkreis-stendal.de/de/aemter-detail/organisationseinheit/97/bauverwaltung__denkmalschutz.html"),
    "15091": dict(dept="Untere Denkmalschutzbehörde", tier="stark",
                  quote="'Zuständige Stelle: Landkreis Wittenberg - Untere Denkmalschutzbehörde'",
                  url="https://buerger.sachsen-anhalt.de/detail?ags=15091160&areaId=16061&infotype=0&pstId=183679"),
}

# ags (8-stellig) -> dict(name, dept, tier, quote, url) - eigenständige Sonderstädte
SONDERSTAEDTE = {
    "15082180": dict(name="Köthen (Anhalt)", dept="Bauordnung / Untere Denkmalschutzbehörde (601)", tier="stark",
                      quote="'Stadt Köthen (Anhalt) - Bauordnung / Untere Denkmalschutzbehörde (601)' als primäre Zuständige Stelle laut Landesportal; Träger: Dezernat 6 > Bauverwaltungs- und Bauordnungsamt (60) > Bauordnung/Untere Denkmalschutzbehörde (601)",
                      url="https://www.koethen-anhalt.de/de/aemter-und-behoerden/organisationseinheit/32/bauordnung__untere_denkmalschutzbehoerde_601.html"),
    "15090535": dict(name="Stendal, Hansestadt", dept="Bauaufsicht - Bauanträge & Denkmalschutz", tier="stark",
                      quote="'Das Bauordnungsamt des Landkreises Stendal ist nicht zuständig für das Gebiet der Einheitsgemeinde Hansestadt Stendal! Bitte wenden Sie sich ... direkt an das Bauaufsichtsamt der Hansestadt Stendal.'",
                      url="https://serviceportal.stendal.de/de/bauen-umwelt.html"),
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit
    from app.models.authority import Authority
    from app.services.address_directory import SATZART_KREIS, build_ars_index, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    ars_index = build_ars_index(df[df["Satzart"] == SATZART_KREIS])

    db = SessionLocal()
    try:
        kreis_names = {u.ags_kreis: u.county_name for u in db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Sachsen-Anhalt").all()}

        staging = JurisdictionStagingService(db)
        batch_id = f"bodendenkmalschutz-sachsenanhalt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags_kreis, info in LANDKREISE.items():
            kreis_name = kreis_names.get(ags_kreis, ags_kreis)
            authority_name = f"Landkreis {kreis_name} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                addr = ars_index.get(ags_kreis)
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Denkmalschutzbehörde (Kreisverwaltungsbehörde)",
                    street=addr.strasse if addr else None, house_number=None,
                    postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                    state="Sachsen-Anhalt", phone=None, email=addr.email if addr else None,
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz Sachsen-Anhalt - Kreisebene",
                request_type_id="BODENDENKMALSCHUTZ", state="Sachsen-Anhalt", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {info['quote']}", source_url=info["url"],
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info))

        for ags, info in SONDERSTAEDTE.items():
            authority_name = f"{info['name']} - {info['dept']}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Untere Denkmalschutzbehörde (Gemeinde mit eigener Bauaufsicht)",
                    street=None, house_number=None, postal_code=None, city=info["name"],
                    state="Sachsen-Anhalt", phone=None, email=None,
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {info['url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Bodendenkmalschutz Sachsen-Anhalt - Sonderstaedte",
                request_type_id="BODENDENKMALSCHUTZ", state="Sachsen-Anhalt", ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {info['quote']}", source_url=info["url"],
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, info))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, info in staged:
            if entry.conflict_type != "NEW":
                continue
            is_stark = info.get("tier") == "stark"
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=info["quote"],
                resulting_verification_status="VERIFIED" if is_stark else "AUTO_IMPORTED",
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
