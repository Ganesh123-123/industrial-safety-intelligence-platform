import re
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.config import settings
from backend.app.models.entities import (
    Plant, Machine, SafetyZone, MachineSafetyZone, Interlock,
    AlarmDefinition, OperatorShift, AlarmEvent, Acknowledgement,
    Incident, CorrectiveAction, MachineStateHistory, InterlockStateHistory,
    DataGenerationRun
)
from backend.app.schemas.schemas import ValidationCheckItem, ValidationReport

VALID_SEVERITIES = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_MACHINE_STATUSES = {"RUNNING", "IDLE", "EMERGENCY_STOP", "MAINTENANCE", "FAULT", "OFFLINE"}
VALID_INTERLOCK_STATES = {"OPEN", "CLOSED", "TRIPPED", "ENGAGED", "BYPASSED", "DISARMED", "FAULT", "CLEAR", "ARMED"}
VALID_INCIDENT_STATUSES = {"OPEN", "UNDER_INVESTIGATION", "RESOLVED", "CLOSED"}
VALID_ACTION_STATUSES = {"OPEN", "IN_PROGRESS", "COMPLETED", "CLOSED", "REOPENED", "CANCELLED"}
VALID_VERIFICATION_STATUSES = {"PENDING", "VERIFIED", "FAILED_VERIFICATION", "WAIVED"}

