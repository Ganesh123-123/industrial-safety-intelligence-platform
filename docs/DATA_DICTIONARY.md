# Industrial Safety Intelligence Platform - Data Dictionary

This document provides the authoritative data dictionary for all core and auxiliary entities used within the Industrial Safety Event Analysis and Incident Intelligence Platform.

---

## 1. Core Entities

### A. Plant (`plants`)
Represents an industrial facility or physical plant location containing multiple machines and safety zones.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `plant_id` | VARCHAR(64) | Yes | PK | Unique | e.g., `PLANT-01`, `PLANT-02` | None | Permanent | Canonical unique plant identifier. |
| `plant_code` | VARCHAR(32) | Yes | None | Unique | Alphanumeric (e.g., `PLT-DET-01`) | None | Permanent | Operational plant code. |
| `plant_name` | VARCHAR(128) | Yes | None | Non-unique | Text | None | Editable | Human-readable plant name. |
| `location` | VARCHAR(256) | Yes | None | Non-unique | City, State/Country | None | Editable | Physical geographical location. |
| `timezone` | VARCHAR(64) | Yes | None | Non-unique | IANA timezone (e.g. `America/Detroit`, `UTC`) | Default `UTC` | Editable | Plant local time zone. |
| `status` | VARCHAR(32) | Yes | None | Non-unique | `ACTIVE`, `MAINTENANCE`, `DECOMMISSIONED` | Default `ACTIVE` | Lifecycle: ACTIVE <-> MAINTENANCE -> DECOMMISSIONED | Plant operational status. |
| `created_at` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | Default `CURRENT_TIMESTAMP` | Append-only | Record creation time. |

---

### B. Machine (`machines`)
Represents an individual industrial machine, robotic cell, press, or processing unit.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `machine_id` | VARCHAR(64) | Yes | PK | Unique | e.g., `MCH-01`, `MCH-02` | None | Permanent | Canonical unique machine identifier. |
| `plant_id` | VARCHAR(64) | Yes | FK | Non-unique | References `plants.plant_id` | None | Immutable | Foreign key linking machine to plant. |
| `machine_code` | VARCHAR(32) | Yes | None | Unique | Alphanumeric (e.g., `CNC-001`, `ROB-004`) | None | Permanent | Asset tag or machine code. |
| `machine_name` | VARCHAR(128) | Yes | None | Non-unique | Text | None | Editable | Descriptive machine name. |
| `machine_type` | VARCHAR(64) | Yes | None | Non-unique | `STAMPING_PRESS`, `ROBOTIC_WELDER`, `CONVEYOR_SYSTEM`, `CNC_MILL`, `CHEMICAL_REACTOR` | None | Immutable | Categorical machine classification. |
| `operational_status`| VARCHAR(32) | Yes | None | Non-unique | `RUNNING`, `IDLE`, `EMERGENCY_STOP`, `MAINTENANCE`, `FAULT`, `OFFLINE` | Default `IDLE` | Dynamic state | Current operational state. |
| `commissioned_at` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Permanent | Date & time machine was commissioned. |
| `retired_at` | TIMESTAMP (UTC) | No | None | Non-unique | ISO 8601 UTC timestamp or NULL | Default NULL | Set when retired | Date & time machine was decommissioned. |
| `created_at` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | Default `CURRENT_TIMESTAMP` | Append-only | Record creation time. |

---

