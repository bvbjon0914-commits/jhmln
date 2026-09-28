"""
Pilot: EINE amtliche Quelle Ende-zu-Ende anschließen (Auftrag Priorität 2).

Vergleicht die bestehende AdministrativeUnit-Referenztabelle (aktuell aus dem
Destatis-Gemeindeverzeichnis befüllt) gegen den amtlichen BKG-VG250-Datensatz
(Verwaltungsgebiete 1:250 000, Stand 01.01., Datenlizenz Deutschland
Namensnennung 2.0 - Attributionspflicht, kommerzielle Nutzung erlaubt).

Bewusst NUR LESEND und NUR EIN VERGLEICH - dieses Skript schreibt NICHTS in
die Datenbank. Es erzeugt einen CSV-Bericht mit allen gefundenen
Abweichungen zur menschlichen Prüfung (Auftrag: "kein Rewrite und keine
künstlich aufgefüllten Datensätze" / sicherer Aktualisierungsprozess - jede
Übernahme braucht eine explizite, spätere Entscheidung).

Voraussetzung: die VG250-Excel-Attributtabelle wurde bereits von
https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_0101/aktuell/vg250_01-01.ee.excel.ebenen.zip
heruntergeladen (mit Nutzer-Zustimmung, siehe Sitzungsprotokoll) und entpackt.

Aufruf:
    venv/Scripts/python.exe scripts/compare_administrative_units_vs_vg250.py \
        --vg250-xlsx <pfad>/verwaltungsgebiete.xlsx
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vg250-xlsx", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    import pandas as pd
    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit

    vg250 = pd.read_excel(args.vg250_xlsx, sheet_name="VGTB_VZ_GEM")
    vg250["ags_padded"] = vg250["AGS_G"].apply(lambda v: str(int(v)).zfill(8))
    vg250_by_ags = {row["ags_padded"]: row for _, row in vg250.iterrows()}

    db = SessionLocal()
    try:
        existing_units = db.query(AdministrativeUnit).all()
        existing_by_ags = {u.ags: u for u in existing_units}

        rows = []

        # 1) Gemeinden, die in unserer Referenztabelle stehen, aber laut VG250
        #    nicht (mehr) existieren - z.B. wegen einer Gemeindezusammenlegung
        #    seit dem Destatis-Import.
        for ags, unit in existing_by_ags.items():
            if ags not in vg250_by_ags:
                rows.append({
                    "ags": ags, "diff_type": "FEHLT_IN_VG250",
                    "unser_stand": f"{unit.municipality_name} ({unit.county_name}, {unit.state_name})",
                    "vg250_stand": "-",
                })

        # 2) Gemeinden, die laut VG250 existieren, aber in unserer
        #    Referenztabelle fehlen (echte Abdeckungslücke der Geo-Basis).
        for ags, vg_row in vg250_by_ags.items():
            if ags not in existing_by_ags:
                rows.append({
                    "ags": ags, "diff_type": "FEHLT_BEI_UNS",
                    "unser_stand": "-",
                    "vg250_stand": f"{vg_row['GEN_G']} ({vg_row['GEN_K']}, {vg_row['GEN_L']})",
                })

        # 3) Gemeinden, die es in beiden gibt, aber mit abweichendem Namen /
        #    Kreis / Bundesland - mögliches Zeichen für eine nicht
        #    nachvollzogene Gebietsänderung.
        for ags, unit in existing_by_ags.items():
            vg_row = vg250_by_ags.get(ags)
            if vg_row is None:
                continue
            mismatches = []
            if _norm(unit.municipality_name) != _norm(vg_row["GEN_G"]):
                mismatches.append(f"Gemeindename: '{unit.municipality_name}' vs. '{vg_row['GEN_G']}'")
            if _norm(unit.county_name) != _norm(vg_row["GEN_K"]):
                mismatches.append(f"Kreis: '{unit.county_name}' vs. '{vg_row['GEN_K']}'")
            if _norm(unit.state_name) != _norm(vg_row["GEN_L"]):
                mismatches.append(f"Bundesland: '{unit.state_name}' vs. '{vg_row['GEN_L']}'")
            if mismatches:
                rows.append({
                    "ags": ags, "diff_type": "ABWEICHUNG",
                    "unser_stand": " | ".join(mismatches),
                    "vg250_stand": "",
                })

        out_path = args.out or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "coverage_reports",
            "administrative_unit_vs_vg250_diff.csv",
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ags", "diff_type", "unser_stand", "vg250_stand"])
            writer.writeheader()
            for r in sorted(rows, key=lambda r: (r["diff_type"], r["ags"])):
                writer.writerow(r)

        print(f"AdministrativeUnit-Zeilen (unser Bestand): {len(existing_by_ags)}")
        print(f"VG250-Gemeinden (Stand siehe dokumentation/aktualitaet.txt):  {len(vg250_by_ags)}")
        print(f"Gefundene Abweichungen insgesamt: {len(rows)}")
        by_type = {}
        for r in rows:
            by_type[r["diff_type"]] = by_type.get(r["diff_type"], 0) + 1
        for k, v in by_type.items():
            print(f"  {k}: {v}")
        print(f"\nBericht geschrieben: {out_path}")
        print("Keine Datenbankänderung vorgenommen - rein lesender Vergleich.")
    finally:
        db.close()


def _norm(value):
    """
    Normalisiert einen Namen für den Vergleich zwischen den zwei Quellen.

    WICHTIG - kein Datenfehler, sondern eine Konventionsdifferenz: Destatis
    (unsere bestehende AdministrativeUnit-Tabelle) hängt bei Städten mit
    besonderem Titel den Zusatz an den Namen an (z.B. "Kiel,
    Landeshauptstadt"), während VG250 Name (GEN_G) und Typ (BEZ_G) in
    getrennten Feldern führt ("Kiel" / "Landeshauptstadt"). Ohne diese
    Normalisierung meldet der Vergleich ca. 2.700 Scheinabweichungen, die
    ausschließlich auf dieser Konvention beruhen, nicht auf echten
    Gebietsänderungen. Vergleicht deshalb nur den Namen VOR dem ersten Komma.
    """
    if value is None:
        return ""
    base = str(value).split(",")[0]
    return base.strip().lower().replace("ß", "ss")


if __name__ == "__main__":
    main()
