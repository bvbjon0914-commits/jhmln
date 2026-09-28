"""
Behebt 11 der in dieser Sitzung diagnostizierten Ambiguitaeten aus der
"374 Paare teilen sich (request_type_id, matching_level, ags)"-Analyse
(siehe docs/ABSCHLUSSBERICHT_DATENQUALITAET.md) fuer Saarlouis (BAUAKTEN/
BAULASTEN) und 9 Baden-Wuerttemberg-KATASTER-Gruppen.

Zwei unterschiedliche Bug-Formen, je nachdem ob eine korrekt skalierte
Ersatz-Regel bereits an anderer Stelle existiert:

GRUPPE A - "Dublette stilllegen" (kein Ersatz noetig, existiert schon):
    Landkreis Saarlouis - Untere Bauaufsichtsbehoerde (BAUAKTEN/BAULASTEN)
    war faelschlich auf MUNICIPALITY/10044115 (die AGS der KREISSTADT
    Saarlouis) gepinnt, obwohl die Behoerde laut kreis-saarlouis.de
    "zustaendig fuer saemtliche kreisangehoerige Kommunen mit Ausnahme der
    Kreisstadt Saarlouis" ist. Eine korrekte COUNTY/10044-Regel fuer
    dieselbe fachliche Zustaendigkeit existierte zum Zeitpunkt dieser
    Korrektur bereits unter einer ANDEREN Authority (aus dem amtlichen
    Anschriftenverzeichnis importiert) - ein Neuanlegen auf COUNTY/10044
    haette also nur eine neue Ambiguitaet an anderer Stelle erzeugt. Die
    Dublette wird daher nur stillgelegt (valid_to + zitierte Begruendung),
    OHNE Ersatzregel.

    Dasselbe Muster bei BW-KATASTER Heilbronn und Karlsruhe: die
    Katasteraemter-Deutschland-GrundEngine-Zeile war faelschlich auf die
    AGS des gleichnamigen, aber separaten STADTKREISES gepinnt, waehrend
    fuer den LANDKREIS bereits eine korrekt skalierte COUNTY-Regel unter
    einer anderen, amtlich recherchierten Authority existierte.

GRUPPE B - "Fehlende Spezifitaet ergaenzen" (Ersatz noetig, existiert noch
    nicht): bei 7 weiteren BW-KATASTER-Paaren (Goeppingen, Ludwigsburg,
    Heidenheim, Konstanz, Loerrach, Reutlingen, Tuebingen) ist die
    Situation KEIN Fehler in der AGS-Wahl, sondern ein Mangel an
    Spezifitaet: die Grosse Kreisstadt betreibt laut LGL Baden-Wuerttemberg
    ("Untere Vermessungsbehoerden - Staedte", Stand 22.07.2026) eine
    eigene, vom Landkreis unabhaengige untere Vermessungsbehoerde fuer ihr
    Stadtgebiet - ein echter, dokumentierter Split (kein Bug) analog zum
    bereits akzeptierten Berlin-Muster (12 Bezirke teilen sich ags=
    11000000). Anders als bei Berlin gibt es hier aber KEINEN Mechanismus,
    der ohne AGS-Unterschied zwischen "Stadt" und "Landkreis" dispatchen
    koennte - die "Stadt"-Zeile teilte sich bislang faelschlich die
    COUNTY-Ebene-AGS mit der allgemeinen Landkreis-Zeile. Fix: die
    "Stadt"-Zeile bekommt ihre eigene MUNICIPALITY-Ebene-AGS (die 8-
    stellige Gemeinde-AGS der Stadt selbst), die Landkreis-Zeile bleibt
    unveraendert (sie deckt weiterhin ueber den COUNTY-Fallback alles im
    Kreis AUSSER der Grossen Kreisstadt ab, sobald diese eine
    spezifischere MUNICIPALITY-Regel hat).

Beide Gruppen wurden vor Anwendung dieses Scripts erst gegen eine
Wegwerf-Kopie der Datenbank getestet und auf verbleibende Ambiguitaet
(mehr als 1 aktive Regel je betroffenem (request_type_id, matching_level,
ags)-Tripel) geprueft - siehe `_post_check()` am Ende dieser Datei, die
bei jedem Lauf erneut ausgefuehrt wird.

Aufruf:
    venv/Scripts/python.exe scripts/fix_saarlouis_bw_kataster_ags_ambiguity.py
"""
import os
import sys
import uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Saarlouis/BW-Kataster AGS-Ambiguitaet)"

