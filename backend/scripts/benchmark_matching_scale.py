"""
Lastmessung der Matching-Engine auf synthetischen Daten (Priorität 2 des
Auditberichts: "Belege Änderungen mit einem Test auf synthetischen Daten;
behaupte keine Leistungsfähigkeit für 2.000 reale Objekte ohne Messung.")

Läuft ausschließlich gegen eine frische, temporäre SQLite-Datei - niemals
gegen backend/authority_matching.db oder eine produktive Datenbank.

WICHTIG - Grenzen dieser Messung (ehrlich benannt, nicht nur behauptet):
- Lokales SQLite ohne Netzwerklatenz. Die Produktivdatenbank (Neon,
  serverloses Postgres) hat pro Anfrage reale Netzwerk-Latenz - die absolute
  Dauer hier ist deshalb eine UNTERGRENZE, kein Produktivwert. Die ANZAHL der
  ausgeführten Datenbankabfragen (die die Netzwerk-Latenz in Produktion
  multipliziert) ist dagegen aussagekräftig und überträgt sich direkt.
- Einfache, gleichverteilte synthetische Daten (eine Handvoll AGS-Werte,
  eine Regel pro AGS+Auskunftsart) - reale Datenverteilungen (viele Gebäude
  pro Gemeinde, Sonderregeln auf Straßenebene) könnten abweichen.

Aufruf:
    DATABASE_URL="sqlite:///./benchmark_tmp.db" venv/Scripts/python.exe scripts/benchmark_matching_scale.py --buildings 2000
"""
import argparse
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--buildings", type=int, default=2000)
    parser.add_argument("--municipalities", type=int, default=50)
    parser.add_argument("--request-types", type=int, default=11)
    parser.add_argument(
        "--coverage-fraction", type=float, default=0.8,
        help="Anteil der (Gemeinde,Auskunftsart)-Kombinationen mit hinterlegter Regel",
    )
    args = parser.parse_args()

    if "DATABASE_URL" not in os.environ:
        print("FEHLER: Bitte DATABASE_URL auf eine TEMPORÄRE SQLite-Datei setzen, "
              "z.B. sqlite:///./benchmark_tmp.db - Abbruch ohne Angabe, um versehentliches "
              "Schreiben in authority_matching.db auszuschließen.")
        sys.exit(1)
    if "authority_matching.db" in os.environ["DATABASE_URL"] and "benchmark" not in os.environ["DATABASE_URL"]:
        print("FEHLER: DATABASE_URL zeigt auf die echte Entwicklungsdatenbank - Abbruch.")
        sys.exit(1)

    from app.database.base import Base
    from app.database.engine import engine, SessionLocal
    from app.models.building import Building
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction
    from app.models.request_type import RequestType, STANDARD_REQUEST_TYPES
    from app.services.jurisdiction_matcher import JurisdictionMatchingService
    from app.api.data_quality import _coverage_gaps
    from sqlalchemy import event

    query_counter = {"n": 0}

    @event.listens_for(engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany):
        query_counter["n"] += 1

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    request_type_ids = list(STANDARD_REQUEST_TYPES)[: args.request_types]
    for code in request_type_ids:
        db.add(RequestType(request_type_id=code, code=code, name=code.title(), active=True))
    db.commit()

    ags_values = [f"{i:08d}" for i in range(args.municipalities)]

    print(f"Erzeuge {len(ags_values)} synthetische Gemeinden (AGS) ...")
    authorities_by_key = {}
    n_jurisdictions = 0
    for ags in ags_values:
        for rt in request_type_ids:
            if hash((ags, rt)) % 100 >= args.coverage_fraction * 100:
                continue  # bewusste Lücke, für die Abdeckungslücken-Messung
            key = (ags, rt)
            auth_id = str(uuid.uuid4())
            authorities_by_key[key] = auth_id
            db.add(Authority(authority_id=auth_id, authority_name=f"Amt {ags}-{rt}", city=f"Ort{ags}", active=True))
            db.add(Jurisdiction(
                jurisdiction_id=str(uuid.uuid4()), request_type_id=rt, authority_id=auth_id,
                ags=ags, priority=40, matching_level="MUNICIPALITY", active=True,
            ))
            n_jurisdictions += 1
    db.commit()
    print(f"  -> {n_jurisdictions} Zuständigkeitsregeln angelegt.")

    print(f"Erzeuge {args.buildings} synthetische Gebäude ...")
    building_ids = []
    t0 = time.perf_counter()
    for i in range(args.buildings):
        ags = ags_values[i % len(ags_values)]
        bid = str(uuid.uuid4())
        building_ids.append((bid, ags))
        db.add(Building(
            building_id=bid, street="Musterstraße", house_number=str(i % 200 + 1),
            postal_code="00000", city=f"Ort{ags}", ags=ags,
        ))
        if (i + 1) % 500 == 0:
            db.commit()
    db.commit()
    print(f"  -> in {time.perf_counter() - t0:.2f}s angelegt.")

    # ---------- Messung 1: Bulk-Matching, wie es der Multi-Gebäude-Wizard
    # (N unabhängige POST /api/matching, hier ohne HTTP-Overhead simuliert)
    # pro Gebäude über alle Auskunftsarten auslösen würde ----------
    print(f"\nMessung 1: match_authorities() für {args.buildings} Gebäude x {len(request_type_ids)} Auskunftsarten ...")
    matcher = JurisdictionMatchingService(db)
    buildings = db.query(Building).all()
    query_counter["n"] = 0
    t0 = time.perf_counter()
    total_results = 0
    for b in buildings:
        results = matcher.match_authorities(b, request_type_ids)
        total_results += len(results)
    elapsed = time.perf_counter() - t0
    n_queries_1 = query_counter["n"]
    print(f"  -> {total_results} Matching-Ergebnisse in {elapsed:.2f}s "
          f"({elapsed / max(total_results, 1) * 1000:.2f} ms/Ergebnis, lokales SQLite ohne Netzwerklatenz).")
    print(f"  -> {total_results / max(elapsed, 0.001):.0f} Matches/Sekunde (lokal).")
    print(f"  -> {n_queries_1} SQL-Abfragen insgesamt ({n_queries_1 / max(total_results, 1):.1f} je Match-Ergebnis).")
    print(f"     Bei Neon-Produktionslatenz von z.B. 20-50ms/Abfrage (typisch für ein "
          f"serverloses Postgres über das offene Internet, nicht selbst gemessen) ergäbe "
          f"das rein rechnerisch {n_queries_1 * 0.02:.0f}-{n_queries_1 * 0.05:.0f}s NUR für "
          f"diese Abfragen, seriell ausgeführt.")

    # ---------- Messung 2: Abdeckungslücken-Prüfung (Datenqualitäts-Modul) ----------
    print("\nMessung 2: _coverage_gaps() (Datenqualitäts-Übersicht) für denselben Bestand ...")
    query_counter["n"] = 0
    t0 = time.perf_counter()
    gaps = _coverage_gaps(db)
    elapsed2 = time.perf_counter() - t0
    n_queries_2 = query_counter["n"]
    print(f"  -> {len(gaps)} Abdeckungslücken-Gruppen gefunden in {elapsed2:.2f}s, {n_queries_2} SQL-Abfragen.")

    db.close()

    print("\n=== Zusammenfassung (lokales SQLite, keine Netzwerklatenz) ===")
    print(f"Gebäude: {args.buildings} | Auskunftsarten: {len(request_type_ids)} | Gemeinden: {args.municipalities}")
    print(f"Bulk-Matching gesamt: {elapsed:.2f}s")
    print(f"Abdeckungslücken-Check gesamt: {elapsed2:.2f}s")
    print("HINWEIS: Absolutwerte sind eine Untergrenze - Produktion (Neon Postgres) hat reale ")
    print("Netzwerklatenz pro Abfrage, die sich mit der Zahl der Abfragen multipliziert (siehe")
    print("Docstring). Aussagekräftig ist vor allem die STRUKTUR: pro Gebäude x Auskunftsart ")
    print("werden bis zu 7 sequenzielle Abfragen ausgeführt, ohne Batching über Gebäude hinweg.")


if __name__ == "__main__":
    main()
