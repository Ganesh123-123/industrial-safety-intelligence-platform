import React, { useEffect, useState } from 'react';
import {
  Building2, Cpu, Search, Filter, Shield, AlertTriangle,
  X, CheckCircle2, ChevronRight, Activity, Clock
} from 'lucide-react';
import { api } from '../services/api';
import { Plant, Machine, Interlock } from '../types';

export const PlantMachineExplorer: React.FC = () => {
  const [plants, setPlants] = useState<Plant[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [totalMachines, setTotalMachines] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [selectedPlant, setSelectedPlant] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(1);

  // Detail Modal
  const [activeMachineDetail, setActiveMachineDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  const loadPlants = async () => {
    try {
      const data = await api.getPlants();
      setPlants(data);
    } catch (err) {
      console.error('Failed to load plants', err);
    }
  };

  const loadMachines = async () => {
    setLoading(true);
    try {
      const res = await api.getMachines({
        plant_id: selectedPlant || undefined,
        machine_type: selectedType || undefined,
        status: selectedStatus || undefined,
        search: searchQuery || undefined,
        page,
        page_size: 15
      });
      setMachines(res.items);
      setTotalMachines(res.total);
    } catch (err) {
      console.error('Failed to load machines', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlants();
  }, []);

  useEffect(() => {
    loadMachines();
  }, [selectedPlant, selectedType, selectedStatus, searchQuery, page]);

  const openMachineDetail = async (machineId: string) => {
    setDetailLoading(true);
    try {
      const detail = await api.getMachineDetail(machineId);
      setActiveMachineDetail(detail);
    } catch (err) {
      console.error('Failed to load machine detail', err);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Building2 className="h-6 w-6 text-cyan-400" />
          Plant & Machine Explorer
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Facility inventory, machine state telemetry, and safety interlock architectures
        </p>
      </div>

      {/* Facilities Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {plants.map((plant) => (
          <div
            key={plant.plant_id}
            onClick={() => setSelectedPlant(selectedPlant === plant.plant_id ? '' : plant.plant_id)}
            className={`p-4 rounded-xl border transition cursor-pointer relative ${
              selectedPlant === plant.plant_id
                ? 'bg-cyan-950/30 border-cyan-500 shadow-md glow-cyan'
                : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                {plant.plant_code}
              </span>
              <span className="text-[11px] font-medium text-emerald-400 flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                {plant.status}
              </span>
            </div>
            <h4 className="font-semibold text-white text-sm mb-1">{plant.plant_name}</h4>
            <p className="text-xs text-slate-400 mb-3">{plant.location}</p>

            <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
              <span>{plant.machine_count || 0} Machines</span>
              <span>{plant.zone_count || 0} Safety Zones</span>
            </div>
          </div>
        ))}
      </div>

      {/* Search & Filters Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Search Input */}
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search code or name..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500 transition"
            />
          </div>

          {/* Machine Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => { setSelectedType(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Machine Types</option>
            <option value="STAMPING_PRESS">Stamping Press</option>
            <option value="ROBOTIC_WELDER">Robotic Welder</option>
            <option value="CONVEYOR_SYSTEM">Conveyor System</option>
            <option value="CNC_MILL">CNC Mill</option>
            <option value="CHEMICAL_REACTOR">Chemical Reactor</option>
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Operating States</option>
            <option value="RUNNING">RUNNING</option>
            <option value="IDLE">IDLE</option>
            <option value="EMERGENCY_STOP">EMERGENCY_STOP</option>
            <option value="FAULT">FAULT</option>
            <option value="MAINTENANCE">MAINTENANCE</option>
          </select>

          {(selectedPlant || selectedType || selectedStatus || searchQuery) && (
            <button
              onClick={() => {
                setSelectedPlant('');
                setSelectedType('');
                setSelectedStatus('');
                setSearchQuery('');
                setPage(1);
              }}
              className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 font-medium"
            >
              <X className="h-3 w-3" /> Clear
            </button>
          )}
        </div>

        <div className="text-xs text-slate-400">
          Showing <span className="font-semibold text-slate-200">{machines.length}</span> of {totalMachines} machines
        </div>
      </div>

      {/* Machine Inventory Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Machine Tag</th>
                <th className="py-3 px-4">Name & Type</th>
                <th className="py-3 px-4">Plant Facility</th>
                <th className="py-3 px-4">Operational Status</th>
                <th className="py-3 px-4 text-center">Active Alarms</th>
                <th className="py-3 px-4 text-center">Risk Score (Rule 1)</th>
                <th className="py-3 px-4">Commissioned</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    Loading machine inventory...
                  </td>
                </tr>
              ) : machines.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No matching machines found.
                  </td>
                </tr>
              ) : (
                machines.map((machine) => (
                  <tr key={machine.machine_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-bold text-cyan-400">
                      {machine.machine_code}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-200">{machine.machine_name}</div>
                      <div className="text-[11px] text-slate-400">{machine.machine_type}</div>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {machine.plant_name || machine.plant_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        machine.operational_status === 'RUNNING' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                        machine.operational_status === 'EMERGENCY_STOP' ? 'bg-red-950 text-red-400 border border-red-800' :
                        machine.operational_status === 'FAULT' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                        'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${
                          machine.operational_status === 'RUNNING' ? 'bg-emerald-400 animate-pulse' :
                          machine.operational_status === 'EMERGENCY_STOP' ? 'bg-red-400 animate-ping' :
                          machine.operational_status === 'FAULT' ? 'bg-amber-400' : 'bg-slate-400'
                        }`} />
                        {machine.operational_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-medium">
                      {(machine.active_alarms_count || 0) > 0 ? (
                        <span className="text-red-400 font-bold">{machine.active_alarms_count}</span>
                      ) : (
                        <span className="text-slate-500">0</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`font-mono text-xs px-2 py-0.5 rounded font-bold ${
                        (machine.repeated_condition_score || 0) >= 45 ? 'bg-purple-950 text-purple-300 border border-purple-800' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {machine.repeated_condition_score || 0}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(machine.commissioned_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => openMachineDetail(machine.machine_id)}
                        className="text-xs bg-slate-800 hover:bg-slate-700 text-cyan-400 px-2.5 py-1 rounded font-medium transition border border-slate-700/60 inline-flex items-center gap-1"
                      >
                        Inspect <ChevronRight className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Machine Detail Modal */}
      {activeMachineDetail && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl p-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="font-mono text-xs text-cyan-400">{activeMachineDetail.machine.machine_code}</span>
                <h3 className="text-lg font-bold text-white">{activeMachineDetail.machine.machine_name}</h3>
              </div>
              <button
                onClick={() => setActiveMachineDetail(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-5">
              {/* Hardware Interlock Architecture */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
                  <Shield className="h-4 w-4 text-purple-400" /> Guard Interlocks ({activeMachineDetail.interlocks.length})
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {activeMachineDetail.interlocks.map((itl: Interlock) => (
                    <div key={itl.interlock_id} className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono text-xs font-bold text-slate-200">{itl.interlock_code}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                          itl.current_state === itl.expected_safe_state ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-red-950 text-red-400 border border-red-800'
                        }`}>
                          {itl.current_state}
                        </span>
                      </div>
                      <div className="text-xs text-slate-300 font-medium">{itl.interlock_name}</div>
                      <div className="text-[11px] text-slate-500 mt-1">Expected Safe: {itl.expected_safe_state}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Assigned Safety Zones */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Assigned Safety Perimeters
                </h4>
                <div className="flex flex-wrap gap-2">
                  {activeMachineDetail.assigned_zones.map((z: any) => (
                    <div key={z.zone_id} className="px-3 py-1.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs flex items-center gap-2">
                      <span className="font-mono text-cyan-400">{z.zone_code}</span>
                      <span className="text-slate-200">{z.name}</span>
                      <span className="text-[10px] text-amber-400 bg-amber-950/60 px-1 rounded">{z.risk}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Append-Only State Transitions */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 mb-2">
                  <Clock className="h-4 w-4 text-cyan-400" /> Recent Machine State Log
                </h4>
                <div className="space-y-1.5 bg-slate-950/70 p-3 rounded-lg border border-slate-800">
                  {activeMachineDetail.recent_state_history.map((hist: any) => (
                    <div key={hist.history_id} className="flex items-center justify-between text-xs py-1 border-b border-slate-900 last:border-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-300">{hist.state}</span>
                        <span className="text-slate-500">via {hist.trigger_source}</span>
                      </div>
                      <span className="font-mono text-[10px] text-slate-500">
                        {new Date(hist.transition_timestamp).toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
