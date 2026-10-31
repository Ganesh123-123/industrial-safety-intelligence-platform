import React, { useEffect, useState } from 'react';
import {
  Bell, Filter, Search, ShieldAlert, AlertTriangle, Clock,
  ChevronLeft, ChevronRight, X, Eye, RefreshCw, Zap
} from 'lucide-react';
import { api } from '../services/api';
import { AlarmEvent, Plant, Machine } from '../types';

export const AlarmExplorer: React.FC = () => {
  const [alarms, setAlarms] = useState<AlarmEvent[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [plants, setPlants] = useState<Plant[]>([]);
  const [selectedPlant, setSelectedPlant] = useState<string>('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [anomalyOnly, setAnomalyOnly] = useState<boolean>(false);
  const [activeEventDetail, setActiveEventDetail] = useState<any | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.getAlarms({
        plant_id: selectedPlant || undefined,
        severity: selectedSeverity || undefined,
        alarm_status: selectedStatus || undefined,
        anomaly_only: anomalyOnly || undefined,
        page,
        page_size: 20
      });
      setAlarms(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load alarms', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.getPlants().then(setPlants).catch(console.error);
  }, []);

  useEffect(() => {
    loadData();
  }, [selectedPlant, selectedSeverity, selectedStatus, anomalyOnly, page]);

  const viewDetail = async (alarmId: string) => {
    try {
      const detail = await api.getAlarmDetail(alarmId);
      setActiveEventDetail(detail);
    } catch (err) {
      console.error('Failed to load alarm detail', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Bell className="h-6 w-6 text-cyan-400" />
          Alarm Explorer & Telemetry Feed
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Historical and live machine alarms, interlock states, SLA response audit, and replay detection
        </p>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Plant Filter */}
          <select
            value={selectedPlant}
            onChange={(e) => { setSelectedPlant(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Facilities</option>
            {plants.map((p) => (
              <option key={p.plant_id} value={p.plant_id}>{p.plant_name}</option>
            ))}
          </select>

          {/* Severity Filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => { setSelectedSeverity(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
            <option value="INFO">INFO</option>
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="CLEARED">CLEARED</option>
            <option value="REPLAYED">REPLAYED</option>
          </select>

          {/* Anomaly Only Toggle */}
          <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold px-3 py-1.5 rounded-lg border border-red-900/50 bg-red-950/20 text-red-300 hover:bg-red-950/40 transition">
            <input
              type="checkbox"
              checked={anomalyOnly}
              onChange={(e) => { setAnomalyOnly(e.target.checked); setPage(1); }}
              className="accent-red-500 cursor-pointer"
            />
            <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
            Anomalies Only
          </label>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>{total.toLocaleString()} total events</span>
          <button
            onClick={loadData}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Alarm Events Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Machine & Zone</th>
                <th className="py-3 px-4">Alarm Description</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Machine / Interlock</th>
                <th className="py-3 px-4">Operator Response</th>
                <th className="py-3 px-4 text-center">Flags</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    Loading alarm telemetry...
                  </td>
                </tr>
              ) : alarms.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No alarm records match criteria.
                  </td>
                </tr>
              ) : (
                alarms.map((alarm) => {
                  const hasAnomaly =
                    alarm.issue_type ||
                    alarm.replay_reference ||
                    (alarm.machine_state === 'RUNNING' && ['TRIPPED', 'OPEN'].includes(alarm.interlock_state_snapshot));

                  return (
                    <tr
                      key={alarm.alarm_event_id}
                      className={`hover:bg-slate-800/40 transition ${
                        hasAnomaly ? 'bg-red-950/10' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-cyan-400 whitespace-nowrap">
                        {alarm.alarm_event_id}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                        {new Date(alarm.event_timestamp).toISOString().replace('T', ' ').slice(0, 19)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-200">{alarm.machine_id}</div>
                        <div className="text-[10px] text-slate-500">{alarm.safety_zone_id || 'Global Zone'}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-slate-300">{alarm.alarm_name || alarm.alarm_definition_id}</div>
                        <div className="text-[10px] text-slate-500 font-mono">Src: {alarm.source_event_id}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          alarm.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' :
                          alarm.severity === 'HIGH' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                          alarm.severity === 'MEDIUM' ? 'bg-yellow-950 text-yellow-400 border border-yellow-800' :
                          'bg-cyan-950 text-cyan-400 border border-cyan-800'
                        }`}>
                          {alarm.severity || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-slate-300 font-medium">{alarm.machine_state}</div>
                        <div className={`text-[10px] font-semibold ${
                          alarm.interlock_state_snapshot === 'TRIPPED' ? 'text-red-400' :
                          alarm.interlock_state_snapshot === 'OPEN' ? 'text-amber-400' : 'text-emerald-400'
                        }`}>
                          ITL: {alarm.interlock_state_snapshot}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        {alarm.acknowledgement ? (
                          <div>
                            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                              alarm.acknowledgement.acknowledgement_status === 'TIMELY' ? 'bg-emerald-950 text-emerald-400' :
                              alarm.acknowledgement.acknowledgement_status === 'DELAYED' ? 'bg-amber-950 text-amber-400' :
                              'bg-red-950 text-red-400'
                            }`}>
                              {alarm.acknowledgement.acknowledgement_status}
                            </span>
                            <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                              {alarm.acknowledgement.response_seconds}s
                            </div>
                          </div>
                        ) : (
                          <span className="text-[10px] text-slate-500 italic">Unacknowledged</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {alarm.issue_type ? (
                          <span className="inline-block text-[9px] font-mono font-bold bg-red-900/60 text-red-200 border border-red-700 px-1.5 py-0.5 rounded uppercase">
                            {alarm.issue_type}
                          </span>
                        ) : alarm.replay_reference ? (
                          <span className="inline-block text-[9px] font-mono bg-purple-950 text-purple-300 border border-purple-800 px-1.5 py-0.5 rounded">
                            REPLAY
                          </span>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => viewDetail(alarm.alarm_event_id)}
                          className="p-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded transition"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between px-4 py-3 bg-slate-950/70 border-t border-slate-800 text-xs text-slate-400">
          <div>
            Page <span className="font-semibold text-slate-200">{page}</span> of {totalPages}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none transition"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:pointer-events-none transition"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Alarm Detail Drawer */}
      {activeEventDetail && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-xl max-h-[90vh] overflow-y-auto shadow-2xl p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="font-mono text-xs font-bold text-cyan-400">
                  {activeEventDetail.alarm_event.alarm_event_id}
                </span>
                <h3 className="text-lg font-bold text-white">Alarm Telemetry Snapshot</h3>
              </div>
              <button
                onClick={() => setActiveEventDetail(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500">Machine</span>
                  <p className="font-semibold text-slate-200">{activeEventDetail.machine_code} ({activeEventDetail.machine_name})</p>
                </div>
                <div>
                  <span className="text-slate-500">Severity</span>
                  <p className="font-semibold text-red-400">{activeEventDetail.alarm_event.severity}</p>
                </div>
                <div>
                  <span className="text-slate-500">Occurred Timestamp</span>
                  <p className="font-mono text-slate-300">{activeEventDetail.alarm_event.event_timestamp}</p>
                </div>
                <div>
                  <span className="text-slate-500">Received Timestamp</span>
                  <p className="font-mono text-slate-300">{activeEventDetail.alarm_event.received_timestamp}</p>
                </div>
                <div>
                  <span className="text-slate-500">Machine State</span>
                  <p className="font-semibold text-slate-200">{activeEventDetail.alarm_event.machine_state}</p>
                </div>
                <div>
                  <span className="text-slate-500">Interlock Snapshot</span>
                  <p className="font-semibold text-slate-200">{activeEventDetail.alarm_event.interlock_state_snapshot}</p>
                </div>
              </div>

              {/* Definition Criteria */}
              {activeEventDetail.definition && (
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 space-y-1">
                  <h4 className="font-semibold text-slate-300 uppercase text-[10px] tracking-wider">Alarm Definition Policy</h4>
                  <p className="text-white font-medium">{activeEventDetail.definition.alarm_name}</p>
                  <p className="text-slate-400">{activeEventDetail.definition.description}</p>
                  <p className="text-slate-400 mt-1">Configured SLA: <span className="font-mono text-cyan-400">{activeEventDetail.definition.acknowledgement_sla_seconds}s</span></p>
                </div>
              )}

              {/* Acknowledgements History */}
              <div>
                <h4 className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider mb-2">Operator Acknowledgement Log</h4>
                {activeEventDetail.acknowledgements.length === 0 ? (
                  <p className="text-slate-500 italic p-3 bg-slate-950/40 rounded border border-slate-800/60">No operator acknowledgement logged for this event.</p>
                ) : (
                  activeEventDetail.acknowledgements.map((ack: any) => (
                    <div key={ack.acknowledgement_id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-cyan-400 font-bold">{ack.acknowledgement_id}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold">{ack.acknowledgement_status}</span>
                      </div>
                      <p className="text-slate-300">Response Delay: <span className="font-mono">{ack.response_seconds}s</span> via {ack.acknowledgement_channel}</p>
                      {ack.notes && <p className="text-slate-400 italic">Notes: {ack.notes}</p>}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
