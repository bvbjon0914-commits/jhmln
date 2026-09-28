# -*- coding: utf-8 -*-
"""Re-scope 8 "Stadt X - Untere Wasserbehoerde" authorities from COUNTY level
(wrongly duplicating their Landkreis's own COUNTY-level rule) down to their
own MUNICIPALITY-level ags, for HOCHWASSERSCHUTZ and WASSERSCHUTZ.

Found by a diagnostic pass over the water-authority COUNTY-level duplicate-ags
groups surfaced by the matching self-test after the Bauaufsicht bulk fix.
Unlike the Offenbach/Kassel cases (a genuinely different entity mis-scoped
onto someone else's ags), these 8 cities are legitimate: Niedersachsen's
"grosse selbstaendige Stadt" status (NKomVG) and Saarland's kreisweite
Kombi-Behoerden ("... Bauaufsichtsbehoerde / Untere Wasserbehoerde") give the
city itself a real, separate Untere Wasserbehoerde alongside its Landkreis's.
The DB already models this correctly for BAUAKTEN/BAULASTEN (see the earlier
bundesweite fix + the Saarland Kreisstadt Bauaufsicht rows): the city's
authority sits at MUNICIPALITY level on its OWN ags, while the Landkreis's
authority stays at COUNTY level - the 7-level hierarchy then picks the more
specific MUNICIPALITY match inside the city and falls back to the Landkreis's
COUNTY match everywhere else in the Kreis, without ambiguity.

For HOCHWASSERSCHUTZ/WASSERSCHUTZ this re-scoping was never done: the city's
authority is still sitting at COUNTY level on the SAME ags as the Landkreis,
which is what causes MULTIPLE_MATCHES. This script:
  1. stages + approves a new MUNICIPALITY-level rule for the SAME existing
     authority_id at the city's own ags (no new authority, no new external
     source - just correcting the scope of an already-known office, exactly
     like app/services/kreis_scope_fix.py does for the mirror-image bug), and
  2. expires the old COUNTY-level rule for that authority (it is now fully
     superseded within the city by the new MUNICIPALITY rule; everywhere
     else in the Kreis it was never correct to have the city's office match
     at all).

Kept OUT of scope deliberately: the 20 Bayern Wasser "Teilzustaendigkeit"
ags-groups (Art. 63 BayWG partial-competency split - a different, apparently
intentional design, not this bug) and the 33 Bayern + 7 Baden-Wuerttemberg
KATASTER groups (also confirmed legitimate dual authority via official
sources - see docs/ABSCHLUSSBERICHT_DATENQUALITAET.md).
"""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Struktur-Korrektur 2026-09-28, Wasserbehoerde-Rescoping analog Bauaufsicht)"

