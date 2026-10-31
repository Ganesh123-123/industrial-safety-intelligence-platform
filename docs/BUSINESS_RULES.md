# Industrial Safety Intelligence Platform - Business Rules & Detection Logic

This document specifies the business rules, anomaly heuristics, scoring formulas, and lifecycle validations enforced by the platform.

> [!CAUTION]
> **Decision-Support Notice**: This platform is an analytical, decision-support, and synthetic data evaluation platform. It does not replace certified industrial functional safety systems (e.g. SIL 3 / PLe compliant controllers, safety PLCs, ISO 13849/IEC 62061 equipment). Scores are synthetic priority ratings and must not be used as physical automated interlock controls.

---

## Rule 1: Repeated Unsafe Conditions

### Purpose
Identify recurring unsafe patterns across machines, safety zones, and interlocks within a moving time window to catch systemic hazards before severe incidents occur.

### Evaluation Criteria
A machine or safety zone is evaluated across a sliding window (default: 72 hours). The engine counts occurrences of:
1. Hazardous machine states (`EMERGENCY_STOP`, `FAULT`, `UNGUARDED_RUNNING`).
2. Interlock violations (`TRIPPED`, `OPEN` while machine is running).
3. High or Critical alarm triggers from the same alarm definition.

### Repeated Condition Score Formula
The explainable repeated-condition score $S_{ruc} \in [0, 100]$ is computed as:
$$S_{ruc} = \min\left(100, \, \left(N_{crit} \times 25\right) + \left(N_{high} \times 15\right) + \left(N_{med} \times 5\right) + \left(N_{viol} \times 20\right) + \left(D_{avg\_sla} \times 0.1\right)\right)$$
Where:
* $N_{crit}, N_{high}, N_{med}$ = Count of critical, high, and medium severity alarms in window.
* $N_{viol}$ = Count of interlock state violations in window.
* $D_{avg\_sla}$ = Average acknowledgement delay beyond SLA in seconds (capped at 100s).

### Limitations
This score relies on sensor event frequency and telemetry accuracy. Sensor packet loss or intermittent network disconnections can artificially deflate the score.

---

## Rule 2: Severity Prioritization

### Purpose
Sort and prioritize alarms and operational triage based on multi-factor risk instead of flat severity strings alone.

### Multi-Factor Priority Score Formula
$$\text{Priority Score} = \text{Base}(\text{Severity}) + \text{StateMultiplier} + \text{InterlockPenalty} + \text{SLAPenalty} + \text{IncidentLinkage}$$
* **Base Severity**: `CRITICAL` = 1000, `HIGH` = 500, `MEDIUM` = 200, `LOW` = 50, `INFO` = 10.
* **State Multiplier**: +300 if machine state is `EMERGENCY_STOP` or `FAULT`.
* **Interlock Penalty**: +400 if current interlock state is `TRIPPED`, `OPEN`, or `BYPASSED`.
* **SLA Penalty**: +150 if acknowledgement SLA is currently breached.
* **Incident Linkage**: +250 if alarm triggered an active open incident.

---

## Rule 3: Delayed & Anomalous Acknowledgements

### Purpose
Track operator response against configured alarm definition SLAs and flag non-compliant or physically impossible responses.

### Calculations
$$\text{response\_seconds} = \text{epoch}(\text{acknowledgement\_timestamp}) - \text{epoch}(\text{event\_timestamp})$$

### Classification
1. **TIMELY**: $0 \le \text{response\_seconds} \le \text{acknowledgement\_sla\_seconds}$.
2. **DELAYED**: $\text{response\_seconds} > \text{acknowledgement\_sla\_seconds}$.
3. **MISSING**: No acknowledgement recorded AND current system time $> (\text{event\_timestamp} + \text{acknowledgement\_sla\_seconds})$.
4. **NOT_YET_DUE**: No acknowledgement recorded BUT current system time $\le (\text{event\_timestamp} + \text{acknowledgement\_sla\_seconds})$.
5. **ACKNOWLEDGEMENT_BEFORE_ALARM (Anomaly)**: $\text{response\_seconds} < 0$. Indicates clock desynchronization or synthetic/telemetry injection error.

---

## Rule 4: Alarm Flood & Duplicate Replay Detection

### Purpose
Identify bursts of alarm storms that overwhelm operator cognitive capacity (per ISA-18.2 / IEC 62682 standards) and detect synthetic telemetry loops.

### Flood Detection Criteria
* **Threshold**: $\ge 10$ alarms per machine within a 10-minute window (or $\ge 20$ alarms across a plant in 10 minutes).
* **Severity Distribution**: Evaluates whether flood is dominated by nuisance warnings or cascading trips.

