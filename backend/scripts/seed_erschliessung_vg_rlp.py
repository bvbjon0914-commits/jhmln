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
  - Verbandsgemeinde Prüm (44 Gemeinden) - eigene Abteilung "2.9
    Erschließungs- u. Ausbaubeiträge", wörtlich genannt - starke Beleglage
  - Verbandsgemeinde Arzfeld (43 Gemeinden) - eigene Seite
    "Erschließungsbeiträge" auf der Amtsseite, wörtlich genannt - starke
    Beleglage; die Seite selbst weist zusätzlich korrekt darauf hin, dass
    rechtlich die Ortsgemeinden erhebungsberechtigt sind und die VG-
    Verwaltung die Sache verwaltungstechnisch bearbeitet
  - Verbandsgemeinde Simmern-Rheinböllen (44 Gemeinden) - "Erschließungs-
    beiträge Verkehrsanlagen" unter Finanzen, wörtlich genannt - starke
    Beleglage
  - Verbandsgemeinde Kirchberg (Hunsrück) (40 Gemeinden, Rhein-Hunsrück-
    Kreis) - "Erschließungs- oder Ausbaubeiträge" im FAQ der Seite
    "Wiederkehrende Beiträge" (Abteilung Bauen und Umwelt), wörtlich
    genannt - starke Beleglage

Adressen/E-Mails für alle Verbandsgemeinden wurden gegen das amtliche
Destatis-Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen (Stand
31.01.2026, vom Nutzer bereitgestellt) abgeglichen und stimmen exakt mit
den unabhängig recherchierten Angaben überein (siehe
app/services/address_directory.py) - AUSSCHLIESSLICH für Adresse/allgemeine
E-Mail, NIE für die fachliche Zuständigkeitsaussage selbst (die bleibt je
VG einzeln über eine amtliche, fachlich einschlägige Quelle belegt).

NICHT bearbeitet: Verbandsgemeinde Südeifel (65 Gemeinden) - Adresse aus
dem Anschriftenverzeichnis bekannt (Pestalozzistraße 7, 54673 Neuerburg),
aber die amtliche Organigramm-Seite ist clientseitig gerendert und lieferte
über WebFetch/Browser keine verwertbare Abteilungsangabe für
Erschließungsbeiträge - zurückgestellt für einen künftigen Durchlauf statt
eine Vermutung als Fundstelle auszugeben (eine Adresse allein erfüllt NICHT
die Anforderung "konkret benannte zuständige Organisation" für diese
Auskunftsart). Die übrigen 124 Verbandsgemeinden RLP sind unverändert
offen.
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

PRUEM_AGS = [
    "07232202", "07232206", "07232207", "07232208", "07232209", "07232216", "07232222", "07232223",
    "07232224", "07232226", "07232227", "07232230", "07232231", "07232236", "07232238", "07232250",
    "07232256", "07232265", "07232266", "07232271", "07232272", "07232276", "07232279", "07232280",
    "07232283", "07232284", "07232288", "07232290", "07232292", "07232295", "07232296", "07232300",
    "07232302", "07232304", "07232305", "07232307", "07232308", "07232318", "07232320", "07232321",
    "07232327", "07232328", "07232329", "07232332",
]

ARZFELD_AGS = [
    "07232201", "07232211", "07232212", "07232213", "07232214", "07232217", "07232220", "07232221",
    "07232229", "07232233", "07232234", "07232240", "07232245", "07232246", "07232247", "07232248",
    "07232249", "07232253", "07232254", "07232255", "07232258", "07232259", "07232260", "07232261",
    "07232262", "07232263", "07232264", "07232267", "07232270", "07232277", "07232285", "07232287",
    "07232291", "07232293", "07232294", "07232297", "07232298", "07232301", "07232309", "07232310",
    "07232315", "07232322", "07232333",
]

