import random
import hashlib
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.entities import (
    Plant, Machine, SafetyZone, MachineSafetyZone, Interlock,
    AlarmDefinition, OperatorShift, AlarmEvent, Acknowledgement,
    Incident, CorrectiveAction, MachineStateHistory, InterlockStateHistory,
    AlarmReplayGroup, AuditLog, DetectionRule, DataGenerationRun
)

MACHINE_TYPES = [
    "STAMPING_PRESS",
    "ROBOTIC_WELDER",
    "CONVEYOR_SYSTEM",
    "CNC_MILL",
    "CHEMICAL_REACTOR"
]

INTERLOCK_TYPES = [
    ("LIGHT_CURTAIN", "CLOSED"),
    ("GUARD_DOOR_SWITCH", "CLOSED"),
    ("EMERGENCY_STOP_BUTTON", "ARMED"),
    ("PRESSURE_MAT", "CLEAR"),
    ("PRESSURE_RELIEF_VALVE", "CLOSED")
]

SEVERITIES = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]

DETECTION_RULES_DEF = [
    ("RULE-001", "Repeated Unsafe Conditions", "SYSTEMIC_RISK", "Evaluates frequency of hazardous states and critical alarms in sliding window"),
    ("RULE-002", "Multi-Factor Severity Prioritization", "TRIAGE", "Ranks events by severity, interlock breach, and escalation criteria"),
    ("RULE-003", "Acknowledgement SLA & Chronology", "OPERATOR_SLA", "Calculates response time and catches delayed or pre-alarm acknowledgements"),
    ("RULE-004", "Alarm Flood & Duplicate Replay", "FLOOD_REPLAY", "Identifies alarm bursts and duplicate telemetry loops"),
    ("RULE-005", "Nuisance Alarm Clustering", "NUISANCE", "Detects frequent low-value chattering alarms without mechanical consequence"),
    ("RULE-006", "Impossible Interlock State Detection", "MECHANICAL_SAFETY", "Detects invalid concurrent machine and interlock physical states"),
    ("RULE-007", "Incident Context & Trigger Validation", "INTEGRITY", "Validates incident telemetry evidence and root alarms"),
    ("RULE-008", "Corrective Action Verification Gate", "COMPLIANCE", "Enforces verification before closure in remediation lifecycle"),
    ("RULE-009", "Event Ordering & Telemetry Chronology", "CHRONOLOGY", "Validates physical sequence monotonic ordering and ingestion lag"),
    ("RULE-010", "End-to-End Incident Traceability", "TRACEABILITY", "Traverses physical and operational provenance graph for incidents"),
]

def deterministic_hash(val: Any) -> int:
    """Deterministic integer hash independent of process-level Python hash seeds."""
    return int(hashlib.sha256(str(val).encode("utf-8")).hexdigest()[:12], 16)

def generate_canonical_hash(data_summary: Dict[str, Any]) -> str:
    """Generate SHA256 canonical hash of sorted deterministic dataset summary."""
    canonical_str = json.dumps(data_summary, sort_keys=True)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

