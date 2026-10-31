# Industrial Safety Intelligence Platform - API Documentation

The platform provides a comprehensive RESTful API built on FastAPI with OpenAPI 3.1.0 specifications, Pydantic validation, and transactional database integrity.

Base URL: `http://localhost:8000/api`
Interactive Swagger UI: `http://localhost:8000/docs`
ReDoc Documentation: `http://localhost:8000/redoc`

---

## 1. Health & System Status

### `GET /api/health`
Returns system liveness, backend version, UTC timestamp, and database connectivity status.

**Response (200 OK):**
```json
{
  "status": "UP",
  "service": "Industrial Safety Event Intelligence Platform",
  "timestamp": "2026-10-31T07:45:00.123456Z",
  "database": "HEALTHY"
}
```

---

## 2. Executive Overview

### `GET /api/overview`
Aggregates enterprise KPI statistics, severity distributions, temporal alarm trends, incident distributions by facility, and top repeated-condition machines.

**Query Parameters:**
* `plant_id` (optional): Filter metrics by plant identifier.
* `date_from` (optional): ISO 8601 UTC start datetime.
* `date_to` (optional): ISO 8601 UTC end datetime.

**Response (200 OK):**
```json
{
  "total_plants": 4,
  "total_machines": 12,
  "total_alarms": 2411,
  "critical_and_high_alarms": 482,
  "open_incidents": 17,
  "delayed_acknowledgements": 340,
  "repeated_unsafe_clusters": 3,
  "unverified_actions": 4,
  "data_quality_exceptions": 24,
  "alarms_by_severity": { "CRITICAL": 240, "HIGH": 242, "MEDIUM": 720, "LOW": 710, "INFO": 499 },
  "alarms_trend": [ { "date": "2026-10-01", "count": 172 }, { "date": "2026-10-02", "count": 185 } ],
  "incidents_by_plant": [ { "plant_name": "Detroit Assembly Center", "count": 9 } ],
  "top_unsafe_machines": [ ... ],
  "recent_critical_events": [ ... ]
}
```

---

## 3. Plant & Machine Explorer

### `GET /api/plants`
Retrieves all physical plant facilities with machine counts and active zone counts.

### `GET /api/machines`
Searchable and filterable machine inventory.
* Query Parameters: `plant_id`, `machine_type`, `status`, `search`, `page`, `page_size`.

### `GET /api/machines/{machine_id}`
Returns complete machine profile, assigned safety zones, interlock hardware array, and recent append-only machine state transition logs.

### `GET /api/safety-zones`
Retrieves safety perimeters filtered by `plant_id` or `risk_level`.

---

## 4. Alarm Explorer

### `GET /api/alarms`
Paginated search over historical and live alarm telemetry.
* Query Parameters:
  * `plant_id`, `machine_id`, `safety_zone_id`
  * `severity`: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
  * `alarm_status`: `ACTIVE`, `ACKNOWLEDGED`, `CLEARED`, `REPLAYED`
  * `anomaly_only`: `true` to filter for events with anomaly tags or impossible interlock states
  * `date_from`, `date_to`
  * `sort_by`, `order`
  * `page`, `page_size`

### `GET /api/alarms/{alarm_event_id}`
Returns full alarm telemetry context, matching alarm definition, physical interlock snapshot, and operator acknowledgement response records.

---

## 5. Incident Intelligence & Traceability

### `GET /api/incidents`
Paginated incident list with status, severity, machine, plant, and corrective action count.

### `GET /api/incidents/{incident_id}`
Detailed incident profile with triggering alarm linkage and classification rule.

### `GET /api/incidents/{incident_id}/timeline`
Generates end-to-end incident traceability graph.
Returns:
* `incident`: Core incident details.
* `timeline`: Chronologically ordered list of graph nodes:
  * `FACILITY_CONTEXT`
  * `MACHINE_STATE`
  * `INTERLOCK_STATE`
  * `ALARM`
  * `ACKNOWLEDGEMENT`
  * `INCIDENT`
  * `ACTION`
  * `VERIFICATION`
  * `GAP_TRIGGER` / `GAP_VERIFICATION` (Explicit missing context nodes)
* `traceability_complete`: Boolean flag.
* `missing_evidence_reasons`: Array of human-readable explanation strings citing specific missing records.

---

## 6. Anomaly Center

### `GET /api/anomalies`
Runs the unified detection pipeline and returns prioritized anomalies.
* Filter by `anomaly_type`, `severity`.
* Each item includes `anomaly_id`, `anomaly_type`, `entity_type`, `entity_id`, `severity`, `detected_at`, `rule_id`, `explanation`, `evidence`, `related_records`, and `advisory_recommendation`.

---

## 7. Corrective Actions Lifecycle

### `GET /api/corrective-actions`
Filterable action log by `incident_id`, `action_status`, `verification_status`.

### `PATCH /api/corrective-actions/{action_id}`
Permitted workflow state transition endpoint with verification gate validation and audit logging.
* Rejects transition to `CLOSED` with HTTP 422 if `verification_status != 'VERIFIED'`.
* Body:
```json
{
  "action_status": "COMPLETED",
  "actor": "QA_AUDITOR_12",
  "notes": "Guards inspected and physical torque verified."
}
```

### `POST /api/corrective-actions/{action_id}/verify`
Independent safety auditor sign-off. Sets `verification_status = 'VERIFIED'`, `action_status = 'CLOSED'`, `verified_at = CURRENT_TIMESTAMP`, and writes to `audit_logs`.

---

## 8. Data Quality & Evaluation

### `GET /api/data-quality` & `POST /api/validate`
Executes all 18 automated data quality checks and returns pass/fail status, records evaluated, exception counts, sample IDs, and investigation protocols.

### `GET /api/metrics/evaluation`
Compares engine predictions against isolated `data/evaluation/ground_truth.csv`. Returns TP, FP, FN, precision, recall, F1 score, and per-category breakdown.

---

## 9. Data Generation & Export

### `GET /api/generation-runs`
Returns history of deterministic generator runs, seeds, profiles, and canonical checksums.

### `POST /api/generate-data`
Executes synthetic data generator on demand.
```json
{
  "seed": 20261022,
  "profile": "starter"
}
```

### `GET /api/export/{entity}?format=csv|json`
Streams CSV or JSON export for `plants`, `machines`, `safety-zones`, `interlocks`, `alarm-definitions`, `alarms`, `acknowledgements`, `incidents`, `corrective-actions`.

### `GET /api/export/manifest`
Returns canonical dataset origin manifest.

### `GET /api/export/evaluation/ground-truth?format=csv|json`
Downloads ground truth dataset isolated in `data/evaluation/` (clearly tagged as evaluation only).
