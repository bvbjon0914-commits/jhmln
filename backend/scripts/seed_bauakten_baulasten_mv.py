"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer MECKLENBURG-VORPOMMERN. Nach
§ 57 Abs. 1 LBauO M-V sind Bauaufsichtsbehoerden "die Landraetinnen und
Landraete oder die Oberbuergermeisterinnen und Oberbuergermeister der
kreisfreien und grossen kreisangehoerigen Staedte als untere
Bauaufsichtsbehoerden". § 83 Abs. 4 LBauO M-V: "Das Baulastenverzeichnis
wird von der Bauaufsichtsbehoerde gefuehrt" - dieselbe untere
Bauaufsichtsbehoerde fuehrt damit auch das Baulastenverzeichnis.

Die 4 "grossen kreisangehoerigen Staedte" sind nach § 7 Abs. 2 KV M-V
(Kommunalverfassung fuer das Land Mecklenburg-Vorpommern) abschliessend
benannt: die Vier-Tore-Stadt Neubrandenburg, die Universitaets- und
Hansestadt Greifswald sowie die Hansestaedte Stralsund und Wismar. Die
2 kreisfreien Staedte sind nach § 7 Abs. 3 KV M-V die Hanse- und
Universitaetsstadt Rostock und die Landeshauptstadt Schwerin.

Alle Zitate (§ 57, § 83 LBauO M-V sowie § 7 KV M-V) wurden in dieser
Sitzung direkt gegen landesrecht-mv.de verifiziert (Wortlaut stimmt
exakt mit den unten zitierten Quellen ueberein) - anders als bei der
urspruenglichen Recherche-Agent-Vorlage, die die § 7 KV M-V-Staedteliste
zunaechst nur ueber eine Sekundaerquelle (anwalt24.de) belegen konnte.
Daher tragen auch die 4 Ausnahme-Staedte hier den vollen "stark"/
VERIFIED-Status (kein Abstufen auf AUTO_IMPORTED noetig).

8 neue COUNTY-Regeln je Auskunftsart (6 Landkreise + Rostock + Schwerin)
+ 4 neue MUNICIPALITY-Regeln je Auskunftsart (die 4 grossen
kreisangehoerigen Staedte, nehmen automatisch Vorrang vor der
COUNTY-Regel ihres Landkreises) = 24 Regeln insgesamt (abzueglich
etwaiger bereits bestehender Alt-Abdeckung, die der Konfliktpruefung
korrekt als Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Mecklenburg-Vorpommern)"
LBAUO_URL = "https://www.landesrecht-mv.de/bsmv/document/jlr-NNLMV000070AENN00000000148"
KV_URL = "https://www.landesrecht-mv.de/bsmv/document/jlr-NNLMV000070E5NN00000000010"
QUOTE_KREIS = ("§ 57 Abs. 1 LBauO M-V: 'Bauaufsichtsbehörden sind 1. die Landrätinnen und Landräte "
               "oder die Oberbürgermeisterinnen und Oberbürgermeister der kreisfreien und großen "
               "kreisangehörigen Städte als untere Bauaufsichtsbehörden ...' § 83 Abs. 4 LBauO M-V: "
               "'Das Baulastenverzeichnis wird von der Bauaufsichtsbehörde geführt.'")
QUOTE_AUSNAHME = ("§ 7 Abs. 2 KV M-V: 'Große kreisangehörige Städte sind die Vier-Tore-Stadt "
                   "Neubrandenburg, die Universitäts- und Hansestadt Greifswald sowie die Hansestädte "
                   "Stralsund und Wismar.' § 57 Abs. 1 LBauO M-V nennt die großen kreisangehörigen "
                   "Städte direkt und abschließend als untere Bauaufsichtsbehörde neben Landkreisen "
                   "und kreisfreien Städten.")

# Grosse kreisangehoerige Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Neubrandenburg": "13071107",
    "Greifswald": "13075039",
    "Stralsund": "13073088",
    "Wismar": "13074087",
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
    mv = df[df["Land_name"] == "Mecklenburg-Vorpommern"]
    kreis_ars_index = build_ars_index(mv[mv["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(mv[mv["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Mecklenburg-Vorpommern").all()
        gpk = {}
        for u in kreis_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        kreisfreie = {k for k, gset in gpk.items() if len(gset) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-mv-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
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
                        state="Mecklenburg-Vorpommern", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Mecklenburg-Vorpommern - Kreise",
                    request_type_id=request_type_id, state="Mecklenburg-Vorpommern", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=LBAUO_URL,
                    source_license="Amtliche Rechtsgrundlage (LBauO M-V) + amtliches Anschriftenverzeichnis",
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
                        authority_type="Untere Bauaufsichtsbehörde (Große kreisangehörige Stadt, § 57 Abs. 1 LBauO M-V)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Mecklenburg-Vorpommern", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Mecklenburg-Vorpommern - Große kreisangehörige Städte",
                    request_type_id=request_type_id, state="Mecklenburg-Vorpommern", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=KV_URL,
                    source_license="Amtliche Rechtsgrundlage (KV M-V/LBauO M-V) + amtliches Anschriftenverzeichnis",
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
