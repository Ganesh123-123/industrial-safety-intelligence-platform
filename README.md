# Industrial Safety Event Analysis & Incident Intelligence Platform

An enterprise-grade, decision-support industrial safety intelligence platform built to monitor machine operational states, detect hazardous condition clusters, audit operator acknowledgement SLAs, evaluate safety interlock compatibility, track remediation lifecycles, and benchmark anomaly detection algorithms against isolated deterministic ground truth.

> [!CAUTION]
> **Industrial Decision-Support Notice**:
> This platform is an analytical, decision-support, and synthetic data evaluation platform. It does not replace certified industrial functional safety systems (e.g., SIL 3 / PLe compliant controllers, safety PLCs, ISO 13849/IEC 62061 equipment). Scores are synthetic priority ratings and must never be wired as physical automated interlock controls.

---

## 1. Architecture & Technology Stack

* **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React icons, Recharts visualizations.
* **Backend**: Python 3.14 / 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic database migrations.
* **Database**: SQLite (default zero-friction local development) & PostgreSQL 16 (production container support via `DATABASE_URL`).
* **Data Engineering & Science**: Pandas, NumPy, deterministic pseudo-random generators, SHA-256 canonical hashing.
* **Validation & QA**: Pytest, 18-point automated integrity framework, empirical evaluation engine.

---

## 2. Core Entities & Database Design

1. **`Plant`**: Monitored industrial facility containing machines and safety perimeters.
2. **`Machine`**: Industrial unit (Stamping Press, Robotic Welder, Conveyor, CNC Mill, Chemical Reactor).
3. **`SafetyZone`**: Physical or optical risk perimeter (e.g. Light curtain zone, press lane).
4. **`MachineSafetyZone`**: Temporal many-to-many bridge mapping machines to active safety zones.
5. **`Interlock`**: Electromechanical safety devices (Light Curtain, Guard Door Switch, E-Stop Button, Pressure Mat).
6. **`AlarmDefinition`**: Alarm criteria, severity (`INFO` to `CRITICAL`), and acknowledgement SLA targets.
7. **`OperatorShift`**: Synthetic operator shift schedule rotation (anonymized, non-PII).
8. **`AlarmEvent`**: Deterministic telemetry record (`ALM-<machine-id>-<sequence:06d>`).
9. **`Acknowledgement`**: Operator alarm acknowledgement (`ACK-<alarm-id>-01`), response duration, and SLA status.
10. **`Incident`**: Documented safety incident or near-miss (`INC-2026-<sequence:06d>`).
11. **`CorrectiveAction`**: Remediation engineering control (`ACT-<incident-id>-01`) with mandatory verification gates.
12. **`MachineStateHistory` & `InterlockStateHistory`**: Append-only event logs for temporal reconstruction.
13. **`AlarmReplayGroup`**: Telemetry replay cluster tracking.
14. **`AuditLog`**: System & operator workflow audit trail.
15. **`DetectionRule`**: Active rule definitions and parameters.
16. **`DataGenerationRun`**: Provenance ledger with seeds and canonical hashes.

---

## 3. Business Logic & Detection Rules