# ---------------------------------------------------------------------------
# GRUPPE A: expire-only (Ersatzregel existiert bereits unter anderer Authority)
# ---------------------------------------------------------------------------
EXPIRE_ONLY = [
    dict(
        jurisdiction_id="7aeee253-12a2-41df-aeca-93d3b3ceba9d",
        label="Saarlouis BAUAKTEN (Landkreis UBA)",
        replacement_jurisdiction_id="cf5991cb-03dd-45c3-ac91-602c33365b12",
        note=(
            "AGS-Zuordnung fehlerhaft: Diese Regel ordnete der Landkreis-eigenen "
            "Unteren Bauaufsichtsbehoerde (Kaiser-Wilhelm-Strasse 8, Authority "
            "a67bc5f9-3681-44fb-8024-a6c2974e20d8) auf MUNICIPALITY-Ebene die "
            "spezifische Gemeinde-AGS der Kreisstadt Saarlouis (10044115) zu. "
            "Laut offizieller Angabe des Landkreises Saarlouis ist diese Behoerde "
            "\"zustaendig fuer saemtliche kreisangehoerige Kommunen mit Ausnahme "
            "der Kreisstadt Saarlouis, die ueber eine eigene UBA verfuegt\" "
            "(Quelle: https://www.kreis-saarlouis.de/Untere-Bauaufsicht.htm, "
            "abgerufen 2026-09-28). Die Kreisstadt Saarlouis selbst wird bereits "
            "korrekt durch jurisdiction_id 217c6f3e-9641-45c9-9647-6dde03fd48c9 "
            "abgedeckt (eigene UBA, ags=10044115, MUNICIPALITY). Kreisweite "
            "Zustaendigkeit (COUNTY, ags=10044) fuer den restlichen Landkreis "
            "ist bereits korrekt durch jurisdiction_id "
            "cf5991cb-03dd-45c3-ac91-602c33365b12 (Authority 'Landkreis "
            "Saarlouis - Bauaufsichtsbehoerde', Quelle: Amtliches "
            "Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen, "
            "Statistische Aemter des Bundes und der Laender) abgedeckt. Diese "
            "Zeile wird daher als redundante/falsch skalierte Dublette "
            "stillgelegt statt neu skaliert, um keinen neuen COUNTY-Ebene-"
            "Konflikt mit der bereits bestehenden korrekten Zeile zu erzeugen."
        ),
    ),
    dict(
        jurisdiction_id="d203c96f-e809-4dc1-a389-bcb602df53d2",
        label="Saarlouis BAULASTEN (Landkreis UBA)",
        replacement_jurisdiction_id="c92beeab-49c3-415a-8e15-863e2cd8748b",
        note=(
            "AGS-Zuordnung fehlerhaft: Diese Regel ordnete der Landkreis-eigenen "
            "Unteren Bauaufsichtsbehoerde (Kaiser-Wilhelm-Strasse 8, Authority "
            "a67bc5f9-3681-44fb-8024-a6c2974e20d8) auf MUNICIPALITY-Ebene die "
            "spezifische Gemeinde-AGS der Kreisstadt Saarlouis (10044115) zu. "
            "Laut offizieller Angabe des Landkreises Saarlouis ist diese Behoerde "
            "\"zustaendig fuer saemtliche kreisangehoerige Kommunen mit Ausnahme "
            "der Kreisstadt Saarlouis, die ueber eine eigene UBA verfuegt\" "
            "(Quelle: https://www.kreis-saarlouis.de/Untere-Bauaufsicht.htm, "
            "abgerufen 2026-09-28). Die Kreisstadt Saarlouis selbst wird bereits "
            "korrekt durch jurisdiction_id 6baee516-7c45-4b07-a870-aa15635f72ee "
            "abgedeckt (eigene UBA, ags=10044115, MUNICIPALITY). Kreisweite "
            "Zustaendigkeit (COUNTY, ags=10044) fuer den restlichen Landkreis "
            "ist bereits korrekt durch jurisdiction_id "
            "c92beeab-49c3-415a-8e15-863e2cd8748b (Authority 'Landkreis "
            "Saarlouis - Bauaufsichtsbehoerde', Quelle: Amtliches "
            "Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen, "
            "Statistische Aemter des Bundes und der Laender) abgedeckt. Diese "
            "Zeile wird daher als redundante/falsch skalierte Dublette "
            "stillgelegt statt neu skaliert, um keinen neuen COUNTY-Ebene-"
            "Konflikt mit der bereits bestehenden korrekten Zeile zu erzeugen."
        ),
    ),
    dict(
        jurisdiction_id="d808d5d9-1e2d-43c3-804a-df17030adde2",
        label="BW KATASTER Heilbronn (Landkreis Vermessungsamt)",
        replacement_jurisdiction_id="dadfd047-d444-4e11-a318-e443d91a6ff9",
        note=(
            "AGS-Zuordnung fehlerhaft: Diese Regel ordnete dem Vermessungsamt "
            "des Landkreises Heilbronn (Lerchenstrasse 40, Authority "
            "e6dbe3d3-84d2-43a6-a049-ac6a7e6eb034) auf MUNICIPALITY-Ebene die "
            "AGS des separaten, eigenstaendigen Stadtkreises Heilbronn "
            "(08121000) zu statt der eigenen Kreis-AGS des Landkreises "
            "Heilbronn (08125, COUNTY). Quelle: "
            "https://www.landkreis-heilbronn.de/vermessungsamt.5366.htm "
            "(bestaetigt Lerchenstrasse 40 als Vermessungsamt des Landkreises "
            "Heilbronn) und "
            "https://www.statistikportal.de/de/gemeindeverzeichnis/08125005 "
            "(amtliches Gemeindeverzeichnis: Kreis 'Heilbronn' = Kreisschluessel "
            "08125, unterscheidet sich vom Stadtkreis Heilbronn 08121000), "
            "beide abgerufen 2026-09-28. Korrekte kreisweite Abdeckung "
            "(COUNTY, ags=08125) besteht bereits ueber jurisdiction_id "
            "dadfd047-d444-4e11-a318-e443d91a6ff9 (Authority 'Landratsamt "
            "Heilbronn - Vermessungsamt', amtlich recherchiert 2026-09-27). "
            "Diese Zeile wird daher als redundante/falsch skalierte Dublette "
            "stillgelegt statt neu skaliert, um keinen neuen COUNTY-Ebene-"
            "Konflikt mit der bereits bestehenden korrekten Zeile zu erzeugen."
        ),
    ),
    dict(
        jurisdiction_id="7145e935-022a-43d6-90b1-403782b4e2be",
        label="BW KATASTER Karlsruhe (Landkreis Vermessungsamt)",
        replacement_jurisdiction_id="fa5a4136-768e-499b-ba5d-bd6c4d703790",
        note=(
            "AGS-Zuordnung fehlerhaft: Diese Regel ordnete dem Amt fuer "
            "Vermessung, Geoinformation und Flurneuordnung des Landkreises "
            "Karlsruhe (Beiertheimer Allee 2, Authority "
            "340e095d-7381-41b8-bf65-41017eed600d) auf MUNICIPALITY-Ebene die "
            "AGS des separaten, eigenstaendigen Stadtkreises Karlsruhe "
            "(08212000) zu statt der eigenen Kreis-AGS des Landkreises "
            "Karlsruhe (08215, COUNTY). Quelle: "
            "https://www.landkreis-karlsruhe.de/index.phtml?sNavID=1863.94 "
            "(bestaetigt Zustaendigkeit fuer rund 400.000 Flurstuecke im "
            "Landkreis Karlsruhe) und "
            "https://www.statistikportal.de/de/gemeindeverzeichnis/08215009 "
            "(amtliches Gemeindeverzeichnis: Kreis 'Karlsruhe' = Kreisschluessel "
            "08215, unterscheidet sich vom Stadtkreis Karlsruhe 08212000), "
            "beide abgerufen 2026-09-28. Korrekte kreisweite Abdeckung "
            "(COUNTY, ags=08215) besteht bereits ueber jurisdiction_id "
            "fa5a4136-768e-499b-ba5d-bd6c4d703790 (Authority 'Landratsamt "
            "Karlsruhe - Amt fuer Vermessung, Geoinformation und "
            "Flurneuordnung', amtlich recherchiert 2026-09-27). Diese Zeile "
            "wird daher als redundante/falsch skalierte Dublette stillgelegt "
            "statt neu skaliert, um keinen neuen COUNTY-Ebene-Konflikt mit der "
            "bereits bestehenden korrekten Zeile zu erzeugen."
        ),
    ),
]

