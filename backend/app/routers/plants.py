from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.entities import Plant, Machine, SafetyZone
from backend.app.schemas.schemas import PlantResponse

router = APIRouter(prefix="/plants", tags=["Plants"])

@router.get("", response_model=List[PlantResponse])
def get_plants(
    status: Optional[str] = Query(None, description="Filter by plant status"),
    db: Session = Depends(get_db)
):
    query = db.query(Plant)
    if status:
        query = query.filter(Plant.status == status)
        
    plants = query.all()
    results = []
    for p in plants:
        resp = PlantResponse.model_validate(p)
        resp.machine_count = db.query(func.count(Machine.machine_id)).filter(Machine.plant_id == p.plant_id).scalar() or 0
        resp.zone_count = db.query(func.count(SafetyZone.safety_zone_id)).filter(SafetyZone.plant_id == p.plant_id).scalar() or 0
        results.append(resp)
    return results

@router.get("/{plant_id}", response_model=PlantResponse)
def get_plant(plant_id: str, db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.plant_id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail=f"Plant {plant_id} not found")
    resp = PlantResponse.model_validate(plant)
    resp.machine_count = db.query(func.count(Machine.machine_id)).filter(Machine.plant_id == plant.plant_id).scalar() or 0
    resp.zone_count = db.query(func.count(SafetyZone.safety_zone_id)).filter(SafetyZone.plant_id == plant.plant_id).scalar() or 0
    return resp