class SyntheticDataGenerator:
    def __init__(self, seed: int = settings.DEFAULT_SEED, profile: str = "starter", event_count: int = None):
        self.seed = seed
        self.profile = profile
        self.rng = random.Random(seed)
        
        # Profile sizing
        if profile == "full":
            self.num_plants = 4
            self.num_machines = 60
            self.num_alarm_defs = 200
            self.target_events = event_count or settings.DEFAULT_FULL_EVENTS
            self.time_window_days = 30
        else: # starter
            self.num_plants = 4
            self.num_machines = 12
            self.num_alarm_defs = 40
            self.target_events = event_count or settings.DEFAULT_STARTER_EVENTS
            self.time_window_days = 14

        self.start_date = datetime(2026, 10, 1, 0, 0, 0)
        self.end_date = self.start_date + timedelta(days=self.time_window_days)
        
        # In-memory storage for generation pass
        self.plants: List[Plant] = []
        self.machines: List[Machine] = []
        self.safety_zones: List[SafetyZone] = []
        self.machine_zones: List[MachineSafetyZone] = []
        self.interlocks: List[Interlock] = []
        self.alarm_defs: List[AlarmDefinition] = []
        self.shifts: List[OperatorShift] = []
        self.machine_state_histories: List[MachineStateHistory] = []
        self.interlock_state_histories: List[InterlockStateHistory] = []
        self.alarm_events: List[AlarmEvent] = []
        self.acknowledgements: List[Acknowledgement] = []
        self.incidents: List[Incident] = []
        self.corrective_actions: List[CorrectiveAction] = []
        self.detection_rules: List[DetectionRule] = []
        self.replay_groups: List[AlarmReplayGroup] = []
        self.audit_logs: List[AuditLog] = []
        
        # Ground truth records (isolated)
        self.ground_truth_records: List[Dict[str, Any]] = []

    def run(self, db: Session = None, export_files: bool = True) -> Dict[str, Any]:
        """Executes full deterministic data generation workflow in dependency order."""
        # 0. Detection Rules
        self._generate_detection_rules()
        
        # 1. Plants
        self._generate_plants()
        
        # 2. Machines
        self._generate_machines()
        
        # 3. Safety Zones
        self._generate_safety_zones()
        
        # 4. Interlocks
        self._generate_interlocks()
        
        # 5. Machine-to-Safety-Zone Relationships
        self._generate_machine_safety_zones()
        
        # 6. Alarm Definitions
        self._generate_alarm_definitions()
        
        # 7. Operator Shifts
        self._generate_operator_shifts()
        
        # 8. Machine and Interlock Initial States & Histories
        self._generate_state_histories()
        
        # 9. Alarm Events (Baseline normal telemetry, flood storms, nuisance clusters)
        self._generate_alarm_events()
        
        # 10. Acknowledgements (Baseline operator response times & SLAs)
        self._generate_acknowledgements()
        
        # 11. Incidents (Genuine safety incidents linked to alarms)
        self._generate_incidents()
        
        # 12. Corrective Actions (Remediation lifecycle)
        self._generate_corrective_actions()
        
        # 13. Controlled Anomaly Fixtures and Isolated Ground Truth Records
        self._inject_controlled_anomalies()
        
        # 14. Audit Logs
        self._generate_audit_logs()
        
        # Compute canonical checksum
        summary = self._compute_summary()
        canonical_checksum = generate_canonical_hash(summary)
        
        manifest = {
            "origin": "Deterministic Synthetic Generator",
            "seed": self.seed,
            "profile": self.profile,
            "schema_version": "1.0.0",
            "generation_timestamp": self.start_date.isoformat(),
            "time_window_start": self.start_date.isoformat(),
            "time_window_end": self.end_date.isoformat(),
            "row_counts": summary,
            "canonical_checksum": canonical_checksum,
            "external_dataset_claim": "None. All records are synthetically generated."
        }

        # Persist to database if db session provided
        if db:
            self._save_to_database(db, manifest, canonical_checksum)
            
        # Export files
        if export_files:
            self._export_csv_and_json(manifest)
            
        return {
            "manifest": manifest,
            "summary": summary,
            "canonical_checksum": canonical_checksum,
            "ground_truth_count": len(self.ground_truth_records)
        }

    def _generate_detection_rules(self):
        for rule_id, name, cat, desc in DETECTION_RULES_DEF:
            rule = DetectionRule(
                rule_id=rule_id,
                rule_name=name,
                category=cat,
                description=desc,
                is_active=True,
                created_at=self.start_date
            )
            self.detection_rules.append(rule)

    def _generate_plants(self):
        plant_names = [
            ("PLANT-01", "PLT-DET-01", "Detroit Assembly Center", "Detroit, MI, USA", "America/Detroit"),
            ("PLANT-02", "PLT-STU-02", "Stuttgart Propulsion Plant", "Stuttgart, Germany", "Europe/Berlin"),
            ("PLANT-03", "PLT-NAG-03", "Nagoya Heavy Pressworks", "Nagoya, Japan", "Asia/Tokyo"),
            ("PLANT-04", "PLT-MON-04", "Monterrey Robotics Hub", "Monterrey, Mexico", "America/Monterrey"),
        ]
        for p_id, code, name, loc, tz in plant_names[:self.num_plants]:
            plant = Plant(
                plant_id=p_id,
                plant_code=code,
                plant_name=name,
                location=loc,
                timezone=tz,
                status="ACTIVE",
                created_at=self.start_date - timedelta(days=365)
            )
            self.plants.append(plant)

    def _generate_machines(self):
        per_plant = self.num_machines // self.num_plants
        rem = self.num_machines % self.num_plants
        
        m_idx = 1
        for p_idx, plant in enumerate(self.plants):
            count = per_plant + (1 if p_idx < rem else 0)
            for j in range(count):
                m_type = MACHINE_TYPES[(m_idx - 1) % len(MACHINE_TYPES)]
                m_id = f"MCH-{m_idx:02d}"
                m_code = f"{m_type[:3]}-{plant.plant_code[4:7]}-{j+1:02d}"
                machine = Machine(
                    machine_id=m_id,
                    plant_id=plant.plant_id,
                    machine_code=m_code,
                    machine_name=f"{m_type.replace('_', ' ').title()} #{j+1}",
                    machine_type=m_type,
                    operational_status="RUNNING" if (m_idx % 7 != 0) else "IDLE",
                    commissioned_at=self.start_date - timedelta(days=self.rng.randint(200, 1000)),
                    retired_at=None,
                    created_at=self.start_date - timedelta(days=150)
                )
                self.machines.append(machine)
                m_idx += 1

    def _generate_safety_zones(self):
        for plant in self.plants:
            zones_spec = [
                (f"ZONE-{plant.plant_id[-2:]}-01", f"SZ-{plant.plant_code[4:7]}-PRESS", "Stamping & Press Perimeter", "CRITICAL"),
                (f"ZONE-{plant.plant_id[-2:]}-02", f"SZ-{plant.plant_code[4:7]}-ROBOT", "Robotic Cell Safety Envelope", "HIGH"),
                (f"ZONE-{plant.plant_id[-2:]}-03", f"SZ-{plant.plant_code[4:7]}-LOGIS", "Conveyor Logistics Lane", "MEDIUM"),
            ]
            for z_id, code, name, risk in zones_spec:
                zone = SafetyZone(
                    safety_zone_id=z_id,
                    plant_id=plant.plant_id,
                    zone_code=code,
                    zone_name=name,
                    risk_level=risk,
                    description=f"Standard primary monitored perimeter for {name}",
                    effective_from=self.start_date - timedelta(days=500),
                    effective_to=None,
                    status="ACTIVE"
                )
                self.safety_zones.append(zone)

    def _generate_interlocks(self):
        for machine in self.machines:
            # Each machine has 2 interlocks
            for k in range(2):
                itype, safe_state = INTERLOCK_TYPES[(deterministic_hash(machine.machine_id) + k) % len(INTERLOCK_TYPES)]
                itl_id = f"ITL-{machine.machine_id[4:]}-{k+1:02d}"
                itl = Interlock(
                    interlock_id=itl_id,
                    machine_id=machine.machine_id,
                    interlock_code=f"{itype[:3]}-{machine.machine_id[4:]}-{k+1}",
                    interlock_name=f"{itype.replace('_', ' ').title()} Guard {k+1}",
                    interlock_type=itype,
                    expected_safe_state=safe_state,
                    current_state=safe_state,
                    effective_from=self.start_date - timedelta(days=250),
                    effective_to=None,
                    status="ACTIVE"
                )
                self.interlocks.append(itl)

    def _generate_machine_safety_zones(self):
        zones_by_plant = {}
        for z in self.safety_zones:
            zones_by_plant.setdefault(z.plant_id, []).append(z)
            
        for machine in self.machines:
            plant_zones = zones_by_plant[machine.plant_id]
            chosen_zone = plant_zones[deterministic_hash(machine.machine_id) % len(plant_zones)]
            msz = MachineSafetyZone(
                machine_id=machine.machine_id,
                safety_zone_id=chosen_zone.safety_zone_id,
                effective_from=self.start_date - timedelta(days=300),
                effective_to=None,
                created_at=self.start_date - timedelta(days=300)
            )
            self.machine_zones.append(msz)

    def _generate_alarm_definitions(self):
        templates = [
            ("EMERGENCY_STOP_TRIPPED", "Emergency Stop Circuit Tripped", "CRITICAL", 60, "TRIPPED"),
            ("EMERGENCY_STOP_CIRCUIT_FAULT", "Emergency Stop Circuit Fault", "CRITICAL", 60, "TRIPPED"),
            ("SAFETY_RELAY_FAILURE", "Safety Relay Feedback Failure", "CRITICAL", 60, "TRIPPED"),
            ("SAFETY_PLC_FAULT", "Safety PLC Watchdog Fault", "CRITICAL", 60, "TRIPPED"),
            ("INTERLOCK_BYPASS", "Safety Interlock Bypass Detected", "CRITICAL", 60, "TRIPPED"),
            ("INTERLOCK_SEQUENCE", "Interlock Sequence Violation", "HIGH", 120, "TRIPPED"),
            ("GUARD_DOOR_OPEN", "Guard Door Open During Operation", "CRITICAL", 60, "OPEN"),
            ("GUARD_LOCK_FAILURE", "Guard Door Lock Feedback Failure", "HIGH", 120, "OPEN"),
            ("SAFETY_ZONE_INTRUSION", "Safety Zone Occupancy Violation", "CRITICAL", 60, "TRIPPED"),
            ("LIGHT_CURTAIN_BREACH", "Light Curtain Perimeter Breach", "CRITICAL", 60, "TRIPPED"),
            ("PRESSURE_MAT_BREACH", "Safety Pressure Mat Activated", "CRITICAL", 60, "TRIPPED"),
            ("OVER_TEMPERATURE", "Equipment Overtemperature", "HIGH", 180, "CLOSED"),
            ("BEARING_TEMPERATURE_HIGH", "Bearing Overheating Threshold Exceeded", "HIGH", 180, "CLOSED"),
            ("COOLANT_TEMPERATURE_HIGH", "Coolant Temperature Above Limit", "MEDIUM", 300, "CLOSED"),
            ("PROCESS_PRESSURE_HIGH", "Process Pressure Above Safe Limit", "HIGH", 120, "CLOSED"),
            ("PROCESS_PRESSURE_LOW", "Process Pressure Below Operating Limit", "HIGH", 180, "CLOSED"),
            ("HYDRAULIC_PRESSURE_LOSS", "Hydraulic Pressure Loss", "HIGH", 180, "CLOSED"),
            ("PNEUMATIC_PRESSURE_DROP", "Pneumatic Supply Pressure Drop", "MEDIUM", 300, "CLOSED"),
            ("MOTOR_VIBRATION_SPIKE", "Motor Vibration Above Trip Threshold", "HIGH", 180, "CLOSED"),
            ("BEARING_VIBRATION_HIGH", "Bearing Vibration Anomaly", "MEDIUM", 300, "CLOSED"),
            ("MOTOR_OVERLOAD", "Motor Thermal Overload", "HIGH", 120, "CLOSED"),
            ("MOTOR_OVERCURRENT", "Motor Overcurrent Detected", "HIGH", 120, "CLOSED"),
            ("DRIVE_EQUIPMENT_FAULT", "Variable-Frequency Drive Fault", "HIGH", 180, "CLOSED"),
            ("GEARBOX_EQUIPMENT_FAULT", "Gearbox Fault Signature Detected", "MEDIUM", 300, "CLOSED"),
            ("CONVEYOR_JAM", "Conveyor Transfer Jam Detected", "MEDIUM", 300, "CLOSED"),
            ("PUMP_CAVITATION", "Pump Cavitation Signature Detected", "MEDIUM", 300, "CLOSED"),
            ("SENSOR_SIGNAL_FAILURE", "Safety Sensor Signal Failure", "HIGH", 120, "TRIPPED"),
            ("SENSOR_CALIBRATION_DRIFT", "Sensor Calibration Drift", "MEDIUM", 600, "CLOSED"),
            ("SENSOR_OUT_OF_RANGE", "Process Sensor Value Out of Range", "HIGH", 180, "CLOSED"),
            ("SENSOR_DISAGREEMENT", "Redundant Sensor Disagreement", "HIGH", 180, "CLOSED"),
            ("ALARM_FLOOD", "Alarm Flood Rate Threshold Exceeded", "HIGH", 120, "CLOSED"),
            ("NUISANCE_ALARM_CHATTER", "Nuisance Alarm Chatter Detected", "LOW", 900, "CLOSED"),
            ("PLC_COMMUNICATION_LOSS", "PLC Communication Link Lost", "HIGH", 120, "CLOSED"),
            ("TELEMETRY_TRANSMISSION_LOSS", "Telemetry Transmission Lost", "MEDIUM", 300, "CLOSED"),
            ("STALE_SENSOR_TELEMETRY", "Stale Sensor Telemetry Received", "MEDIUM", 300, "CLOSED"),
            ("TELEMETRY_TIME_SYNC", "Telemetry Clock Synchronization Error", "INFO", 1800, "CLOSED"),
            ("FIRE_SMOKE_DETECTED", "Fire or Smoke Detector Activated", "CRITICAL", 60, "TRIPPED"),
            ("HAZARDOUS_GAS_DETECTED", "Hazardous Gas Concentration High", "CRITICAL", 60, "TRIPPED"),
            ("CHEMICAL_CONTAINMENT_BREACH", "Chemical Containment Zone Breach", "CRITICAL", 60, "TRIPPED"),
            ("COOLING_SYSTEM_FAILURE", "Equipment Cooling System Failure", "HIGH", 180, "CLOSED"),
        ]
        
        def_idx = 1
        for i in range(self.num_alarm_defs):
            m_type = MACHINE_TYPES[i % len(MACHINE_TYPES)]
            t_code, t_name, t_sev, sla, safe_itl = templates[i // len(MACHINE_TYPES)]
            alarm_def = AlarmDefinition(
                alarm_definition_id=f"ALMDEF-{def_idx:03d}",
                alarm_code=f"{t_code}_{def_idx:03d}",
                machine_type=m_type,
                alarm_name=f"{t_name} ({m_type.replace('_', ' ').title()})",
                description=f"Standard telemetry alert: {t_name} on {m_type}",
                severity=t_sev,
                acknowledgement_required=True if t_sev in ["CRITICAL", "HIGH", "MEDIUM"] else (i % 2 == 0),
                acknowledgement_sla_seconds=sla,
                expected_interlock_state=safe_itl,
                active_from=self.start_date - timedelta(days=200),
                active_to=None,
                status="ACTIVE"
            )
            self.alarm_defs.append(alarm_def)
            def_idx += 1

    def _preserve_complete_full_dataset(self, db: Session, manifest: Dict[str, Any], canonical_checksum: str) -> bool:
        if (
            self.profile != "full"
            or self.seed != settings.DEFAULT_SEED
            or self.target_events != settings.DEFAULT_FULL_EVENTS
        ):
            return False

        if (
            db.query(Plant).count() != self.num_plants
            or db.query(Machine).count() != self.num_machines
            or db.query(AlarmDefinition).count() != self.num_alarm_defs
            or db.query(AlarmEvent).count() != self.target_events
        ):
            return False

        if {row[0] for row in db.query(Plant.plant_id).all()} != {plant.plant_id for plant in self.plants}:
            return False
        if {row[0] for row in db.query(Machine.machine_id).all()} != {machine.machine_id for machine in self.machines}:
            return False

        expected_machine_types = {
            definition.alarm_definition_id: definition.machine_type for definition in self.alarm_defs
        }
        existing_machine_types = dict(
            db.query(AlarmDefinition.alarm_definition_id, AlarmDefinition.machine_type).all()
        )
        if existing_machine_types != expected_machine_types:
            return False

        invalid_event_references = (
            db.query(AlarmEvent.alarm_event_id)
            .outerjoin(Machine, AlarmEvent.machine_id == Machine.machine_id)
            .outerjoin(AlarmDefinition, AlarmEvent.alarm_definition_id == AlarmDefinition.alarm_definition_id)
            .filter(
                (Machine.machine_id.is_(None))
                | (AlarmDefinition.alarm_definition_id.is_(None))
                | (Machine.machine_type != AlarmDefinition.machine_type)
            )
            .count()
        )
        if invalid_event_references:
            return False

        definition_codes = {definition.alarm_code for definition in self.alarm_defs}
        existing_codes = {row[0] for row in db.query(AlarmDefinition.alarm_code).all()}
        temporary_prefix = "__GEN_REFRESH"
        while any(
            f"{temporary_prefix}_{index:03d}" in definition_codes | existing_codes
            for index in range(1, len(self.alarm_defs) + 1)
        ):
            temporary_prefix += "_"

        db.bulk_update_mappings(
            AlarmDefinition,
            [
                {
                    "alarm_definition_id": definition.alarm_definition_id,
                    "alarm_code": f"{temporary_prefix}_{index:03d}",
                }
                for index, definition in enumerate(self.alarm_defs, 1)
            ],
        )
        db.bulk_update_mappings(
            AlarmDefinition,
            [
                {
                    "alarm_definition_id": definition.alarm_definition_id,
                    "alarm_code": definition.alarm_code,
                    "machine_type": definition.machine_type,
                    "alarm_name": definition.alarm_name,
                    "description": definition.description,
                    "severity": definition.severity,
                    "acknowledgement_required": definition.acknowledgement_required,
                    "acknowledgement_sla_seconds": definition.acknowledgement_sla_seconds,
                    "expected_interlock_state": definition.expected_interlock_state,
                    "active_from": definition.active_from,
                    "active_to": definition.active_to,
                    "status": definition.status,
                }
                for definition in self.alarm_defs
            ],
        )
        db.add(
            DataGenerationRun(
                run_id=f"RUN-{self.seed}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                seed=self.seed,
                profile=self.profile,
                generated_at=datetime.utcnow(),
                manifest_json=json.dumps(manifest),
                canonical_checksum=canonical_checksum,
            )
        )
        db.commit()
        return True

    def _generate_operator_shifts(self):
        shift_names = ["MORNING", "AFTERNOON", "NIGHT"]
        
        s_id = 1
        current = self.start_date
        while current < self.end_date:
            for plant in self.plants:
                for s_num, s_name in enumerate(shift_names):
                    s_start = current + timedelta(hours=s_num * 8)
                    s_end = s_start + timedelta(hours=8)
                    op_code = f"OP-{(s_id * 137) % 9000 + 1000}"
                    shift = OperatorShift(
                        shift_id=f"SHF-{plant.plant_id[6:]}-{s_start.strftime('%Y%m%d')}-{s_num+1:02d}",
                        operator_code=op_code,
                        shift_name=s_name,
                        plant_id=plant.plant_id,
                        shift_start=s_start,
                        shift_end=s_end,
                        status="COMPLETED"
                    )
                    self.shifts.append(shift)
                    s_id += 1
            current += timedelta(days=1)

    def _generate_state_histories(self):
        states_cycle = ["IDLE", "RUNNING", "RUNNING", "RUNNING", "MAINTENANCE", "RUNNING", "IDLE"]
        for machine in self.machines:
            cur_time = self.start_date
            h_step = 0
            self.machine_state_histories.append(MachineStateHistory(
                machine_id=machine.machine_id,
                state="IDLE",
                transition_timestamp=self.start_date,
                trigger_source="PLC_COMMISSIONING",
                notes="Initial commissioned baseline state"
            ))
            while cur_time < self.end_date:
                h_step += 1
                hours_step = 36 + (deterministic_hash((machine.machine_id, h_step)) % 48)
                cur_time += timedelta(hours=hours_step)
                if cur_time < self.end_date:
                    st = states_cycle[h_step % len(states_cycle)]
                    msh = MachineStateHistory(
                        machine_id=machine.machine_id,
                        state=st,
                        transition_timestamp=cur_time,
                        trigger_source="PLC_TELEMETRY",
                        notes=f"Operational state shift transition to {st}"
                    )
                    self.machine_state_histories.append(msh)

        for itl in self.interlocks:
            ish = InterlockStateHistory(
                interlock_id=itl.interlock_id,
                state=itl.expected_safe_state,
                transition_timestamp=self.start_date,
                trigger_event_id=None,
                notes="Initial commissioned safe state"
            )
            self.interlock_state_histories.append(ish)

    def _generate_alarm_events(self):
        total_seconds = int((self.end_date - self.start_date).total_seconds())
        
        defs_by_type = {}
        for d in self.alarm_defs:
            defs_by_type.setdefault(d.machine_type, []).append(d)
            
        machine_zones = {m.machine_id: z.safety_zone_id for m in self.machines for z in self.machine_zones if z.machine_id == m.machine_id}
        
        # In _inject_controlled_anomalies, exactly 11 anomaly alarm events are added:
        # 5 IMPOSSIBLE_INTERLOCK_STATE + 6 DUPLICATE_ALARM_REPLAY = 11 events.
        baseline_target = self.target_events - 11
        
        raw_events: List[Dict[str, Any]] = []
        
        # 1. Generate Realistic Alarm Flood Bursts (10 episodes where >=10 alarms occur in 10m on a machine)
        num_floods = min(10, max(1, baseline_target // 100))
        flood_size = 12
        for f in range(num_floods):
            f_mch = self.machines[(f * 7 + 1) % len(self.machines)]
            f_defs = defs_by_type.get(f_mch.machine_type, self.alarm_defs)
            f_day = (f * 3 + 2) % max(1, self.time_window_days - 2) + 1
            f_start = self.start_date + timedelta(days=f_day, hours=14, minutes=10 * f)
            for step in range(flood_size):
                evt_t = f_start + timedelta(seconds=step * 20)
                a_def = f_defs[step % len(f_defs)]
                raw_events.append({
                    "machine": f_mch,
                    "alarm_def": a_def,
                    "event_time": evt_t,
                    "machine_state": "RUNNING" if step < 8 else "EMERGENCY_STOP",
                    "interlock_snapshot": "CLOSED" if step < 8 else "TRIPPED",
                    "status": "ACKNOWLEDGED" if (step % 4 != 0) else "ACTIVE",
                })
                
        # 2. Generate Realistic Nuisance Alarm Clusters (10 episodes of chattering non-critical alarms)
        num_nuis = min(10, max(1, baseline_target // 100))
        nuis_size = 7
        for n in range(num_nuis):
            n_mch = self.machines[(n * 5 + 3) % len(self.machines)]
            n_defs = defs_by_type.get(n_mch.machine_type, self.alarm_defs)
            low_med_defs = [d for d in n_defs if d.severity in ["LOW", "MEDIUM", "INFO"]] or n_defs
            target_def = low_med_defs[n % len(low_med_defs)]
            n_day = (n * 2 + 1) % max(1, self.time_window_days - 2) + 1
            n_start = self.start_date + timedelta(days=n_day, hours=8, minutes=15 * n)
            for step in range(nuis_size):
                evt_t = n_start + timedelta(seconds=step * 90)
                raw_events.append({
                    "machine": n_mch,
                    "alarm_def": target_def,
                    "event_time": evt_t,
                    "machine_state": "RUNNING",
                    "interlock_snapshot": "CLOSED",
                    "status": "ACKNOWLEDGED",
                })
                
        # 3. Regular Operational Baseline Events
        used_cluster_count = len(raw_events)
        regular_count = baseline_target - used_cluster_count
        
        for i in range(regular_count):
            machine = self.machines[i % len(self.machines)]
            applicable_defs = defs_by_type.get(machine.machine_type, self.alarm_defs)
            alarm_def = applicable_defs[(i // len(self.machines)) % len(applicable_defs)]
            
            # Deterministic pseudo-random time spanning the full window
            rel_sec = (i * 1234567 + 98765) % total_seconds
            event_time = self.start_date + timedelta(seconds=rel_sec)
            
            m_state = "RUNNING" if (i % 6 != 0) else "IDLE"
            itl_snapshot = "CLOSED" if m_state == "RUNNING" else "OPEN"
            
            raw_events.append({
                "machine": machine,
                "alarm_def": alarm_def,
                "event_time": event_time,
                "machine_state": m_state,
                "interlock_snapshot": itl_snapshot,
                "status": "ACKNOWLEDGED" if (i % 6 != 0) else "ACTIVE",
            })
            
        # Sort raw events chronologically by timestamp and machine
        raw_events.sort(key=lambda x: (x["event_time"], x["machine"].machine_id))
        
        # Assign deterministic per-machine sequences and canonical IDs
        m_sequences = {m.machine_id: 1 for m in self.machines}
        
        for ev in raw_events:
            machine = ev["machine"]
            m_id = machine.machine_id
            seq = m_sequences[m_id]
            m_sequences[m_id] += 1
            
            alm_id = f"ALM-{m_id}-{seq:06d}"
            event_time = ev["event_time"]
            lag_ms = 100 + (deterministic_hash((m_id, seq)) % 2400)
            recv_time = event_time + timedelta(milliseconds=lag_ms)
            
            alarm_event = AlarmEvent(
                alarm_event_id=alm_id,
                machine_id=m_id,
                alarm_definition_id=ev["alarm_def"].alarm_definition_id,
                safety_zone_id=machine_zones.get(m_id),
                event_timestamp=event_time,
                received_timestamp=recv_time,
                event_sequence=seq,
                machine_state=ev["machine_state"],
                interlock_state_snapshot=ev["interlock_snapshot"],
                alarm_status=ev["status"],
                source_event_id=f"SRC-{m_id}-{seq:06d}",
                replay_reference=None,
                issue_type=None,
                created_at=recv_time
            )
            self.alarm_events.append(alarm_event)

        # Sort alarm events deterministically by timestamp and sequence
        self.alarm_events.sort(key=lambda x: (x.event_timestamp, x.event_sequence, x.alarm_event_id))

    def _generate_acknowledgements(self):
        for idx, event in enumerate(self.alarm_events):
            if event.alarm_status == "ACKNOWLEDGED":
                sla = 300
                for d in self.alarm_defs:
                    if d.alarm_definition_id == event.alarm_definition_id:
                        sla = d.acknowledgement_sla_seconds
                        break
                        
                # 85% timely, 15% delayed
                is_delayed = (idx % 7 == 0)
                if is_delayed:
                    resp_sec = sla + (idx % 400) + 30
                    status = "DELAYED"
                else:
                    resp_sec = max(5, int(sla * ((idx % 70) / 100.0)))
                    status = "TIMELY"
                    
                ack_time = event.event_timestamp + timedelta(seconds=resp_sec)
                ack_id = f"ACK-{event.alarm_event_id}-01"
                
                ack = Acknowledgement(
                    acknowledgement_id=ack_id,
                    alarm_event_id=event.alarm_event_id,
                    shift_id=None,
                    acknowledgement_timestamp=ack_time,
                    acknowledgement_status=status,
                    response_seconds=resp_sec,
                    acknowledgement_channel="HMI_TOUCHPANEL",
                    notes="Standard operator verification",
                    issue_type=None
                )
                self.acknowledgements.append(ack)

    def _generate_incidents(self):
        # Create genuine incidents from authentic high/critical alarms
        critical_alarms = [
            e for e in self.alarm_events 
            if any(d.alarm_definition_id == e.alarm_definition_id and d.severity in ["CRITICAL", "HIGH"] for d in self.alarm_defs)
        ]
        
        inc_count = 30 if self.profile == "starter" else 50
        machine_zones = {m.machine_id: z.safety_zone_id for m in self.machines for z in self.machine_zones if z.machine_id == m.machine_id}
        machine_plants = {m.machine_id: m.plant_id for m in self.machines}
        
        step = max(1, len(critical_alarms) // inc_count)
        for inc_idx in range(inc_count):
            if inc_idx * step < len(critical_alarms):
                trigger_alarm = critical_alarms[inc_idx * step]
                m_id = trigger_alarm.machine_id
                z_id = machine_zones.get(m_id)
                p_id = machine_plants.get(m_id)
                inc_time = trigger_alarm.event_timestamp + timedelta(seconds=15)
                sev = "CRITICAL" if inc_idx % 3 == 0 else "HIGH"
                inc_type = "INTERLOCK_BREACH" if inc_idx % 2 == 0 else "EMERGENCY_STOP_TRIP"
                rule_id = "RULE-001" if inc_idx % 2 == 0 else "RULE-002"
                
                inc = Incident(
                    incident_id=f"INC-2026-{inc_idx+1:06d}",
                    plant_id=p_id,
                    machine_id=m_id,
                    safety_zone_id=z_id,
                    incident_timestamp=inc_time,
                    incident_type=inc_type,
                    severity=sev,
                    description=f"Automated incident generated following {sev} alarm {trigger_alarm.alarm_event_id}",
                    triggering_alarm_event_id=trigger_alarm.alarm_event_id,
                    detection_rule_id=rule_id,
                    incident_status="RESOLVED" if inc_idx % 2 == 0 else "OPEN",
                    ground_truth_label=None,
                    created_at=inc_time
                )
                self.incidents.append(inc)
                
                # Append machine state transition evidence for incident context
                self.machine_state_histories.append(MachineStateHistory(
                    machine_id=m_id,
                    state="EMERGENCY_STOP" if inc_type == "EMERGENCY_STOP_TRIP" else "FAULT",
                    transition_timestamp=inc_time - timedelta(seconds=2),
                    trigger_source="SAFETY_CONTROLLER",
                    notes=f"Emergency trip following safety incident {inc.incident_id}"
                ))

    def _generate_corrective_actions(self):
        for idx, inc in enumerate(self.incidents):
            c_time = inc.incident_timestamp + timedelta(minutes=10)
            s_time = c_time + timedelta(hours=1)
            comp_time = s_time + timedelta(hours=4)
            ver_time = comp_time + timedelta(hours=2)
            
            # Normal completed actions:
            if inc.incident_status == "RESOLVED":
                act = CorrectiveAction(
                    corrective_action_id=f"ACT-{inc.incident_id}-01",
                    incident_id=inc.incident_id,
                    action_type="MECHANICAL_REPAIR" if idx % 2 == 0 else "GUARD_REPLACEMENT",
                    description=f"Inspect and remediate mechanical cause of incident {inc.incident_id}",
                    assigned_team="SAFETY_ENGINEERING" if idx % 2 == 0 else "MAINTENANCE_MECH",
                    created_at=c_time,
                    started_at=s_time,
                    completed_at=comp_time,
                    verified_at=ver_time,
                    verification_status="VERIFIED",
                    action_status="CLOSED",
                    issue_type=None
                )
            else:
                act = CorrectiveAction(
                    corrective_action_id=f"ACT-{inc.incident_id}-01",
                    incident_id=inc.incident_id,
                    action_type="INTERLOCK_RECALIBRATION",
                    description=f"Active remediation investigation for incident {inc.incident_id}",
                    assigned_team="MAINTENANCE_ELEC",
                    created_at=c_time,
                    started_at=s_time,
                    completed_at=None,
                    verified_at=None,
                    verification_status="PENDING",
                    action_status="IN_PROGRESS",
                    issue_type=None
                )
            self.corrective_actions.append(act)

    def _inject_controlled_anomalies(self):
        """Inject the 5 required controlled anomaly fixture categories and record ground truth."""
        machine_zones = {m.machine_id: z.safety_zone_id for m in self.machines for z in self.machine_zones if z.machine_id == m.machine_id}
        machine_plants = {m.machine_id: m.plant_id for m in self.machines}
        defs_by_type = {}
        for d in self.alarm_defs:
            defs_by_type.setdefault(d.machine_type, []).append(d)
        
        # 1. ACKNOWLEDGEMENT_BEFORE_ALARM (Inject 5 fixtures)
        for i in range(5):
            target_alarm = self.alarm_events[i * 10]
            neg_sec = -1 * (30 + (i * 15))
            bad_ack_time = target_alarm.event_timestamp + timedelta(seconds=neg_sec)
            ack_id = f"ACK-{target_alarm.alarm_event_id}-99"
            
            ack = Acknowledgement(
                acknowledgement_id=ack_id,
                alarm_event_id=target_alarm.alarm_event_id,
                shift_id=None,
                acknowledgement_timestamp=bad_ack_time,
                acknowledgement_status="PRE_ALARM_INVALID",
                response_seconds=neg_sec,
                acknowledgement_channel="HMI_TOUCHPANEL",
                notes="Deliberate anomaly fixture: operator ack timestamp precedes event timestamp",
                issue_type="ACKNOWLEDGEMENT_BEFORE_ALARM"
            )
            self.acknowledgements.append(ack)
            
            gt = {
                "evaluation_record_id": f"GT-ACK-NEG-{i+1:03d}",
                "affected_entity_type": "acknowledgements",
                "affected_entity_id": ack_id,
                "expected_anomaly_type": "ACKNOWLEDGEMENT_BEFORE_ALARM",
                "expected_detection": True,
                "expected_severity": "HIGH",
                "expected_reason": f"Response time is negative ({neg_sec}s). Acknowledgement timestamp precedes alarm.",
                "related_record_ids": target_alarm.alarm_event_id
            }
            self.ground_truth_records.append(gt)

        # 2. IMPOSSIBLE_INTERLOCK_STATE (Inject 5 fixtures)
        for i in range(5):
            target_machine = self.machines[i % len(self.machines)]
            target_def = defs_by_type[target_machine.machine_type][0]
            event_time = self.start_date + timedelta(days=2 + i, hours=10)
            recv_time = event_time + timedelta(milliseconds=500)
            
            seq = 9000 + i
            alm_id = f"ALM-{target_machine.machine_id}-{seq:06d}"
            
            event = AlarmEvent(
                alarm_event_id=alm_id,
                machine_id=target_machine.machine_id,
                alarm_definition_id=target_def.alarm_definition_id,
                safety_zone_id=machine_zones.get(target_machine.machine_id),
                event_timestamp=event_time,
                received_timestamp=recv_time,
                event_sequence=seq,
                machine_state="RUNNING",
                interlock_state_snapshot="TRIPPED",
                alarm_status="ACTIVE",
                source_event_id=f"SRC-INJECT-IMPOSS-{i+1}",
                replay_reference=None,
                issue_type="IMPOSSIBLE_INTERLOCK_STATE",
                created_at=recv_time
            )
            self.alarm_events.append(event)
            
            gt = {
                "evaluation_record_id": f"GT-ITL-IMP-{i+1:03d}",
                "affected_entity_type": "alarm_events",
                "affected_entity_id": alm_id,
                "expected_anomaly_type": "IMPOSSIBLE_INTERLOCK_STATE",
                "expected_detection": True,
                "expected_severity": "CRITICAL",
                "expected_reason": "Machine state is RUNNING while interlock snapshot reports TRIPPED without bypass.",
                "related_record_ids": target_machine.machine_id
            }
            self.ground_truth_records.append(gt)

        # 3. INCIDENT_MISSING_TRIGGER_CONTEXT (Inject 4 fixtures)
        for i in range(4):
            target_machine = self.machines[-(i+1)]
            inc_time = self.start_date + timedelta(days=5 + i, hours=3)
            inc_id = f"INC-2026-900{i+1:03d}"
            
            inc = Incident(
                incident_id=inc_id,
                plant_id=machine_plants.get(target_machine.machine_id),
                machine_id=target_machine.machine_id,
                safety_zone_id=machine_zones.get(target_machine.machine_id),
                incident_timestamp=inc_time,
                incident_type="UNGROUNDED_HAZARD",
                severity="HIGH",
                description="Controlled fixture: Incident logged without any triggering alarm or telemetry corroboration.",
                triggering_alarm_event_id=None,
                detection_rule_id="RULE-007",
                incident_status="OPEN",
                ground_truth_label="INCIDENT_MISSING_TRIGGER_CONTEXT",
                created_at=inc_time
            )
            self.incidents.append(inc)
            
            gt = {
                "evaluation_record_id": f"GT-INC-MISS-{i+1:03d}",
                "affected_entity_type": "incidents",
                "affected_entity_id": inc_id,
                "expected_anomaly_type": "INCIDENT_MISSING_TRIGGER_CONTEXT",
                "expected_detection": True,
                "expected_severity": "MEDIUM",
                "expected_reason": "Incident lacks triggering alarm event ID and has no supporting machine state change within window.",
                "related_record_ids": target_machine.machine_id
            }
            self.ground_truth_records.append(gt)

        # 4. DUPLICATE_ALARM_REPLAY (Inject 6 fixtures)
        for i in range(6):
            parent_event = self.alarm_events[i * 15]
            replay_time = parent_event.event_timestamp + timedelta(milliseconds=250)
            recv_time = replay_time + timedelta(milliseconds=100)
            
            seq = 8000 + i
            replay_id = f"ALM-{parent_event.machine_id}-{seq:06d}"
            
            replay_event = AlarmEvent(
                alarm_event_id=replay_id,
                machine_id=parent_event.machine_id,
                alarm_definition_id=parent_event.alarm_definition_id,
                safety_zone_id=parent_event.safety_zone_id,
                event_timestamp=replay_time,
                received_timestamp=recv_time,
                event_sequence=seq,
                machine_state=parent_event.machine_state,
                interlock_state_snapshot=parent_event.interlock_state_snapshot,
                alarm_status="REPLAYED",
                source_event_id=parent_event.source_event_id,
                replay_reference=parent_event.alarm_event_id,
                issue_type="DUPLICATE_ALARM_REPLAY",
                created_at=recv_time
            )
            self.alarm_events.append(replay_event)
            
            replay_grp = AlarmReplayGroup(
                group_id=f"GRP-REPLAY-{i+1:03d}",
                original_event_id=parent_event.alarm_event_id,
                replay_event_id=replay_id,
                time_delta_seconds=0.25,
                detected_at=recv_time
            )
            self.replay_groups.append(replay_grp)
            
            gt = {
                "evaluation_record_id": f"GT-ALM-DUP-{i+1:03d}",
                "affected_entity_type": "alarm_events",
                "affected_entity_id": replay_id,
                "expected_anomaly_type": "DUPLICATE_ALARM_REPLAY",
                "expected_detection": True,
                "expected_severity": "LOW",
                "expected_reason": f"Duplicate telemetry frame replaying source_event_id {parent_event.source_event_id} within 0.25s.",
                "related_record_ids": parent_event.alarm_event_id
            }
            self.ground_truth_records.append(gt)

        # 5. ACTION_CLOSED_WITHOUT_VERIFICATION (Inject 4 fixtures)
        for i in range(4):
            parent_inc = self.incidents[i]
            act_id = f"ACT-{parent_inc.incident_id}-99"
            
            act = CorrectiveAction(
                corrective_action_id=act_id,
                incident_id=parent_inc.incident_id,
                action_type="SOP_RETRAINING",
                description="Controlled fixture: Action marked CLOSED without passing verification gate.",
                assigned_team="OPERATIONS",
                created_at=parent_inc.incident_timestamp + timedelta(hours=1),
                started_at=parent_inc.incident_timestamp + timedelta(hours=2),
                completed_at=parent_inc.incident_timestamp + timedelta(hours=5),
                verified_at=None,
                verification_status="PENDING",
                action_status="CLOSED",
                issue_type="ACTION_CLOSED_WITHOUT_VERIFICATION"
            )
            self.corrective_actions.append(act)
            
            gt = {
                "evaluation_record_id": f"GT-ACT-UNVER-{i+1:03d}",
                "affected_entity_type": "corrective_actions",
                "affected_entity_id": act_id,
                "expected_anomaly_type": "ACTION_CLOSED_WITHOUT_VERIFICATION",
                "expected_detection": True,
                "expected_severity": "HIGH",
                "expected_reason": "Corrective action has action_status CLOSED but verification_status is PENDING and verified_at is empty.",
                "related_record_ids": parent_inc.incident_id
            }
            self.ground_truth_records.append(gt)

        # Resort all alarm events
        self.alarm_events.sort(key=lambda x: (x.event_timestamp, x.event_sequence, x.alarm_event_id))

    def _generate_audit_logs(self):
        audit_idx = 1
        # System dataset generation event
        self.audit_logs.append(AuditLog(
            audit_id=audit_idx,
            entity_type="SYSTEM",
            entity_id=f"GEN-{self.profile}",
            action="DATASET_GENERATION",
            actor="SYSTEM_SYNTHETIC_GENERATOR",
            changes_json=json.dumps({"profile": self.profile, "seed": self.seed, "target_events": self.target_events}),
            timestamp=self.start_date
        ))
        audit_idx += 1
        
        # Incident and action audit records
        for inc in self.incidents:
            self.audit_logs.append(AuditLog(
                audit_id=audit_idx,
                entity_type="incidents",
                entity_id=inc.incident_id,
                action="CREATE_INCIDENT",
                actor="AUTOMATED_SAFETY_SYSTEM",
                changes_json=json.dumps({"severity": inc.severity, "type": inc.incident_type}),
                timestamp=inc.incident_timestamp
            ))
            audit_idx += 1
            
        for act in self.corrective_actions:
            self.audit_logs.append(AuditLog(
                audit_id=audit_idx,
                entity_type="corrective_actions",
                entity_id=act.corrective_action_id,
                action="UPDATE_ACTION",
                actor="LEAD_SAFETY_AUDITOR",
                changes_json=json.dumps({"status": act.action_status, "verification": act.verification_status}),
                timestamp=act.completed_at or act.started_at or act.created_at
            ))
            audit_idx += 1

    def _compute_summary(self) -> Dict[str, Any]:
        """Calculates deterministic summary numbers for canonical hashing."""
        return {
            "plants": len(self.plants),
            "machines": len(self.machines),
            "safety_zones": len(self.safety_zones),
            "machine_safety_zones": len(self.machine_zones),
            "interlocks": len(self.interlocks),
            "alarm_definitions": len(self.alarm_defs),
            "operator_shifts": len(self.shifts),
            "machine_state_histories": len(self.machine_state_histories),
            "interlock_state_histories": len(self.interlock_state_histories),
            "alarm_events": len(self.alarm_events),
            "acknowledgements": len(self.acknowledgements),
            "incidents": len(self.incidents),
            "corrective_actions": len(self.corrective_actions),
            "detection_rules": len(self.detection_rules),
            "alarm_replay_groups": len(self.replay_groups),
            "audit_logs": len(self.audit_logs),
            "ground_truth_anomalies": len(self.ground_truth_records)
        }

    def _save_to_database(self, db: Session, manifest: Dict[str, Any], canonical_checksum: str):
        if self._preserve_complete_full_dataset(db, manifest, canonical_checksum):
            return

        # Truncate / clear existing tables in reverse dependency order
        for model in [
            AuditLog, AlarmReplayGroup, CorrectiveAction, Incident, Acknowledgement,
            AlarmEvent, InterlockStateHistory, MachineStateHistory,
            OperatorShift, AlarmDefinition, MachineSafetyZone, Interlock,
            SafetyZone, Machine, Plant, DetectionRule, DataGenerationRun
        ]:
            db.query(model).delete()
        db.commit()

        # Insert in dependency order
        db.bulk_save_objects(self.detection_rules)
        db.bulk_save_objects(self.plants)
        db.commit()
        
        db.bulk_save_objects(self.machines)
        db.bulk_save_objects(self.safety_zones)
        db.commit()
        
        db.bulk_save_objects(self.interlocks)
        db.bulk_save_objects(self.machine_zones)
        db.bulk_save_objects(self.alarm_defs)
        db.bulk_save_objects(self.shifts)
        db.commit()
        
        db.bulk_save_objects(self.machine_state_histories)
        db.bulk_save_objects(self.interlock_state_histories)
        db.commit()
        
        # Batch insert alarm events (chunks of 2000)
        chunk_size = 2000
        for i in range(0, len(self.alarm_events), chunk_size):
            db.bulk_save_objects(self.alarm_events[i:i+chunk_size])
            db.commit()

        # Batch insert acknowledgements (chunks of 2000)
        for i in range(0, len(self.acknowledgements), chunk_size):
            db.bulk_save_objects(self.acknowledgements[i:i+chunk_size])
            db.commit()

        db.bulk_save_objects(self.incidents)
        db.bulk_save_objects(self.corrective_actions)
        db.bulk_save_objects(self.replay_groups)
        db.bulk_save_objects(self.audit_logs)
        
        # Record generation run
        run_record = DataGenerationRun(
            run_id=f"RUN-{self.seed}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            seed=self.seed,
            profile=self.profile,
            generated_at=datetime.utcnow(),
            manifest_json=json.dumps(manifest),
            canonical_checksum=canonical_checksum
        )
        db.add(run_record)
        db.commit()

    def _export_csv_and_json(self, manifest: Dict[str, Any]):
        gen_dir = settings.GENERATED_DATA_DIR
        eval_dir = settings.EVALUATION_DATA_DIR
        
        # 1. Export Ground Truth to isolated evaluation folder
        gt_csv_path = eval_dir / "ground_truth.csv"
        with open(gt_csv_path, mode="w", newline="", encoding="utf-8") as f:
            if self.ground_truth_records:
                writer = csv.DictWriter(f, fieldnames=list(self.ground_truth_records[0].keys()))
                writer.writeheader()
                writer.writerows(self.ground_truth_records)
                
        gt_json_path = eval_dir / "ground_truth.json"
        with open(gt_json_path, mode="w", encoding="utf-8") as f:
            json.dump(self.ground_truth_records, f, indent=2)

        # 2. Export manifest
        with open(gen_dir / "manifest.json", mode="w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 3. Export core entities to CSV
        def write_csv(filename: str, records: list, fieldnames: list):
            path = gen_dir / filename
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                for r in records:
                    row = [getattr(r, fn, "") for fn in fieldnames]
                    row = [x.isoformat() if isinstance(x, datetime) else x for x in row]
                    writer.writerow(row)

        write_csv("plants.csv", self.plants, ["plant_id", "plant_code", "plant_name", "location", "timezone", "status", "created_at"])
        write_csv("machines.csv", self.machines, ["machine_id", "plant_id", "machine_code", "machine_name", "machine_type", "operational_status", "commissioned_at", "retired_at", "created_at"])
        write_csv("safety_zones.csv", self.safety_zones, ["safety_zone_id", "plant_id", "zone_code", "zone_name", "risk_level", "description", "effective_from", "effective_to", "status"])
        write_csv("interlocks.csv", self.interlocks, ["interlock_id", "machine_id", "interlock_code", "interlock_name", "interlock_type", "expected_safe_state", "current_state", "effective_from", "effective_to", "status"])
        write_csv("alarm_definitions.csv", self.alarm_defs, ["alarm_definition_id", "alarm_code", "machine_type", "alarm_name", "description", "severity", "acknowledgement_required", "acknowledgement_sla_seconds", "expected_interlock_state", "active_from", "active_to", "status"])
        write_csv("alarm_events.csv", self.alarm_events, ["alarm_event_id", "machine_id", "alarm_definition_id", "safety_zone_id", "event_timestamp", "received_timestamp", "event_sequence", "machine_state", "interlock_state_snapshot", "alarm_status", "source_event_id", "replay_reference", "issue_type", "created_at"])
        write_csv("acknowledgements.csv", self.acknowledgements, ["acknowledgement_id", "alarm_event_id", "shift_id", "acknowledgement_timestamp", "acknowledgement_status", "response_seconds", "acknowledgement_channel", "notes", "issue_type"])
        write_csv("incidents.csv", self.incidents, ["incident_id", "plant_id", "machine_id", "safety_zone_id", "incident_timestamp", "incident_type", "severity", "description", "triggering_alarm_event_id", "detection_rule_id", "incident_status", "ground_truth_label", "created_at"])
        write_csv("corrective_actions.csv", self.corrective_actions, ["corrective_action_id", "incident_id", "action_type", "description", "assigned_team", "created_at", "started_at", "completed_at", "verified_at", "verification_status", "action_status", "issue_type"])
        write_csv("audit_logs.csv", self.audit_logs, ["audit_id", "entity_type", "entity_id", "action", "actor", "changes_json", "timestamp"])
