"""
API Routes: Geo-Zuordnung (Ort -> AGS)

Löst einen eingegebenen Orts-/Gemeindenamen (optional mit Bundesland)
über die offizielle Gemeindetabelle (administrative_units) zu einem
Amtlichen Gemeindeschlüssel (AGS) auf.

WICHTIG (gleiche Philosophie wie beim Matching): Es wird NICHT geraten.
Bei mehreren möglichen Treffern werden alle Kandidaten zurückgegeben,
damit der Nutzer selbst auswählen kann, statt dass das System einen
falschen Treffer automatisch übernimmt.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.administrative_unit import AdministrativeUnit

router = APIRouter()


def _serialize(u: AdministrativeUnit) -> dict:
    return {
        "ags": u.ags,
        "ags_kreis": u.ags_kreis,
        "state_name": u.state_name,
        "county_name": u.county_name,
        "municipality_name": u.municipality_name,
        "municipality_type": u.municipality_type,
        "postal_code": u.postal_code,
    }


@router.get("/geo/resolve-ags", tags=["Geo"])
def resolve_ags(
    city: str = Query(..., min_length=2, description="Ortsname / Gemeindename"),
    state: Optional[str] = Query(None, description="Bundesland, optional zur Eingrenzung"),
    db: Session = Depends(get_db_session),
):
    """
    Ermittelt den AGS zu einem Ortsnamen.

    Rückgabe:
      - status="MATCHED": genau ein Kandidat -> candidates[0] verwenden
      - status="AMBIGUOUS": mehrere Kandidaten -> Nutzer muss auswählen
      - status="NOT_FOUND": kein Treffer -> AGS muss manuell gepflegt werden
    """
    city_norm = city.strip().lower()

    def base_query():
        q = db.query(AdministrativeUnit).filter(
            AdministrativeUnit.municipality_name.ilike(f"%{city_norm}%")
        )
        if state:
            q = q.filter(func.lower(AdministrativeUnit.state_name) == state.strip().lower())
        return q.order_by(AdministrativeUnit.municipality_name).limit(200).all()

    pool = base_query()

    # Amtliche Namen tragen oft einen Zusatz nach einem Komma, z.B.
    # "München, Landeshauptstadt" oder "Neustadt a.d.Aisch, St" - der Teil
    # vor dem Komma ist der eigentliche Ortsname. Exakter Treffer auf diesem
    # Teil ist zuverlässiger als eine reine Teilstring-Suche.
    def short_name(u: AdministrativeUnit) -> str:
        return u.municipality_name.split(",")[0].strip().lower()

    exact_matches = [u for u in pool if short_name(u) == city_norm]
    matches = exact_matches if exact_matches else pool

    candidates: List[dict] = [_serialize(u) for u in matches]

    if len(candidates) == 1:
        status = "MATCHED"
    elif len(candidates) == 0:
        status = "NOT_FOUND"
    else:
        status = "AMBIGUOUS"

    return {"status": status, "query": {"city": city_norm, "state": state}, "candidates": candidates}
