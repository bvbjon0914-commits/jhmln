# -*- coding: utf-8 -*-
"""Re-scope 7 "Katasteramt X, Stadt" authorities in Baden-Wuerttemberg from
COUNTY level (wrongly duplicating their Landkreis's own COUNTY-level
"Katasteramt X" rule) down to their own MUNICIPALITY-level ags, for KATASTER.

Found by a diagnostic pass over the KATASTER COUNTY-level duplicate-ags
groups surfaced by the matching self-test, then verified via official
sources (see docs/ABSCHLUSSBERICHT_DATENQUALITAET.md): Baden-Wuerttemberg's
Vermessungsgesetz (VermG BW, in Kraft seit 01.01.2005) kommunalisierte das
Vermessungswesen auf die Landkreise, benennt in Paragraph 7 Absatz 2 VermG
aber zusaetzlich einzelne Grosse Kreisstaedte als eigene untere
Vermessungsbehoerde, getrennt von ihrem Landkreis - amtlich bestaetigt durch
die LGL-Liste "Untere Vermessungsbehoerden - Staedte". Goeppingen,
Ludwigsburg, Heidenheim an der Brenz, Konstanz, Loerrach, Reutlingen und
Tuebingen stehen alle auf dieser Liste: beide Behoerden (Stadt + Landkreis)
sind real und aktiv, aber die Datenbank gab ihnen bisher identischen Scope
(dieselbe Kreis-AGS statt nach Gebiet getrennt) - genau wie das bereits
gefixte Wasserbehoerde-Muster (fix_wasserbehoerde_stadt_rescope.py).

This script:
  1. stages + approves a new MUNICIPALITY-level rule for the SAME existing
     "Katasteramt X, Stadt" authority_id at the city's own ags (no new
     authority, no new external source needed beyond the already-verified
     legal basis - just correcting the scope of an already-known office), and
  2. expires the old COUNTY-level rule for that authority (it is now fully
     superseded within the city by the new MUNICIPALITY rule; the Landkreis's
     own "Katasteramt X" COUNTY rule is left untouched and continues to
     correctly cover the rest of the Kreis).

Kept OUT of scope deliberately: the 33 Bayern KATASTER duplicate-ags groups
(documented AEDBV multi-Kreis consolidation per VermBezV - a different,
already-legitimate pattern, not this bug).
"""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Struktur-Korrektur 2026-09-28, Kataster-BW-Rescoping analog Wasserbehoerde)"

# (ags_kreis, city's own municipality ags, city name as it appears after "Katasteramt ")
TARGETS = [
    ("08117", "08117026", "Göppingen"),
    ("08118", "08118048", "Ludwigsburg"),
    ("08135", "08135019", "Heidenheim"),
    ("08335", "08335043", "Konstanz"),
    ("08336", "08336050", "Lörrach"),
    ("08415", "08415061", "Reutlingen"),
    ("08416", "08416041", "Tübingen"),
]
REQUEST_TYPE_CODE = "KATASTER"