### C. SafetyZone (`safety_zones`)
Represents a monitored safety perimeter, cell boundary, or risk area within a plant.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `safety_zone_id` | VARCHAR(64) | Yes | PK | Unique | e.g., `ZONE-01-01` | None | Permanent | Canonical unique zone identifier. |
| `plant_id` | VARCHAR(64) | Yes | FK | Non-unique | References `plants.plant_id` | None | Immutable | Plant containing this safety zone. |
| `zone_code` | VARCHAR(32) | Yes | None | Non-unique | Alphanumeric (e.g., `ZONE-PRESS-A`) | None | Editable | Local zone code. |
| `zone_name` | VARCHAR(128) | Yes | None | Non-unique | Text | None | Editable | Human-readable zone designation. |
| `risk_level` | VARCHAR(32) | Yes | None | Non-unique | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | None | Editable | Inherent risk classification of zone. |
| `description` | TEXT | No | None | Non-unique | Text | None | Editable | Description of physical perimeter/hazards. |
| `effective_from` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Start date | Boundary validity start. |
| `effective_to` | TIMESTAMP (UTC) | No | None | Non-unique | ISO 8601 UTC timestamp or NULL | Default NULL | Expiration date | Boundary validity end. |
| `status` | VARCHAR(32) | Yes | None | Non-unique | `ACTIVE`, `INACTIVE`, `RECONFIGURED` | Default `ACTIVE` | Lifecycle state | Current zone status. |

---

### D. Interlock (`interlocks`)
Represents an electromechanical or software safety interlock (e.g., light curtain, gate guard switch, emergency stop button).

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `interlock_id` | VARCHAR(64) | Yes | PK | Unique | e.g., `ITL-01-001` | None | Permanent | Canonical unique interlock identifier. |
| `machine_id` | VARCHAR(64) | Yes | FK | Non-unique | References `machines.machine_id` | None | Immutable | Parent machine guarded by interlock. |
| `interlock_code`| VARCHAR(32) | Yes | None | Non-unique | Alphanumeric (e.g., `LC-01`, `E-STOP-01`) | None | Permanent | Hardware tag/code. |
| `interlock_name`| VARCHAR(128) | Yes | None | Non-unique | Text | None | Editable | Interlock device name. |
| `interlock_type`| VARCHAR(64) | Yes | None | Non-unique | `LIGHT_CURTAIN`, `GUARD_DOOR_SWITCH`, `EMERGENCY_STOP_BUTTON`, `PRESSURE_MAT`, `PRESSURE_RELIEF_VALVE` | None | Immutable | Hardware sensor classification. |
| `expected_safe_state`| VARCHAR(32)| Yes | None | Non-unique | `CLOSED`, `ENGAGED`, `ACTIVE`, `ARMED` | None | Configurable | Normal safe state required when running. |
| `current_state` | VARCHAR(32) | Yes | None | Non-unique | `OPEN`, `CLOSED`, `TRIPPED`, `ENGAGED`, `BYPASSED`, `DISARMED`, `FAULT` | None | Dynamic state | Current physical/logical state. |
| `effective_from`| TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Start date | Interlock commissioning timestamp. |
| `effective_to` | TIMESTAMP (UTC) | No | None | Non-unique | ISO 8601 UTC timestamp or NULL | Default NULL | Expiration date | Interlock decommissioning timestamp. |
| `status` | VARCHAR(32) | Yes | None | Non-unique | `ACTIVE`, `MAINTENANCE`, `BYPASSED`, `DECOMMISSIONED` | Default `ACTIVE` | Lifecycle state | Supervisory status of interlock. |

---

