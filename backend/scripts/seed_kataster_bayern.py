"""
KATASTER (amtliches Liegenschaftskataster) für Bayern. Anders als die
übrigen Auskunftsarten läuft das bayerische Kataster NICHT über die 96
Landkreise/kreisfreien Städte, sondern über 51 Ämter für Digitalisierung,
Breitband und Vermessung (AEDBV) - jedes AEDBV deckt oft mehrere
Landkreise gemeinsam ab (Aufsichtsbehörde: Landesamt für Digitalisierung,
Breitband und Vermessung, LDBV, München).

Ein Recherche-Agent erstellte die vollständige Zuordnungstabelle anhand
der rechtsverbindlichen "Verordnung über die Bezeichnung, den Sitz und
die Bezirke der Ämter für Digitalisierung, Breitband und Vermessung in
Bayern" (VermBezV, BayRS 219-4-F, https://www.gesetze-bayern.de/Content/
Document/BayVermBezV/true) - eine noch belastbarere Quelle als eine reine
Amtsseite, weil es sich um geltendes Recht handelt, nicht nur um eine
Verwaltungsauskunft. Adressen/Kontakt stammen von der offiziellen
Amtsuche (ldbv.bayern.de/vermessung/amtsuche/). Alle 96 Landkreise/
kreisfreien Städte sind einem der 51 AEDBV zugeordnet - keine offenen
Fälle bei dieser Auskunftsart (anders als bei BODENDENKMALSCHUTZ, wo pro
Kreis eine eigene Fachzuordnung nötig war - hier ist die Zuständigkeit
selbst schon die gesuchte Auskunft, nicht nur eine Adresse).

51 COUNTY-Regeln pro abgedecktem Landkreis (also insgesamt 96 einzelne
COUNTY-Regeln, eine je ags_kreis, die auf eines der 51 AEDBV verweisen) -
matching_level=COUNTY, ags=ags_kreis.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, AEDBV-Zuordnung KATASTER Bayern)"
VERMBEZV_URL = "https://www.gesetze-bayern.de/Content/Document/BayVermBezV/true"

# AEDBV-Name -> dict(street, postal_code, city, phone, email, kreise=[Anzeigename wie von der VermBezV verwendet])
AEDBV = {
    "Amt für Digitalisierung, Breitband und Vermessung Abensberg": dict(
        street="Aventinusplatz 6", postal_code="93326", city="Abensberg", phone="09443 924-0",
        email="poststelle@adbv-abe.bayern.de", kreise=["Landkreis Kelheim"]),
    "Amt für Digitalisierung, Breitband und Vermessung Aichach": dict(
        street="Münchener Straße 7", postal_code="86551", city="Aichach", phone="08251 8738-0",
        email="poststelle@adbv-aic.bayern.de", kreise=["Landkreis Aichach-Friedberg"]),
    "Amt für Digitalisierung, Breitband und Vermessung Amberg": dict(
        street="Kirchensteig 1", postal_code="92224", city="Amberg", phone="09621 96543-0",
        email="poststelle@adbv-am.bayern.de", kreise=["Stadt Amberg", "Landkreis Amberg-Sulzbach"]),
    "Amt für Digitalisierung, Breitband und Vermessung Ansbach": dict(
        street="Dollmannstraße 56", postal_code="91522", city="Ansbach", phone="0981 203637-0",
        email="poststelle@adbv-an.bayern.de", kreise=["Stadt Ansbach", "Landkreis Ansbach"]),
    "Amt für Digitalisierung, Breitband und Vermessung Aschaffenburg": dict(
        street="Stengerstraße 2", postal_code="63741", city="Aschaffenburg", phone="06021 42945-0",
        email="poststelle@adbv-ab.bayern.de",
        kreise=["Stadt Aschaffenburg", "Landkreis Aschaffenburg", "Landkreis Miltenberg"]),
    "Amt für Digitalisierung, Breitband und Vermessung Augsburg": dict(
        street="Fronhof 12", postal_code="86152", city="Augsburg", phone="0821 242290-0",
        email="poststelle@adbv-a.bayern.de", kreise=["Stadt Augsburg", "Landkreis Augsburg"]),
    "Amt für Digitalisierung, Breitband und Vermessung Bad Kissingen": dict(
        street="Im Luitpoldpark 1", postal_code="97688", city="Bad Kissingen", phone="0971 7275-0",
        email="poststelle@adbv-kg.bayern.de", kreise=["Landkreis Bad Kissingen", "Landkreis Rhön-Grabfeld"]),
    "Amt für Digitalisierung, Breitband und Vermessung Bamberg": dict(
        street="Schranne 3", postal_code="96049", city="Bamberg", phone="0951 9533-0",
        email="poststelle@adbv-ba.bayern.de",
        kreise=["Stadt Bamberg", "Landkreis Bamberg", "Landkreis Forchheim"]),
    "Amt für Digitalisierung, Breitband und Vermessung Bayreuth": dict(
        street="Wittelsbacherring 15", postal_code="95444", city="Bayreuth", phone="0921 76468-0",
        email="poststelle@adbv-bt.bayern.de", kreise=["Stadt Bayreuth", "Landkreis Bayreuth"]),
    "Amt für Digitalisierung, Breitband und Vermessung Cham": dict(
        street="Ludwigstraße 23", postal_code="93413", city="Cham", phone="09971 848-6",
        email="poststelle@adbv-cha.bayern.de", kreise=["Landkreis Cham"]),
    "Amt für Digitalisierung, Breitband und Vermessung Coburg": dict(
        street="Wettiner Anlage 1", postal_code="96450", city="Coburg", phone="09561 8047-0",
        email="poststelle@adbv-co.bayern.de",
        kreise=["Stadt Coburg", "Landkreis Coburg", "Landkreis Lichtenfels"]),
    "Amt für Digitalisierung, Breitband und Vermessung Dachau": dict(
        street="Krankenhausstraße 9", postal_code="85221", city="Dachau", phone="08131 376-3",
        email="poststelle@adbv-dah.bayern.de", kreise=["Landkreis Dachau", "Landkreis Fürstenfeldbruck"]),
    "Amt für Digitalisierung, Breitband und Vermessung Dillingen a.d.Donau": dict(
        street="Königstraße 15", postal_code="89407", city="Dillingen a.d.Donau", phone="09071 5004-0",
        email="poststelle@adbv-dlg.bayern.de", kreise=["Landkreis Dillingen a.d.Donau"]),
    "Amt für Digitalisierung, Breitband und Vermessung Donauwörth": dict(
        street="Berger Vorstadt 16", postal_code="86609", city="Donauwörth", phone="0906 70588-0",
        email="poststelle@adbv-don.bayern.de", kreise=["Landkreis Donau-Ries"]),
    "Amt für Digitalisierung, Breitband und Vermessung Ebersberg": dict(
        street="Dr.-Wintrich-Straße 7", postal_code="85560", city="Ebersberg", phone="08092 2099-0",
        email="poststelle@adbv-ebe.bayern.de", kreise=["Landkreis Ebersberg"]),
    "Amt für Digitalisierung, Breitband und Vermessung Erding": dict(
        street="Dorfener Straße 15", postal_code="85435", city="Erding", phone="08122 960-0",
        email="poststelle@adbv-ed.bayern.de", kreise=["Landkreis Erding"]),
    "Amt für Digitalisierung, Breitband und Vermessung Erlangen": dict(
        street="Nägelsbachstraße 67", postal_code="91052", city="Erlangen", phone="09131 306-0",
        email="poststelle@adbv-er.bayern.de", kreise=["Stadt Erlangen", "Landkreis Erlangen-Höchstadt"]),
    "Amt für Digitalisierung, Breitband und Vermessung Freilassing": dict(
        street="Fürstenweg 19", postal_code="83395", city="Freilassing", phone="08654 4637-0",
        email="poststelle@adbv-frls.bayern.de", kreise=["Landkreis Berchtesgadener Land"]),
    "Amt für Digitalisierung, Breitband und Vermessung Freising": dict(
        street="Domberg 20", postal_code="85354", city="Freising", phone="08161 5391-0",
        email="poststelle@adbv-fs.bayern.de", kreise=["Landkreis Freising"]),
    "Amt für Digitalisierung, Breitband und Vermessung Freyung": dict(
        street="Grafenauer Straße 17", postal_code="94078", city="Freyung", phone="08551 9613-0",
        email="poststelle@adbv-frg.bayern.de", kreise=["Landkreis Freyung-Grafenau", "Landkreis Regen"]),
    "Amt für Digitalisierung, Breitband und Vermessung Günzburg": dict(
        street="Augsburger Straße 1", postal_code="89312", city="Günzburg", phone="08221 3660-0",
        email="poststelle@adbv-gz.bayern.de", kreise=["Landkreis Günzburg", "Landkreis Neu-Ulm"]),
    "Amt für Digitalisierung, Breitband und Vermessung Immenstadt i.Allgäu": dict(
        street="Marienplatz 12", postal_code="87509", city="Immenstadt i.Allgäu", phone="08323 8005-0",
        email="poststelle@adbv-immen.bayern.de",
        kreise=["Stadt Kempten (Allgäu)", "Landkreis Lindau (Bodensee)", "Landkreis Oberallgäu"]),
    "Amt für Digitalisierung, Breitband und Vermessung Ingolstadt": dict(
        street="Rechbergstraße 8", postal_code="85049", city="Ingolstadt", phone="0841 9359-0",
        email="poststelle@adbv-in.bayern.de",
        kreise=["Stadt Ingolstadt", "Landkreis Eichstätt", "Landkreis Neuburg-Schrobenhausen"]),
    "Amt für Digitalisierung, Breitband und Vermessung Kulmbach": dict(
        street="Georg-Hagen-Straße 17", postal_code="95326", city="Kulmbach", phone="09221 9072-0",
        email="poststelle@adbv-ku.bayern.de", kreise=["Landkreis Kronach", "Landkreis Kulmbach"]),
    "Amt für Digitalisierung, Breitband und Vermessung Landau a.d.Isar": dict(
        street="Marienplatz 5 a", postal_code="94405", city="Landau a.d.Isar", phone="09951 9801-0",
        email="poststelle@adbv-lan.bayern.de", kreise=["Landkreis Deggendorf", "Landkreis Dingolfing-Landau"]),
    "Amt für Digitalisierung, Breitband und Vermessung Landsberg am Lech": dict(
        street="Roßmarkt 198", postal_code="86899", city="Landsberg am Lech", phone="08191 930-0",
        email="poststelle@adbv-ll.bayern.de", kreise=["Landkreis Landsberg am Lech", "Landkreis Starnberg"]),
    "Amt für Digitalisierung, Breitband und Vermessung Landshut": dict(
        street="Gestütstraße 10", postal_code="84028", city="Landshut", phone="0871 40472-000",
        email="poststelle@adbv-la.bayern.de", kreise=["Stadt Landshut", "Landkreis Landshut"]),
    "Amt für Digitalisierung, Breitband und Vermessung Lohr a.Main": dict(
        street="Erthalstraße 1", postal_code="97816", city="Lohr a.Main", phone="09352 8794-0",
        email="poststelle@adbv-loh.bayern.de", kreise=["Landkreis Main-Spessart"]),
    "Amt für Digitalisierung, Breitband und Vermessung Marktoberdorf": dict(
        street="Kurfürstenstraße 19", postal_code="87616", city="Marktoberdorf", phone="08342 7009-0",
        email="poststelle@adbv-mod.bayern.de", kreise=["Stadt Kaufbeuren", "Landkreis Ostallgäu"]),
    "Amt für Digitalisierung, Breitband und Vermessung Memmingen": dict(
        street="Bismarckstraße 1", postal_code="87700", city="Memmingen", phone="08331 9648-0",
        email="poststelle@adbv-mm.bayern.de", kreise=["Stadt Memmingen", "Landkreis Unterallgäu"]),
    "Amt für Digitalisierung, Breitband und Vermessung Miesbach": dict(
        street="Münchner Straße 1", postal_code="83714", city="Miesbach", phone="08025 2826-0",
        email="poststelle@adbv-mb.bayern.de", kreise=["Landkreis Miesbach"]),
    "Amt für Digitalisierung, Breitband und Vermessung Mühldorf a.Inn": dict(
        street="Stadtplatz 48", postal_code="84453", city="Mühldorf a.Inn", phone="08631 169-0",
        email="poststelle@adbv-mue.bayern.de", kreise=["Landkreis Altötting", "Landkreis Mühldorf a.Inn"]),
    "Amt für Digitalisierung, Breitband und Vermessung München": dict(
        street="Prinzregentenstraße 5", postal_code="80538", city="München", phone="089 21638-0",
        email="poststelle@adbv-m.bayern.de", kreise=["Stadt München", "Landkreis München"]),
    "Amt für Digitalisierung, Breitband und Vermessung Nabburg": dict(
        street="Obertor 12", postal_code="92507", city="Nabburg", phone="09433 2405-0",
        email="poststelle@adbv-nab.bayern.de", kreise=["Landkreis Schwandorf"]),
    "Amt für Digitalisierung, Breitband und Vermessung Neumarkt i.d.OPf.": dict(
        street="Woffenbacher Straße 32", postal_code="92318", city="Neumarkt i.d.OPf.", phone="09181 467-0",
        email="poststelle@adbv-nm.bayern.de", kreise=["Landkreis Neumarkt i.d.OPf."]),
    "Amt für Digitalisierung, Breitband und Vermessung Neustadt a.d.Aisch": dict(
        street="Parkstraße 10", postal_code="91413", city="Neustadt a.d.Aisch", phone="09161 30708-0",
        email="poststelle@adbv-nea.bayern.de",
        kreise=["Landkreis Fürth", "Landkreis Neustadt a.d.Aisch-Bad Windsheim"]),
    "Amt für Digitalisierung, Breitband und Vermessung Nürnberg": dict(
        street="Flaschenhofstraße 59", postal_code="90402", city="Nürnberg", phone="0911 462595-0",
        email="poststelle@adbv-n.bayern.de",
        kreise=["Stadt Fürth", "Stadt Nürnberg", "Landkreis Nürnberger Land"]),
    "Amt für Digitalisierung, Breitband und Vermessung Pfaffenhofen a.d.Ilm": dict(
        street="Kellerstraße 6", postal_code="85276", city="Pfaffenhofen a.d.Ilm", phone="08441 891-0",
        email="poststelle@adbv-paf.bayern.de", kreise=["Landkreis Pfaffenhofen a.d.Ilm"]),
    "Amt für Digitalisierung, Breitband und Vermessung Pfarrkirchen": dict(
        street="Rennbahnstraße 9", postal_code="84347", city="Pfarrkirchen", phone="08561 977-0",
        email="poststelle@adbv-pan.bayern.de", kreise=["Landkreis Rottal-Inn"]),
    "Amt für Digitalisierung, Breitband und Vermessung Regensburg": dict(
        street="Franziskanerplatz 10", postal_code="93059", city="Regensburg", phone="0941 8102-0",
        email="poststelle@adbv-r.bayern.de", kreise=["Stadt Regensburg", "Landkreis Regensburg"]),
    "Amt für Digitalisierung, Breitband und Vermessung Rosenheim": dict(
        street="Münchener Straße 23", postal_code="83022", city="Rosenheim", phone="08031 366-0",
        email="poststelle@adbv-ro.bayern.de", kreise=["Stadt Rosenheim", "Landkreis Rosenheim"]),
    "Amt für Digitalisierung, Breitband und Vermessung Schwabach": dict(
        street="Theodor-Heuss-Straße 61", postal_code="91126", city="Schwabach", phone="09122 1804-0",
        email="poststelle@adbv-sc.bayern.de",
        kreise=["Stadt Schwabach", "Landkreis Roth", "Landkreis Weißenburg-Gunzenhausen"]),
    "Amt für Digitalisierung, Breitband und Vermessung Schweinfurt": dict(
        street="Mainberger Straße 14", postal_code="97422", city="Schweinfurt", phone="09721 20938-0",
        email="poststelle@adbv-sw.bayern.de",
        kreise=["Stadt Schweinfurt", "Landkreis Haßberge", "Landkreis Schweinfurt"]),
    "Amt für Digitalisierung, Breitband und Vermessung Straubing": dict(
        street="Wittelsbacherhöhe 3", postal_code="94315", city="Straubing", phone="09421 977-0",
        email="poststelle@adbv-sr.bayern.de", kreise=["Stadt Straubing", "Landkreis Straubing-Bogen"]),
    "Amt für Digitalisierung, Breitband und Vermessung Traunstein": dict(
        street="Salinenstraße 4", postal_code="83278", city="Traunstein", phone="0861 9872-0",
        email="poststelle@adbv-ts.bayern.de", kreise=["Landkreis Traunstein"]),
    "Amt für Digitalisierung, Breitband und Vermessung Vilshofen an der Donau": dict(
        street="Kapuzinerstraße 11", postal_code="94474", city="Vilshofen an der Donau", phone="08541 9607-0",
        email="poststelle@adbv-vof.bayern.de", kreise=["Stadt Passau", "Landkreis Passau"]),
    "Amt für Digitalisierung, Breitband und Vermessung Weiden i.d.OPf.": dict(
        street="Gabelsbergerstraße 2", postal_code="92637", city="Weiden i.d.OPf.", phone="0961 631836-0",
        email="poststelle@adbv-wen.bayern.de",
        kreise=["Stadt Weiden i.d.OPf.", "Landkreis Neustadt a.d.Waldnaab", "Landkreis Tirschenreuth"]),
    "Amt für Digitalisierung, Breitband und Vermessung Weilheim i.OB": dict(
        street="Hofstraße 21", postal_code="82362", city="Weilheim i.OB", phone="0881 986-0",
        email="poststelle@adbv-wm.bayern.de",
        kreise=["Landkreis Garmisch-Partenkirchen", "Landkreis Weilheim-Schongau"]),
    "Amt für Digitalisierung, Breitband und Vermessung Wolfratshausen": dict(
        street="Heimgartenstraße 3", postal_code="82515", city="Wolfratshausen", phone="08171 81833-0",
        email="poststelle@adbv-wor.bayern.de", kreise=["Landkreis Bad Tölz-Wolfratshausen"]),
    "Amt für Digitalisierung, Breitband und Vermessung Wunsiedel": dict(
        street="Von-Kotzau-Straße 4", postal_code="95632", city="Wunsiedel", phone="09232 9902-0",
        email="poststelle@adbv-wun.bayern.de",
        kreise=["Stadt Hof", "Landkreis Hof", "Landkreis Wunsiedel i.Fichtelgebirge"]),
    "Amt für Digitalisierung, Breitband und Vermessung Würzburg": dict(
        street="Weißenburgstraße 10", postal_code="97082", city="Würzburg", phone="0931 3906-0",
        email="poststelle@adbv-wue.bayern.de",
        kreise=["Stadt Würzburg", "Landkreis Kitzingen", "Landkreis Würzburg"]),
}


def _build_kreis_lookup(db):
    """'Stadt <Name>' / 'Landkreis <Name>' -> ags_kreis, abgeleitet aus der
    tatsächlichen AdministrativeUnit-Struktur (kreisfreie Stadt = Kreis mit
    genau einer Gemeinde), nicht aus einer fehleranfälligen Namens-Heuristik."""
    from app.models.administrative_unit import AdministrativeUnit

    units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Bayern").all()
    gemeinden_pro_kreis = {}
    for u in units:
        gemeinden_pro_kreis.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)

    lookup = {}
    seen_kreise = set()
    for u in units:
        if u.ags_kreis in seen_kreise:
            continue
        seen_kreise.add(u.ags_kreis)
        ist_kreisfrei = len(gemeinden_pro_kreis[u.ags_kreis]) == 1
        prefix = "Stadt" if ist_kreisfrei else "Landkreis"
        lookup[f"{prefix} {u.county_name}"] = u.ags_kreis
    # "München, Landeshauptstadt" ist der amtliche AdministrativeUnit-Name der
    # kreisfreien Stadt München - die VermBezV/AEDBV-Liste verwendet dafür
    # schlicht "Stadt München".
    if "Stadt München, Landeshauptstadt" in lookup:
        lookup["Stadt München"] = lookup["Stadt München, Landeshauptstadt"]
    return lookup


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
        kreis_lookup = _build_kreis_lookup(db)
        staging = JurisdictionStagingService(db)
        batch_id = f"kataster-bayern-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []
        unresolved = []

        for aedbv_name, info in AEDBV.items():
            authority = db.query(Authority).filter(Authority.authority_name == aedbv_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=aedbv_name,
                    authority_type="Amt für Digitalisierung, Breitband und Vermessung (Kataster)",
                    street=info["street"], house_number=None, postal_code=info["postal_code"],
                    city=info["city"], state="Bayern", phone=info["phone"], email=info["email"],
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {VERMBEZV_URL}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {aedbv_name}")

            for kreis_name in info["kreise"]:
                ags_kreis = kreis_lookup.get(kreis_name)
                if ags_kreis is None:
                    unresolved.append((aedbv_name, kreis_name))
                    continue
                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label="Kataster Bayern - AEDBV-Zuordnung",
                    request_type_id="KATASTER", state="Bayern", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{aedbv_name} - zuständig laut VermBezV für {kreis_name}",
                    source_url=VERMBEZV_URL,
                    source_license="Amtliche Rechtsverordnung (Freistaat Bayern)",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)
        db.commit()

        if unresolved:
            print(f"\nWARNUNG: {len(unresolved)} Kreis-Namen konnten nicht aufgelöst werden: {unresolved}")

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}) für {len(AEDBV)} AEDBV.")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                review_notes="Amtliche Rechtsverordnung VermBezV weist diesem AEDBV den Landkreis wörtlich zu.",
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
