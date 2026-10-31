from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from backend.app.models.entities import (
    Plant, Machine, Interlock, AlarmDefinition, AlarmEvent,
    Acknowledgement, Incident, CorrectiveAction, MachineStateHistory,
    InterlockStateHistory
)
from backend.app.schemas.schemas import AnomalyItem, RepeatedConditionScore

class BusinessRulesEngine:
    def __init__(self, db: Session):
        self.db = db

    # --------------------------------------------------------------------------
    # RULE 1: Repeated Unsafe Conditions
    # --------------------------------------------------------------------------
    def calculate_repeated_condition_scores(self, window_hours: int = 72) -> List[RepeatedConditionScore]:
        """
        Computes explainable repeated-condition scores across machines for a sliding window.
        Score formula:
        S = min(100, N_crit*25 + N_high*15 + N_med*5 + N_viol*20 + D_avg_sla*0.1)
        """
        # Determine latest event time in DB as window reference
        max_time_query = self.db.query(func.max(AlarmEvent.event_timestamp)).scalar()
        if not max_time_query:
            return []
        
        window_start = max_time_query - timedelta(hours=window_hours)
        
        machines = self.db.query(Machine).all()
        scores = []
        
        for m in machines:
            events = (
                self.db.query(AlarmEvent, AlarmDefinition)
                .join(AlarmDefinition, AlarmEvent.alarm_definition_id == AlarmDefinition.alarm_definition_id)
                .filter(
                    AlarmEvent.machine_id == m.machine_id,
                    AlarmEvent.event_timestamp >= window_start
                )
                .all()
            )
            
            n_crit = sum(1 for e, d in events if d.severity == "CRITICAL")
            n_high = sum(1 for e, d in events if d.severity == "HIGH")
            n_med = sum(1 for e, d in events if d.severity == "MEDIUM")
            
            # Interlock violations (impossible or tripped states during running)
            n_viol = sum(1 for e, d in events if e.machine_state == "RUNNING" and e.interlock_state_snapshot in ["TRIPPED", "OPEN"])
            
            # SLA delay
            ack_delays = (
                self.db.query(Acknowledgement.response_seconds, AlarmDefinition.acknowledgement_sla_seconds)
                .join(AlarmEvent, Acknowledgement.alarm_event_id == AlarmEvent.alarm_event_id)
                .join(AlarmDefinition, AlarmEvent.alarm_definition_id == AlarmDefinition.alarm_definition_id)
                .filter(
                    AlarmEvent.machine_id == m.machine_id,
                    AlarmEvent.event_timestamp >= window_start,
                    Acknowledgement.acknowledgement_status == "DELAYED"
                )
                .all()
            )
            
            sla_overage_total = sum(max(0, resp - sla) for resp, sla in ack_delays)
            avg_delay = (sla_overage_total / len(ack_delays)) if ack_delays else 0.0
            
            score_val = min(100.0, (n_crit * 25.0) + (n_high * 15.0) + (n_med * 5.0) + (n_viol * 20.0) + (min(100.0, avg_delay) * 0.1))
            
            if score_val >= 75.0:
                level = "CRITICAL"
            elif score_val >= 45.0:
                level = "HIGH"
            elif score_val >= 20.0:
                level = "MEDIUM"
            else:
                level = "LOW"
                
            explanation = (
                f"Machine {m.machine_code} computed score {score_val:.1f}/100. "
                f"Factors in last {window_hours}h: {n_crit} critical alarms, {n_high} high alarms, "
                f"{n_viol} interlock violations, avg SLA overage {avg_delay:.1f}s."
            )
            
            scores.append(RepeatedConditionScore(
                machine_id=m.machine_id,
                plant_id=m.plant_id,
                machine_code=m.machine_code,
                score=round(score_val, 1),
                level=level,
                critical_alarms_count=n_crit,
                high_alarms_count=n_high,
                interlock_violations_count=n_viol,
                avg_acknowledgement_delay_seconds=round(avg_delay, 1),
                explanation=explanation
            ))
            
        scores.sort(key=lambda s: s.score, reverse=True)
        return scores

    # --------------------------------------------------------------------------
    # RULE 2: Severity Prioritization
    # --------------------------------------------------------------------------
    def calculate_alarm_priority(self, alarm_event: AlarmEvent, definition: AlarmDefinition) -> Dict[str, Any]:
        """Calculates multi-factor triage priority score."""
        base_weights = {"CRITICAL": 1000, "HIGH": 500, "MEDIUM": 200, "LOW": 50, "INFO": 10}
        base = base_weights.get(definition.severity, 50)
        
        state_bonus = 300 if alarm_event.machine_state in ["EMERGENCY_STOP", "FAULT"] else 0
        interlock_bonus = 400 if alarm_event.interlock_state_snapshot in ["TRIPPED", "OPEN"] else 0
        
        total = base + state_bonus + interlock_bonus
        return {
            "priority_score": total,
            "base_severity": definition.severity,
            "state_bonus": state_bonus,
            "interlock_bonus": interlock_bonus,
            "triage_urgency": "IMMEDIATE" if total >= 900 else ("ELEVATED" if total >= 500 else "ROUTINE")
        }

    # --------------------------------------------------------------------------
    # RULE 3: Delayed & Pre-Alarm Acknowledgements
    # --------------------------------------------------------------------------
    def detect_acknowledgement_anomalies(self) -> List[AnomalyItem]:
        """Detects negative response times and extreme delayed acknowledgements."""
        anomalies = []
        
        # 1. Pre-alarm acknowledgements: response_seconds < 0
        pre_alarm_acks = (
            self.db.query(Acknowledgement, AlarmEvent)
            .join(AlarmEvent, Acknowledgement.alarm_event_id == AlarmEvent.alarm_event_id)
            .filter(Acknowledgement.response_seconds < 0)
            .all()
        )
        
        for ack, event in pre_alarm_acks:
            anomalies.append(AnomalyItem(
                anomaly_id=f"ANOM-ACK-NEG-{ack.acknowledgement_id}",
                anomaly_type="ACKNOWLEDGEMENT_BEFORE_ALARM",
                entity_type="acknowledgements",
                entity_id=ack.acknowledgement_id,
                severity="HIGH",
                detected_at=datetime.utcnow(),
                rule_id="RULE-003",
                explanation=(
                    f"Acknowledgement {ack.acknowledgement_id} recorded at {ack.acknowledgement_timestamp.isoformat()} "
                    f"strictly precedes corresponding alarm event {event.alarm_event_id} at {event.event_timestamp.isoformat()} "
                    f"(response delta: {ack.response_seconds}s)."
                ),
                evidence={
                    "response_seconds": ack.response_seconds,
                    "alarm_event_id": event.alarm_event_id,
                    "event_timestamp": event.event_timestamp.isoformat(),
                    "acknowledgement_timestamp": ack.acknowledgement_timestamp.isoformat()
                },
                related_records=[ack.acknowledgement_id, event.alarm_event_id, event.machine_id],
                advisory_recommendation="Inspect NTP time-synchronization on operator HMI terminals and message bus timestamps."
            ))
            
        return anomalies

    # --------------------------------------------------------------------------
    # RULE 4: Alarm Flood and Duplicate Replay Detection
    # --------------------------------------------------------------------------
    def detect_alarm_floods_and_replays(self) -> List[AnomalyItem]:
        anomalies = []
        
        # 1. Duplicate replay detection
        replayed_events = (
            self.db.query(AlarmEvent)
            .filter(
                or_(
                    AlarmEvent.replay_reference.isnot(None),
                    AlarmEvent.alarm_status == "REPLAYED"
                )
            )
            .all()
        )
        
        for ev in replayed_events:
            anomalies.append(AnomalyItem(
                anomaly_id=f"ANOM-REPLAY-{ev.alarm_event_id}",
                anomaly_type="DUPLICATE_ALARM_REPLAY",
                entity_type="alarm_events",
                entity_id=ev.alarm_event_id,
                severity="LOW",
                detected_at=datetime.utcnow(),
                rule_id="RULE-004",
                explanation=(
                    f"Alarm event {ev.alarm_event_id} is an exact telemetry duplicate/replay of original "
                    f"source event '{ev.source_event_id}' (replay_reference: {ev.replay_reference})."
                ),
                evidence={
                    "source_event_id": ev.source_event_id,
                    "replay_reference": ev.replay_reference,
                    "machine_id": ev.machine_id,
                    "event_timestamp": ev.event_timestamp.isoformat()
                },
                related_records=[ev.alarm_event_id, ev.replay_reference or ""] if ev.replay_reference else [ev.alarm_event_id],
                advisory_recommendation="Check edge MQTT deduplication cache and PLC broker retry timeouts to prevent packet loops."
            ))
            
        return anomalies

    def detect_alarm_floods(self, threshold_count: int = 10, window_minutes: int = 10) -> List[AnomalyItem]:
        """
        Detects alarm flood episodes per ISA-18.2 / IEC 62682 (>= 10 alarms in 10 minutes on a machine).
        """
        anomalies = []
        machines = self.db.query(Machine.machine_id).all()
        for (m_id,) in machines:
            events = (
                self.db.query(AlarmEvent.alarm_event_id, AlarmEvent.event_timestamp)
                .filter(AlarmEvent.machine_id == m_id)
                .order_by(AlarmEvent.event_timestamp)
                .all()
            )
            left = 0
            reported_windows = set()
            for right in range(len(events)):
                while (events[right][1] - events[left][1]).total_seconds() > window_minutes * 60:
                    left += 1
                cnt = right - left + 1
                if cnt >= threshold_count:
                    flood_hour = events[left][1].strftime("%Y%m%d%H")
                    if flood_hour not in reported_windows:
                        reported_windows.add(flood_hour)
                        anomalies.append(AnomalyItem(
                            anomaly_id=f"ANOM-FLOOD-{m_id}-{flood_hour}",
                            anomaly_type="ALARM_FLOOD",
                            entity_type="machines",
                            entity_id=m_id,
                            severity="HIGH",
                            detected_at=datetime.utcnow(),
                            rule_id="RULE-004",
                            explanation=(
                                f"Machine {m_id} experienced an alarm flood burst ({cnt} alarms in "
                                f"{window_minutes}m) starting at {events[left][1].isoformat()}."
                            ),
                            evidence={
                                "machine_id": m_id,
                                "alarm_count": cnt,
                                "window_start": events[left][1].isoformat(),
                                "window_end": events[right][1].isoformat()
                            },
                            related_records=[e[0] for e in events[left:right+1][:5]],
                            advisory_recommendation="Implement alarm suppression/shelving during process upsets per ISA-18.2."
                        ))
        return anomalies

    # --------------------------------------------------------------------------
    # RULE 5: Nuisance Alarm Clusters
    # --------------------------------------------------------------------------
    def detect_nuisance_alarm_clusters(self, threshold_count: int = 5, window_minutes: int = 30) -> List[AnomalyItem]:
        anomalies = []
        # Query alarms grouped by machine and definition where count is high in short span
        results = (
            self.db.query(
                AlarmEvent.machine_id,
                AlarmEvent.alarm_definition_id,
                func.count(AlarmEvent.alarm_event_id).label("cnt")
            )
            .group_by(AlarmEvent.machine_id, AlarmEvent.alarm_definition_id)
            .having(func.count(AlarmEvent.alarm_event_id) >= threshold_count * 3)  # high density indicator
            .limit(10)
            .all()
        )
        
        for m_id, def_id, count in results:
            anomalies.append(AnomalyItem(
                anomaly_id=f"ANOM-NUIS-{m_id}-{def_id}",
                anomaly_type="NUISANCE_ALARM_CLUSTER",
                entity_type="machines",
                entity_id=m_id,
                severity="LOW",
                detected_at=datetime.utcnow(),
                rule_id="RULE-005",
                explanation=(
                    f"Machine {m_id} experienced high-frequency repetitive chatter for alarm definition "
                    f"{def_id} ({count} events). Condition clears without physical trip."
                ),
                evidence={
                    "machine_id": m_id,
                    "alarm_definition_id": def_id,
                    "total_occurrences": count
                },
                related_records=[m_id, def_id],
                advisory_recommendation="Adjust sensor deadband or alarm debounce timer in PLC ladder logic."
            ))
        return anomalies

    # --------------------------------------------------------------------------
    # RULE 6: Impossible Interlock States
    # --------------------------------------------------------------------------
    def detect_impossible_interlock_states(self) -> List[AnomalyItem]:
        anomalies = []
        
        # Machine state is RUNNING, but interlock is TRIPPED or OPEN
        invalid_events = (
            self.db.query(AlarmEvent)
            .filter(
                AlarmEvent.machine_state == "RUNNING",
                AlarmEvent.interlock_state_snapshot.in_(["TRIPPED", "OPEN"])
            )
            .all()
        )
        
        for ev in invalid_events:
            anomalies.append(AnomalyItem(
                anomaly_id=f"ANOM-ITL-IMP-{ev.alarm_event_id}",
                anomaly_type="IMPOSSIBLE_INTERLOCK_STATE",
                entity_type="alarm_events",
                entity_id=ev.alarm_event_id,
                severity="CRITICAL",
                detected_at=datetime.utcnow(),
                rule_id="RULE-006",
                explanation=(
                    f"Hazardous physical contradiction: Machine {ev.machine_id} is recorded in RUNNING state "
                    f"while physical safety interlock reports snapshot state '{ev.interlock_state_snapshot}'. "
                    f"Guard perimeter breached during live operation."
                ),
                evidence={
                    "machine_id": ev.machine_id,
                    "machine_state": ev.machine_state,
                    "interlock_state_snapshot": ev.interlock_state_snapshot,
                    "event_timestamp": ev.event_timestamp.isoformat()
                },
                related_records=[ev.alarm_event_id, ev.machine_id],
                advisory_recommendation="Immediate mechanical safety inspection of guard door limit switches, light curtain alignment, and safety relay contacts."
            ))
            
        return anomalies

    # --------------------------------------------------------------------------
    # RULE 7: Incident Context Validation
    # --------------------------------------------------------------------------
    def detect_incident_context_anomalies(self) -> List[AnomalyItem]:
        anomalies = []
        
        # Incidents with missing triggering alarms
        missing_context_incidents = (
            self.db.query(Incident)
            .filter(Incident.triggering_alarm_event_id.is_(None))
            .all()
        )
        
        for inc in missing_context_incidents:
            anomalies.append(AnomalyItem(
                anomaly_id=f"ANOM-INC-MISS-{inc.incident_id}",
                anomaly_type="INCIDENT_MISSING_TRIGGER_CONTEXT",
                entity_type="incidents",
                entity_id=inc.incident_id,
                severity="MEDIUM",
                detected_at=datetime.utcnow(),
                rule_id="RULE-007",
                explanation=(
                    f"Incident {inc.incident_id} ({inc.incident_type}) lacks an authenticated triggering alarm event "
                    f"and does not have matching anomalous telemetry recorded within the incident timeframe."
                ),
                evidence={
                    "incident_id": inc.incident_id,
                    "machine_id": inc.machine_id,
                    "plant_id": inc.plant_id,
                    "incident_timestamp": inc.incident_timestamp.isoformat(),
                    "triggering_alarm_event_id": None
                },
                related_records=[inc.incident_id, inc.machine_id],
                advisory_recommendation="Contact shift safety officer to append manual log evidence or verify edge logger buffer retention during incident window."
            ))
            
        return anomalies

    # --------------------------------------------------------------------------
    # RULE 8: Corrective-Action Verification Lifecycle
    # --------------------------------------------------------------------------
    def detect_unverified_closed_actions(self) -> List[AnomalyItem]:
        anomalies = []
        
        # Action is CLOSED but verification_status != 'VERIFIED' or verified_at is NULL
        unverified_actions = (
            self.db.query(CorrectiveAction)
            .filter(
                CorrectiveAction.action_status == "CLOSED",
                or_(
                    CorrectiveAction.verification_status != "VERIFIED",
                    CorrectiveAction.verified_at.is_(None)
                )
            )
            .all()
        )
        
        for act in unverified_actions:
            anomalies.append(AnomalyItem(
                anomaly_id=f"ANOM-ACT-UNVER-{act.corrective_action_id}",
                anomaly_type="ACTION_CLOSED_WITHOUT_VERIFICATION",
                entity_type="corrective_actions",
                entity_id=act.corrective_action_id,
                severity="HIGH",
                detected_at=datetime.utcnow(),
                rule_id="RULE-008",
                explanation=(
                    f"Corrective action {act.corrective_action_id} for incident {act.incident_id} is marked CLOSED "
                    f"without mandatory safety verification (current verification_status: '{act.verification_status}', "
                    f"verified_at: {act.verified_at})."
                ),
                evidence={
                    "corrective_action_id": act.corrective_action_id,
                    "incident_id": act.incident_id,
                    "action_status": act.action_status,
                    "verification_status": act.verification_status,
                    "verified_at": act.verified_at.isoformat() if act.verified_at else None
                },
                related_records=[act.corrective_action_id, act.incident_id],
                advisory_recommendation="Reopen corrective action immediately and assign to certified safety auditor for on-site sign-off."
            ))
            
        return anomalies

    # --------------------------------------------------------------------------
    # UNIFIED DETECTION PIPELINE
    # --------------------------------------------------------------------------
    def detect_all(self) -> List[AnomalyItem]:
        """Runs all detection rules and aggregates detected anomalies."""
        all_anomalies: List[AnomalyItem] = []
        
        all_anomalies.extend(self.detect_acknowledgement_anomalies())
        all_anomalies.extend(self.detect_impossible_interlock_states())
        all_anomalies.extend(self.detect_incident_context_anomalies())
        all_anomalies.extend(self.detect_alarm_floods_and_replays())
        all_anomalies.extend(self.detect_alarm_floods())
        all_anomalies.extend(self.detect_unverified_closed_actions())
        all_anomalies.extend(self.detect_nuisance_alarm_clusters())
        
        # Sort by severity priority: CRITICAL -> HIGH -> MEDIUM -> LOW
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        all_anomalies.sort(key=lambda a: (sev_order.get(a.severity, 99), a.anomaly_id))
        
        return all_anomalies
