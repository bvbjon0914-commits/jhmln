# -*- coding: utf-8 -*-
"""One-off, read-only: full nationwide coverage report using the existing,
already-tested CoverageAnalysisService - checks EVERY official Gemeinde
(10749 AdministrativeUnit rows) against EVERY active request type (11), via
the real matching engine. Prints per-request-type and overall percentages.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.engine import SessionLocal  # noqa: E402
from app.services.coverage_analysis import (  # noqa: E402
    CATEGORY_CONFLICTING,
    CATEGORY_FALLBACK_ONLY,
    CATEGORY_NO_MATCH,
    CATEGORY_NOT_APPLICABLE,
    CATEGORY_UNVERIFIED_OR_STALE,
    CATEGORY_VERIFIED,
    CoverageAnalysisService,
)


def progress(done, total):
    print(f"... {done}/{total} done", flush=True)


def main():
    db = SessionLocal()
    try:
        svc = CoverageAnalysisService(db)
        t0 = time.time()
        entries = svc.analyze(progress_callback=progress, progress_every=5000)
        print(f"\nAnalysis took {time.time() - t0:.1f}s, {len(entries)} entries\n")

        by_rt = CoverageAnalysisService.summarize_by(entries, "request_type_name")
        print("=== Per Auskunftsart (% of total Gemeinden je Kategorie) ===")
        for row in sorted(by_rt, key=lambda r: r["group"]):
            total = row["total"]
            verified = row.get(CATEGORY_VERIFIED, 0)
            unverified = row.get(CATEGORY_UNVERIFIED_OR_STALE, 0)
            fallback = row.get(CATEGORY_FALLBACK_ONLY, 0)
            no_match = row.get(CATEGORY_NO_MATCH, 0)
            conflicting = row.get(CATEGORY_CONFLICTING, 0)
            not_applicable = row.get(CATEGORY_NOT_APPLICABLE, 0)

            def pct(n):
                return 100.0 * n / total if total else 0.0

            print(
                f"{row['group']:22s} total={total:5d} "
                f"VERIFIED={verified:5d}({pct(verified):4.1f}%) "
                f"UNVERIFIED={unverified:5d}({pct(unverified):4.1f}%) "
                f"FALLBACK_ONLY={fallback:5d}({pct(fallback):4.1f}%) "
                f"NO_MATCH={no_match:5d}({pct(no_match):4.1f}%) "
                f"CONFLICTING={conflicting:5d}({pct(conflicting):4.1f}%) "
                f"NOT_APPLICABLE={not_applicable:5d}({pct(not_applicable):4.1f}%)"
            )

        overall = CoverageAnalysisService.overall_summary(entries)
        print("\n=== Overall ===")
        print(overall)
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