SIMMERN_RHEINBOELLEN_AGS = [
    "07140002", "07140003", "07140008", "07140011", "07140012", "07140015", "07140020", "07140023",
    "07140027", "07140035", "07140037", "07140039", "07140056", "07140058", "07140065", "07140068",
    "07140070", "07140076", "07140077", "07140079", "07140085", "07140092", "07140096", "07140099",
    "07140100", "07140101", "07140106", "07140113", "07140115", "07140118", "07140119", "07140121",
    "07140123", "07140125", "07140126", "07140127", "07140134", "07140138", "07140139", "07140144",
    "07140148", "07140150", "07140158", "07140166",
]

KIRCHBERG_HUNSRUECK_AGS = [
    "07140006", "07140007", "07140024", "07140028", "07140029", "07140030", "07140040", "07140041",
    "07140044", "07140048", "07140049", "07140050", "07140053", "07140062", "07140067", "07140071",
    "07140081", "07140082", "07140086", "07140090", "07140094", "07140105", "07140107", "07140109",
    "07140111", "07140120", "07140122", "07140128", "07140129", "07140130", "07140135", "07140141",
    "07140145", "07140146", "07140151", "07140154", "07140159", "07140163", "07140164", "07140165",
]

DAUN_AGS = [
    "07233006", "07233008", "07233011", "07233014", "07233016", "07233017", "07233018", "07233020",
    "07233021", "07233025", "07233027", "07233030", "07233031", "07233034", "07233039", "07233040",
    "07233042", "07233043", "07233046", "07233049", "07233052", "07233055", "07233061", "07233062",
    "07233063", "07233064", "07233065", "07233067", "07233068", "07233070", "07233071", "07233074",
    "07233075", "07233077", "07233079", "07233081", "07233084", "07233501",
]

GEROLSTEIN_AGS = [
    "07233002", "07233004", "07233005", "07233007", "07233019", "07233022", "07233023", "07233026",
    "07233028", "07233029", "07233033", "07233035", "07233036", "07233038", "07233041", "07233050",
    "07233053", "07233054", "07233056", "07233058", "07233060", "07233076", "07233080", "07233083",
    "07233204", "07233209", "07233211", "07233214", "07233219", "07233223", "07233227", "07233229",
    "07233232", "07233235", "07233237", "07233239", "07233240", "07233241",
]

NORDPFAELZER_LAND_AGS = [
    "07333003", "07333004", "07333008", "07333014", "07333016", "07333021", "07333023", "07333024",
    "07333025", "07333028", "07333034", "07333036", "07333037", "07333043", "07333049", "07333050",
    "07333051", "07333053", "07333054", "07333055", "07333061", "07333065", "07333066", "07333067",
    "07333068", "07333072", "07333073", "07333077", "07333078", "07333079", "07333083", "07333084",
    "07333201", "07333202", "07333203", "07333502",
]

KUSEL_ALTENGLAN_AGS = [
    "07336002", "07336003", "07336006", "07336009", "07336015", "07336018", "07336021", "07336022",
    "07336024", "07336025", "07336034", "07336039", "07336046", "07336051", "07336052", "07336055",
    "07336066", "07336067", "07336068", "07336070", "07336071", "07336077", "07336079", "07336081",
    "07336084", "07336088", "07336089", "07336091", "07336094", "07336097", "07336098", "07336099",
    "07336103", "07336106",
]

