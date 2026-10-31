from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.entities import (
    Machine, Plant, AlarmEvent, Interlock, MachineSafetyZone,
    SafetyZone, MachineStateHistory
)
from backend.app.services.rules import BusinessRulesEngine
from backend.app.schemas.schemas import MachineResponse, PaginatedResponse, InterlockResponse

router = APIRouter(prefix="/machines", tags=["Machines"])

@router.get("", response_model=PaginatedResponse[MachineResponse])
def get_machines(
    plant_id: Optional[str] = Query(None, description="Filter by plant"),
    machine_type: Optional[str] = Query(None, description="Filter by machine type"),
    status: Optional[str] = Query(None, description="Filter by operational status"),
    search: Optional[str] = Query(None, description="Search machine name or code"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Machine).join(Plant, Machine.plant_id == Plant.plant_id)
    if plant_id:
        query = query.filter(Machine.plant_id == plant_id)
    if machine_type:
        query = query.filter(Machine.machine_type == machine_type)
    if status:
        query = query.filter(Machine.operational_status == status)
    if search:
        query = query.filter(
            Machine.machine_name.ilike(f"%{search}%") | Machine.machine_code.ilike(f"%{search}%")
        )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size
    machines = query.offset(offset).limit(page_size).all()

    # Precalculate repeated scores
    rules_engine = BusinessRulesEngine(db)
    scores = {s.machine_id: s.score for s in rules_engine.calculate_repeated_condition_scores(window_hours=72)}

    items = []
    for m in machines:
        resp = MachineResponse.model_validate(m)
        resp.plant_name = m.plant.plant_name if m.plant else None
        resp.active_alarms_count = db.query(func.count(AlarmEvent.alarm_event_id)).filter(
            AlarmEvent.machine_id == m.machine_id,
            AlarmEvent.alarm_status == "ACTIVE"
        ).scalar() or 0
        resp.repeated_condition_score = scores.get(m.machine_id, 0.0)
        items.append(resp)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{machine_id}")
def get_machine_detail(machine_id: str, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")

    interlocks = db.query(Interlock).filter(Interlock.machine_id == machine_id).all()
    zone_mappings = (
        db.query(SafetyZone)
        .join(MachineSafetyZone, SafetyZone.safety_zone_id == MachineSafetyZone.safety_zone_id)
        .filter(MachineSafetyZone.machine_id == machine_id)
        .all()
    )
    recent_history = (
        db.query(MachineStateHistory)
        .filter(MachineStateHistory.machine_id == machine_id)
        .order_by(MachineStateHistory.transition_timestamp.desc())
        .limit(10)
        .all()
    )

    resp = MachineResponse.model_validate(machine)
    resp.plant_name = machine.plant.plant_name if machine.plant else None

    return {
        "machine": resp,
        "interlocks": [InterlockResponse.model_validate(i) for i in interlocks],
        "assigned_zones": [{"zone_id": z.safety_zone_id, "zone_code": z.zone_code, "name": z.zone_name, "risk": z.risk_level} for z in zone_mappings],
        "recent_state_history": [
            {
                "history_id": h.history_id,
                "state": h.state,
                "transition_timestamp": h.transition_timestamp.isoformat(),
                "trigger_source": h.trigger_source,
                "notes": h.notes
            } for h in recent_history
        ]
    }