# ---------------------------------------------------------------------------
# GRUPPE B: expire + Ersatzregel einfuegen (fehlende Spezifitaet)
# ---------------------------------------------------------------------------
LGL_SOURCE = (
    "https://www.lgl-bw.de/export/sites/lgl/Ueber-Uns/Galerien/Dokumente/"
    "Untere_Vermessungsbehoerden_Staedte.pdf"
)

EXPIRE_AND_REPLACE = [
    dict(
        jurisdiction_id="2421d62c-f9fd-436b-8319-114666541268",
        label="BW KATASTER Goeppingen, Stadt", new_ags="08117026", city="Goeppingen",
        landkreis_quote_url=(
            "https://www.landkreis-goeppingen.de/landratsamt/aemter/"
            "vermessung-und-flurneuordnung/liegenschaftskataster"
        ),
        landkreis_quote=(
            "\"Das Amt fuer Vermessung und Flurneuordnung ist zustaendig fuer "
            "die Gemeinden und Staedte im Landkreis Goeppingen ohne der Stadt "
            "Goeppingen.\""
        ),
        ags_source_url="https://www.statistikportal.de/de/gemeindeverzeichnis/08117026",
    ),
    dict(
        jurisdiction_id="b8aee35e-a026-4f3a-8260-3575b43bf356",
        label="BW KATASTER Ludwigsburg, Stadt", new_ags="08118048", city="Ludwigsburg",
        landkreis_quote_url=None, landkreis_quote=None,
        ags_source_url="https://www.statistikportal.de/de/gemeindeverzeichnis/08118048",
    ),
    dict(
        jurisdiction_id="98356d30-a9ab-485c-be4b-a7ec310110b1",
        label="BW KATASTER Heidenheim an der Brenz, Stadt", new_ags="08135019", city="Heidenheim an der Brenz",
        landkreis_quote_url=None, landkreis_quote=None,
        ags_source_url="https://www.statistikportal.de/de/gemeindeverzeichnis/08135019",
    ),
    dict(
        jurisdiction_id="ea90b206-8c2d-4748-af44-4c26898dcaa1",
        label="BW KATASTER Konstanz, Stadt", new_ags="08335043", city="Konstanz",
        landkreis_quote_url=None, landkreis_quote=None,
        ags_source_url="https://www.statistikportal.de/de/gemeindeverzeichnis/08335043",
    ),
    dict(
        jurisdiction_id="ee4854c4-6042-49aa-b6c9-3fa81792349f",
        label="BW KATASTER Loerrach, Stadt", new_ags="08336050", city="Loerrach",
        landkreis_quote_url=None, landkreis_quote=None,
        ags_source_url="https://www.statistikportal.de/de/gemeindeverzeichnis/08336050",
    ),
    dict(
        jurisdiction_id="e440e955-e151-49eb-b66c-7163f7fd6b20",
        label="BW KATASTER Reutlingen, Stadt", new_ags="08415061", city="Reutlingen",
        landkreis_quote_url=None, landkreis_quote=None,
        ags_source_url="https://www.statistikportal.de/de/gemeindeverzeichnis/08415061",
    ),
    dict(
        jurisdiction_id="1ab39443-c3bc-4d25-ac68-177092d6ceb6",
        label="BW KATASTER Tuebingen, Stadt", new_ags="08416041", city="Tuebingen",
        landkreis_quote_url=None, landkreis_quote=None,
        ags_source_url="https://www.statistikportal.de/de/gemeindeverzeichnis/08416041",
    ),
]


