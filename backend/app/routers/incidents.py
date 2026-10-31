from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.app.database import get_db
from backend.app.models.entities import Incident, Plant, Machine, SafetyZone, CorrectiveAction
from backend.app.services.traceability import TraceabilityService
from backend.app.schemas.schemas import IncidentResponse, IncidentTimelineResponse, PaginatedResponse

router = APIRouter(prefix="/incidents", tags=["Incident Intelligence"])

@router.get("", response_model=PaginatedResponse[IncidentResponse])
def get_incidents(
    plant_id: Optional[str] = Query(None, description="Filter by plant"),
    machine_id: Optional[str] = Query(None, description="Filter by machine"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status (OPEN, RESOLVED, etc.)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Incident, Plant, Machine, SafetyZone)
        .join(Plant, Incident.plant_id == Plant.plant_id)
        .join(Machine, Incident.machine_id == Machine.machine_id)
        .join(SafetyZone, Incident.safety_zone_id == SafetyZone.safety_zone_id)
    )

    if plant_id:
        query = query.filter(Incident.plant_id == plant_id)
    if machine_id:
        query = query.filter(Incident.machine_id == machine_id)
    if severity:
        query = query.filter(Incident.severity == severity)
    if status:
        query = query.filter(Incident.incident_status == status)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size
    records = query.order_by(desc(Incident.incident_timestamp)).offset(offset).limit(page_size).all()

    items = []
    for inc, plt, mch, zn in records:
        resp = IncidentResponse.model_validate(inc)
        resp.plant_name = plt.plant_name
        resp.machine_code = mch.machine_code
        resp.zone_code = zn.zone_code
        resp.corrective_actions_count = db.query(func.count(CorrectiveAction.corrective_action_id)).filter(
            CorrectiveAction.incident_id == inc.incident_id
        ).scalar() or 0
        items.append(resp)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    plant = db.query(Plant).filter(Plant.plant_id == inc.plant_id).first()
    machine = db.query(Machine).filter(Machine.machine_id == inc.machine_id).first()
    zone = db.query(SafetyZone).filter(SafetyZone.safety_zone_id == inc.safety_zone_id).first()

    resp = IncidentResponse.model_validate(inc)
    resp.plant_name = plant.plant_name if plant else None
    resp.machine_code = machine.machine_code if machine else None
    resp.zone_code = zone.zone_code if zone else None
    resp.corrective_actions_count = db.query(func.count(CorrectiveAction.corrective_action_id)).filter(
        CorrectiveAction.incident_id == inc.incident_id
    ).scalar() or 0
    return resp

@router.get("/{incident_id}/timeline", response_model=IncidentTimelineResponse)
def get_incident_timeline(incident_id: str, db: Session = Depends(get_db)):
    trace_service = TraceabilityService(db)
    result = trace_service.build_incident_traceability(incident_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return result
