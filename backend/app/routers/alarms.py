from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from backend.app.database import get_db
from backend.app.models.entities import (
    AlarmEvent, AlarmDefinition, Machine, Plant, Acknowledgement, SafetyZone
)
from backend.app.schemas.schemas import (
    AlarmEventResponse, PaginatedResponse, AcknowledgementResponse, AlarmDefinitionResponse
)

router = APIRouter(prefix="/alarms", tags=["Alarm Explorer"])

@router.get("", response_model=PaginatedResponse[AlarmEventResponse])
def get_alarms(
    plant_id: Optional[str] = Query(None, description="Filter by plant"),
    machine_id: Optional[str] = Query(None, description="Filter by machine"),
    safety_zone_id: Optional[str] = Query(None, description="Filter by safety zone"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    alarm_status: Optional[str] = Query(None, description="Filter by alarm status"),
    anomaly_only: Optional[bool] = Query(False, description="Filter only records with anomaly flags"),
    date_from: Optional[datetime] = Query(None, description="Start timestamp"),
    date_to: Optional[datetime] = Query(None, description="End timestamp"),
    sort_by: Optional[str] = Query("event_timestamp", description="Sort field"),
    order: Optional[str] = Query("desc", description="Sort direction (asc/desc)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = (
        db.query(AlarmEvent, AlarmDefinition, Machine)
        .join(AlarmDefinition, AlarmEvent.alarm_definition_id == AlarmDefinition.alarm_definition_id)
        .join(Machine, AlarmEvent.machine_id == Machine.machine_id)
    )

    if plant_id:
        query = query.filter(Machine.plant_id == plant_id)
    if machine_id:
        query = query.filter(AlarmEvent.machine_id == machine_id)
    if safety_zone_id:
        query = query.filter(AlarmEvent.safety_zone_id == safety_zone_id)
    if severity:
        query = query.filter(AlarmDefinition.severity == severity)
    if alarm_status:
        query = query.filter(AlarmEvent.alarm_status == alarm_status)
    if anomaly_only:
        query = query.filter(
            (AlarmEvent.issue_type.isnot(None)) | 
            (AlarmEvent.replay_reference.isnot(None)) |
            ((AlarmEvent.machine_state == "RUNNING") & (AlarmEvent.interlock_state_snapshot.in_(["TRIPPED", "OPEN"])))
        )
    if date_from:
        query = query.filter(AlarmEvent.event_timestamp >= date_from)
    if date_to:
        query = query.filter(AlarmEvent.event_timestamp <= date_to)

    # Sorting
    sort_col = getattr(AlarmEvent, sort_by, AlarmEvent.event_timestamp)
    query = query.order_by(desc(sort_col) if order == "desc" else asc(sort_col))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items: List[AlarmEventResponse] = []
    # Fetch acknowledgements for these events
    event_ids = [e.alarm_event_id for e, _, _ in records]
    acks = db.query(Acknowledgement).filter(Acknowledgement.alarm_event_id.in_(event_ids)).all()
    ack_map = {a.alarm_event_id: AcknowledgementResponse.model_validate(a) for a in acks}

    for ev, ad, mch in records:
        resp = AlarmEventResponse.model_validate(ev)
        resp.severity = ad.severity
        resp.alarm_name = ad.alarm_name
        resp.plant_id = mch.plant_id
        resp.acknowledgement = ack_map.get(ev.alarm_event_id)
        items.append(resp)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{alarm_event_id}")
def get_alarm_detail(alarm_event_id: str, db: Session = Depends(get_db)):
    event = db.query(AlarmEvent).filter(AlarmEvent.alarm_event_id == alarm_event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Alarm event {alarm_event_id} not found")

    alarm_def = db.query(AlarmDefinition).filter(AlarmDefinition.alarm_definition_id == event.alarm_definition_id).first()
    machine = db.query(Machine).filter(Machine.machine_id == event.machine_id).first()
    zone = db.query(SafetyZone).filter(SafetyZone.safety_zone_id == event.safety_zone_id).first() if event.safety_zone_id else None
    acknowledgements = db.query(Acknowledgement).filter(Acknowledgement.alarm_event_id == alarm_event_id).all()

    resp = AlarmEventResponse.model_validate(event)
    if alarm_def:
        resp.severity = alarm_def.severity
        resp.alarm_name = alarm_def.alarm_name
    if machine:
        resp.plant_id = machine.plant_id

    return {
        "alarm_event": resp,
        "definition": AlarmDefinitionResponse.model_validate(alarm_def) if alarm_def else None,
        "machine_code": machine.machine_code if machine else None,
        "machine_name": machine.machine_name if machine else None,
        "zone_name": zone.zone_name if zone else None,
        "acknowledgements": [AcknowledgementResponse.model_validate(a) for a in acknowledgements]
    }
