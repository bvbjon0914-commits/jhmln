"""
Führt die AGS x Auskunftsart-Abdeckungsanalyse (CoverageAnalysisService)
gegen eine echte Datenbank aus und schreibt die Ergebnisse als CSV.

Rein LESEND - schreibt oder verändert keine einzige Zeile in jurisdictions,
authorities, buildings oder administrative_units. Sicher gegen die lokale
Entwicklungsdatenbank; NIE gegen Produktion ausführen (siehe Auftrag: "Keine
Migration, kein Import ... gegen Produktion" - das schließt auch rein lesende
Analysen aus Vorsicht ein, wenn DATABASE_URL auf Produktion zeigt).

Aufruf (gegen die lokale Entwicklungsdatenbank, Standard-DATABASE_URL):
    venv/Scripts/python.exe scripts/run_coverage_analysis.py

Aufruf gegen eine andere DB:
    DATABASE_URL="sqlite:///./irgendeine_kopie.db" venv/Scripts/python.exe scripts/run_coverage_analysis.py
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print(
            "FEHLER: DATABASE_URL sieht nach einer entfernten/produktiven Postgres-Verbindung aus. "
            "Dieses Skript ist rein lesend, aber der Auftrag verlangt ausdrücklich, dass produktive "
            "Zugriffe nur explizit und mit Bedacht erfolgen - Abbruch. Setze DATABASE_URL bewusst, "
            "falls dies wirklich beabsichtigt (read-only) ist, z.B. über eine schreibgeschützte Rolle."
        )
        sys.exit(1)

    from app.database.engine import SessionLocal
    from app.services.coverage_analysis import CoverageAnalysisService, ALL_CATEGORIES

    print(f"Analysiere Abdeckung gegen: {database_url}")
    db = SessionLocal()
    try:
        service = CoverageAnalysisService(db)

        start = time.time()

        def progress(done, total):
            elapsed = time.time() - start
            rate = done / elapsed if elapsed > 0 else 0
            print(f"  {done}/{total} Proben ({rate:.0f}/s)", flush=True)

        entries = service.analyze(progress_callback=progress)
        elapsed = time.time() - start
        print(f"Fertig: {len(entries)} Proben in {elapsed:.1f}s")

        overall = CoverageAnalysisService.overall_summary(entries)
        print("\n=== Gesamtübersicht ===")
        for cat in ALL_CATEGORIES:
            pct = (overall[cat] / overall["total"] * 100) if overall["total"] else 0
            print(f"  {cat:22s}: {overall[cat]:7d}  ({pct:5.1f}%)")

        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "coverage_reports")
        os.makedirs(out_dir, exist_ok=True)

        detail_path = os.path.join(out_dir, "coverage_detail.csv")
        with open(detail_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ags", "state_name", "county_name", "municipality_name",
                "request_type_id", "request_type_name", "category",
                "matching_level", "jurisdiction_id", "portfolio_building_count", "reason",
            ])
            for e in entries:
                writer.writerow([
                    e.ags, e.state_name, e.county_name, e.municipality_name,
                    e.request_type_id, e.request_type_name, e.category,
                    e.matching_level, e.jurisdiction_id, e.portfolio_building_count, e.reason,
                ])
        print(f"\nDetailtabelle geschrieben: {detail_path}")

        for group_field, filename in [
            ("state_name", "coverage_by_state.csv"),
            ("county_name", "coverage_by_county.csv"),
            ("municipality_name", "coverage_by_municipality.csv"),
            ("request_type_name", "coverage_by_request_type.csv"),
        ]:
            grouped = CoverageAnalysisService.summarize_by(entries, group_field)
            path = os.path.join(out_dir, filename)
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["group", "total", "affected_buildings"] + ALL_CATEGORIES)
                for g in grouped:
                    row = [g["group"], g["total"], g["affected_buildings"]] + [g[c] for c in ALL_CATEGORIES]
                    writer.writerow(row)
            print(f"Gruppierung nach {group_field} geschrieben: {path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
