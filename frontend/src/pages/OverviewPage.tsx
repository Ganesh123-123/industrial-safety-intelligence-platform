import React, { useEffect, useState } from 'react';
import {
  AlertTriangle, ShieldAlert, Cpu, Building2, Bell, Clock,
  CheckCircle2, RefreshCw, Activity, ArrowUpRight, Filter
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { OverviewMetrics, Plant } from '../types';

interface OverviewPageProps {
  onNavigateToTab?: (tab: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#06b6d4',
  INFO: '#3b82f6',
};

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigateToTab }) => {
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [plants, setPlants] = useState<Plant[]>([]);
  const [selectedPlant, setSelectedPlant] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, p] = await Promise.all([
        api.getOverview(selectedPlant || undefined),
        api.getPlants()
      ]);
      setMetrics(m);
      setPlants(p);
    } catch (err: any) {
      setError(err.message || 'Failed to load executive overview data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedPlant]);

  if (loading && !metrics) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <RefreshCw className="h-8 w-8 animate-spin text-cyan-400" />
          <p className="text-sm tracking-wide">Aggregating industrial telemetry & risk models...</p>
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="rounded-xl border border-red-800/50 bg-red-950/20 p-6 text-red-300">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-6 w-6 text-red-400" />
          <h3 className="font-semibold text-lg">Failed to Load Overview Metrics</h3>
        </div>
        <p className="mt-2 text-sm text-red-400/80">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 rounded-lg bg-red-900/60 px-4 py-2 text-xs font-semibold hover:bg-red-800 transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const sevData = metrics
    ? Object.entries(metrics.alarms_by_severity).map(([sev, count]) => ({
        severity: sev,
        count: count,
        color: SEVERITY_COLORS[sev] || '#64748b'
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Top Header & Plant Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="h-6 w-6 text-cyan-400" />
            Executive Safety Overview
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time industrial telemetry, priority scores, and anomaly intelligence
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300">
            <Filter className="h-3.5 w-3.5 text-cyan-400" />
            <select
              value={selectedPlant}
              onChange={(e) => setSelectedPlant(e.target.value)}
              className="bg-transparent text-slate-200 outline-none cursor-pointer"
            >
              <option value="" className="bg-slate-900">All Industrial Plants ({plants.length})</option>
              {plants.map((p) => (
                <option key={p.plant_id} value={p.plant_id} className="bg-slate-900">
                  {p.plant_name} ({p.plant_code})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={loadData}
            title="Refresh Metrics"
            className="flex items-center gap-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg text-xs font-medium transition border border-slate-700/60"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            Sync
          </button>
        </div>
      </div>

      {/* KPI Stat Cards (9 Metrics) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* Total Plants */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Facilities</span>
            <Building2 className="h-4 w-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-white">{metrics?.total_plants}</div>
          <div className="text-[11px] text-slate-400 mt-1">Active monitored sites</div>
        </div>

        {/* Total Machines */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Machines</span>
            <Cpu className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white">{metrics?.total_machines}</div>
          <div className="text-[11px] text-slate-400 mt-1">Interlock-monitored units</div>
        </div>

        {/* Total Alarms */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Alarm Events</span>
            <Bell className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">{metrics?.total_alarms.toLocaleString()}</div>
          <div className="text-[11px] text-slate-400 mt-1">Historical telemetry events</div>
        </div>

        {/* Critical & High Alarms */}
        <div className="bg-slate-900/80 border border-red-900/40 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-red-700/60 transition glow-critical">
          <div className="flex items-center justify-between text-red-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Critical & High</span>
            <ShieldAlert className="h-4 w-4 text-red-400" />
          </div>
          <div className="text-2xl font-bold text-red-400">{metrics?.critical_and_high_alarms}</div>
          <div className="text-[11px] text-red-300/70 mt-1">Elevated hazard priority</div>
        </div>

        {/* Open Incidents */}
        <div className="bg-slate-900/80 border border-amber-900/40 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-amber-700/60 transition glow-warning">
          <div className="flex items-center justify-between text-amber-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Open Incidents</span>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400">{metrics?.open_incidents}</div>
          <div className="text-[11px] text-amber-300/70 mt-1">Active investigations</div>
        </div>

        {/* Delayed Acknowledgements */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">SLA Delayed</span>
            <Clock className="h-4 w-4 text-orange-400" />
          </div>
          <div className="text-2xl font-bold text-orange-400">{metrics?.delayed_acknowledgements}</div>
          <div className="text-[11px] text-slate-400 mt-1">Exceeded response SLA</div>
        </div>

        {/* Repeated Unsafe Clusters */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Repeated Hazards</span>
            <Activity className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-purple-400">{metrics?.repeated_unsafe_clusters}</div>
          <div className="text-[11px] text-slate-400 mt-1">Rule 1 score &gt;= 45</div>
        </div>

        {/* Unverified Actions */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Unverified Actions</span>
            <CheckCircle2 className="h-4 w-4 text-yellow-400" />
          </div>
          <div className="text-2xl font-bold text-yellow-400">{metrics?.unverified_actions}</div>
          <div className="text-[11px] text-slate-400 mt-1">Rule 8 gate anomalies</div>
        </div>

        {/* Data Quality Exceptions */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-xl p-4 shadow-sm relative overflow-hidden group hover:border-slate-700 transition col-span-2 lg:col-span-2">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Validation Exceptions</span>
            <ShieldAlert className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="flex items-center gap-3">
            <div className="text-2xl font-bold text-cyan-400">{metrics?.data_quality_exceptions}</div>
            <div className="text-xs text-slate-400">
              Controlled evaluation fixtures & telemetry anomalies isolated
            </div>
          </div>
        </div>
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Temporal Alarm Trend Chart */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white text-sm">Telemetry Event Trend (Daily Volume)</h3>
              <p className="text-xs text-slate-400">Chronological distribution across evaluation window</p>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-800/40">
              30-Day Moving Window
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics?.alarms_trend || []}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.35}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f1f5f9' }}
                />
                <Area type="monotone" dataKey="count" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="mb-4">
            <h3 className="font-semibold text-white text-sm">Alarm Severity Breakdown</h3>
            <p className="text-xs text-slate-400">Distribution by configured severity grade</p>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sevData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={10} />
                <YAxis dataKey="severity" type="category" stroke="#94a3b8" fontSize={11} width={75} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f1f5f9' }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {sevData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Lower Row: Top Unsafe Machines & Recent Critical Alarms */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Machines by Repeated Unsafe Condition Score */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white text-sm">Top Repeated Unsafe Conditions (Rule 1)</h3>
              <p className="text-xs text-slate-400">Machines prioritized by multi-factor hazard scoring formula</p>
            </div>
            {onNavigateToTab && (
              <button
                onClick={() => onNavigateToTab('machines')}
                className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium transition"
              >
                Explorer <ArrowUpRight className="h-3 w-3" />
              </button>
            )}
          </div>

          <div className="space-y-3">
            {metrics?.top_unsafe_machines.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No machine risk scores evaluated yet.</p>
            ) : (
              metrics?.top_unsafe_machines.map((machine) => (
                <div key={machine.machine_id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-slate-200">{machine.machine_code}</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                        machine.level === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' :
                        machine.level === 'HIGH' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                        machine.level === 'MEDIUM' ? 'bg-yellow-950 text-yellow-400 border border-yellow-800' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {machine.level}
                      </span>
                    </div>
                    <div className="text-sm font-mono font-bold text-white">
                      {machine.score}<span className="text-xs text-slate-500 font-normal">/100</span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden mb-2">
                    <div
                      className={`h-full rounded-full ${
                        machine.level === 'CRITICAL' ? 'bg-red-500' :
                        machine.level === 'HIGH' ? 'bg-amber-500' :
                        machine.level === 'MEDIUM' ? 'bg-yellow-500' : 'bg-cyan-500'
                      }`}
                      style={{ width: `${Math.min(100, machine.score)}%` }}
                    />
                  </div>

                  <p className="text-[11px] text-slate-400 leading-tight">
                    {machine.explanation}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Critical Events */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white text-sm">Recent Critical Telemetry Alarms</h3>
              <p className="text-xs text-slate-400">Real-time feed of highest priority safety events</p>
            </div>
            {onNavigateToTab && (
              <button
                onClick={() => onNavigateToTab('alarms')}
                className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium transition"
              >
                Alarm Table <ArrowUpRight className="h-3 w-3" />
              </button>
            )}
          </div>

          <div className="space-y-2 overflow-y-auto max-h-80 pr-1">
            {metrics?.recent_critical_events.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No recent critical events.</p>
            ) : (
              metrics?.recent_critical_events.map((event) => (
                <div
                  key={event.alarm_event_id}
                  className="flex items-start justify-between p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80 hover:border-slate-700 transition"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-red-400">{event.alarm_event_id}</span>
                      <span className="text-[10px] px-1.5 py-0.2 bg-red-950 text-red-300 border border-red-800/60 rounded">
                        {event.severity}
                      </span>
                      <span className="text-xs text-slate-300 font-medium">{event.alarm_name}</span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Machine: <span className="text-slate-300">{event.machine_id}</span> | State: <span className="text-slate-300">{event.machine_state}</span> | Interlock: <span className="text-slate-300">{event.interlock_state_snapshot}</span>
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono whitespace-nowrap">
                    {new Date(event.event_timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