def _build_old_note(item):
    parts = [
        "AGS zu unspezifisch: Diese Regel fuer die staedtische Katasterbehoerde "
        "(eigene untere Vermessungsbehoerde der Grossen Kreisstadt %s) teilte "
        "sich bislang die COUNTY-Ebene-AGS mit der Landkreis-weiten Regel, "
        "wodurch beide Regeln fuer denselben (request_type_id, matching_level, "
        "ags) nicht unterscheidbar waren." % item["city"],
        "Laut LGL Baden-Wuerttemberg ('Untere Vermessungsbehoerden - Staedte', "
        "Stand 22.07.2026, %s) fuehrt die Stadt %s eine eigene untere "
        "Vermessungsbehoerde fuer ihr Stadtgebiet." % (LGL_SOURCE, item["city"]),
    ]
    if item["landkreis_quote"]:
        parts.append(
            "Der Landkreis bestaetigt zusaetzlich offiziell: %s (Quelle: %s, "
            "abgerufen 2026-09-28)." % (item["landkreis_quote"], item["landkreis_quote_url"])
        )
    parts.append(
        "Korrigiert auf die spezifische Gemeinde-AGS %s (MUNICIPALITY-Ebene; "
        "Quelle: %s, amtliches Gemeindeverzeichnis-Informationssystem GV-ISys "
        "der Statistischen Aemter des Bundes und der Laender, abgerufen "
        "2026-09-28), siehe Nachfolgeregel." % (item["new_ags"], item["ags_source_url"])
    )
    return " ".join(parts)