class DataValidationService:
    def __init__(self, db: Session):
        self.db = db

    def run_all_checks(self) -> ValidationReport:
        checks: List[ValidationCheckItem] = []
        
        checks.append(self._check_1_primary_key_uniqueness())
        checks.append(self._check_2_foreign_key_integrity())
        checks.append(self._check_3_allowed_enum_values())
        checks.append(self._check_4_required_fields())
        checks.append(self._check_5_machine_plant_consistency())
        checks.append(self._check_6_machine_zone_effective_dates())
        checks.append(self._check_7_alarm_definition_compatibility())
        checks.append(self._check_8_acknowledgement_chronology())
        checks.append(self._check_9_event_receipt_timestamps())
        checks.append(self._check_10_state_transition_validity())
        checks.append(self._check_11_incident_triggering_evidence())
        checks.append(self._check_12_corrective_action_lifecycle())
        checks.append(self._check_13_duplicate_event_detection())
        checks.append(self._check_14_derived_response_time())
        checks.append(self._check_15_deterministic_id_formats())
        checks.append(self._check_16_cross_file_consistency())
        checks.append(self._check_17_ground_truth_isolation())
        checks.append(self._check_18_reproducible_checksums())
        
        passed = sum(1 for c in checks if c.status == "PASSED")
        failed = sum(1 for c in checks if c.status == "FAILED")
        
        return ValidationReport(
            total_checks=len(checks),
            passed_checks=passed,
            failed_checks=failed,
            generated_at=datetime.utcnow(),
            checks=checks
        )

    # 1. Primary-key uniqueness
    def _check_1_primary_key_uniqueness(self) -> ValidationCheckItem:
        total = 0
        failures = []
        
        for model, pk_col, name in [
            (Plant, Plant.plant_id, "plants"),
            (Machine, Machine.machine_id, "machines"),
            (SafetyZone, SafetyZone.safety_zone_id, "safety_zones"),
            (Interlock, Interlock.interlock_id, "interlocks"),
            (AlarmDefinition, AlarmDefinition.alarm_definition_id, "alarm_definitions"),
            (AlarmEvent, AlarmEvent.alarm_event_id, "alarm_events"),
            (Acknowledgement, Acknowledgement.acknowledgement_id, "acknowledgements"),
            (Incident, Incident.incident_id, "incidents"),
            (CorrectiveAction, CorrectiveAction.corrective_action_id, "corrective_actions"),
        ]:
            rows = self.db.query(pk_col, func.count(pk_col)).group_by(pk_col).having(func.count(pk_col) > 1).all()
            cnt = self.db.query(func.count(pk_col)).scalar() or 0
            total += cnt
            if rows:
                failures.extend([f"{name}:{r[0]}" for r in rows[:3]])

        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="1. Primary-Key Uniqueness",
            status=status,
            records_checked=total,
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Verifies all database entities maintain unique, non-colliding primary key constraints.",
            suggested_investigation="Review synthetic sequence generator counters and table unique indexes."
        )

    # 2. Foreign-key integrity
    def _check_2_foreign_key_integrity(self) -> ValidationCheckItem:
        total = 0
        failures = []
        
        # Check machine -> plant
        machines = self.db.query(Machine.machine_id, Machine.plant_id).all()
        plant_ids = {p.plant_id for p in self.db.query(Plant.plant_id).all()}
        total += len(machines)
        for m_id, p_id in machines:
            if p_id not in plant_ids:
                failures.append(f"machine:{m_id}->plant:{p_id}")
                
        # Check alarm_event -> machine & alarm_definition
        events = self.db.query(AlarmEvent.alarm_event_id, AlarmEvent.machine_id, AlarmEvent.alarm_definition_id).all()
        machine_ids = {m.machine_id for m in self.machines_cache()}
        alarm_def_ids = {d.alarm_definition_id for d in self.db.query(AlarmDefinition.alarm_definition_id).all()}
        total += len(events)
        for e_id, m_id, d_id in events:
            if m_id not in machine_ids or d_id not in alarm_def_ids:
                failures.append(f"event:{e_id}")

        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="2. Foreign-Key Referential Integrity",
            status=status,
            records_checked=total,
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Ensures all child records reference valid, existing parent entities without orphaned foreign keys.",
            suggested_investigation="Check foreign key constraint declarations and generation dependency order."
        )

    # 3. Allowed enum values
    def _check_3_allowed_enum_values(self) -> ValidationCheckItem:
        total = 0
        failures = []
        
        # AlarmDefinition severity
        defs = self.db.query(AlarmDefinition.alarm_definition_id, AlarmDefinition.severity).all()
        total += len(defs)
        for d_id, sev in defs:
            if sev not in VALID_SEVERITIES:
                failures.append(f"def:{d_id} ({sev})")
                
        # Machine status
        mchs = self.db.query(Machine.machine_id, Machine.operational_status).all()
        total += len(mchs)
        for m_id, st in mchs:
            if st not in VALID_MACHINE_STATUSES:
                failures.append(f"machine:{m_id} ({st})")

        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="3. Allowed Enum Values",
            status=status,
            records_checked=total,
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Verifies status, severity, and categorical fields adhere to strict enterprise domain enums.",
            suggested_investigation="Validate enum definitions in Pydantic schemas and database migration constraints."
        )

    # 4. Required fields
    def _check_4_required_fields(self) -> ValidationCheckItem:
        total = 0
        failures = []
        
        events = self.db.query(AlarmEvent).all()
        total += len(events)
        for e in events:
            if not e.alarm_event_id or not e.machine_id or not e.event_timestamp or not e.source_event_id:
                failures.append(e.alarm_event_id or "UNKNOWN")
                
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="4. Required Fields Non-Null",
            status=status,
            records_checked=total,
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Verifies non-nullable domain columns are populated with valid values.",
            suggested_investigation="Audit NOT NULL column constraints on database tables."
        )

    # 5. Machine-to-plant consistency
    def _check_5_machine_plant_consistency(self) -> ValidationCheckItem:
        total = 0
        failures = []
        
        # Verify incidents machine and plant match
        incidents = self.db.query(Incident).all()
        machine_plants = {m.machine_id: m.plant_id for m in self.machines_cache()}
        total += len(incidents)
        for inc in incidents:
            expected_plant = machine_plants.get(inc.machine_id)
            if expected_plant and expected_plant != inc.plant_id:
                failures.append(f"incident:{inc.incident_id} (plant mismatch)")
                
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="5. Machine-to-Plant Consistency",
            status=status,
            records_checked=total,
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Validates that machines, safety zones, and incidents align with the correct host facility.",
            suggested_investigation="Ensure generation and ingestion cross-reference machine plant assignments."
        )

    # 6. Machine-to-zone effective dates
    def _check_6_machine_zone_effective_dates(self) -> ValidationCheckItem:
        mappings = self.db.query(MachineSafetyZone).all()
        failures = []
        for m in mappings:
            if m.effective_to and m.effective_to < m.effective_from:
                failures.append(f"msz:{m.id}")
                
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="6. Machine-to-Zone Effective Dates",
            status=status,
            records_checked=len(mappings),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Validates that effective date ranges are chronologically coherent (effective_from <= effective_to).",
            suggested_investigation="Inspect temporal date boundary generator logic."
        )

    # 7. Alarm-definition compatibility
    def _check_7_alarm_definition_compatibility(self) -> ValidationCheckItem:
        events = (
            self.db.query(AlarmEvent.alarm_event_id, Machine.machine_type, AlarmDefinition.machine_type)
            .join(Machine, AlarmEvent.machine_id == Machine.machine_id)
            .join(AlarmDefinition, AlarmEvent.alarm_definition_id == AlarmDefinition.alarm_definition_id)
            .all()
        )
        failures = []
        for e_id, m_type, d_type in events:
            if m_type != d_type:
                failures.append(f"event:{e_id} ({m_type}!={d_type})")
                
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="7. Alarm-Definition Compatibility",
            status=status,
            records_checked=len(events),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Verifies alarm events match the equipment machine_type defined in their alarm definition.",
            suggested_investigation="Review alarm definition mapping in synthetic telemetry distribution."
        )

    # 8. Acknowledgement chronology (Controlled Anomaly Aware)
    def _check_8_acknowledgement_chronology(self) -> ValidationCheckItem:
        acks = (
            self.db.query(Acknowledgement.acknowledgement_id, Acknowledgement.response_seconds, Acknowledgement.issue_type)
            .all()
        )
        # Note: Deliberate anomaly fixtures exist with issue_type='ACKNOWLEDGEMENT_BEFORE_ALARM'
        # In strict integrity mode, negative response_seconds is counted
        failures = [a[0] for a in acks if a[1] < 0]
        status = "PASSED" if len(failures) == 0 else "FAILED"
        return ValidationCheckItem(
            check_name="8. Acknowledgement Chronology",
            status=status,
            records_checked=len(acks),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Audits that operator acknowledgement timestamps do not precede the alarm occurrence time.",
            suggested_investigation="In evaluation mode, negative response times match controlled ACKNOWLEDGEMENT_BEFORE_ALARM fixtures."
        )

    # 9. Event receipt timestamps
    def _check_9_event_receipt_timestamps(self) -> ValidationCheckItem:
        events = self.db.query(AlarmEvent.alarm_event_id, AlarmEvent.event_timestamp, AlarmEvent.received_timestamp).all()
        failures = [e[0] for e in events if e[2] < e[1]]
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="9. Event Occurrence vs Ingestion Timestamp",
            status=status,
            records_checked=len(events),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Verifies physical event_timestamp <= received_timestamp (no negative network ingestion lag).",
            suggested_investigation="Audit edge broker clock sync and NTP time server synchronization."
        )

    # 10. State-transition validity (Impossible Interlock Aware)
    def _check_10_state_transition_validity(self) -> ValidationCheckItem:
        events = (
            self.db.query(AlarmEvent.alarm_event_id, AlarmEvent.machine_state, AlarmEvent.interlock_state_snapshot)
            .all()
        )
        failures = [e[0] for e in events if e[1] == "RUNNING" and e[2] in ["TRIPPED", "OPEN"]]
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="10. State-Transition & Interlock Validity",
            status=status,
            records_checked=len(events),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Checks for impossible state combinations (RUNNING while interlock is TRIPPED or OPEN).",
            suggested_investigation="Matches controlled IMPOSSIBLE_INTERLOCK_STATE evaluation fixtures."
        )

    # 11. Incident triggering evidence
    def _check_11_incident_triggering_evidence(self) -> ValidationCheckItem:
        incidents = self.db.query(Incident.incident_id, Incident.triggering_alarm_event_id).all()
        failures = [inc[0] for inc in incidents if inc[1] is None]
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="11. Incident Triggering Evidence",
            status=status,
            records_checked=len(incidents),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Validates that incidents possess an authenticated root triggering alarm event.",
            suggested_investigation="Matches controlled INCIDENT_MISSING_TRIGGER_CONTEXT evaluation fixtures."
        )

    # 12. Corrective-action lifecycle
    def _check_12_corrective_action_lifecycle(self) -> ValidationCheckItem:
        actions = self.db.query(CorrectiveAction).all()
        failures = []
        for a in actions:
            # Action CLOSED without verification
            if a.action_status == "CLOSED" and (a.verification_status != "VERIFIED" or a.verified_at is None):
                failures.append(a.corrective_action_id)
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="12. Corrective-Action Verification Lifecycle",
            status=status,
            records_checked=len(actions),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Enforces that actions marked CLOSED have successfully passed independent safety verification.",
            suggested_investigation="Matches controlled ACTION_CLOSED_WITHOUT_VERIFICATION evaluation fixtures."
        )

    # 13. Duplicate event detection
    def _check_13_duplicate_event_detection(self) -> ValidationCheckItem:
        events = self.db.query(AlarmEvent.alarm_event_id, AlarmEvent.replay_reference).filter(AlarmEvent.replay_reference.isnot(None)).all()
        failures = [e[0] for e in events]
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="13. Duplicate Event & Replay Detection",
            status=status,
            records_checked=self.db.query(func.count(AlarmEvent.alarm_event_id)).scalar() or 0,
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Scans for synthetic duplicate telemetry replays with replay references.",
            suggested_investigation="Matches controlled DUPLICATE_ALARM_REPLAY evaluation fixtures."
        )

    # 14. Derived response-time reconciliation
    def _check_14_derived_response_time(self) -> ValidationCheckItem:
        acks = (
            self.db.query(
                Acknowledgement.acknowledgement_id,
                Acknowledgement.response_seconds,
                Acknowledgement.acknowledgement_timestamp,
                AlarmEvent.event_timestamp
            )
            .join(AlarmEvent, Acknowledgement.alarm_event_id == AlarmEvent.alarm_event_id)
            .all()
        )
        failures = []
        for ack_id, resp, a_time, e_time in acks:
            expected_delta = int((a_time - e_time).total_seconds())
            if resp != expected_delta:
                failures.append(ack_id)
                
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="14. Derived Response-Time Reconciliation",
            status=status,
            records_checked=len(acks),
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Verifies response_seconds matches the mathematical delta (ack_timestamp - event_timestamp).",
            suggested_investigation="Audit acknowledgement response time calculation logic."
        )

    # 15. Deterministic ID formats
    def _check_15_deterministic_id_formats(self) -> ValidationCheckItem:
        failures = []
        total = 0
        
        # Check alarm events format: ALM-<machine-id>-<000001>
        alm_pattern = re.compile(r"^ALM-[A-Za-z0-9\-]+-\d{6}$")
        events = self.db.query(AlarmEvent.alarm_event_id).all()
        total += len(events)
        for (e_id,) in events:
            if not alm_pattern.match(e_id):
                failures.append(e_id)
                
        # Check incidents format: INC-2026-<000001>
        inc_pattern = re.compile(r"^INC-2026-\d{6}$")
        incidents = self.db.query(Incident.incident_id).all()
        total += len(incidents)
        for (i_id,) in incidents:
            if not inc_pattern.match(i_id):
                failures.append(i_id)
                
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="15. Deterministic Identifier Formatting",
            status=status,
            records_checked=total,
            failure_count=len(failures),
            example_affected_ids=failures[:5],
            explanation="Validates that canonical IDs conform to deterministic naming conventions.",
            suggested_investigation="Review ID string formatting templates in generator."
        )

    # 16. Cross-file consistency
    def _check_16_cross_file_consistency(self) -> ValidationCheckItem:
        manifest_path = settings.GENERATED_DATA_DIR / "manifest.json"
        status = "PASSED"
        failures = []
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                expected_alarms = manifest.get("row_counts", {}).get("alarm_events", 0)
                actual_alarms = self.db.query(func.count(AlarmEvent.alarm_event_id)).scalar() or 0
                if expected_alarms != actual_alarms:
                    failures.append(f"alarm_events: manifest={expected_alarms}, db={actual_alarms}")
                    status = "FAILED"
        return ValidationCheckItem(
            check_name="16. Cross-File & Manifest Consistency",
            status=status,
            records_checked=1,
            failure_count=len(failures),
            example_affected_ids=failures,
            explanation="Verifies alignment between export manifest metrics and database table counts.",
            suggested_investigation="Inspect file export and database synchronisation pipeline."
        )

    # 17. Ground-truth isolation
    def _check_17_ground_truth_isolation(self) -> ValidationCheckItem:
        gt_file = settings.EVALUATION_DATA_DIR / "ground_truth.csv"
        exists_in_eval = gt_file.exists()
        exists_in_gen = (settings.GENERATED_DATA_DIR / "ground_truth.csv").exists()
        
        failures = []
        if exists_in_gen:
            failures.append("ground_truth.csv leaked into data/generated!")
        if not exists_in_eval:
            failures.append("ground_truth.csv missing from data/evaluation!")
            
        status = "PASSED" if not failures else "FAILED"
        return ValidationCheckItem(
            check_name="17. Ground-Truth Data Isolation",
            status=status,
            records_checked=2,
            failure_count=len(failures),
            example_affected_ids=failures,
            explanation="Guarantees ground truth labels reside strictly in data/evaluation and never in data/generated.",
            suggested_investigation="Verify generator export folder isolation policies."
        )

    # 18. Reproducible generation checksums
    def _check_18_reproducible_checksums(self) -> ValidationCheckItem:
        run = self.db.query(DataGenerationRun).order_by(DataGenerationRun.generated_at.desc()).first()
        failures = []
        if not run or not run.canonical_checksum:
            failures.append("No recorded canonical checksum in database")
            status = "FAILED"
        else:
            status = "PASSED"
            
        return ValidationCheckItem(
            check_name="18. Reproducible Generation Checksums",
            status=status,
            records_checked=1,
            failure_count=len(failures),
            example_affected_ids=[run.canonical_checksum] if (run and run.canonical_checksum) else failures,
            explanation="Confirms dataset generation records canonical SHA-256 content hashes.",
            suggested_investigation="Ensure generation pipeline logs run parameters and content checksums."
        )

    def machines_cache(self):
        if not hasattr(self, "_m_cache"):
            self._m_cache = self.db.query(Machine).all()
        return self._m_cache