### E. AlarmDefinition (`alarm_definitions`)
Defines alarm criteria, machine types, severity levels, and acknowledgement SLA requirements.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `alarm_definition_id` | VARCHAR(64) | Yes | PK | Unique | e.g., `ALMDEF-001` | None | Permanent | Canonical definition ID. |
| `alarm_code` | VARCHAR(32) | Yes | None | Unique | e.g., `E_STOP_TRIPPED`, `CURTAIN_BREACH` | None | Permanent | Standardized alarm mnemonic code. |
| `machine_type` | VARCHAR(64) | Yes | None | Non-unique | Matches machine classifications | None | Filter | Applicable machine category. |
| `alarm_name` | VARCHAR(128) | Yes | None | Non-unique | Text | None | Editable | Human-readable alarm title. |
| `description` | TEXT | No | None | Non-unique | Text | None | Editable | Root cause guidance and procedures. |
| `severity` | VARCHAR(16) | Yes | None | Non-unique | `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | None | Configurable | Incident escalation severity. |
| `acknowledgement_required` | BOOLEAN | Yes | None | Non-unique | `TRUE`, `FALSE` | Default `TRUE` | Configurable | True if operator must acknowledge. |
| `acknowledgement_sla_seconds` | INTEGER | Yes | None | Non-unique | >= 0 | Seconds (e.g. 60, 300, 900) | Configurable | Maximum allowed delay for acknowledgement. |
| `expected_interlock_state` | VARCHAR(32) | No | None | Non-unique | `CLOSED`, `ARMED`, `TRIPPED`, etc. | Default NULL | Configurable | Interlock state associated with condition. |
| `active_from` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Start date | Policy start timestamp. |
| `active_to` | TIMESTAMP (UTC) | No | None | Non-unique | ISO 8601 UTC timestamp or NULL | Default NULL | Expiration date | Policy sunset timestamp. |
| `status` | VARCHAR(32) | Yes | None | Non-unique | `ACTIVE`, `RETIRED`, `DRAFT` | Default `ACTIVE` | Lifecycle state | Active policy flag. |

---

### F. AlarmEvent (`alarm_events`)
Records an individual alarm instance emitted by a machine or monitoring system.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `alarm_event_id` | VARCHAR(64) | Yes | PK | Unique | `ALM-<machine-id>-<sequence:06d>` | None | Permanent | Deterministic canonical event identifier. |
| `machine_id` | VARCHAR(64) | Yes | FK | Non-unique | References `machines.machine_id` | None | Immutable | Machine where alarm originated. |
| `alarm_definition_id` | VARCHAR(64) | Yes | FK | Non-unique | References `alarm_definitions` | None | Immutable | Specification defining this alarm. |
| `safety_zone_id` | VARCHAR(64) | No | FK | Non-unique | References `safety_zones` | Default NULL | Immutable | Zone active at event time. |
| `event_timestamp`| TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Immutable | Exact time event occurred at source machine. |
| `received_timestamp`| TIMESTAMP (UTC)| Yes | None | Non-unique | ISO 8601 UTC timestamp (>= event_timestamp) | None | Append-only | Time event was received by backend/broker. |
| `event_sequence` | INTEGER | Yes | None | Non-unique | >= 1 | Sequence number | Monotonic per machine | Monotonically increasing sequence ID. |
| `machine_state` | VARCHAR(32) | Yes | None | Non-unique | `RUNNING`, `IDLE`, `EMERGENCY_STOP`, `MAINTENANCE`, `FAULT`, `OFFLINE` | None | Immutable snapshot | Machine operational state at alarm time. |
| `interlock_state_snapshot` | VARCHAR(64) | Yes | None | Non-unique | `CLOSED`, `OPEN`, `TRIPPED`, `BYPASSED` | None | Immutable snapshot | State of primary guard interlock. |
| `alarm_status` | VARCHAR(32) | Yes | None | Non-unique | `ACTIVE`, `ACKNOWLEDGED`, `CLEARED`, `REPLAYED` | Default `ACTIVE` | State machine: ACTIVE -> ACKNOWLEDGED -> CLEARED | Current status of alarm event. |
| `source_event_id`| VARCHAR(64) | Yes | None | Non-unique | Originating PLC/edge event ID | None | Immutable | Identifier assigned at machine/edge PLC. |
| `replay_reference`| VARCHAR(64) | No | None | Non-unique | Original `alarm_event_id` if duplicate/replay | Default NULL | Evaluation provenance | Set when synthetic replay injection is active. |
| `issue_type` | VARCHAR(64) | No | None | Non-unique | `DUPLICATE_ALARM_REPLAY`, `IMPOSSIBLE_INTERLOCK_STATE`, etc. | Default NULL | Provenance | Explicit anomaly fixture marker. |
| `created_at` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | Default `CURRENT_TIMESTAMP` | Append-only | Row insertion timestamp. |

---

### G. OperatorShift (`operator_shifts`)
Records operator shift windows for plant operations without storing personal identifiable information.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `shift_id` | VARCHAR(64) | Yes | PK | Unique | e.g., `SHF-PLT01-20261022-01` | None | Permanent | Unique shift identifier. |
| `operator_code` | VARCHAR(32) | Yes | None | Non-unique | e.g., `OP-4821`, `OP-9912` | None | Anonymized | Synthetic operator code (non-PII). |
| `shift_name` | VARCHAR(64) | Yes | None | Non-unique | `MORNING`, `AFTERNOON`, `NIGHT`, `SWING` | None | Categorical | Shift rotation name. |
| `plant_id` | VARCHAR(64) | Yes | FK | Non-unique | References `plants.plant_id` | None | Immutable | Plant where shift took place. |
| `shift_start` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Immutable | Scheduled start time of shift. |
| `shift_end` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp (> shift_start) | None | Immutable | Scheduled end time of shift. |
| `status` | VARCHAR(32) | Yes | None | Non-unique | `SCHEDULED`, `ACTIVE`, `COMPLETED`, `CANCELLED` | Default `COMPLETED` | Lifecycle state | Operational shift status. |

---

### H. Acknowledgement (`acknowledgements`)
Records operator acknowledgements in response to alarm events.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `acknowledgement_id` | VARCHAR(64) | Yes | PK | Unique | `ACK-<alarm-id>-<sequence:02d>` | None | Permanent | Deterministic acknowledgement ID. |
| `alarm_event_id` | VARCHAR(64) | Yes | FK | Non-unique | References `alarm_events.alarm_event_id` | None | Immutable | The alarm being acknowledged. |
| `shift_id` | VARCHAR(64) | No | FK | Non-unique | References `operator_shifts.shift_id` | Default NULL | Contextual | The active shift when acknowledged. |
| `acknowledgement_timestamp` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Immutable | Time operator confirmed the alarm. |
| `acknowledgement_status` | VARCHAR(32) | Yes | None | Non-unique | `TIMELY`, `DELAYED`, `MISSING`, `PRE_ALARM_INVALID`, `REJECTED` | Default `TIMELY` | Derived / Validated | SLA evaluation status. |
| `response_seconds` | INTEGER | Yes | None | Non-unique | `acknowledgement_timestamp - event_timestamp` | Seconds | Derived | Time elapsed between alarm and acknowledgement. |
| `acknowledgement_channel` | VARCHAR(32) | Yes | None | Non-unique | `HMI_TOUCHPANEL`, `SCADA_CONSOLE`, `MOBILE_TABLET`, `PAGER` | Default `HMI_TOUCHPANEL` | Audit trail | Physical console used. |
| `notes` | TEXT | No | None | Non-unique | Free-form operational notes | Default NULL | Editable | Operator commentary or root-cause notes. |
| `issue_type` | VARCHAR(64) | No | None | Non-unique | `ACKNOWLEDGEMENT_BEFORE_ALARM`, etc. | Default NULL | Provenance | Marked if generated as an anomaly fixture. |

---

### I. Incident (`incidents`)
Represents an industrial safety incident, hazardous breach, emergency stop escalation, or near-miss.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `incident_id` | VARCHAR(64) | Yes | PK | Unique | `INC-2026-<sequence:06d>` | None | Permanent | Deterministic incident identifier. |
| `plant_id` | VARCHAR(64) | Yes | FK | Non-unique | References `plants.plant_id` | None | Immutable | Plant where incident occurred. |
| `machine_id` | VARCHAR(64) | Yes | FK | Non-unique | References `machines.machine_id` | None | Immutable | Machine involved in incident. |
| `safety_zone_id`| VARCHAR(64) | Yes | FK | Non-unique | References `safety_zones.safety_zone_id` | None | Immutable | Specific zone location. |
| `incident_timestamp` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | None | Immutable | Occurrence timestamp of incident. |
| `incident_type` | VARCHAR(64) | Yes | None | Non-unique | `INTERLOCK_BREACH`, `EMERGENCY_STOP_TRIP`, `NEAR_MISS`, `ALARM_SLA_BREACH`, `EQUIPMENT_FAILSAFE` | None | Categorical | Incident classification category. |
| `severity` | VARCHAR(16) | Yes | None | Non-unique | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | None | Inherent severity | Severity rating of the incident. |
| `description` | TEXT | Yes | None | Non-unique | Text | None | Detailed context | Detailed narrative of incident. |
| `triggering_alarm_event_id` | VARCHAR(64) | No | FK | Non-unique | References `alarm_events.alarm_event_id` | Default NULL | Traceability root | Alarm event that provoked the incident. |
| `detection_rule_id` | VARCHAR(64) | Yes | None | Non-unique | e.g., `RULE-001`, `RULE-007` | None | Rule audit | Business/detection rule that triggered creation. |
| `incident_status` | VARCHAR(32) | Yes | None | Non-unique | `OPEN`, `UNDER_INVESTIGATION`, `RESOLVED`, `CLOSED` | Default `OPEN` | State machine | Incident investigation status. |
| `ground_truth_label` | VARCHAR(64) | No | None | Non-unique | `INCIDENT_MISSING_TRIGGER_CONTEXT`, `LEGITIMATE`, etc. | Default NULL | Evaluation only | Controlled evaluation label. |
| `created_at` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | Default `CURRENT_TIMESTAMP` | Append-only | Record insertion time. |

---

### J. CorrectiveAction (`corrective_actions`)
Represents an action item or engineering control created to address an incident and prevent recurrence.

| Field Name | Data Type | Required? | Key | Uniqueness | Allowed Values / Format | Units / Default | Effective / Lifecycle Behavior | Description |
|---|---|---|---|---|---|---|---|---|
| `corrective_action_id` | VARCHAR(64) | Yes | PK | Unique | `ACT-<incident-id>-<sequence:02d>` | None | Permanent | Deterministic corrective action ID. |
| `incident_id` | VARCHAR(64) | Yes | FK | Non-unique | References `incidents.incident_id` | None | Immutable | Parent incident being remediated. |
| `action_type` | VARCHAR(64) | Yes | None | Non-unique | `MECHANICAL_REPAIR`, `INTERLOCK_RECALIBRATION`, `SOFTWARE_PATCH`, `SOP_RETRAINING`, `GUARD_REPLACEMENT` | None | Categorical | Remediation type. |
| `description` | TEXT | Yes | None | Non-unique | Text | None | Context | Detailed engineering action steps. |
| `assigned_team` | VARCHAR(64) | Yes | None | Non-unique | `MAINTENANCE_ELEC`, `MAINTENANCE_MECH`, `SAFETY_ENGINEERING`, `OPERATIONS` | None | Team assignment | Team responsible for remediation. |
| `created_at` | TIMESTAMP (UTC) | Yes | None | Non-unique | ISO 8601 UTC timestamp | Default `CURRENT_TIMESTAMP` | Append-only | Initiation timestamp. |
| `started_at` | TIMESTAMP (UTC) | No | None | Non-unique | ISO 8601 UTC timestamp or NULL | Default NULL | Work started | Timestamp work began. |
| `completed_at` | TIMESTAMP (UTC) | No | None | Non-unique | ISO 8601 UTC timestamp or NULL | Default NULL | Work completed | Timestamp work finished. |
| `verified_at` | TIMESTAMP (UTC) | No | None | Non-unique | ISO 8601 UTC timestamp or NULL | Default NULL | Work verified | Independent QA verification timestamp. |
| `verification_status`| VARCHAR(32) | Yes | None | Non-unique | `PENDING`, `VERIFIED`, `FAILED_VERIFICATION`, `WAIVED` | Default `PENDING` | State machine | Verification gate status. |
| `action_status` | VARCHAR(32) | Yes | None | Non-unique | `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CLOSED`, `REOPENED`, `CANCELLED` | Default `OPEN` | State machine | Overall action lifecycle status. |
| `issue_type` | VARCHAR(64) | No | None | Non-unique | `ACTION_CLOSED_WITHOUT_VERIFICATION`, etc. | Default NULL | Evaluation provenance | Marked if deliberate anomaly fixture. |

---

## 2. Auxiliary, Bridge, and History Tables

### 1. `machine_safety_zones` (Many-to-Many Bridge)
Maps machines to safety zones across time with effective dates.
* `id` (INTEGER, PK, Autoincrement)
* `machine_id` (VARCHAR(64), FK -> `machines.machine_id`, Required)
* `safety_zone_id` (VARCHAR(64), FK -> `safety_zones.safety_zone_id`, Required)
* `effective_from` (TIMESTAMP, Required)
* `effective_to` (TIMESTAMP, Nullable)
* `created_at` (TIMESTAMP, Default `CURRENT_TIMESTAMP`)

### 2. `machine_state_history` (Append-Only Event Sourcing)
Maintains high-fidelity machine operational state transitions.
* `history_id` (INTEGER, PK, Autoincrement)
* `machine_id` (VARCHAR(64), FK -> `machines.machine_id`, Required)
* `state` (VARCHAR(32), Allowed: `RUNNING`, `IDLE`, `EMERGENCY_STOP`, `MAINTENANCE`, `FAULT`, `OFFLINE`)
* `transition_timestamp` (TIMESTAMP, Required)
* `trigger_source` (VARCHAR(64), e.g. `PLC_TELEMETRY`, `OPERATOR_STOP`, `INTERLOCK_TRIP`)
* `notes` (TEXT, Nullable)

### 3. `interlock_state_history` (Append-Only Interlock Log)
Maintains physical interlock sensor state transitions.
* `history_id` (INTEGER, PK, Autoincrement)
* `interlock_id` (VARCHAR(64), FK -> `interlocks.interlock_id`, Required)
* `state` (VARCHAR(32), Allowed: `OPEN`, `CLOSED`, `TRIPPED`, `ENGAGED`, `BYPASSED`, `DISARMED`, `FAULT`)
* `transition_timestamp` (TIMESTAMP, Required)
* `trigger_event_id` (VARCHAR(64), Nullable)
* `notes` (TEXT, Nullable)

### 4. `alarm_replay_groups` (Replay Tracking)
Groups duplicate alarm events identified as telemetry replay or network loop storms.
* `group_id` (VARCHAR(64), PK)
* `original_event_id` (VARCHAR(64), FK -> `alarm_events.alarm_event_id`, Required)
* `replay_event_id` (VARCHAR(64), FK -> `alarm_events.alarm_event_id`, Required)
* `time_delta_seconds` (DOUBLE PRECISION, Required)
* `detected_at` (TIMESTAMP, Default `CURRENT_TIMESTAMP`)

### 5. `audit_logs` (System & Workflow Auditing)
Audit trail for administrative changes, rule evaluations, and manual overrides.
* `audit_id` (INTEGER, PK, Autoincrement)
* `entity_type` (VARCHAR(64), Required)
* `entity_id` (VARCHAR(64), Required)
* `action` (VARCHAR(32), e.g., `CREATE`, `UPDATE`, `STATUS_CHANGE`, `ANOMALY_OVERRIDE`)
* `actor` (VARCHAR(64), Required, e.g., `SYSTEM_ENGINE`, `OP-4821`)
* `changes_json` (TEXT, Nullable)
* `timestamp` (TIMESTAMP, Default `CURRENT_TIMESTAMP`)

### 6. `detection_rules` (Rule Metadata Catalog)
Documents active anomaly and incident detection rules.
* `rule_id` (VARCHAR(64), PK, e.g. `RULE-001`)
* `rule_name` (VARCHAR(128), Required)
* `category` (VARCHAR(64), Required)
* `description` (TEXT, Required)
* `threshold_config_json` (TEXT, Nullable)
* `is_active` (BOOLEAN, Default `TRUE`)
* `created_at` (TIMESTAMP, Default `CURRENT_TIMESTAMP`)

### 7. `data_generation_runs` (Synthetic Provenance Ledger)
Tracks deterministic generator runs, seeds, parameters, row counts, and canonical hashes.
* `run_id` (VARCHAR(64), PK)
* `seed` (INTEGER, Required)
* `profile` (VARCHAR(32), e.g., `starter`, `full`)
* `generated_at` (TIMESTAMP, Default `CURRENT_TIMESTAMP`)
* `manifest_json` (TEXT, Required)
* `canonical_checksum` (VARCHAR(64), Required)