# (ags_kreis, city's own municipality ags, city name for the Stadt-authority match)
TARGETS = [
    ("03153", "03153017", "Goslar"),
    ("03159", "03159016", "Göttingen"),
    ("03254", "03254021", "Hildesheim"),
    ("03351", "03351006", "Celle"),
    ("03352", "03352011", "Cuxhaven"),
    ("03355", "03355022", "Lüneburg"),
    ("10043", "10043114", "Neunkirchen"),
    ("10044", "10044115", "Saarlouis"),
]
REQUEST_TYPE_CODES = ["HOCHWASSERSCHUTZ", "WASSERSCHUTZ"]


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
    batch_id = f"fix-wasserbehoerde-rescope-{date.today().isoformat()}"
    staging = JurisdictionStagingService(db)
    today = date.today()
    yesterday = today - timedelta(days=1)

    try:
        rt_ids = {
            code: db.query(RequestType.request_type_id).filter(RequestType.code == code).scalar()
            for code in REQUEST_TYPE_CODES
        }

        results = []
        for ags_kreis, city_ags, city_name in TARGETS:
            for code, rt_id in rt_ids.items():
                old_rule = (
                    db.query(Jurisdiction)
                    .join(Authority, Authority.authority_id == Jurisdiction.authority_id)
                    .filter(
                        Jurisdiction.request_type_id == rt_id,
                        Jurisdiction.ags == ags_kreis,
                        Jurisdiction.matching_level == "COUNTY",
                        Jurisdiction.active.is_(True),
                        Authority.authority_name.like(f"Stadt {city_name}%"),
                    )
                    .first()
                )
                if old_rule is None:
                    print(f"SKIP {code} {ags_kreis} ({city_name}): keine passende COUNTY-Zeile gefunden")
                    continue
                if old_rule.valid_to is not None and old_rule.valid_to < today:
                    print(f"SKIP {code} {ags_kreis} ({city_name}): bereits abgelaufen (idempotent)")
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
                    print(f"SKIP {code} {ags_kreis} ({city_name}): MUNICIPALITY-Regel bei {city_ags} existiert bereits")
                    continue

                print(
                    f"{code} {ags_kreis} ({city_name}): rescope authority_id={old_rule.authority_id} "
                    f"von COUNTY/{ags_kreis} (jurisdiction_id={old_rule.jurisdiction_id}) "
                    f"nach MUNICIPALITY/{city_ags}"
                )
                results.append((code, rt_id, ags_kreis, city_ags, city_name, old_rule))

        if not results:
            print("Nichts zu tun.")
            return

        if not apply_changes:
            print(f"\n{len(results)} Kandidaten. Dry-run only - keine Aenderung. --apply zum Anwenden.")
            return

        approved = []
        conflicts = []
        for code, rt_id, ags_kreis, city_ags, city_name, old_rule in results:
            entry = staging.stage_entry(
                batch_id=batch_id,
                batch_label="Struktur-Korrektur: Wasserbehoerde-Rescoping (Stadt -> eigene Gemeinde-AGS)",
                request_type_id=rt_id, ags=city_ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=old_rule.authority_id,
                source=(
                    f"Interne Struktur-Korrektur: Authority war bereits als Untere Wasserbehoerde der "
                    f"Stadt {city_name} in der Datenbank vorhanden (Regel {old_rule.jurisdiction_id}), "
                    f"faelschlich auf die Kreis-AGS {ags_kreis} statt auf die eigene Gemeinde-AGS "
                    f"{city_ags} skaliert. Analog zur bereits durchgefuehrten Bauaufsicht-Korrektur fuer "
                    f"dieselbe Stadt (grosse selbstaendige Stadt / Saarland-Kreisstadt-Kombibehoerde)."
                ),
                source_license="Interne Korrektur (keine externe Datenquelle)",
                source_retrieved_at=None,
            )
            if entry.conflict_type != ConflictType.NEW:
                conflicts.append((entry, code, ags_kreis, city_name))
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER,
                resulting_verification_status=old_rule.verification_status,
                review_notes=(
                    f"Rescoping: {city_name} Untere Wasserbehoerde von COUNTY/{ags_kreis} nach "
                    f"MUNICIPALITY/{city_ags}, alte COUNTY-Zeile {old_rule.jurisdiction_id} wird abgelaufen."
                ),
            )
            old_rule.valid_to = yesterday
            old_rule.notes = (
                (old_rule.notes + " | " if old_rule.notes else "")
                + f"Expired {today.isoformat()}: rescoped nach MUNICIPALITY/{city_ags} "
                f"(jurisdiction_id siehe Batch {batch_id})."
            )
            approved.append((entry, code, ags_kreis, city_name))

        db.commit()
        print(f"\nBatch: {batch_id}")
        print(f"Angewendet: {len(approved)}, Konflikte (blieben PENDING, nichts geaendert): {len(conflicts)}")
        for entry, code, ags_kreis, city_name in conflicts:
            print(f"  KONFLIKT #{entry.id} {code} {ags_kreis} ({city_name}): {entry.conflict_type} - {entry.conflict_reason}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