* **Rule 1: Repeated Unsafe Conditions**: Computes an explainable hazard score $S \in [0, 100]$ based on critical alarms, high alarms, interlock breaches, and SLA overages.
* **Rule 2: Severity Prioritization**: Multi-factor urgency triage ranking alarms by machine state, interlock breaches, and active incidents.
* **Rule 3: Delayed Acknowledgements**: Tracks response seconds against alarm definition SLAs; flags missing, delayed, and pre-alarm anomalies.
* **Rule 4: Alarm Flood & Duplicate Replay**: Detects bursts of alarms exceeding cognitive thresholds and flags duplicate telemetry without dropping data.
* **Rule 5: Nuisance Alarm Clusters**: Heuristic identification of chattering alarms that clear quickly without mechanical escalation.
* **Rule 6: Impossible Interlock States**: Validates machine operational state against physical guard sensor states (flags `RUNNING` + `TRIPPED`).
* **Rule 7: Incident Context Validation**: Verifies that incidents are backed by authentic triggering alarms and machine state history.
* **Rule 8: Corrective-Action Verification**: Enforces the quality lifecycle (`OPEN` $\to$ `IN_PROGRESS` $\to$ `COMPLETED` $\to$ `VERIFIED` $\to$ `CLOSED`); rejects closures without independent sign-off.
* **Rule 9: Event Ordering & Chronology**: Validates event timestamp monotonic sequences and non-negative ingestion lag.
* **Rule 10: End-to-End Traceability**: Traverses and renders full graph from Plant $\to$ Machine $\to$ Interlock $\to$ Alarm $\to$ Ack $\to$ Incident $\to$ Action $\to$ Verification, displaying explicit gap notices for missing links.

---

## 4. Controlled Anomaly Scenarios & Evaluation

The generator injects 5 controlled anomaly fixture categories with strictly isolated ground truth:
1. `ACKNOWLEDGEMENT_BEFORE_ALARM`
2. `IMPOSSIBLE_INTERLOCK_STATE`
3. `INCIDENT_MISSING_TRIGGER_CONTEXT`
4. `DUPLICATE_ALARM_REPLAY`
5. `ACTION_CLOSED_WITHOUT_VERIFICATION`

### Ground Truth Isolation Guarantee
Ground-truth labels are stored exclusively in `data/evaluation/ground_truth.csv` and `data/evaluation/ground_truth.json`. The detection engine **never reads** ground-truth files during evaluation.

### Empirical Evaluation Results
```
Overall Precision : 100.00%
Overall Recall    : 100.00%
Overall F1 Score  : 100.00%
```

---

## 5. Quick Start Guide

### Prerequisites
* Python 3.11+ (tested on Python 3.14)
* Node.js 18+ (tested on Node.js v24.15.0)

### 1. Setup & Dependencies
```bash
# Backend dependencies
python -m pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Generate Deterministic Synthetic Data

The platform includes a shared, parameterized synthetic generator supporting both **starter** (development) and **full** (enterprise benchmark) profiles using the fixed random seed `20261022`.

* **Starter profile** (~2,500 alarms, 12 machines, 4 plants, 40 definitions, 14 days):
  ```bash
  python scripts/generate_data.py --profile starter
  ```

* **Full enterprise profile** (exactly 50,000 alarms, 60 machines, 4 plants, 200 alarm definitions, 30 days):
  ```bash
  python scripts/generate_data.py --profile full
  ```
  When the canonical full dataset is already present and its event references are valid, rerunning this command refreshes the 200 alarm definitions in place and preserves the existing 50,000 alarm-event rows. If the existing dataset is incomplete or incompatible, the generator falls back to its deterministic full-dataset rebuild.

* **Custom seed & event count options**:
  ```bash
  python scripts/generate_data.py --profile full --seed 20261022 --events 50000
  ```

#### Generation Data Flow & Dependency Order
Records are generated and inserted in strict parent-child dependency order:
1. `plants` (4 industrial facilities)
2. `machines` (60 industrial units across 5 equipment classes)
3. `safety_zones` (12 physical/optical perimeters)
4. `interlocks` (120 electromechanical safety devices)
5. `machine_safety_zones` (temporal zone assignments)
6. `alarm_definitions` (200 alarm criteria and SLA definitions)
7. `operator_shifts` (360 8-hour shift rotations)
8. `machine_state_histories` & `interlock_state_histories` (temporal telemetry logs across 30 days)
9. `alarm_events` (exactly 50,000 alarm telemetry records including floods and nuisance clusters)
10. `acknowledgements` (operator responses with SLA reconciliation)
11. `incidents` (genuine safety incidents + 4 isolated context gap fixtures)
12. `corrective_actions` (remediation lifecycle + 4 isolated unverified gate fixtures)
13. `audit_logs` & `data_generation_runs` (system audit trail and provenance ledger)

Output locations:
* Database: `industrial_safety.db` (SQLite)
* CSV Exports & Manifest: `data/generated/` (`plants.csv`, `machines.csv`, `alarm_events.csv`, `manifest.json`, etc.)
* Isolated Ground Truth: `data/evaluation/` (`ground_truth.csv`, `ground_truth.json`)

### 3. Run Validation & Evaluation
```bash
# Run 18-point automated validation framework
python scripts/validate_data.py

