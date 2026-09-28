"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer SCHLESWIG-HOLSTEIN. Nach
§ 57 Abs. 1 LBO SH sind Bauaufsichtsbehoerden "die Landraetinnen und
Landraete" sowie "die Buergermeisterinnen und Buergermeister der
kreisfreien Staedte" als untere Bauaufsichtsbehoerden. § 83 Abs. 4
LBO SH: "Das Baulastenverzeichnis wird von der Bauaufsichtsbehoerde
gefuehrt" - dieselbe untere Bauaufsichtsbehoerde fuehrt damit auch das
Baulastenverzeichnis.

§ 57 Abs. 2 LBO SH erlaubt zusaetzlich die Uebertragung der unteren
Bauaufsichtsbehoerde auf einzelne kreisangehoerige Gemeinden per
Landesverordnung. Die abschliessende Liste der so beliehenen 18 Staedte
ergibt sich aus der Landesverordnung ueber die Zustaendigkeit der
unteren Bauaufsichtsbehoerden (BauAufsUEV SH) vom 3. Juni 2022: Ahrensburg,
Bad Oldesloe, Bad Schwartau, Brunsbuettel, Eckernfoerde, Elmshorn,
Geesthacht, Heide, Husum, Itzehoe, Neustadt in Holstein, Norderstedt,
Pinneberg, Preetz, Reinbek, Rendsburg, Schleswig, Wedel (Holstein).

Alle Zitate (§ 57, § 83 LBO SH sowie § 1 BauAufsUEV SH) wurden in dieser
Sitzung direkt gegen gesetze-rechtsprechung.sh.juris.de wortgleich
verifiziert.

15 neue COUNTY-Regeln je Auskunftsart (11 Kreise + 4 kreisfreie Staedte)
+ 18 neue MUNICIPALITY-Regeln je Auskunftsart (die 18 per BauAufsUEV SH
beliehenen Staedte, nehmen automatisch Vorrang vor der COUNTY-Regel
ihres Kreises) = 66 Regeln insgesamt (abzueglich etwaiger bereits
bestehender Alt-Abdeckung, die der Konfliktpruefung korrekt als
Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Schleswig-Holstein)"
LBO_URL = "https://www.gesetze-rechtsprechung.sh.juris.de/bssh/document/jlr-NNLSH00002BBDNN00000000075"
BAUAUFSUEV_URL = "https://www.gesetze-rechtsprechung.sh.juris.de/perma?d=jlr-NNLSH00003321NN00000000002"
QUOTE_KREIS = ("§ 57 Abs. 1 LBO SH: Bauaufsichtsbehörden sind die Landrätinnen und Landräte sowie die "
               "Bürgermeisterinnen und Bürgermeister der kreisfreien Städte als untere "
               "Bauaufsichtsbehörden. § 83 Abs. 4 LBO SH: 'Das Baulastenverzeichnis wird von der "
               "Bauaufsichtsbehörde geführt.'")
QUOTE_AUSNAHME = ("§ 1 BauAufsUEV SH (Landesverordnung über die Zuständigkeit der unteren "
                   "Bauaufsichtsbehörden vom 3. Juni 2022) i. V. m. § 57 Abs. 2 LBO SH: die Aufgaben "
                   "der unteren Bauaufsichtsbehörde werden für das Gebiet dieser Stadt auf die "
                   "Stadt selbst übertragen.")

# Per BauAufsUEV SH beliehene Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Ahrensburg": "01062001",
    "Bad Oldesloe": "01062004",
    "Bad Schwartau": "01055004",
    "Brunsbüttel": "01051011",
    "Eckernförde": "01058043",
    "Elmshorn": "01056015",
    "Geesthacht": "01053032",
    "Heide": "01051044",
    "Husum": "01054056",
    "Itzehoe": "01061046",
    "Neustadt in Holstein": "01055032",
    "Norderstedt": "01060063",
    "Pinneberg": "01056039",
    "Preetz": "01057062",
    "Reinbek": "01062060",
    "Rendsburg": "01058135",
    "Schleswig": "01059075",
    "Wedel": "01056050",
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
    sh = df[df["Land_name"] == "Schleswig-Holstein"]
    kreis_ars_index = build_ars_index(sh[sh["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(sh[sh["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Schleswig-Holstein").all()
        gpk = {}
        for u in kreis_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        kreisfreie = {k for k, gset in gpk.items() if len(gset) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-sh-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                is_kreisfrei = ags_kreis in kreisfreie
                authority_name = f"{kreis_name} - Bauaufsichtsbehörde" if is_kreisfrei \
                    else f"Kreis {kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Kreis/kreisfreie Stadt)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Schleswig-Holstein", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Schleswig-Holstein - Kreise",
                    request_type_id=request_type_id, state="Schleswig-Holstein", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=LBO_URL,
                    source_license="Amtliche Rechtsgrundlage (LBO SH) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (§ 57 Abs. 2 LBO SH, BauAufsÜV SH)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (beliehene kreisangehörige Stadt, § 57 Abs. 2 LBO SH)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Schleswig-Holstein", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Schleswig-Holstein - Beliehene Städte (BauAufsÜV SH)",
                    request_type_id=request_type_id, state="Schleswig-Holstein", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=BAUAUFSUEV_URL,
                    source_license="Amtliche Rechtsgrundlage (BauAufsÜV SH/LBO SH) + amtliches Anschriftenverzeichnis",
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
