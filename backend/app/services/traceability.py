from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    Plant, Machine, SafetyZone, MachineSafetyZone, Interlock,
    AlarmDefinition, AlarmEvent, Acknowledgement, Incident,
    CorrectiveAction, MachineStateHistory, InterlockStateHistory
)
from backend.app.schemas.schemas import (
    IncidentTimelineResponse, IncidentTimelineNode, IncidentResponse
)

class TraceabilityService:
    def __init__(self, db: Session):
        self.db = db

    def build_incident_traceability(self, incident_id: str) -> Optional[IncidentTimelineResponse]:
        incident = self.db.query(Incident).filter(Incident.incident_id == incident_id).first()
        if not incident:
            return None

        plant = self.db.query(Plant).filter(Plant.plant_id == incident.plant_id).first()
        machine = self.db.query(Machine).filter(Machine.machine_id == incident.machine_id).first()
        zone = self.db.query(SafetyZone).filter(SafetyZone.safety_zone_id == incident.safety_zone_id).first()
        
        timeline_nodes: List[IncidentTimelineNode] = []
        missing_reasons: List[str] = []
        
        # 1. Facility & Machine Commissioning / Boundary Context
        if plant and machine:
            timeline_nodes.append(IncidentTimelineNode(
                node_id=f"FAC-{plant.plant_id}",
                timestamp=incident.incident_timestamp - timedelta(hours=48),
                node_type="FACILITY_CONTEXT",
                title=f"Facility: {plant.plant_name}",
                description=f"Location: {plant.location} | Active Safety Zone: {zone.zone_name if zone else 'Unknown'}",
                status=plant.status,
                metadata={"plant_id": plant.plant_id, "machine_id": machine.machine_id}
            ))

        # 2. Machine State History (Preceding 24 hours)
        recent_msh = (
            self.db.query(MachineStateHistory)
            .filter(
                MachineStateHistory.machine_id == incident.machine_id,
                MachineStateHistory.transition_timestamp <= incident.incident_timestamp
            )
            .order_by(MachineStateHistory.transition_timestamp.desc())
            .limit(3)
            .all()
        )
        if recent_msh:
            for msh in reversed(recent_msh):
                timeline_nodes.append(IncidentTimelineNode(
                    node_id=f"MSH-{msh.history_id}",
                    timestamp=msh.transition_timestamp,
                    node_type="MACHINE_STATE",
                    title=f"Machine Transition: {msh.state}",
                    description=f"Triggered by {msh.trigger_source}. Notes: {msh.notes or 'None'}",
                    status=msh.state,
                    metadata={"history_id": msh.history_id}
                ))
        else:
            missing_reasons.append("No preceding machine state history transitions logged in window.")

        # 3. Interlock State History
        interlocks = self.db.query(Interlock).filter(Interlock.machine_id == incident.machine_id).all()
        for itl in interlocks:
            timeline_nodes.append(IncidentTimelineNode(
                node_id=f"ITL-{itl.interlock_id}",
                timestamp=incident.incident_timestamp - timedelta(minutes=10),
                node_type="INTERLOCK_STATE",
                title=f"Interlock: {itl.interlock_name} ({itl.interlock_code})",
                description=f"Current State: {itl.current_state} (Expected safe: {itl.expected_safe_state})",
                status=itl.current_state,
                metadata={"interlock_id": itl.interlock_id, "type": itl.interlock_type}
            ))

        # 4. Triggering Alarm Event
        if incident.triggering_alarm_event_id:
            alarm = self.db.query(AlarmEvent).filter(AlarmEvent.alarm_event_id == incident.triggering_alarm_event_id).first()
            if alarm:
                alarm_def = self.db.query(AlarmDefinition).filter(AlarmDefinition.alarm_definition_id == alarm.alarm_definition_id).first()
                timeline_nodes.append(IncidentTimelineNode(
                    node_id=alarm.alarm_event_id,
                    timestamp=alarm.event_timestamp,
                    node_type="ALARM",
                    title=f"Triggering Alarm: {alarm_def.alarm_name if alarm_def else alarm.alarm_event_id}",
                    description=(
                        f"Machine State: {alarm.machine_state} | Interlock: {alarm.interlock_state_snapshot} | "
                        f"Source Event: {alarm.source_event_id}"
                    ),
                    severity=alarm_def.severity if alarm_def else "HIGH",
                    status=alarm.alarm_status,
                    metadata={"alarm_event_id": alarm.alarm_event_id}
                ))
                
                # 5. Acknowledgement for triggering alarm
                acks = self.db.query(Acknowledgement).filter(Acknowledgement.alarm_event_id == alarm.alarm_event_id).all()
                if acks:
                    for ack in acks:
                        timeline_nodes.append(IncidentTimelineNode(
                            node_id=ack.acknowledgement_id,
                            timestamp=ack.acknowledgement_timestamp,
                            node_type="ACKNOWLEDGEMENT",
                            title=f"Operator Acknowledgement ({ack.acknowledgement_status})",
                            description=f"Response time: {ack.response_seconds}s via {ack.acknowledgement_channel}. Notes: {ack.notes or 'None'}",
                            status=ack.acknowledgement_status,
                            metadata={"acknowledgement_id": ack.acknowledgement_id}
                        ))
                else:
                    missing_reasons.append("Triggering alarm has no operator acknowledgement record.")
        else:
            missing_reasons.append("Incident has no linked triggering alarm event (Missing Trigger Context).")
            timeline_nodes.append(IncidentTimelineNode(
                node_id="GAP-TRIGGER-ALARM",
                timestamp=incident.incident_timestamp - timedelta(minutes=1),
                node_type="GAP_TRIGGER",
                title="Telemetry Gap: Missing Triggering Alarm",
                description="No physical alarm link found. Incident was initiated manually or via heuristic detection.",
                severity="MEDIUM",
                is_gap=True
            ))

        # 6. Incident Itself
        timeline_nodes.append(IncidentTimelineNode(
            node_id=incident.incident_id,
            timestamp=incident.incident_timestamp,
            node_type="INCIDENT",
            title=f"Incident Raised: {incident.incident_type}",
            description=incident.description,
            severity=incident.severity,
            status=incident.incident_status,
            metadata={"detection_rule_id": incident.detection_rule_id}
        ))

        # 7. Corrective Actions and Verification
        actions = self.db.query(CorrectiveAction).filter(CorrectiveAction.incident_id == incident.incident_id).all()
        if actions:
            for act in actions:
                timeline_nodes.append(IncidentTimelineNode(
                    node_id=act.corrective_action_id,
                    timestamp=act.created_at,
                    node_type="ACTION",
                    title=f"Corrective Action: {act.action_type}",
                    description=f"{act.description} (Assigned: {act.assigned_team})",
                    status=act.action_status,
                    metadata={"action_id": act.corrective_action_id}
                ))
                
                if act.completed_at:
                    timeline_nodes.append(IncidentTimelineNode(
                        node_id=f"COMP-{act.corrective_action_id}",
                        timestamp=act.completed_at,
                        node_type="ACTION_COMPLETED",
                        title=f"Action Work Completed: {act.corrective_action_id}",
                        description=f"Remediation tasks completed by {act.assigned_team}.",
                        status="COMPLETED"
                    ))
                    
                if act.verified_at:
                    timeline_nodes.append(IncidentTimelineNode(
                        node_id=f"VERIF-{act.corrective_action_id}",
                        timestamp=act.verified_at,
                        node_type="VERIFICATION",
                        title=f"Independent Verification: {act.verification_status}",
                        description=f"Audited by plant safety supervisor.",
                        status=act.verification_status
                    ))
                elif act.action_status == "CLOSED":
                    missing_reasons.append(f"Corrective action {act.corrective_action_id} closed without verification.")
                    timeline_nodes.append(IncidentTimelineNode(
                        node_id=f"GAP-VERIF-{act.corrective_action_id}",
                        timestamp=act.completed_at or act.created_at,
                        node_type="GAP_VERIFICATION",
                        title="Compliance Gap: Closed Without Verification",
                        description=f"Action {act.corrective_action_id} is marked CLOSED but lacks verified_at timestamp.",
                        severity="HIGH",
                        is_gap=True
                    ))
        else:
            missing_reasons.append("No corrective actions created for this incident.")

        # Sort nodes chronologically
        timeline_nodes.sort(key=lambda n: n.timestamp)

        inc_resp = IncidentResponse.model_validate(incident)
        if plant:
            inc_resp.plant_name = plant.plant_name
        if machine:
            inc_resp.machine_code = machine.machine_code
        if zone:
            inc_resp.zone_code = zone.zone_code
        inc_resp.corrective_actions_count = len(actions)

        return IncidentTimelineResponse(
            incident=inc_resp,
            timeline=timeline_nodes,
            traceability_complete=len(missing_reasons) == 0,
            missing_evidence_reasons=missing_reasons
        )
