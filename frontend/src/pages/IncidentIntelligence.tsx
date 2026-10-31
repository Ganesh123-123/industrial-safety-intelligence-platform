import React, { useEffect, useState } from 'react';
import {
  ShieldAlert, AlertTriangle, CheckCircle2, Clock, GitCommit,
  ChevronRight, X, AlertOctagon, HelpCircle, Layers, FileText
} from 'lucide-react';
import { api } from '../services/api';
import { Incident, IncidentTimelineResponse, IncidentTimelineNode } from '../types';

export const IncidentIntelligence: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  // Selected Incident Timeline
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [timelineData, setTimelineData] = useState<IncidentTimelineResponse | null>(null);
  const [timelineLoading, setTimelineLoading] = useState<boolean>(false);

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const res = await api.getIncidents({ page, page_size: 20 });
      setIncidents(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load incidents', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [page]);

  const openTimeline = async (incidentId: string) => {
    setSelectedIncidentId(incidentId);
    setTimelineLoading(true);
    try {
      const data = await api.getIncidentTimeline(incidentId);
      setTimelineData(data);
    } catch (err) {
      console.error('Failed to load incident timeline', err);
    } finally {
      setTimelineLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <ShieldAlert className="h-6 w-6 text-red-400" />
          Incident Intelligence & Traceability
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Root cause analysis, chronological event graph reconstruction, and telemetry gap verification
        </p>
      </div>

      {/* Incidents Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Incident ID</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Machine & Facility</th>
                <th className="py-3 px-4">Incident Type & Narrative</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Triggering Alarm</th>
                <th className="py-3 px-4">Detection Rule</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Traceability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    Loading incident register...
                  </td>
                </tr>
              ) : incidents.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No recorded incidents.
                  </td>
                </tr>
              ) : (
                incidents.map((inc) => {
                  const hasMissingTrigger = !inc.triggering_alarm_event_id;

                  return (
                    <tr
                      key={inc.incident_id}
                      className={`hover:bg-slate-800/40 transition ${
                        hasMissingTrigger ? 'bg-amber-950/10' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-cyan-400 whitespace-nowrap">
                        {inc.incident_id}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                        {new Date(inc.incident_timestamp).toISOString().replace('T', ' ').slice(0, 19)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-200">{inc.machine_code || inc.machine_id}</div>
                        <div className="text-[10px] text-slate-400">{inc.plant_name || inc.plant_id}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-200">{inc.incident_type}</div>
                        <div className="text-[11px] text-slate-400 line-clamp-1">{inc.description}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          inc.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' :
                          inc.severity === 'HIGH' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                          'bg-yellow-950 text-yellow-400 border border-yellow-800'
                        }`}>
                          {inc.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {inc.triggering_alarm_event_id ? (
                          <span className="font-mono text-cyan-400 text-[11px]">
                            {inc.triggering_alarm_event_id}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800/70 font-semibold">
                            <AlertTriangle className="h-3 w-3" /> Missing Context
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-300">
                        {inc.detection_rule_id}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          inc.incident_status === 'RESOLVED' || inc.incident_status === 'CLOSED'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}>
                          {inc.incident_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => openTimeline(inc.incident_id)}
                          className="text-xs bg-slate-800 hover:bg-slate-700 text-cyan-400 px-3 py-1 rounded font-medium transition border border-slate-700/60 inline-flex items-center gap-1"
                        >
                          Timeline <ChevronRight className="h-3 w-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Incident Traceability Timeline Modal */}
      {selectedIncidentId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto shadow-2xl p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <ShieldAlert className="h-6 w-6 text-red-400" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-cyan-400">{selectedIncidentId}</span>
                    {timelineData && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        timelineData.traceability_complete
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : 'bg-amber-950 text-amber-400 border border-amber-800'
                      }`}>
                        {timelineData.traceability_complete ? 'Complete Traceability (10/10)' : 'Incomplete Evidence (Trace Gap)'}
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-bold text-white">
                    {timelineData?.incident.incident_type || 'Incident Timeline'}
                  </h3>
                </div>
              </div>
              <button
                onClick={() => { setSelectedIncidentId(null); setTimelineData(null); }}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Traceability Gap Alert Warning */}
            {timelineData && !timelineData.traceability_complete && (
              <div className="mt-4 p-4 rounded-lg bg-amber-950/30 border border-amber-800/80 text-amber-300 space-y-1">
                <div className="flex items-center gap-2 font-semibold text-xs text-amber-400">
                  <AlertTriangle className="h-4 w-4" />
                  Incomplete Traceability Chain Detected
                </div>
                <p className="text-[11px] text-amber-300/80">
                  The analytical engine identified missing root-cause nodes in this incident's telemetry chain:
                </p>
                <ul className="list-disc list-inside text-[11px] space-y-0.5 text-amber-200 mt-1">
                  {timelineData.missing_evidence_reasons.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Timeline Stream */}
            <div className="mt-6 relative pl-6 border-l-2 border-slate-800 space-y-6">
              {timelineLoading ? (
                <p className="text-xs text-slate-500 py-6">Traversing physical and operational event graph...</p>
              ) : timelineData?.timeline.map((node, idx) => (
                <div key={node.node_id || idx} className="relative group">
                  {/* Timeline bullet */}
                  <div className={`absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full border-2 border-slate-900 ${
                    node.is_gap ? 'bg-amber-500 animate-ping' :
                    node.node_type === 'INCIDENT' ? 'bg-red-500' :
                    node.node_type === 'ALARM' ? 'bg-orange-500' :
                    node.node_type === 'VERIFICATION' ? 'bg-emerald-500' :
                    node.node_type === 'ACKNOWLEDGEMENT' ? 'bg-blue-500' :
                    'bg-slate-500'
                  }`} />

                  <div className={`p-3 rounded-lg border text-xs transition ${
                    node.is_gap
                      ? 'bg-amber-950/20 border-amber-800/60 text-amber-200'
                      : node.node_type === 'INCIDENT'
                      ? 'bg-red-950/20 border-red-800/60 text-slate-200'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300'
                  }`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-white">{node.title}</span>
                      <span className="font-mono text-[10px] text-slate-500">
                        {new Date(node.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">{node.description}</p>
                    {node.status && (
                      <div className="mt-1.5 flex items-center gap-2">
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          Status: {node.status}
                        </span>
                        {node.severity && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-red-950 text-red-300 border border-red-800">
                            {node.severity}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
