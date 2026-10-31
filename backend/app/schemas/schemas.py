from datetime import datetime
from typing import Optional, List, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# Plant
class PlantBase(BaseModel):
    plant_id: str
    plant_code: str
    plant_name: str
    location: str
    timezone: str
    status: str

class PlantResponse(PlantBase):
    created_at: datetime
    machine_count: Optional[int] = 0
    zone_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Machine
class MachineBase(BaseModel):
    machine_id: str
    plant_id: str
    machine_code: str
    machine_name: str
    machine_type: str
    operational_status: str
    commissioned_at: datetime
    retired_at: Optional[datetime] = None

class MachineResponse(MachineBase):
    created_at: datetime
    plant_name: Optional[str] = None
    active_alarms_count: Optional[int] = 0
    repeated_condition_score: Optional[float] = 0.0

    class Config:
        from_attributes = True

# SafetyZone
class SafetyZoneBase(BaseModel):
    safety_zone_id: str
    plant_id: str
    zone_code: str
    zone_name: str
    risk_level: str
    description: Optional[str] = None
    effective_from: datetime
    effective_to: Optional[datetime] = None
    status: str

class SafetyZoneResponse(SafetyZoneBase):
    class Config:
        from_attributes = True

# Interlock
class InterlockResponse(BaseModel):
    interlock_id: str
    machine_id: str
    interlock_code: str
    interlock_name: str
    interlock_type: str
    expected_safe_state: str
    current_state: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True

# AlarmDefinition
class AlarmDefinitionResponse(BaseModel):
    alarm_definition_id: str
    alarm_code: str
    machine_type: str
    alarm_name: str
    description: Optional[str] = None
    severity: str
    acknowledgement_required: bool
    acknowledgement_sla_seconds: int
    expected_interlock_state: Optional[str] = None
    active_from: datetime
    active_to: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True

# Acknowledgement
class AcknowledgementResponse(BaseModel):
    acknowledgement_id: str
    alarm_event_id: str
    shift_id: Optional[str] = None
    acknowledgement_timestamp: datetime
    acknowledgement_status: str
    response_seconds: int
    acknowledgement_channel: str
    notes: Optional[str] = None
    issue_type: Optional[str] = None

    class Config:
        from_attributes = True

# AlarmEvent
class AlarmEventResponse(BaseModel):
    alarm_event_id: str
    machine_id: str
    alarm_definition_id: str
    safety_zone_id: Optional[str] = None
    event_timestamp: datetime
    received_timestamp: datetime
    event_sequence: int
    machine_state: str
    interlock_state_snapshot: str
    alarm_status: str
    source_event_id: str
    replay_reference: Optional[str] = None
    issue_type: Optional[str] = None
    created_at: datetime
    
    # Enrichment fields
    severity: Optional[str] = None
    alarm_name: Optional[str] = None
    plant_id: Optional[str] = None
    acknowledgement: Optional[AcknowledgementResponse] = None

    class Config:
        from_attributes = True

# Incident
class IncidentResponse(BaseModel):
    incident_id: str
    plant_id: str
    machine_id: str
    safety_zone_id: str
    incident_timestamp: datetime
    incident_type: str
    severity: str
    description: str
    triggering_alarm_event_id: Optional[str] = None
    detection_rule_id: str
    incident_status: str
    ground_truth_label: Optional[str] = None
    created_at: datetime

    # Enrichment fields
    plant_name: Optional[str] = None
    machine_code: Optional[str] = None
    zone_code: Optional[str] = None
    corrective_actions_count: Optional[int] = 0

    class Config:
        from_attributes = True

# CorrectiveAction
class CorrectiveActionResponse(BaseModel):
    corrective_action_id: str
    incident_id: str
    action_type: str
    description: str
    assigned_team: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verification_status: str
    action_status: str
    issue_type: Optional[str] = None

    class Config:
        from_attributes = True

class CorrectiveActionUpdate(BaseModel):
    action_status: Optional[str] = None
    verification_status: Optional[str] = None
    actor: str = "SAFETY_AUDITOR"
    notes: Optional[str] = None

# Anomaly Item
class AnomalyItem(BaseModel):
    anomaly_id: str
    anomaly_type: str
    entity_type: str
    entity_id: str
    severity: str
    detected_at: datetime
    rule_id: str
    explanation: str
    evidence: Dict[str, Any]
    related_records: List[str]
    advisory_recommendation: str

# Incident Timeline Node
class IncidentTimelineNode(BaseModel):
    node_id: str
    timestamp: datetime
    node_type: str  # MACHINE_STATE, INTERLOCK_STATE, ALARM, ACKNOWLEDGEMENT, INCIDENT, ACTION, VERIFICATION
    title: str
    description: str
    severity: Optional[str] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = {}
    is_gap: bool = False

class IncidentTimelineResponse(BaseModel):
    incident: IncidentResponse
    timeline: List[IncidentTimelineNode]
    traceability_complete: bool
    missing_evidence_reasons: List[str]

# Repeated Condition Score
class RepeatedConditionScore(BaseModel):
    machine_id: str
    plant_id: str
    machine_code: str
    score: float
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    critical_alarms_count: int
    high_alarms_count: int
    interlock_violations_count: int
    avg_acknowledgement_delay_seconds: float
    explanation: str

# Overview Metrics
class OverviewMetrics(BaseModel):
    total_plants: int
    total_machines: int
    total_alarms: int
    critical_and_high_alarms: int
    open_incidents: int
    delayed_acknowledgements: int
    repeated_unsafe_clusters: int
    unverified_actions: int
    data_quality_exceptions: int
    alarms_by_severity: Dict[str, int]
    alarms_trend: List[Dict[str, Any]]
    incidents_by_plant: List[Dict[str, Any]]
    top_unsafe_machines: List[RepeatedConditionScore]
    recent_critical_events: List[AlarmEventResponse]

# Validation
class ValidationCheckItem(BaseModel):
    check_name: str
    status: str  # PASSED, FAILED
    records_checked: int
    failure_count: int
    example_affected_ids: List[str]
    explanation: str
    suggested_investigation: str

class ValidationReport(BaseModel):
    total_checks: int
    passed_checks: int
    failed_checks: int
    generated_at: datetime
    checks: List[ValidationCheckItem]

# Evaluation Metrics
class EvaluationMetricCategory(BaseModel):
    anomaly_type: str
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    detection_rate: float
    total_ground_truth: int

class EvaluationReport(BaseModel):
    overall_precision: float
    overall_recall: float
    overall_f1: float
    overall_detection_rate: float
    total_ground_truth_anomalies: int
    total_detected_anomalies: int
    categories: List[EvaluationMetricCategory]
    zero_division_policy: str = "Returns 0.0 when denominator is zero"

# Generation Request
class DataGenerationRequest(BaseModel):
    seed: int = 20261022
    profile: str = "starter"  # starter, full
    event_count: Optional[int] = None
    time_window_days: int = 30
