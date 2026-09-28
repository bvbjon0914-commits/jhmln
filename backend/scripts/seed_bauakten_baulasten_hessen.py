"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer HESSEN. Nach § 60 Abs. 1
HBO (Hessische Bauordnung, Fassung vom 09.10.2025) sind untere
Bauaufsichtsbehoerde "der Gemeindevorstand in den kreisfreien Staedten
und Sonderstatus-Staedten nach § 4a der Hessischen Gemeindeordnung ...
und in den sonstigen Gemeinden, denen die Bauaufsicht uebertragen ist"
sowie "der Kreisausschuss in den Landkreisen". § 85 Abs. 4 HBO: "Das
Baulastenverzeichnis wird von der Bauaufsichtsbehoerde ... gefuehrt" -
dieselbe untere Bauaufsichtsbehoerde fuehrt damit auch das
Baulastenverzeichnis. Beide Zitate stammen von der amtlichen Datenbank
Hessenrecht (rv.hessenrecht.hessen.de).

6 kreisfreie Staedte nach § 4a Abs. 1 HGO (Fassung ab 01.01.2026):
Darmstadt, Frankfurt am Main, Hanau, Kassel, Offenbach am Main,
Wiesbaden. Hanau ist seit 1.1.2026 per Hanau-Auskreisungsgesetz die
sechste kreisfreie Stadt (unabhaengig verifiziert, siehe
scripts/seed_kataster_wave2.py fuer Details).

Ausnahme (§ 4a Abs. 2 HGO): 6 kreisangehoerige "Sonderstatus-Staedte"
mit eigener unterer Bauaufsichtsbehoerde: Bad Homburg v. d. Hoehe,
Fulda, Giessen, Marburg, Ruesselsheim am Main, Wetzlar.

26 neue COUNTY-Regeln je Auskunftsart (21 Landkreise + Hanau + die
bereits etablierten 5 kreisfreien Staedte werden ueber dieselbe
COUNTY-Regel abgedeckt, da sie jeweils nur 1 Gemeinde im Kreis sind) +
6 neue MUNICIPALITY-Regeln je Auskunftsart (die 6 Sonderstatus-Staedte,
nehmen automatisch Vorrang vor der COUNTY-Regel ihres Landkreises) = 64
Regeln insgesamt (abzueglich etwaiger bereits bestehender
Alt-Abdeckung, die der Konfliktpruefung korrekt als Duplikat erkannt
und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Hessen)"
HBO_URL = "https://www.rv.hessenrecht.hessen.de/perma?j=BauO_HE_!_60"
QUOTE_KREIS = ("§ 60 Abs. 1 HBO: 'Bauaufsichtsbehörden sind 1. als untere Bauaufsichtsbehörde a) der "
               "Gemeindevorstand in den kreisfreien Städten und Sonderstatus-Städten nach § 4a der "
               "Hessischen Gemeindeordnung und in den sonstigen Gemeinden, denen die Bauaufsicht "
               "übertragen ist, b) der Kreisausschuss in den Landkreisen ...' § 85 Abs. 4 HBO: 'Das "
               "Baulastenverzeichnis wird von der Bauaufsichtsbehörde oder von der durch "
               "Rechtsverordnung bestimmten Stelle geführt.'")
QUOTE_AUSNAHME = ("§ 4a Abs. 2 HGO: 'Sonderstatus-Städte erfüllen neben ihren Aufgaben als Gemeinden "
                   "zusätzlich einzelne, ihnen durch Gesetz oder Rechtsverordnung übertragene "
                   "Aufgaben der Landkreise. Bad Homburg v. d. Höhe, Fulda, Gießen, Marburg, "
                   "Rüsselsheim am Main und Wetzlar sind kreisangehörige Sonderstatus-Städte.'")

# Ausnahme-Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Bad Homburg v. d. Höhe": "06434001",
    "Fulda": "06631009",
    "Gießen": "06531005",
    "Marburg": "06534014",
    "Rüsselsheim am Main": "06433012",
    "Wetzlar": "06532023",
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
    he = df[df["Land_name"] == "Hessen"]
    kreis_ars_index = build_ars_index(he[he["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(he[he["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        # AdministrativeUnit hat fuer 06415 (Hanau) noch keinen county_name -
        # daher direkt aus dem Anschriftenverzeichnis lesen, das Hanau als
        # "Hanau, Brüder-Grimm-Stadt" bereits korrekt als 06415 fuehrt.
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Hessen").all()
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        for ags5, entry in kreis_ars_index.items():
            key = ags5.zfill(5)
            if key not in kreis_names or not kreis_names.get(key):
                kreis_names[key] = entry.name

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-hessen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                is_kreisfrei = "Stadt" in kreis_name or "Kassel, documenta-Stadt" in kreis_name
                authority_name = f"{kreis_name} - Bauaufsichtsbehörde" if is_kreisfrei \
                    else f"Landkreis {kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Kreisausschuss/Gemeindevorstand)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Hessen", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Hessen - Kreise",
                    request_type_id=request_type_id, state="Hessen", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=HBO_URL,
                    source_license="Amtliche Rechtsgrundlage (HBO) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Sonderstatus-Stadt {name} - Bauaufsichtsbehörde (§ 4a Abs. 2 HGO)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Sonderstatus-Stadt, § 4a Abs. 2 HGO)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Hessen", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Hessen - Sonderstatus-Städte",
                    request_type_id=request_type_id, state="Hessen", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=HBO_URL,
                    source_license="Amtliche Rechtsgrundlage (HGO) + amtliches Anschriftenverzeichnis",
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