VERBANDSGEMEINDEN = {
    "Verbandsgemeindeverwaltung Bitburger Land - Abt. 4 (Bauen und Umwelt)": dict(
        street="Hubert-Prim-Straße", house_number="7", postal_code="54634", city="Bitburg",
        phone="06561 66-0", email="info@bitburgerland.de",
        source_url="https://www.bitburgerland.de/buergerservice-1/leistungen/RLP:entry:216385/strassenausbaubeitraege-wiederkehrende-strassenausbaubeitraege/",
        belegt_fuer="Straßenausbaubeiträge/wiederkehrende Beiträge für Verkehrsanlagen (Abt. 4: Bauen und Umwelt)",
        beleglage="schwaecher", ags_liste=BITBURGER_LAND_AGS,
    ),
    "Verbandsgemeindeverwaltung Altenkirchen-Flammersfeld - Fachgebiet 3.2 (Beiträge für Verkehrsanlagen, Infrastruktur)": dict(
        street="Rathausstraße", house_number="13", postal_code="57610", city="Altenkirchen",
        phone="02681 85-0", email="rathaus@vg-ak-ff.de",
        source_url="https://www.vg-altenkirchen-flammersfeld.de/gemeinde-politik/rathaus/buergerservice/organisationseinheiten",
        belegt_fuer="Fachgebiet 3.2 - Beiträge für Verkehrsanlagen, Infrastruktur (Fachbereich 3: Infrastruktur, Umwelt und Bauen)",
        beleglage="schwaecher", ags_liste=ALTENKIRCHEN_FLAMMERSFELD_AGS,
    ),
    "Verbandsgemeindeverwaltung Prüm - Abt. 2.9 (Erschließungs- u. Ausbaubeiträge)": dict(
        street="Tiergartenstraße", house_number="54", postal_code="54595", city="Prüm",
        phone="06551 943-0", email="poststelle@vg-pruem.de",
        source_url="https://www.pruem.de/rathaus-buergerservice/fachbereiche/",
        belegt_fuer="Abt. 2.9 - Erschließungs- u. Ausbaubeiträge (wörtlich genannt)",
        beleglage="stark", ags_liste=PRUEM_AGS,
    ),
    "Verbandsgemeindeverwaltung Arzfeld - Fachbereich Bauen & Umwelt": dict(
        street="Luxemburger Straße", house_number="6", postal_code="54687", city="Arzfeld",
        phone="06550 974-0", email="info@vg-arzfeld.de",
        source_url="https://www.vg-arzfeld.de/rathaus/buergerservice/bauen/erschliessungsbeitraege",
        belegt_fuer="eigene Amtsseite 'Erschließungsbeiträge' (Fachbereich Bauen & Umwelt), wörtlich genannt",
        beleglage="stark", ags_liste=ARZFELD_AGS,
    ),
    "Verbandsgemeindeverwaltung Simmern-Rheinböllen - Finanzen": dict(
        street="Brühlstraße", house_number="2", postal_code="55469", city="Simmern/Hunsrück",
        phone=None, email="info@sim-rhb.de",
        source_url="https://www.sim-rhb.de/rathaus/verwaltung/was-erledige-ich-wo",
        belegt_fuer="'Erschließungsbeiträge Verkehrsanlagen' unter Finanzen, wörtlich genannt",
        beleglage="stark", ags_liste=SIMMERN_RHEINBOELLEN_AGS,
    ),
    "Verbandsgemeindeverwaltung Kirchberg (Hunsrück) - Bauen und Umwelt": dict(
        street="Marktplatz", house_number="5", postal_code="55481", city="Kirchberg (Hunsrück)",
        phone="06763 910-0", email="rathaus@kirchberg-hunsrueck.de",
        source_url="https://www.kirchberg-hunsrueck.de/de/rathaus/bauen-umwelt/wiederkehrende-beitraege/",
        belegt_fuer=(
            "'Erschließungs- oder Ausbaubeiträge' im FAQ der Seite 'Wiederkehrende Beiträge' "
            "(Abteilung Bauen und Umwelt), Begriff 'Erschließung' wörtlich genannt"
        ),
        beleglage="stark", ags_liste=KIRCHBERG_HUNSRUECK_AGS,
    ),
    "Verbandsgemeindeverwaltung Daun - Sachgebiet 4.2 (Abgaben)": dict(
        street="Leopoldstraße", house_number="29", postal_code="54550", city="Daun",
        phone="06592 939-0", email="info@vgv.daun.de",
        source_url="https://www.vgv-daun.de/buergerservice-1/abteilungen/RLP:department:267684/sachgebiet-4-2-abgaben/",
        belegt_fuer="'Erschließungsbeitrag zahlen' explizit als Aufgabe von Sachgebiet 4.2 - Abgaben gelistet",
        beleglage="stark", ags_liste=DAUN_AGS,
    ),
    "Verbandsgemeindeverwaltung Gerolstein - 2.2 (Bauleitplanung, Umwelt, Beiträge)": dict(
        street="Kyllweg", house_number="1", postal_code="54568", city="Gerolstein",
        phone="06591 13-0", email="post@gerolstein.de",
        source_url="https://www.gerolstein.de/buergerservice/leistungen/RLP:entry:64968/anliegerbeitraege/",
        belegt_fuer=(
            "eigene Amtsseite 'Anliegerbeiträge' nennt Erschließungsbeiträge explizit als Unterart "
            "('erstmaliger bebauungsplanmäßiger Ausbau'), Abteilung 2.2 Bauleitplanung, Umwelt, Beiträge"
        ),
        beleglage="stark", ags_liste=GEROLSTEIN_AGS,
    ),
    "Verbandsgemeindeverwaltung Nordpfälzer Land - 2. Finanzen": dict(
        street="Bezirksamtsstraße", house_number="7", postal_code="67806", city="Rockenhausen",
        phone="06361 451-0", email="info@vg-nl.de",
        source_url="https://www.xn--nordpflzerland-bib.de/buergerservice/abteilungen/RLP:department:412/2-finanzen/",
        belegt_fuer="Abteilung 2 Finanzen listet nur generisch 'Abgaben', NICHT wörtlich 'Erschließungsbeiträge'",
        beleglage="schwaecher", ags_liste=NORDPFAELZER_LAND_AGS,
    ),
    "Verbandsgemeindeverwaltung Kusel-Altenglan": dict(
        street="Marktplatz", house_number="1", postal_code="66869", city="Kusel",
        phone="06381 6080-0", email="info@vgka.de",
        source_url="https://www.vgka.de/aktuelles/wiederkehrende-beitraege/allgemeines/",
        belegt_fuer=(
            "eigene Amtsseite nennt 'Erschließungsbeiträgen' wörtlich im Kontext wiederkehrender "
            "Beiträge, aber ohne eigene Sachgebiets-Zuordnung - Zuständigkeit bei der "
            "Verbandsgemeindeverwaltung als Ganzes, nicht bei einem benannten Sachgebiet"
        ),
        beleglage="stark", ags_liste=KUSEL_ALTENGLAN_AGS,
    ),
}

BELEGLAGE_HINWEIS_SCHWAECHER = (
    "Quelle bestätigt die Zuständigkeit dieser Organisationseinheit ausdrücklich für '{belegt_fuer}', "
    "NICHT wörtlich für 'Erschließungsbeiträge' (§ 127 ff. BauGB) - beide Beitragsarten werden in der "
    "kommunalen Praxis nahezu durchgängig von derselben Stelle bearbeitet, das ist hier aber nicht "
    "wörtlich einzeln belegt (anders als beim bereits verifizierten Trier-Fall). Schwächere Beleglage, "
    "explizit als solche markiert."
)
BELEGLAGE_HINWEIS_STARK = (
    "Quelle bestätigt '{belegt_fuer}' - Begriff 'Erschließung(s)' wörtlich auf der amtlichen Seite "
    "genannt, gleichwertige Beleglage wie beim bereits verifizierten Trier-Fall."
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
            is_stark = info.get("beleglage") == "stark"
            hinweis = BELEGLAGE_HINWEIS_STARK if is_stark else BELEGLAGE_HINWEIS_SCHWAECHER
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                review_notes=hinweis.format(belegt_fuer=info["belegt_fuer"]),
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
