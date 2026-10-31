import React, { useEffect, useState } from 'react';
import {
  AlertTriangle, ShieldAlert, Cpu, CheckCircle2, Clock,
  Filter, Search, RefreshCw, Zap, ArrowRight, ExternalLink
} from 'lucide-react';
import { api } from '../services/api';
import { AnomalyItem } from '../types';

export const AnomalyCenter: React.FC = () => {
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [analyzing, setAnalyzing] = useState<boolean>(false);

  const loadAnomalies = async () => {
    setLoading(true);
    try {
      const data = await api.getAnomalies(selectedType || undefined, selectedSeverity || undefined);
      setAnomalies(data);
    } catch (err) {
      console.error('Failed to load anomalies', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnomalies();
  }, [selectedType, selectedSeverity]);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      await api.triggerAnalysis();
      await loadAnomalies();
    } catch (err) {
      console.error('Analysis trigger failed', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const filteredAnomalies = anomalies.filter((a) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.anomaly_id.toLowerCase().includes(q) ||
      a.entity_id.toLowerCase().includes(q) ||
      a.explanation.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-amber-400" />
            Operational Anomaly Center
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Algorithmic detection of impossible mechanical states, replay storms, SLA breaches, and quality gates
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={analyzing}
          className="flex items-center gap-2 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white px-4 py-2 rounded-lg text-xs font-bold transition shadow-md disabled:opacity-50"
        >
          <Zap className={`h-4 w-4 ${analyzing ? 'animate-bounce' : ''}`} />
          {analyzing ? 'Scanning Telemetry...' : 'Trigger Full Anomaly Scan'}
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search entity, ID, explanation..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500 transition"
            />
          </div>

          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Anomaly Categories</option>
            <option value="IMPOSSIBLE_INTERLOCK_STATE">Impossible Interlock State</option>
            <option value="ACKNOWLEDGEMENT_BEFORE_ALARM">Acknowledgement Before Alarm</option>
            <option value="INCIDENT_MISSING_TRIGGER_CONTEXT">Incident Missing Trigger Context</option>
            <option value="DUPLICATE_ALARM_REPLAY">Duplicate Alarm Replay</option>
            <option value="ACTION_CLOSED_WITHOUT_VERIFICATION">Action Closed Without Verification</option>
            <option value="NUISANCE_ALARM_CLUSTER">Nuisance Alarm Cluster</option>
          </select>

          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        <div className="text-xs text-slate-400">
          Identified <span className="font-semibold text-white">{filteredAnomalies.length}</span> active anomalies
        </div>
      </div>

      {/* Anomaly Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          <div className="col-span-2 text-center py-12 text-slate-500">
            Running detection rules against active database records...
          </div>
        ) : filteredAnomalies.length === 0 ? (
          <div className="col-span-2 text-center py-12 text-slate-500">
            No active anomalies detected matching filters.
          </div>
        ) : (
          filteredAnomalies.map((anom) => (
            <div
              key={anom.anomaly_id}
              className={`p-5 rounded-xl border transition shadow-sm space-y-3 relative ${
                anom.severity === 'CRITICAL' ? 'bg-red-950/20 border-red-900/60' :
                anom.severity === 'HIGH' ? 'bg-amber-950/20 border-amber-900/60' :
                'bg-slate-900/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs font-bold text-cyan-400">{anom.anomaly_id}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                      anom.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' :
                      anom.severity === 'HIGH' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                      'bg-cyan-950 text-cyan-400 border border-cyan-800'
                    }`}>
                      {anom.severity}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.2 rounded">
                      {anom.rule_id}
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-200 text-sm">
                    {anom.anomaly_type.replace(/_/g, ' ')}
                  </h4>
                </div>

                <span className="text-[10px] text-slate-500 font-mono whitespace-nowrap">
                  {new Date(anom.detected_at).toLocaleTimeString()}
                </span>
              </div>

              {/* Entity info & Explanation */}
              <div className="text-xs text-slate-300">
                <span className="text-slate-500">Target Entity:</span> <span className="font-mono text-white font-medium">{anom.entity_type} ({anom.entity_id})</span>
                <p className="mt-1 text-slate-400 leading-relaxed">{anom.explanation}</p>
              </div>

              {/* Evidence Snapshot */}
              <div className="p-2.5 rounded bg-slate-950 border border-slate-800/90 font-mono text-[11px] text-slate-300 overflow-x-auto">
                <div className="text-[10px] text-slate-500 uppercase font-sans font-semibold mb-1">Telemetry Proof / Evidence:</div>
                <pre className="text-cyan-300">{JSON.stringify(anom.evidence, null, 2)}</pre>
              </div>

              {/* Related Records */}
              {anom.related_records.length > 0 && (
                <div className="flex items-center gap-2 text-[11px] text-slate-400">
                  <span className="text-slate-500">Correlated Records:</span>
                  <div className="flex flex-wrap gap-1">
                    {anom.related_records.filter(Boolean).map((rec, i) => (
                      <span key={i} className="font-mono bg-slate-800 text-slate-300 px-1.5 py-0.2 rounded text-[10px]">
                        {rec}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Advisory Recommendation (Decision Support Notice) */}
              <div className="pt-2 border-t border-slate-800/80">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1 mb-0.5">
                  <ArrowRight className="h-3 w-3" /> Advisory Next Investigation Step
                </div>
                <p className="text-[11px] text-amber-200/90 leading-tight">
                  {anom.advisory_recommendation}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
