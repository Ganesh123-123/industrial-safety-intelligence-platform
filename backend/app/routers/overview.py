from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from backend.app.database import get_db
from backend.app.models.entities import (
    Plant, Machine, SafetyZone, AlarmDefinition, AlarmEvent,
    Acknowledgement, Incident, CorrectiveAction
)
from backend.app.services.rules import BusinessRulesEngine
from backend.app.services.validation import DataValidationService
from backend.app.schemas.schemas import OverviewMetrics, AlarmEventResponse

router = APIRouter(prefix="", tags=["Executive Overview"])

@router.get("/overview", response_model=OverviewMetrics)
def get_overview(
    plant_id: Optional[str] = Query(None, description="Filter by plant"),
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    # Total counts
    plant_q = db.query(func.count(Plant.plant_id))
    if plant_id:
        plant_q = plant_q.filter(Plant.plant_id == plant_id)
    total_plants = plant_q.scalar() or 0

    machine_q = db.query(func.count(Machine.machine_id))
    if plant_id:
        machine_q = machine_q.filter(Machine.plant_id == plant_id)
    total_machines = machine_q.scalar() or 0

    # Base alarm query with filters
    alarm_q = db.query(AlarmEvent).join(Machine, AlarmEvent.machine_id == Machine.machine_id)
    if plant_id:
        alarm_q = alarm_q.filter(Machine.plant_id == plant_id)
    if date_from:
        alarm_q = alarm_q.filter(AlarmEvent.event_timestamp >= date_from)
    if date_to:
        alarm_q = alarm_q.filter(AlarmEvent.event_timestamp <= date_to)

    total_alarms = alarm_q.count()

    # Severity distribution
    sev_rows = (
        db.query(AlarmDefinition.severity, func.count(AlarmEvent.alarm_event_id))
        .join(AlarmEvent, AlarmDefinition.alarm_definition_id == AlarmEvent.alarm_definition_id)
        .join(Machine, AlarmEvent.machine_id == Machine.machine_id)
    )
    if plant_id:
        sev_rows = sev_rows.filter(Machine.plant_id == plant_id)
    if date_from:
        sev_rows = sev_rows.filter(AlarmEvent.event_timestamp >= date_from)
    if date_to:
        sev_rows = sev_rows.filter(AlarmEvent.event_timestamp <= date_to)
    sev_counts = dict(sev_rows.group_by(AlarmDefinition.severity).all())

    crit_high = sev_counts.get("CRITICAL", 0) + sev_counts.get("HIGH", 0)

    # Open incidents
    inc_q = db.query(Incident).filter(Incident.incident_status.in_(["OPEN", "UNDER_INVESTIGATION"]))
    if plant_id:
        inc_q = inc_q.filter(Incident.plant_id == plant_id)
    open_incidents = inc_q.count()

    # Delayed acknowledgements
    ack_q = db.query(Acknowledgement).join(AlarmEvent, Acknowledgement.alarm_event_id == AlarmEvent.alarm_event_id).join(Machine, AlarmEvent.machine_id == Machine.machine_id)
    if plant_id:
        ack_q = ack_q.filter(Machine.plant_id == plant_id)
    delayed_acks = ack_q.filter(Acknowledgement.acknowledgement_status == "DELAYED").count()

    # Unverified corrective actions
    unver_actions = db.query(CorrectiveAction).filter(
        CorrectiveAction.action_status == "CLOSED",
        or_(CorrectiveAction.verification_status != "VERIFIED", CorrectiveAction.verified_at.is_(None))
    ).count()

    # Top repeated unsafe machines
    rules_engine = BusinessRulesEngine(db)
    repeated_scores = rules_engine.calculate_repeated_condition_scores(window_hours=72)
    if plant_id:
        repeated_scores = [s for s in repeated_scores if s.plant_id == plant_id]
    repeated_clusters = sum(1 for s in repeated_scores if s.score >= 45.0)

    # Data quality exceptions
    val_service = DataValidationService(db)
    report = val_service.run_all_checks()
    data_quality_exceptions = sum(c.failure_count for c in report.checks if c.status == "FAILED")

    # Alarm trend (group by day)
    trend_rows = (
        db.query(
            func.date(AlarmEvent.event_timestamp).label("day"),
            func.count(AlarmEvent.alarm_event_id).label("cnt")
        )
        .join(Machine, AlarmEvent.machine_id == Machine.machine_id)
    )
    if plant_id:
        trend_rows = trend_rows.filter(Machine.plant_id == plant_id)
    trend_data = [{"date": str(r[0]), "count": r[1]} for r in trend_rows.group_by(func.date(AlarmEvent.event_timestamp)).order_by("day").all()]

    # Incidents by plant
    inc_plant_rows = (
        db.query(Plant.plant_name, func.count(Incident.incident_id))
        .join(Incident, Plant.plant_id == Incident.plant_id)
        .group_by(Plant.plant_name)
        .all()
    )
    incidents_by_plant = [{"plant_name": r[0], "count": r[1]} for r in inc_plant_rows]

    # Recent critical events (last 10)
    crit_events = (
        db.query(AlarmEvent, AlarmDefinition, Machine)
        .join(AlarmDefinition, AlarmEvent.alarm_definition_id == AlarmDefinition.alarm_definition_id)
        .join(Machine, AlarmEvent.machine_id == Machine.machine_id)
        .filter(AlarmDefinition.severity == "CRITICAL")
        .order_by(AlarmEvent.event_timestamp.desc())
        .limit(10)
        .all()
    )
    recent_critical: List[AlarmEventResponse] = []
    for ev, ad, mch in crit_events:
        item = AlarmEventResponse.model_validate(ev)
        item.severity = ad.severity
        item.alarm_name = ad.alarm_name
        item.plant_id = mch.plant_id
        recent_critical.append(item)

    return OverviewMetrics(
        total_plants=total_plants,
        total_machines=total_machines,
        total_alarms=total_alarms,
        critical_and_high_alarms=crit_high,
        open_incidents=open_incidents,
        delayed_acknowledgements=delayed_acks,
        repeated_unsafe_clusters=repeated_clusters,
        unverified_actions=unver_actions,
        data_quality_exceptions=data_quality_exceptions,
        alarms_by_severity=sev_counts,
        alarms_trend=trend_data,
        incidents_by_plant=incidents_by_plant,
        top_unsafe_machines=repeated_scores[:5],
        recent_critical_events=recent_critical
    )
