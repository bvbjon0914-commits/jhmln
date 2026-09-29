# -*- coding: utf-8 -*-
"""Fast approximation of _full_coverage_report.py: one representative
Gemeinde per Kreis (401 total, same MIN(ags) convention as
_selftest_matching_sample.py) x all active request types, using the same
CoverageAnalysisService classification (VERIFIED / UNVERIFIED_OR_STALE /
FALLBACK_ONLY / NO_MATCH / CONFLICTING) as the full nationwide report.
~28x fewer combinations than checking every Gemeinde, so a rough estimate
in minutes rather than ~1.5-2 hours - NOT a substitute for the full report
when exact Gemeinde-level counts matter.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func  # noqa: E402

from app.database.engine import SessionLocal  # noqa: E402
from app.models.administrative_unit import AdministrativeUnit  # noqa: E402
from app.models.building import Building  # noqa: E402
from app.models.request_type import RequestType  # noqa: E402
from app.services.coverage_analysis import (  # noqa: E402
    CATEGORY_CONFLICTING,
    CATEGORY_FALLBACK_ONLY,
    CATEGORY_NO_MATCH,
    CATEGORY_NOT_APPLICABLE,
    CATEGORY_UNVERIFIED_OR_STALE,
    CATEGORY_VERIFIED,
    CoverageAnalysisService,
)


def main():
    db = SessionLocal()
    try:
        svc = CoverageAnalysisService(db)

        min_ags_per_kreis = (
            db.query(func.min(AdministrativeUnit.ags))
            .group_by(AdministrativeUnit.ags_kreis)
            .all()
        )
        sample_ags = [r[0] for r in min_ags_per_kreis]
        units = (
            db.query(AdministrativeUnit)
            .filter(AdministrativeUnit.ags.in_(sample_ags))
            .all()
        )
        request_types = db.query(RequestType).filter(RequestType.active.is_(True)).all()
        print(f"{len(units)} Kreise (Stichprobe) x {len(request_types)} Auskunftsarten "
              f"= {len(units) * len(request_types)} Kombinationen\n")

        by_rt = {rt.name: {c: 0 for c in (
            CATEGORY_VERIFIED, CATEGORY_UNVERIFIED_OR_STALE, CATEGORY_FALLBACK_ONLY,
            CATEGORY_NO_MATCH, CATEGORY_CONFLICTING, CATEGORY_NOT_APPLICABLE)} for rt in request_types}
        overall = {c: 0 for c in by_rt[request_types[0].name]}

        for unit in units:
            probe = Building(
                building_id="__coverage_probe__", street="", house_number="",
                city=unit.municipality_name, postal_code=unit.postal_code,
                district=None, state=unit.state_name, ags=unit.ags,
            )
            for rt in request_types:
                result = svc.matcher.match_authority(probe, rt.request_type_id)
                category, _ = svc._classify(result)
                by_rt[rt.name][category] += 1
                overall[category] += 1

        total_per_rt = len(units)
        print("=== Per Auskunftsart (Stichprobe: 1 Gemeinde je Kreis) ===")
        for name in sorted(by_rt):
            counts = by_rt[name]

            def pct(n):
                return 100.0 * n / total_per_rt if total_per_rt else 0.0

            print(
                f"{name:22s} total={total_per_rt:4d} "
                f"VERIFIED={counts[CATEGORY_VERIFIED]:4d}({pct(counts[CATEGORY_VERIFIED]):4.1f}%) "
                f"UNVERIFIED={counts[CATEGORY_UNVERIFIED_OR_STALE]:4d}"
                f"({pct(counts[CATEGORY_UNVERIFIED_OR_STALE]):4.1f}%) "
                f"FALLBACK_ONLY={counts[CATEGORY_FALLBACK_ONLY]:4d}({pct(counts[CATEGORY_FALLBACK_ONLY]):4.1f}%) "
                f"NO_MATCH={counts[CATEGORY_NO_MATCH]:4d}({pct(counts[CATEGORY_NO_MATCH]):4.1f}%) "
                f"CONFLICTING={counts[CATEGORY_CONFLICTING]:4d}({pct(counts[CATEGORY_CONFLICTING]):4.1f}%) "
                f"NOT_APPLICABLE={counts[CATEGORY_NOT_APPLICABLE]:4d}"
                f"({pct(counts[CATEGORY_NOT_APPLICABLE]):4.1f}%)"
            )

        total_all = len(units) * len(request_types)
        print("\n=== Overall (Stichprobe) ===")
        for k, v in overall.items():
            print(f"  {k}: {v} ({100.0 * v / total_all:.1f}%)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
