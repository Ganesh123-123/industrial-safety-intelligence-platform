export interface Plant {
  plant_id: string;
  plant_code: string;
  plant_name: string;
  location: string;
  timezone: string;
  status: string;
  created_at: string;
  machine_count?: number;
  zone_count?: number;
}

export interface Machine {
  machine_id: string;
  plant_id: string;
  machine_code: string;
  machine_name: string;
  machine_type: string;
  operational_status: string;
  commissioned_at: string;
  retired_at?: string | null;
  created_at: string;
  plant_name?: string;
  active_alarms_count?: number;
  repeated_condition_score?: number;
}

export interface SafetyZone {
  safety_zone_id: string;
  plant_id: string;
  zone_code: string;
  zone_name: string;
  risk_level: string;
  description?: string;
  effective_from: string;
  effective_to?: string | null;
  status: string;
}

export interface Interlock {
  interlock_id: string;
  machine_id: string;
  interlock_code: string;
  interlock_name: string;
  interlock_type: string;
  expected_safe_state: string;
  current_state: string;
  effective_from: string;
  effective_to?: string | null;
  status: string;
}

export interface AlarmDefinition {
  alarm_definition_id: string;
  alarm_code: string;
  machine_type: string;
  alarm_name: string;
  description?: string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  acknowledgement_required: boolean;
  acknowledgement_sla_seconds: number;
  expected_interlock_state?: string;
  active_from: string;
  active_to?: string | null;
  status: string;
}

export interface Acknowledgement {
  acknowledgement_id: string;
  alarm_event_id: string;
  shift_id?: string;
  acknowledgement_timestamp: string;
  acknowledgement_status: string;
  response_seconds: number;
  acknowledgement_channel: string;
  notes?: string;
  issue_type?: string;
}

export interface AlarmEvent {
  alarm_event_id: string;
  machine_id: string;
  alarm_definition_id: string;
  safety_zone_id?: string;
  event_timestamp: string;
  received_timestamp: string;
  event_sequence: number;
  machine_state: string;
  interlock_state_snapshot: string;
  alarm_status: string;
  source_event_id: string;
  replay_reference?: string | null;
  issue_type?: string | null;
  created_at: string;
  severity?: string;
  alarm_name?: string;
  plant_id?: string;
  acknowledgement?: Acknowledgement;
}

export interface Incident {
  incident_id: string;
  plant_id: string;
  machine_id: string;
  safety_zone_id: string;
  incident_timestamp: string;
  incident_type: string;
  severity: string;
  description: string;
  triggering_alarm_event_id?: string | null;
  detection_rule_id: string;
  incident_status: string;
  ground_truth_label?: string | null;
  created_at: string;
  plant_name?: string;
  machine_code?: string;
  zone_code?: string;
  corrective_actions_count?: number;
}

export interface CorrectiveAction {
  corrective_action_id: string;
  incident_id: string;
  action_type: string;
  description: string;
  assigned_team: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  verified_at?: string | null;
  verification_status: string;
  action_status: string;
  issue_type?: string | null;
}

export interface IncidentTimelineNode {
  node_id: string;
  timestamp: string;
  node_type: string;
  title: string;
  description: string;
  severity?: string;
  status?: string;
  metadata?: Record<string, any>;
  is_gap?: boolean;
}

export interface IncidentTimelineResponse {
  incident: Incident;
  timeline: IncidentTimelineNode[];
  traceability_complete: boolean;
  missing_evidence_reasons: string[];
}

export interface AnomalyItem {
  anomaly_id: string;
  anomaly_type: string;
  entity_type: string;
  entity_id: string;
  severity: string;
  detected_at: string;
  rule_id: string;
  explanation: string;
  evidence: Record<string, any>;
  related_records: string[];
  advisory_recommendation: string;
}

export interface RepeatedConditionScore {
  machine_id: string;
  plant_id: string;
  machine_code: string;
  score: number;
  level: string;
  critical_alarms_count: number;
  high_alarms_count: number;
  interlock_violations_count: number;
  avg_acknowledgement_delay_seconds: number;
  explanation: string;
}

export interface OverviewMetrics {
  total_plants: number;
  total_machines: number;
  total_alarms: number;
  critical_and_high_alarms: number;
  open_incidents: number;
  delayed_acknowledgements: number;
  repeated_unsafe_clusters: number;
  unverified_actions: number;
  data_quality_exceptions: number;
  alarms_by_severity: Record<string, number>;
  alarms_trend: Array<{ date: string; count: number }>;
  incidents_by_plant: Array<{ plant_name: string; count: number }>;
  top_unsafe_machines: RepeatedConditionScore[];
  recent_critical_events: AlarmEvent[];
}

export interface ValidationCheckItem {
  check_name: string;
  status: string;
  records_checked: number;
  failure_count: number;
  example_affected_ids: string[];
  explanation: string;
  suggested_investigation: string;
}

export interface ValidationReport {
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  generated_at: string;
  checks: ValidationCheckItem[];
}

export interface EvaluationMetricCategory {
  anomaly_type: string;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  detection_rate: number;
  total_ground_truth: number;
}

export interface EvaluationReport {
  overall_precision: number;
  overall_recall: number;
  overall_f1: number;
  overall_detection_rate: number;
  total_ground_truth_anomalies: number;
  total_detected_anomalies: number;
  categories: EvaluationMetricCategory[];
  zero_division_policy: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
