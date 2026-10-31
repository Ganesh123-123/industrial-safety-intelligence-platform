import {
  Plant, Machine, SafetyZone, AlarmEvent, Incident,
  CorrectiveAction, IncidentTimelineResponse, AnomalyItem,
  OverviewMetrics, ValidationReport, EvaluationReport, PaginatedResponse
} from '../types';

const configuredApiBase = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE = configuredApiBase
  ? `${configuredApiBase.startsWith('http') ? '' : 'https://'}${configuredApiBase.replace(/\/$/, '')}/api`
  : '/api';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorBody.detail || `HTTP Error ${res.status}`);
  }
  return res.json();
}

export const api = {
  getHealth: () => fetchJson<{ status: string; service: string; database: string }>(`${API_BASE}/health`),

  getOverview: (plantId?: string, dateFrom?: string, dateTo?: string) => {
    const params = new URLSearchParams();
    if (plantId) params.append('plant_id', plantId);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    return fetchJson<OverviewMetrics>(`${API_BASE}/overview?${params.toString()}`);
  },

  getPlants: () => fetchJson<Plant[]>(`${API_BASE}/plants`),

  getMachines: (params: { plant_id?: string; machine_type?: string; status?: string; search?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params.plant_id) q.append('plant_id', params.plant_id);
    if (params.machine_type) q.append('machine_type', params.machine_type);
    if (params.status) q.append('status', params.status);
    if (params.search) q.append('search', params.search);
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    return fetchJson<PaginatedResponse<Machine>>(`${API_BASE}/machines?${q.toString()}`);
  },

  getMachineDetail: (machineId: string) => fetchJson<any>(`${API_BASE}/machines/${machineId}`),

  getSafetyZones: (plantId?: string) => {
    const q = plantId ? `?plant_id=${plantId}` : '';
    return fetchJson<SafetyZone[]>(`${API_BASE}/safety-zones${q}`);
  },

  getAlarms: (params: {
    plant_id?: string;
    machine_id?: string;
    severity?: string;
    alarm_status?: string;
    anomaly_only?: boolean;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    order?: string;
  }) => {
    const q = new URLSearchParams();
    if (params.plant_id) q.append('plant_id', params.plant_id);
    if (params.machine_id) q.append('machine_id', params.machine_id);
    if (params.severity) q.append('severity', params.severity);
    if (params.alarm_status) q.append('alarm_status', params.alarm_status);
    if (params.anomaly_only) q.append('anomaly_only', 'true');
    if (params.date_from) q.append('date_from', params.date_from);
    if (params.date_to) q.append('date_to', params.date_to);
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    if (params.sort_by) q.append('sort_by', params.sort_by);
    if (params.order) q.append('order', params.order);
    return fetchJson<PaginatedResponse<AlarmEvent>>(`${API_BASE}/alarms?${q.toString()}`);
  },

  getAlarmDetail: (alarmId: string) => fetchJson<any>(`${API_BASE}/alarms/${alarmId}`),

  getIncidents: (params: { plant_id?: string; machine_id?: string; severity?: string; status?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params.plant_id) q.append('plant_id', params.plant_id);
    if (params.machine_id) q.append('machine_id', params.machine_id);
    if (params.severity) q.append('severity', params.severity);
    if (params.status) q.append('status', params.status);
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    return fetchJson<PaginatedResponse<Incident>>(`${API_BASE}/incidents?${q.toString()}`);
  },

  getIncidentDetail: (incidentId: string) => fetchJson<Incident>(`${API_BASE}/incidents/${incidentId}`),

  getIncidentTimeline: (incidentId: string) => fetchJson<IncidentTimelineResponse>(`${API_BASE}/incidents/${incidentId}/timeline`),

  getAnomalies: (anomalyType?: string, severity?: string) => {
    const q = new URLSearchParams();
    if (anomalyType) q.append('anomaly_type', anomalyType);
    if (severity) q.append('severity', severity);
    return fetchJson<AnomalyItem[]>(`${API_BASE}/anomalies?${q.toString()}`);
  },

  getCorrectiveActions: (params: { incident_id?: string; action_status?: string; verification_status?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params.incident_id) q.append('incident_id', params.incident_id);
    if (params.action_status) q.append('action_status', params.action_status);
    if (params.verification_status) q.append('verification_status', params.verification_status);
    if (params.page) q.append('page', params.page.toString());
    if (params.page_size) q.append('page_size', params.page_size.toString());
    return fetchJson<PaginatedResponse<CorrectiveAction>>(`${API_BASE}/corrective-actions?${q.toString()}`);
  },

  updateCorrectiveAction: (actionId: string, data: { action_status?: string; verification_status?: string; actor?: string; notes?: string }) => {
    return fetchJson<CorrectiveAction>(`${API_BASE}/corrective-actions/${actionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
  },

  verifyCorrectiveAction: (actionId: string, actor: string = 'QA_AUDITOR', notes?: string) => {
    const q = new URLSearchParams({ actor });
    if (notes) q.append('notes', notes);
    return fetchJson<CorrectiveAction>(`${API_BASE}/corrective-actions/${actionId}/verify?${q.toString()}`, {
      method: 'POST'
    });
  },

  getDataQualityReport: () => fetchJson<ValidationReport>(`${API_BASE}/data-quality`),

  runValidation: () => fetchJson<ValidationReport>(`${API_BASE}/validate`, { method: 'POST' }),

  getEvaluationMetrics: () => fetchJson<EvaluationReport>(`${API_BASE}/metrics/evaluation`),

  triggerAnalysis: () => fetchJson<any>(`${API_BASE}/analyze`, { method: 'POST' }),

  getGenerationRuns: () => fetchJson<any[]>(`${API_BASE}/generation-runs`),

  generateData: (seed: number, profile: string, eventCount?: number) => {
    return fetchJson<any>(`${API_BASE}/generate-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed, profile, event_count: eventCount })
    });
  },

  getManifest: () => fetchJson<any>(`${API_BASE}/export/manifest`),

  getExportUrl: (entity: string, format: 'csv' | 'json') => `${API_BASE}/export/${entity}?format=${format}`,

  getGroundTruthExportUrl: (format: 'csv' | 'json') => `${API_BASE}/export/evaluation/ground-truth?format=${format}`
};