def main(apply_changes: bool) -> None:
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction
    from app.models.request_type import RequestType
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import ConflictType, JurisdictionStagingService

    db = SessionLocal()
    batch_id = f"fix-kataster-bw-rescope-{date.today().isoformat()}"
    staging = JurisdictionStagingService(db)
    today = date.today()
    yesterday = today - timedelta(days=1)

    try:
        rt_id = db.query(RequestType.request_type_id).filter(RequestType.code == REQUEST_TYPE_CODE).scalar()

        results = []
        for ags_kreis, city_ags, city_name in TARGETS:
            old_rule = (
                db.query(Jurisdiction)
                .join(Authority, Authority.authority_id == Jurisdiction.authority_id)
                .filter(
                    Jurisdiction.request_type_id == rt_id,
                    Jurisdiction.ags == ags_kreis,
                    Jurisdiction.matching_level == "COUNTY",
                    Jurisdiction.active.is_(True),
                    Authority.authority_name == f"Katasteramt {city_name}, Stadt",
                )
                .first()
            )
            if old_rule is None:
                print(f"SKIP {ags_kreis} ({city_name}): keine passende COUNTY-Zeile gefunden")
                continue
            if old_rule.valid_to is not None and old_rule.valid_to < today:
                print(f"SKIP {ags_kreis} ({city_name}): bereits abgelaufen (idempotent)")
                continue

            existing_muni = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.request_type_id == rt_id,
                    Jurisdiction.ags == city_ags,
                    Jurisdiction.active.is_(True),
                )
                .first()
            )
            if existing_muni is not None:
                print(f"SKIP {ags_kreis} ({city_name}): MUNICIPALITY-Regel bei {city_ags} existiert bereits")
                continue

            print(
                f"KATASTER {ags_kreis} ({city_name}): rescope authority_id={old_rule.authority_id} "
                f"von COUNTY/{ags_kreis} (jurisdiction_id={old_rule.jurisdiction_id}) "
                f"nach MUNICIPALITY/{city_ags}"
            )
            results.append((ags_kreis, city_ags, city_name, old_rule))

        if not results:
            print("Nichts zu tun.")
            return

        if not apply_changes:
            print(f"\n{len(results)} Kandidaten. Dry-run only - keine Aenderung. --apply zum Anwenden.")
            return

        approved = []
        conflicts = []
        for ags_kreis, city_ags, city_name, old_rule in results:
            entry = staging.stage_entry(
                batch_id=batch_id,
                batch_label="Struktur-Korrektur: Kataster-BW-Rescoping (Stadt -> eigene Gemeinde-AGS)",
                request_type_id=rt_id, ags=city_ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=old_rule.authority_id,
                source=(
                    f"Interne Struktur-Korrektur nach Verifikation gegen offizielle Quellen (VermG BW "
                    f"Paragraph 7 Abs. 2, LGL-BW-Liste 'Untere Vermessungsbehoerden - Staedte', "
                    f"Stand 12.09.2019): Authority war bereits als eigene untere Vermessungsbehoerde der "
                    f"Stadt {city_name} in der Datenbank vorhanden (Regel {old_rule.jurisdiction_id}), "
                    f"faelschlich auf die Kreis-AGS {ags_kreis} statt auf die eigene Gemeinde-AGS "
                    f"{city_ags} skaliert. Das Landkreis-Katasteramt bleibt unveraendert auf COUNTY-Ebene."
                ),
                source_license="Interne Korrektur (Rescoping, externe Quelle siehe oben)",
                source_retrieved_at=None,
            )
            if entry.conflict_type != ConflictType.NEW:
                conflicts.append((entry, ags_kreis, city_name))
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                resulting_verification_status=old_rule.verification_status,
                review_notes=(
                    f"Rescoping: Katasteramt {city_name}, Stadt von COUNTY/{ags_kreis} nach "
                    f"MUNICIPALITY/{city_ags}, alte COUNTY-Zeile {old_rule.jurisdiction_id} wird abgelaufen."
                ),
            )
            old_rule.valid_to = yesterday
            old_rule.notes = (
                (old_rule.notes + " | " if old_rule.notes else "")
                + f"Expired {today.isoformat()}: rescoped nach MUNICIPALITY/{city_ags} "
                f"(jurisdiction_id siehe Batch {batch_id})."
            )
            approved.append((entry, ags_kreis, city_name))

        db.commit()
        print(f"\nBatch: {batch_id}")
        print(f"Angewendet: {len(approved)}, Konflikte (blieben PENDING, nichts geaendert): {len(conflicts)}")
        for entry, ags_kreis, city_name in conflicts:
            print(f"  KONFLIKT #{entry.id} {ags_kreis} ({city_name}): {entry.conflict_type} - {entry.conflict_reason}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