# Evaluate detection against isolated ground truth
python scripts/evaluate_detection.py

# Verify 100% deterministic reproducibility across runs
python scripts/compare_checksums.py --profile starter
python scripts/compare_checksums.py --profile full
```

### 4. Run Automated Pytest Suite
```bash
python -m pytest -v
```

### 5. Launch the Platform
In Terminal 1 (Start FastAPI Backend):
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

In Terminal 2 (Start Vite React Frontend):
```bash
cd frontend
npm run dev
```

* **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
* **Backend API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 6. Project Deliverables

* `docs/DATA_DICTIONARY.md`: Complete field-level schema dictionary.
* `docs/ENTITY_RELATIONSHIPS.md`: Mermaid ER diagram, cardinalities, indexes.
* `docs/BUSINESS_RULES.md`: Mathematical scoring formulas and lifecycle rules.
* `docs/ANOMALY_CATALOG.md`: Catalog of all controlled anomaly fixtures and advisory actions.
* `docs/API_DOCUMENTATION.md`: REST endpoints and payload specifications.
* `docs/VALIDATION_REPORT.md`: Latest 18-point data quality report.
* `scripts/generate_data.py`: Deterministic data generator.
* `scripts/validate_data.py`: Validation runner.
* `scripts/evaluate_detection.py`: Evaluation benchmark runner.
* `scripts/compare_checksums.py`: Reproducibility auditor.
* `data/generated/`: CSV data exports and `manifest.json`.
* `data/evaluation/`: Isolated `ground_truth.csv` and `ground_truth.json`.


7. AI-Assisted Development and Transparency

AI-assisted development tools, including Antigravity, were used to support project implementation, code review, debugging, and documentation where applicable.

AI assistance was used to help with:

Reviewing the project architecture and database relationships.
Developing and refining synthetic data generation requirements.
Reviewing anomaly-detection logic and evaluation workflows.
Improving validation procedures, documentation, and setup instructions.

AI-generated suggestions are not treated as proof of correctness. Implementation details and test results must be verified against the actual repository.

The project submission should include representative prompts, the changes retained after review, the verification performed, and any remaining limitations.

See docs/AI_USAGE.md for the prompt history and development review record.


8. Developer Contributions and Review

The project brings together synthetic industrial telemetry, relational data modelling, anomaly detection, data validation, and a dashboard for safety-event analysis.

My development and review responsibilities for this project include the tasks I personally performed, such as:

Reviewing database entities and relationships.
Working with deterministic data-generation requirements.
Reviewing anomaly scenarios and traceability requirements.
Checking application behaviour and documenting observed issues.
Reviewing test results and updating documentation to reflect verified functionality.

AI-assisted implementation was reviewed against project requirements wherever verification was performed. Features and results that have not been independently verified are documented as pending verification.

9. Design Decisions and Trade-offs
SQLite for local development: Supports a straightforward local setup without requiring a separate database server.
PostgreSQL support: Provides an alternative database backend where the implemented configuration supports it.
Deterministic synthetic data: A fixed random seed supports repeatable dataset generation and controlled evaluation.
Isolated evaluation ground truth: Separating labels from detection inputs helps reduce the risk of evaluation leakage.
Rule-based anomaly detection: Provides interpretable detection logic that can be inspected and tested.
Decision-support approach: The platform provides analytical findings for review rather than directly controlling physical industrial safety equipment.
