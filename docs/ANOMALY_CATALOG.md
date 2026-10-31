# Industrial Safety Intelligence Platform - Anomaly Catalog & Fixtures

This catalog documents the controlled anomaly fixtures, detection logic, expected ground truth classifications, and advisory investigation workflows.

---

## Controlled Anomaly Fixtures Overview

The platform implements controlled anomaly injection to evaluate detection rule efficacy against deterministic ground truth. Each fixture is isolated, labeled with `issue_type` and mapped into `data/evaluation/ground_truth.csv` and `data/evaluation/ground_truth.json`.

---

## 1. `ACKNOWLEDGEMENT_BEFORE_ALARM`

| Attribute | Specification |
|---|---|
| **Affected Entity** | `acknowledgements` |
| **Identifier Format** | `ACK-<alarm-id>-<sequence:02d>` |
| **Anomaly Code** | `ACKNOWLEDGEMENT_BEFORE_ALARM` |
| **Expected Detection** | Detected by **Rule 3** (Delayed & Anomalous Acknowledgements) and **Rule 9** (Chronology). |
| **Severity Category** | `HIGH` (Data Integrity / Clock Drift) |
| **Technical Definition** | $\text{response\_seconds} = T_{ack} - T_{alarm} < 0$. Operator timestamp strictly precedes event timestamp. |
| **Injection Mechanism** | Acknowledgement is injected with $T_{ack} = T_{alarm} - \text{Uniform}(10, 120)\text{s}$. |
| **Explainable Evidence** | `response_seconds is negative (-45s). Acknowledgement timestamp 2026-10-15T08:14:15Z precedes alarm timestamp 2026-10-15T08:15:00Z.` |
| **Advisory Next Step** | Verify NTP / PTP clock synchronization between HMI terminal and SCADA event broker; inspect message queue replay buffers. |

---

## 2. `IMPOSSIBLE_INTERLOCK_STATE`

| Attribute | Specification |
|---|---|
| **Affected Entity** | `alarm_events` |
| **Identifier Format** | `ALM-<machine-id>-<sequence:06d>` |
| **Anomaly Code** | `IMPOSSIBLE_INTERLOCK_STATE` |
| **Expected Detection** | Detected by **Rule 6** (Impossible Interlock States). |
| **Severity Category** | `CRITICAL` (Mechanical Safety Violation) |
| **Technical Definition** | Machine operational state is `RUNNING` while safety interlock snapshot is `OPEN` or `TRIPPED` without an authorized bypass. |
| **Injection Mechanism** | Injected telemetry frame with `machine_state = 'RUNNING'` and `interlock_state_snapshot = 'OPEN'`. |
| **Explainable Evidence** | `Machine MCH-04 state is RUNNING while primary guard interlock LC-01 reports TRIPPED. Physical violation of guard envelope.` |
| **Advisory Next Step** | Immediately dispatch maintenance safety technician to audit interlock physical wiring, guard limit switch integrity, and PLC safe input card channels. |

---

## 3. `INCIDENT_MISSING_TRIGGER_CONTEXT`

| Attribute | Specification |
|---|---|
| **Affected Entity** | `incidents` |
| **Identifier Format** | `INC-2026-<sequence:06d>` |
| **Anomaly Code** | `INCIDENT_MISSING_TRIGGER_CONTEXT` |
| **Expected Detection** | Detected by **Rule 7** (Incident Context Validation) and **Rule 10** (Traceability). |
| **Severity Category** | `MEDIUM` (Traceability Gap / Telemetry Loss) |
| **Technical Definition** | Incident record exists with `triggering_alarm_event_id = NULL` and zero preceding alarm events or machine state trips on that machine within $\pm 30$ minutes. |
| **Injection Mechanism** | Generated incident record on a machine with empty alarm history in the incident window. |
| **Explainable Evidence** | `Incident INC-2026-000012 has no triggering alarm link and no anomalous machine state transitions within 30 minutes of occurrence.` |
| **Advisory Next Step** | Interview shift supervisor for manual incident entry context; verify field gateway logger uptime during the incident window. |

---

## 4. `DUPLICATE_ALARM_REPLAY`

| Attribute | Specification |
|---|---|
| **Affected Entity** | `alarm_events` |
| **Identifier Format** | `ALM-<machine-id>-<sequence:06d>` |
| **Anomaly Code** | `DUPLICATE_ALARM_REPLAY` |
| **Expected Detection** | Detected by **Rule 4** (Alarm Flood & Duplicate Replay). |
| **Severity Category** | `LOW` to `MEDIUM` (Network Replay / Duplicate Telemetry) |
| **Technical Definition** | Multiple alarm event records share identical `source_event_id`, machine, and alarm definition with $0 \le \Delta t \le 1.0 \text{ sec}$ and non-null `replay_reference`. |
| **Injection Mechanism** | Synthetic event duplicated with a 0.2s timestamp offset and pointing to the parent event via `replay_reference`. |
| **Explainable Evidence** | `Alarm ALM-MCH02-000142 is an exact duplicate of ALM-MCH02-000141 with identical source_event_id SRC-9941 within 0.2s window.` |
| **Advisory Next Step** | Check MQTT/AMQP broker deduplication policies and inspect edge PLC retry queues for message looping. |

---

## 5. `ACTION_CLOSED_WITHOUT_VERIFICATION`

| Attribute | Specification |
|---|---|
| **Affected Entity** | `corrective_actions` |
| **Identifier Format** | `ACT-<incident-id>-<sequence:02d>` |
| **Anomaly Code** | `ACTION_CLOSED_WITHOUT_VERIFICATION` |
| **Expected Detection** | Detected by **Rule 8** (Corrective-Action Verification Lifecycle). |
| **Severity Category** | `HIGH` (Compliance / Quality Management Failure) |
| **Technical Definition** | Corrective action record has `action_status = 'CLOSED'` but `verification_status != 'VERIFIED'` or `verified_at IS NULL`. |
| **Injection Mechanism** | Generated action record set to `action_status = 'CLOSED'` with `verification_status = 'PENDING'` and `verified_at = NULL`. |
| **Explainable Evidence** | `Corrective action ACT-INC001-01 has status CLOSED, but verification_status is PENDING and verified_at is empty.` |
| **Advisory Next Step** | Reopen corrective action; notify plant EHS quality director for mandatory on-site physical inspection before re-closing. |
