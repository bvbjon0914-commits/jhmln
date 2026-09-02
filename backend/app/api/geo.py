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

import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.administrative_unit import AdministrativeUnit
from app.models.authority import Authority
from app.models.authority_location import AuthorityLocation
from app.models.building import Building
from app.services.geocoding import geocode_address

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


@router.get("/geo/administrative-unit/{ags}", tags=["Geo"])
def get_administrative_unit_area(ags: str, db: Session = Depends(get_db_session)):
    """
    Liefert die Gemeindefläche zu einem AGS, inkl. eines daraus abgeleiteten
    "flächengleichen" Kreisradius (r = sqrt(Fläche / π)).

    WICHTIG: Das ist NUR eine grobe Visualisierungshilfe, kein echter
    Amtsbezirk – Gemeindegrenzen sind unregelmäßige Polygone, kein Kreis.
    """
    unit = db.query(AdministrativeUnit).filter(AdministrativeUnit.ags == ags).first()
    if not unit:
        raise HTTPException(status_code=404, detail=f"Keine Gemeinde mit AGS {ags} gefunden")
    if not unit.area_km2:
        return {
            "ags": ags,
            "municipality_name": unit.municipality_name,
            "area_km2": None,
            "approx_radius_meters": None,
        }

    radius_meters = math.sqrt(unit.area_km2 * 1_000_000 / math.pi)
    return {
        "ags": ags,
        "municipality_name": unit.municipality_name,
        "area_km2": unit.area_km2,
        "approx_radius_meters": round(radius_meters),
    }


@router.post("/geo/geocode-building/{building_id}", tags=["Geo"])
def geocode_building(building_id: str, db: Session = Depends(get_db_session)):
    """
    Ermittelt Lat/Lng für ein Gebäude über dessen Adresse und speichert sie.
    Überspringt die Anfrage, wenn bereits Koordinaten hinterlegt sind.
    """
    building = db.query(Building).filter(Building.building_id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Gebäude {building_id} nicht gefunden")

    if building.latitude is not None and building.longitude is not None:
        return {"latitude": building.latitude, "longitude": building.longitude, "cached": True}

    address_parts = [
        f"{building.street} {building.house_number}",
        building.postal_code,
        building.city,
        "Deutschland",
    ]
    query = ", ".join(p for p in address_parts if p)

    coords = geocode_address(query)
    if not coords:
        raise HTTPException(status_code=404, detail="Adresse konnte nicht geocodiert werden.")

    building.latitude, building.longitude = coords
    db.commit()
    return {"latitude": coords[0], "longitude": coords[1], "cached": False}


@router.get("/geo/authority-location/{authority_id}", tags=["Geo"])
def get_authority_location(authority_id: str, db: Session = Depends(get_db_session)):
    """
    Ermittelt und cached die Koordinaten einer Behörde über deren Adresse.
    """
    authority = db.query(Authority).filter(Authority.authority_id == authority_id).first()
    if not authority:
        raise HTTPException(status_code=404, detail=f"Behörde {authority_id} nicht gefunden")

    existing = (
        db.query(AuthorityLocation)
        .filter(AuthorityLocation.authority_id == authority_id)
        .first()
    )
    if existing:
        return {"latitude": existing.latitude, "longitude": existing.longitude, "cached": True}

    street_line = None
    if authority.street:
        street_line = f"{authority.street} {authority.house_number}" if authority.house_number else authority.street

    address_parts = [street_line, authority.postal_code, authority.city, "Deutschland"]
    query = ", ".join(p for p in address_parts if p)

    coords = geocode_address(query)
    if not coords:
        raise HTTPException(status_code=404, detail="Adresse konnte nicht geocodiert werden.")

    location = AuthorityLocation(authority_id=authority_id, latitude=coords[0], longitude=coords[1])
    db.add(location)
    db.commit()
    return {"latitude": coords[0], "longitude": coords[1], "cached": False}
