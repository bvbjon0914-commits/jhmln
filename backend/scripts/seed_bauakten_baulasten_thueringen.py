"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer THUERINGEN. Nach § 60 Abs. 1
ThuerBO (Thueringer Bauordnung vom 2. Juli 2024) sind "die Landkreise
und die kreisfreien Staedte im uebertragenen Wirkungskreis" untere
Bauaufsichtsbehoerden. § 90 Abs. 4 ThuerBO: "Das Baulastenverzeichnis
ist von der Bauaufsichtsbehoerde zu fuehren" - dieselbe untere
Bauaufsichtsbehoerde fuehrt damit auch das Baulastenverzeichnis (§ 60
Abs. 2: die untere Bauaufsichtsbehoerde ist fuer den Gesetzesvollzug
zustaendig, soweit nichts anderes bestimmt ist). Beide Zitate per
Live-Browser-Abruf direkt gegen landesrecht.thueringen.de
wort-fuer-wort verifiziert.

Thueringen hat aktuell 22 Kreise (17 Landkreise + 5 kreisfreie Staedte:
Erfurt, Gera, Jena, Suhl, Weimar - Eisenach verlor 2021 den
Kreisfrei-Status und ist seither Teil des Wartburgkreises).

Ausnahme (§ 6 Abs. 4 ThuerKO i.V.m. den beiden Thueringer
Uebertragungsverordnungen von 1994): 5 "Grosse kreisangehoerige
Staedte" mit eigener unterer Bauaufsichtsbehoerde: Altenburg
(Landkreis Altenburger Land), Gotha (Landkreis Gotha), Muehlhausen
(Unstrut-Hainich-Kreis), Nordhausen (Landkreis Nordhausen), Ilmenau
(Ilm-Kreis).

22 neue COUNTY-Regeln je Auskunftsart (eine je Landkreis/kreisfreier
Stadt) + 5 neue MUNICIPALITY-Regeln je Auskunftsart (die 5 Grossen
kreisangehoerigen Staedte, nehmen automatisch Vorrang vor der
COUNTY-Regel ihres Landkreises) = 54 Regeln insgesamt (abzueglich
etwaiger bereits bestehender Alt-Abdeckung, die der Konfliktpruefung
korrekt als Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Thüringen)"
THUERBO_URL = "https://landesrecht.thueringen.de/perma?j=BauO_TH_!_60"
QUOTE_KREIS = ("§ 60 Abs. 1 ThürBO: 'Bauaufsichtsbehörden sind 1. die Landkreise und die kreisfreien "
               "Städte im übertragenen Wirkungskreis als untere Bauaufsichtsbehörden ...' § 60 Abs. 2: "
               "'Für den Vollzug dieses Gesetzes ... ist die untere Bauaufsichtsbehörde zuständig.' "
               "§ 90 Abs. 4 ThürBO: 'Das Baulastenverzeichnis ist von der Bauaufsichtsbehörde zu "
               "führen.'")
QUOTE_AUSNAHME = ("§ 6 Abs. 4 ThürKO i.V.m. den Thüringer Übertragungsverordnungen von 1994: fünf "
                   "Große kreisangehörige Städte (Altenburg, Gotha, Mühlhausen, Nordhausen, Ilmenau) "
                   "sind eigene untere Bauaufsichtsbehörde ('die Aufgaben der unteren "
                   "Bauaufsichtsbehörde').")

# Ausnahme-Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Altenburg": "16077001",
    "Gotha": "16067029",
    "Mühlhausen": "16064046",
    "Nordhausen": "16062041",
    "Ilmenau": "16070029",
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
    from app.services.address_directory import SATZART_GEMEINDE, SATZART_KREIS, build_ars_index, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    th = df[df["Land_name"] == "Thüringen"]
    kreis_ars_index = build_ars_index(th[th["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(th[th["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Thüringen").all()
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-thueringen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                authority_name = f"Landkreis {kreis_name} - Bauaufsichtsbehörde" if "Stadt" not in kreis_name \
                    else f"{kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Landkreis/kreisfreie Stadt)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Thüringen", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Thüringen - Kreise",
                    request_type_id=request_type_id, state="Thüringen", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=THUERBO_URL,
                    source_license="Amtliche Rechtsgrundlage (ThürBO) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (Große kreisangehörige Stadt)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Große kreisangehörige Stadt, § 6 Abs. 4 ThürKO)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Thüringen", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Thüringen - Ausnahmen",
                    request_type_id=request_type_id, state="Thüringen", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=THUERBO_URL,
                    source_license="Amtliche Rechtsgrundlage (ThürKO) + amtliches Anschriftenverzeichnis",
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
