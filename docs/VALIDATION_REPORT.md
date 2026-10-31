# Industrial Safety Intelligence Platform - Data Validation Report

**Execution Timestamp**: 2026-10-31T10:11:08.324286 UTC
**Total Checks Run**: 18
**Passed**: 13 | **Failed / Exceptions Detected**: 5

> [!NOTE]
> In anomaly evaluation mode, checks corresponding to controlled anomaly fixtures (e.g. pre-alarm acknowledgements, impossible interlock states, missing incident contexts, replays, unverified closures) flag intentional synthetic fixture exceptions.

## Check Results Breakdown

| # | Check Name | Status | Records Evaluated | Failure / Anomaly Count | Explanation |
|---|---|---|---|---|---|
| 1 | **1. Primary-Key Uniqueness** | `PASSED` | 92168 | 0 | Verifies all database entities maintain unique, non-colliding primary key constraints. |
| 2 | **2. Foreign-Key Referential Integrity** | `PASSED` | 50060 | 0 | Ensures all child records reference valid, existing parent entities without orphaned foreign keys. |
| 3 | **3. Allowed Enum Values** | `PASSED` | 260 | 0 | Verifies status, severity, and categorical fields adhere to strict enterprise domain enums. |
| 4 | **4. Required Fields Non-Null** | `PASSED` | 50000 | 0 | Verifies non-nullable domain columns are populated with valid values. |
| 5 | **5. Machine-to-Plant Consistency** | `PASSED` | 54 | 0 | Validates that machines, safety zones, and incidents align with the correct host facility. |
| 6 | **6. Machine-to-Zone Effective Dates** | `PASSED` | 60 | 0 | Validates that effective date ranges are chronologically coherent (effective_from <= effective_to). |
| 7 | **7. Alarm-Definition Compatibility** | `PASSED` | 50000 | 0 | Verifies alarm events match the equipment machine_type defined in their alarm definition. |
| 8 | **8. Acknowledgement Chronology** | `FAILED` | 41664 | 5 | Audits that operator acknowledgement timestamps do not precede the alarm occurrence time. |
| 9 | **9. Event Occurrence vs Ingestion Timestamp** | `PASSED` | 50000 | 0 | Verifies physical event_timestamp <= received_timestamp (no negative network ingestion lag). |
| 10 | **10. State-Transition & Interlock Validity** | `FAILED` | 50000 | 5 | Checks for impossible state combinations (RUNNING while interlock is TRIPPED or OPEN). |
| 11 | **11. Incident Triggering Evidence** | `FAILED` | 54 | 4 | Validates that incidents possess an authenticated root triggering alarm event. |
| 12 | **12. Corrective-Action Verification Lifecycle** | `FAILED` | 54 | 4 | Enforces that actions marked CLOSED have successfully passed independent safety verification. |
| 13 | **13. Duplicate Event & Replay Detection** | `FAILED` | 50000 | 6 | Scans for synthetic duplicate telemetry replays with replay references. |
| 14 | **14. Derived Response-Time Reconciliation** | `PASSED` | 41664 | 0 | Verifies response_seconds matches the mathematical delta (ack_timestamp - event_timestamp). |
| 15 | **15. Deterministic Identifier Formatting** | `PASSED` | 50054 | 0 | Validates that canonical IDs conform to deterministic naming conventions. |
| 16 | **16. Cross-File & Manifest Consistency** | `PASSED` | 1 | 0 | Verifies alignment between export manifest metrics and database table counts. |
| 17 | **17. Ground-Truth Data Isolation** | `PASSED` | 2 | 0 | Guarantees ground truth labels reside strictly in data/evaluation and never in data/generated. |
| 18 | **18. Reproducible Generation Checksums** | `PASSED` | 1 | 0 | Confirms dataset generation records canonical SHA-256 content hashes. |

## Detailed Investigation Guidance

### 8. 8. Acknowledgement Chronology
- **Status**: `FAILED`
- **Affected Count**: 5
- **Sample IDs**: `ACK-ALM-MCH-18-000001-99, ACK-ALM-MCH-38-000001-99, ACK-ALM-MCH-58-000001-99, ACK-ALM-MCH-43-000001-99, ACK-ALM-MCH-03-000001-99`
- **Investigation Protocol**: In evaluation mode, negative response times match controlled ACKNOWLEDGEMENT_BEFORE_ALARM fixtures.

### 10. 10. State-Transition & Interlock Validity
- **Status**: `FAILED`
- **Affected Count**: 5
- **Sample IDs**: `ALM-MCH-01-009000, ALM-MCH-02-009001, ALM-MCH-03-009002, ALM-MCH-04-009003, ALM-MCH-05-009004`
- **Investigation Protocol**: Matches controlled IMPOSSIBLE_INTERLOCK_STATE evaluation fixtures.

### 11. 11. Incident Triggering Evidence
- **Status**: `FAILED`
- **Affected Count**: 4
- **Sample IDs**: `INC-2026-900001, INC-2026-900002, INC-2026-900003, INC-2026-900004`
- **Investigation Protocol**: Matches controlled INCIDENT_MISSING_TRIGGER_CONTEXT evaluation fixtures.

### 12. 12. Corrective-Action Verification Lifecycle
- **Status**: `FAILED`
- **Affected Count**: 4
- **Sample IDs**: `ACT-INC-2026-000001-99, ACT-INC-2026-000002-99, ACT-INC-2026-000003-99, ACT-INC-2026-000004-99`
- **Investigation Protocol**: Matches controlled ACTION_CLOSED_WITHOUT_VERIFICATION evaluation fixtures.

### 13. 13. Duplicate Event & Replay Detection
- **Status**: `FAILED`
- **Affected Count**: 6
- **Sample IDs**: `ALM-MCH-18-008000, ALM-MCH-48-008001, ALM-MCH-43-008002, ALM-MCH-13-008003, ALM-MCH-08-008004`
- **Investigation Protocol**: Matches controlled DUPLICATE_ALARM_REPLAY evaluation fixtures.
