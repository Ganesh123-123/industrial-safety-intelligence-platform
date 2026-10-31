from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import SafetyZone
from backend.app.schemas.schemas import SafetyZoneResponse

router = APIRouter(prefix="/safety-zones", tags=["Safety Zones"])

@router.get("", response_model=List[SafetyZoneResponse])
def get_safety_zones(
    plant_id: Optional[str] = Query(None, description="Filter by plant"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    db: Session = Depends(get_db)
):
    query = db.query(SafetyZone)
    if plant_id:
        query = query.filter(SafetyZone.plant_id == plant_id)
    if risk_level:
        query = query.filter(SafetyZone.risk_level == risk_level)
    return query.all()

@router.get("/{zone_id}", response_model=SafetyZoneResponse)
def get_safety_zone(zone_id: str, db: Session = Depends(get_db)):
    zone = db.query(SafetyZone).filter(SafetyZone.safety_zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Safety zone {zone_id} not found")
    return zone
