"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer RHEINLAND-PFALZ. Nach § 58
Abs. 1 Nr. 3 LBauO ist untere Bauaufsichtsbehoerde "die Kreisverwaltung,
in kreisfreien und grossen kreisangehoerigen Staedten die
Stadtverwaltung". § 86 Abs. 3 LBauO: "Das Baulastenverzeichnis wird von
der Bauaufsichtsbehoerde gefuehrt" - dieselbe untere Bauaufsichtsbehoerde
fuehrt damit auch das Baulastenverzeichnis.

Die 8 "grossen kreisangehoerigen Staedte" (§ 6 GemO: kreisangehoerige
Staedte mit mehr als 25.000 Einwohnern, durch Gesetz oder Rechts-
verordnung der Landesregierung erklaert) sind abschliessend durch
einzelne Landesverordnungen benannt: Andernach, Bingen am Rhein und
Lahnstein (Landesverordnung vom 9.12.1969, GVBl. 1969, 210), Mayen
(Landesverordnung vom 25.2.1975, GVBl. 1975, 98), Ingelheim am Rhein
(Landesverordnung vom 27.10.1972, GVBl. 1972, 346) sowie Bad Kreuznach,
Idar-Oberstein und Neuwied (Landesverordnung vom 29.3.1960, GVBl. 1960,
55). Alle drei Verordnungen wurden in dieser Sitzung direkt gegen
landesrecht.rlp.de als weiterhin geltendes Recht bestaetigt; ebenso
wurde die vom urspruenglichen Recherche-Agenten offen gelassene
Paragraphennummer des § 6 GemO (statt einer vermuteten Verschiebung auf
§ 5) gegen die aktuelle Gesamtausgabe der GemO (Stand 28.9.2026)
verifiziert - keine Verschiebung, § 6 GemO ist weiterhin korrekt.

§ 58 Abs. 1 Satz 2 LBauO erlaubt zusaetzlich die Uebertragung der
unteren Bauaufsichtsbehoerde auf einzelne Verbandsgemeindeverwaltungen;
eine vollstaendige amtliche Liste dieser Faelle konnte in dieser
Sitzung nicht ermittelt werden und wird daher bewusst NICHT umgesetzt
(bekannte, dokumentierte Einschraenkung, keine stille Luecke).

36 neue COUNTY-Regeln je Auskunftsart (24 Landkreise + 12 kreisfreie
Staedte, wobei die kreisfreien Staedte i.d.R. bereits durch bundesweite
Kreisebenen-Kampagnen abgedeckt sind und von der Konfliktpruefung
korrekt als Duplikat erkannt werden) + 8 neue MUNICIPALITY-Regeln je
Auskunftsart (die 8 grossen kreisangehoerigen Staedte, nehmen
automatisch Vorrang vor der COUNTY-Regel ihres Landkreises) = 88
Regeln insgesamt gestaged (abzueglich etwaiger bereits bestehender
Alt-Abdeckung, die der Konfliktpruefung korrekt als Duplikat erkannt
und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Rheinland-Pfalz)"
LBAUO_URL = "https://www.landesrecht.rlp.de/bsrp/document/jlr-NNLRP00005B3ENN00000000188"
GEMO_URL = "https://www.landesrecht.rlp.de/bsrp/document/jlr-NNLRP00005C21NN00000000018"
QUOTE_KREIS = ("§ 58 Abs. 1 Nr. 3 LBauO: 'Bauaufsichtsbehörden sind ... die Kreisverwaltung, in "
               "kreisfreien und großen kreisangehörigen Städten die Stadtverwaltung, als untere "
               "Bauaufsichtsbehörde.' § 86 Abs. 3 LBauO: 'Das Baulastenverzeichnis wird von der "
               "Bauaufsichtsbehörde geführt.'")
QUOTE_AUSNAHME = ("§ 6 GemO: 'Kreisangehörige Städte mit mehr als 25.000 Einwohnern können durch "
                   "Gesetz oder auf ihren Antrag durch Rechtsverordnung der Landesregierung zu großen "
                   "kreisangehörigen Städten erklärt werden.' § 58 Abs. 1 Nr. 3 LBauO nennt die großen "
                   "kreisangehörigen Städte direkt als untere Bauaufsichtsbehörde neben Landkreisen "
                   "und kreisfreien Städten.")

# Grosse kreisangehoerige Stadt -> (AGS, Landesverordnung) - aus dem amtlichen
# Anschriftenverzeichnis bzw. den einzelnen Erklaerungs-Landesverordnungen ermittelt
AUSNAHMEN = {
    "Andernach": ("07137003", "Landesverordnung vom 9.12.1969 (GVBl. 1969, 210)"),
    "Bingen am Rhein": ("07339005", "Landesverordnung vom 9.12.1969 (GVBl. 1969, 210)"),
    "Lahnstein": ("07141075", "Landesverordnung vom 9.12.1969 (GVBl. 1969, 210)"),
    "Mayen": ("07137068", "Landesverordnung vom 25.2.1975 (GVBl. 1975, 98)"),
    "Ingelheim am Rhein": ("07339030", "Landesverordnung vom 27.10.1972 (GVBl. 1972, 346)"),
    "Bad Kreuznach": ("07133006", "Landesverordnung vom 29.3.1960 (GVBl. 1960, 55)"),
    "Idar-Oberstein": ("07134045", "Landesverordnung vom 29.3.1960 (GVBl. 1960, 55)"),
    "Neuwied": ("07138045", "Landesverordnung vom 29.3.1960 (GVBl. 1960, 55)"),
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
    rlp = df[df["Land_name"] == "Rheinland-Pfalz"]
    kreis_ars_index = build_ars_index(rlp[rlp["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(rlp[rlp["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Rheinland-Pfalz").all()
        gpk = {}
        for u in kreis_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        kreisfreie = {k for k, gset in gpk.items() if len(gset) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-rlp-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                is_kreisfrei = ags_kreis in kreisfreie
                authority_name = f"{kreis_name} - Bauaufsichtsbehörde" if is_kreisfrei \
                    else f"Landkreis {kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Landkreis/kreisfreie Stadt)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Rheinland-Pfalz", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Rheinland-Pfalz - Kreise",
                    request_type_id=request_type_id, state="Rheinland-Pfalz", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=LBAUO_URL,
                    source_license="Amtliche Rechtsgrundlage (LBauO) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, (ags, verordnung) in AUSNAHMEN.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (Große kreisangehörige Stadt)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Große kreisangehörige Stadt, § 58 Abs. 1 Nr. 3 LBauO)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Rheinland-Pfalz", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Rheinland-Pfalz - Große kreisangehörige Städte",
                    request_type_id=request_type_id, state="Rheinland-Pfalz", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME} {verordnung}.", source_url=GEMO_URL,
                    source_license="Amtliche Rechtsgrundlage (GemO/LBauO/Landesverordnung) + amtliches "
                                   "Anschriftenverzeichnis",
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