def _build_new_note(item, old_id, new_id):
    parts = [
        "Korrigierte AGS-Zuordnung: Stadt %s (eigene untere Vermessungsbehoerde) "
        "erhaelt die eigene Gemeinde-AGS %s auf MUNICIPALITY-Ebene statt der "
        "zuvor mit dem Landkreis geteilten COUNTY-Ebene-AGS." % (item["city"], item["new_ags"]),
        "Loest die fruehere jurisdiction_id %s ab (dort abgelaufen am %s)." % (old_id, YESTERDAY.isoformat()),
        "Quellen: LGL Baden-Wuerttemberg 'Untere Vermessungsbehoerden - Staedte' "
        "(Stand 22.07.2026, %s)." % LGL_SOURCE,
    ]
    if item["landkreis_quote"]:
        parts.append("Landkreis-Bestaetigung: %s (%s)." % (item["landkreis_quote"], item["landkreis_quote_url"]))
    parts.append(
        "statistikportal.de Gemeindeverzeichnis (%s). Neue jurisdiction_id: %s."
        % (item["ags_source_url"], new_id)
    )
    return " ".join(parts)


def _apply(db):
    from app.models.jurisdiction import Jurisdiction

    expired, inserted, skipped = 0, 0, []

    for item in EXPIRE_ONLY:
        row = db.query(Jurisdiction).filter(Jurisdiction.jurisdiction_id == item["jurisdiction_id"]).first()
        if row is None:
            skipped.append((item["label"], "nicht gefunden"))
            continue
        if not row.active or row.valid_to is not None:
            skipped.append((item["label"], "bereits abgelaufen/inaktiv"))
            continue
        row.valid_to = YESTERDAY
        row.notes = (row.notes + " | " if row.notes else "") + item["note"]
        expired += 1
        print(f"EXPIRED: {item['label']} {item['jurisdiction_id']} -> Ersatz {item['replacement_jurisdiction_id']}")

    for item in EXPIRE_AND_REPLACE:
        row = db.query(Jurisdiction).filter(Jurisdiction.jurisdiction_id == item["jurisdiction_id"]).first()
        if row is None:
            skipped.append((item["label"], "nicht gefunden"))
            continue
        if not row.active or row.valid_to is not None:
            skipped.append((item["label"], "bereits abgelaufen/inaktiv"))
            continue

        new_id = str(uuid.uuid4())
        row.valid_to = YESTERDAY
        row.notes = (row.notes + " | " if row.notes else "") + _build_old_note(item)
        expired += 1

        new_row = Jurisdiction(
            jurisdiction_id=new_id,
            request_type_id=row.request_type_id,
            authority_id=row.authority_id,
            country=row.country,
            state=row.state,
            ags=item["new_ags"],
            municipality=row.municipality,
            district=row.district,
            postal_code=row.postal_code,
            street=row.street,
            house_number=row.house_number,
            valid_from=TODAY,
            valid_to=None,
            priority=row.priority,
            matching_level="MUNICIPALITY",
            source=row.source,
            last_verified_at=None,
            verified_by=REVIEWER,
            active=True,
            notes=_build_new_note(item, item["jurisdiction_id"], new_id),
            source_url=item["ags_source_url"],
            source_license=None,
            source_retrieved_at=None,
            verification_status="CORRECTED",
        )
        db.add(new_row)
        inserted += 1
        print(f"EXPIRED+REPLACED: {item['label']} {item['jurisdiction_id']} -> neu {new_id} ags {item['new_ags']}")

    for label, reason in skipped:
        print(f"SKIP: {label} ({reason})")

    return expired, inserted