### Duplicate Replay Detection Criteria
* Event shares identical `source_event_id` or identical `(machine_id, alarm_definition_id, machine_state)` within a tight time window ($\Delta t \le 1.0 \text{ sec}$) with a non-null `replay_reference`.
* **Policy**: Replayed events are **never deleted**. They are preserved in `alarm_events` and flagged with `issue_type = 'DUPLICATE_ALARM_REPLAY'` and linked into `alarm_replay_groups`.

---

## Rule 5: Nuisance Alarm Clusters

### Purpose
Detect chattering or fleeting alarms that trigger repeatedly without operator intervention or mechanical necessity.

### Heuristic Rules
* An alarm is flagged as a **Nuisance Alarm Cluster** if:
  1. The same `(machine_id, alarm_definition_id)` triggers $\ge 5$ times in a 30-minute window.
  2. Each occurrence clears or resets within 120 seconds.
  3. No corresponding incident or machine state change (`FAULT`, `EMERGENCY_STOP`) was initiated.
* Provides clear explainability citing event IDs, recurrence intervals, and lack of mechanical escalation.

---

## Rule 6: Impossible Interlock States

### Purpose
Detect physically impossible combinations of machine operating state and safety interlock state.

### Compatibility Matrix

| Machine Operational State | Interlock Physical State | Permitted? | Condition Classification |
|---|---|---|---|
| `RUNNING` | `CLOSED` / `ENGAGED` / `ARMED` | YES | Normal Operation |
| `RUNNING` | `OPEN` / `TRIPPED` | **NO** | **IMPOSSIBLE_INTERLOCK_STATE (Critical Hazard)** |
| `RUNNING` | `BYPASSED` | Exception | Requires active verified safety bypass permit |
| `IDLE` | `OPEN` / `CLOSED` / `TRIPPED` | YES | Standby mode |
| `EMERGENCY_STOP` | `OPEN` / `TRIPPED` / `CLOSED` | YES | Safe shutdown reached |
| `MAINTENANCE` | `OPEN` / `BYPASSED` / `TRIPPED` | YES | Controlled maintenance mode |

When detected, the event is flagged with `issue_type = 'IMPOSSIBLE_INTERLOCK_STATE'`. The physical record is never silently rewritten.

---

## Rule 7: Incident Context Validation

### Purpose
Verify that every logged incident is supported by documented physical telemetry and triggering alarm evidence.

### Validation Rules
1. **Missing Triggering Alarm**: Incident lacks `triggering_alarm_event_id` and has no alarms recorded on that machine within $\pm 15$ minutes.
2. **Missing State History**: Machine has no corresponding state transition within 1 hour preceding incident.
3. **Timestamp Inconsistency**: `incident_timestamp` precedes the triggering alarm timestamp or is in the future.
4. **Relational Mismatch**: Machine does not belong to the incident's plant, or safety zone does not map to the machine.

Distinguishes between *missing evidence* (data ingestion gap) versus *invalid incident* (bogus synthetic or manual record).

---

## Rule 8: Corrective-Action Verification Lifecycle

### Purpose
Ensure all corrective actions follow an immutable quality lifecycle and prevent unverified closures.

### Permitted State Transitions
$$\text{OPEN} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{COMPLETED} \longrightarrow \text{VERIFIED} \longrightarrow \text{CLOSED}$$

* **Verification Gate**: An action **CANNOT** transition to `CLOSED` or `VERIFIED` without:
  1. `completed_at` is non-null and $\le \text{verified\_at}$.
  2. `verified_at` is non-null.
  3. `verification_status` is explicitly set to `VERIFIED` by an authorized safety auditor.
* **Anomaly Flag**: Any action found with `action_status = 'CLOSED'` but `verification_status != 'VERIFIED'` or null `verified_at` is flagged as `ACTION_CLOSED_WITHOUT_VERIFICATION`.

---

## Rule 9: Event Ordering and Chronology Validation

### Rules
1. $T_{event} \le T_{received}$ (No negative ingestion lag).
2. For each machine, `event_sequence` must be strictly monotonically increasing with time: $T(Seq_{k}) \ge T(Seq_{k-1})$.
3. $T_{alarm} \le T_{ack}$ (Acknowledgement cannot occur before alarm event).
4. $T_{incident} \ge T_{triggering\_alarm} - 60s$ (Incident cannot predate trigger).
5. $T_{created} \le T_{started} \le T_{completed} \le T_{verified}$ for corrective actions.

---

## Rule 10: End-to-End Traceability

### Traceability Graph
For any incident, the engine traverses and constructs the following graph:
$$\text{Plant} \to \text{Machine} \to \text{Safety Zone} \to \text{MachineStateHistory} \to \text{InterlockStateHistory} \to \text{AlarmEvent} \to \text{Acknowledgement} \to \text{Incident} \to \text{CorrectiveAction} \to \text{Verification}$$

Missing nodes are represented as **explicit gap indicators** in the UI and API response, never as fabricated dummy objects.
