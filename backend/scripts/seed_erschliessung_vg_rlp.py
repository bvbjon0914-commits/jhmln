"""
Erschließungsbeiträge / Anliegerbescheinigung - Ausweitung über
VG250-Verbandsgemeinde-Zuordnung (Fortsetzung des Trier-Einzelfall-Piloten,
siehe scripts/seed_rlp_bodendenkmal_erschliessung.py).

Fachlicher Hintergrund: Erschließungsbeiträge nach §§ 127 ff. BauGB werden
in Rheinland-Pfalz für kreisangehörige Gemeinden von der jeweiligen
VERBANDSGEMEINDEVERWALTUNG erhoben, nicht von der Ortsgemeinde selbst und
nicht vom Landkreis. RLP hat 129 Verbandsgemeinden (+ 41 verbandsfreie
Gemeinden/kreisfreie Städte) - eine vollständige Abdeckung braucht daher
~170 einzeln recherchierte Zuständigkeiten, nicht nur eine Landesregel.

Gemeinde-zu-Verbandsgemeinde-Zuordnung stammt aus der amtlichen
BKG-VG250-Attributtabelle (Sheet VGTB_VZ_GEM, Spalten ARS_V/GEN_V/BEZ_V -
siehe docs/OFFICIAL_SOURCES.md für die Quelle), NICHT selbst erfunden.

WICHTIGE EINSCHRÄNKUNG DER BELEGLAGE (bewusst nicht verschwiegen): für
beide unten aufgeführten Verbandsgemeinden bestätigt die jeweilige
amtliche Quelle die Zuständigkeit der genannten Abteilung für
"Ausbaubeiträge" bzw. "Beiträge für Verkehrsanlagen/Infrastruktur" -
KEINE der beiden Quellen verwendet wörtlich "Erschließungsbeiträge". Beide
Begriffe bezeichnen fachlich verschiedene Rechtsgrundlagen (Erschließung:
§ 127 ff. BauGB, Erstherstellung; Ausbau: kommunales Abgabengesetz,
Erneuerung/Verbesserung bereits bestehender Anlagen), werden aber in der
kommunalen Praxis nahezu durchgängig von derselben Organisationseinheit
bearbeitet (dieselbe Systematik wie beim bereits verifizierten Trier-Fall,
wo die Quelle ausdrücklich BEIDE Begriffe kombiniert genannt hat - hier
fehlt diese explizite Kombination). Deshalb bewusst NICHT mit derselben
Beleglage wie Trier gleichgesetzt - siehe `notes` je Regel.

Bearbeitet in diesem Durchlauf (von 129 Verbandsgemeinden RLP):
  - Verbandsgemeinde Bitburger Land (71 Gemeinden) - größte VG in RLP
  - Verbandsgemeinde Altenkirchen-Flammersfeld (67 Gemeinden)

NICHT bearbeitet: Verbandsgemeinde Südeifel (65 Gemeinden) - die
amtliche Organigramm-Seite ist clientseitig gerendert und lieferte über
WebFetch/Browser keine verwertbare Abteilungsangabe; zurückgestellt für
einen künftigen Durchlauf statt eine Vermutung als Fundstelle auszugeben.
Die übrigen 126 Verbandsgemeinden RLP sind unverändert offen.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-26, siehe source_url und Beleglage-Hinweis je Regel)"

BITBURGER_LAND_AGS = [
    "07232007", "07232009", "07232013", "07232014", "07232015", "07232017", "07232020", "07232024",
    "07232026", "07232027", "07232029", "07232030", "07232032", "07232034", "07232035", "07232036",
    "07232039", "07232043", "07232044", "07232045", "07232046", "07232048", "07232057", "07232058",
    "07232060", "07232061", "07232062", "07232070", "07232071", "07232074", "07232075", "07232076",
    "07232077", "07232079", "07232081", "07232083", "07232086", "07232087", "07232091", "07232092",
    "07232097", "07232098", "07232099", "07232100", "07232101", "07232105", "07232109", "07232111",
    "07232113", "07232115", "07232118", "07232119", "07232120", "07232124", "07232125", "07232126",
    "07232129", "07232133", "07232134", "07232135", "07232137", "07232203", "07232210", "07232228",
    "07232273", "07232282", "07232306", "07232313", "07232331", "07232501", "07232502",
]

ALTENKIRCHEN_FLAMMERSFELD_AGS = [
    "07132001", "07132004", "07132005", "07132009", "07132015", "07132016", "07132017", "07132022",
    "07132023", "07132027", "07132029", "07132031", "07132032", "07132033", "07132035", "07132040",
    "07132041", "07132043", "07132046", "07132047", "07132048", "07132049", "07132051", "07132052",
    "07132053", "07132055", "07132056", "07132057", "07132058", "07132060", "07132061", "07132062",
    "07132064", "07132065", "07132067", "07132069", "07132070", "07132078", "07132081", "07132082",
    "07132083", "07132085", "07132086", "07132087", "07132088", "07132089", "07132090", "07132092",
    "07132093", "07132094", "07132097", "07132099", "07132100", "07132103", "07132104", "07132106",
    "07132109", "07132110", "07132112", "07132114", "07132115", "07132116", "07132118", "07132119",
    "07132201", "07132501", "07132502",
]

VERBANDSGEMEINDEN = {
    "Verbandsgemeindeverwaltung Bitburger Land - Abt. 4 (Bauen und Umwelt)": dict(
        street="Hubert-Prim-Straße", house_number="7", postal_code="54634", city="Bitburg",
        phone="06561 66-0", email="info@bitburgerland.de",
        source_url="https://www.bitburgerland.de/buergerservice-1/leistungen/RLP:entry:216385/strassenausbaubeitraege-wiederkehrende-strassenausbaubeitraege/",
        belegt_fuer="Straßenausbaubeiträge/wiederkehrende Beiträge für Verkehrsanlagen (Abt. 4: Bauen und Umwelt)",
        ags_liste=BITBURGER_LAND_AGS,
    ),
    "Verbandsgemeindeverwaltung Altenkirchen-Flammersfeld - Fachgebiet 3.2 (Beiträge für Verkehrsanlagen, Infrastruktur)": dict(
        street="Rathausstraße", house_number="13", postal_code="57610", city="Altenkirchen",
        phone="02681 85-0", email="rathaus@vg-ak-ff.de",
        source_url="https://www.vg-altenkirchen-flammersfeld.de/gemeinde-politik/rathaus/buergerservice/organisationseinheiten",
        belegt_fuer="Fachgebiet 3.2 - Beiträge für Verkehrsanlagen, Infrastruktur (Fachbereich 3: Infrastruktur, Umwelt und Bauen)",
        ags_liste=ALTENKIRCHEN_FLAMMERSFELD_AGS,
    ),
}

BELEGLAGE_HINWEIS = (
    "Quelle bestätigt die Zuständigkeit dieser Organisationseinheit ausdrücklich für '{belegt_fuer}', "
    "NICHT wörtlich für 'Erschließungsbeiträge' (§ 127 ff. BauGB) - beide Beitragsarten werden in der "
    "kommunalen Praxis nahezu durchgängig von derselben Stelle bearbeitet, das ist hier aber nicht "
    "wörtlich einzeln belegt (anders als beim bereits verifizierten Trier-Fall). Schwächere Beleglage, "
    "explizit als solche markiert."
)


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
        batch_id = f"erschliessung-vg-rlp-{datetime.utcnow().strftime('%Y%m%d')}"
        staged = []

        for name, info in VERBANDSGEMEINDEN.items():
            authority = db.query(Authority).filter(Authority.authority_name == name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=name,
                    authority_type="Kommunale Beitragsstelle (Verbandsgemeinde)",
                    street=info["street"], house_number=info["house_number"],
                    postal_code=info["postal_code"], city=info["city"], state="Rheinland-Pfalz",
                    phone=info["phone"], email=info["email"],
                    source=f"Amtliche Kontaktseite, recherchiert 2026-09-26: {info['source_url']}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {name} ({authority.authority_id})")
            else:
                print(f"Authority bereits vorhanden, wird wiederverwendet: {name}")

            for ags in info["ags_liste"]:
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label="Erschließungsbeiträge - VG250-Verbandsgemeinde-Ausweitung RLP",
                    request_type_id="ERSCHLIESSUNG", state="Rheinland-Pfalz", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"Verbandsgemeindeverwaltung - {info['belegt_fuer']}",
                    source_url=info["source_url"],
                    source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append((entry, info))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts:
            print(f"  KONFLIKT #{c.id} ags={c.ags} conflict={c.conflict_type} - {c.conflict_reason}")

        approved = 0
        for entry, info in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                review_notes=BELEGLAGE_HINWEIS.format(belegt_fuer=info["belegt_fuer"]),
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