def _post_check(db):
    from app.models.jurisdiction import Jurisdiction

    combos = set()
    for item in EXPIRE_ONLY:
        r = db.query(Jurisdiction).filter(Jurisdiction.jurisdiction_id == item["replacement_jurisdiction_id"]).first()
        if r:
            combos.add((r.request_type_id, r.matching_level, r.ags))
    for item in EXPIRE_AND_REPLACE:
        combos.add(("KATASTER", "MUNICIPALITY", item["new_ags"]))

    print("\n=== Post-Check: aktive Zeilen je beruehrtem (request_type, matching_level, ags) ===")
    all_ok = True
    for rt, level, ags in sorted(combos):
        rows = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == rt, Jurisdiction.matching_level == level,
                Jurisdiction.ags == ags, Jurisdiction.active.is_(True),
            )
            .filter((Jurisdiction.valid_to.is_(None)) | (Jurisdiction.valid_to >= TODAY))
            .all()
        )
        ok = len(rows) <= 1
        all_ok = all_ok and ok
        print(("OK  " if ok else "!!! "), rt, level, ags, "->", [r.jurisdiction_id for r in rows])
    if not all_ok:
        raise AssertionError("Nachbearbeitung hat neue Ambiguitaet erzeugt - siehe Ausgabe oben.")


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal

    db = SessionLocal()
    try:
        expired, inserted = _apply(db)
        db.flush()
        _post_check(db)
        db.commit()
        print(f"\n{expired} Regeln abgelaufen, {inserted} neue Regeln eingefuegt.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
