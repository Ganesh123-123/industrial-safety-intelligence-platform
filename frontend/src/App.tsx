import React, { useState, useEffect } from 'react';
import {
  Activity, Building2, Bell, ShieldAlert, AlertTriangle,
  CheckCircle2, ShieldCheck, Database, Radio, Wrench, ChevronRight
} from 'lucide-react';
import { OverviewPage } from './pages/OverviewPage';
import { PlantMachineExplorer } from './pages/PlantMachineExplorer';
import { AlarmExplorer } from './pages/AlarmExplorer';
import { IncidentIntelligence } from './pages/IncidentIntelligence';
import { AnomalyCenter } from './pages/AnomalyCenter';
import { CorrectiveActionsPage } from './pages/CorrectiveActionsPage';
import { DataQualityEvaluation } from './pages/DataQualityEvaluation';
import { DataGenerationExport } from './pages/DataGenerationExport';
import { api } from './services/api';

const NAV_TABS = [
  { id: 'overview', label: 'Executive Overview', icon: Activity },
  { id: 'machines', label: 'Plant & Machines', icon: Building2 },
  { id: 'alarms', label: 'Alarm Explorer', icon: Bell },
  { id: 'incidents', label: 'Incident Intelligence', icon: ShieldAlert },
  { id: 'anomalies', label: 'Anomaly Center', icon: AlertTriangle },
  { id: 'actions', label: 'Corrective Actions', icon: CheckCircle2 },
  { id: 'quality', label: 'Quality & Evaluation', icon: ShieldCheck },
  { id: 'generator', label: 'Generator & Exports', icon: Database },
];

export function App() {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [backendStatus, setBackendStatus] = useState<string>('CONNECTING');

  useEffect(() => {
    api.getHealth()
      .then((h) => setBackendStatus(h.database === 'HEALTHY' ? 'ONLINE' : 'DEGRADED'))
      .catch(() => setBackendStatus('OFFLINE'));
  }, []);

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 flex flex-col antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Enterprise Bar */}
      <header className="h-14 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-md">
            <Radio className="h-4 w-4 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
              APEX SAFETY INTELLIGENCE
              <span className="text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                v1.0.0
              </span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono">
              Industrial Safety Event Analysis & Decision Support
            </p>
          </div>
        </div>

        {/* System Health Status & Disclaimers */}
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
            <span>Database:</span>
            <span className="text-slate-200 font-semibold">Postgres / SQLite</span>
          </div>

          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono">
            <span className={`h-2 w-2 rounded-full ${
              backendStatus === 'ONLINE' ? 'bg-emerald-400 animate-pulse' :
              backendStatus === 'DEGRADED' ? 'bg-amber-400' : 'bg-red-500'
            }`} />
            <span className="text-[11px] font-medium text-slate-300">
              API: {backendStatus}
            </span>
          </div>
        </div>
      </header>

      {/* Main App Layout */}
      <div className="flex-1 flex flex-col md:flex-row">
        {/* Navigation Sidebar */}
        <aside className="w-full md:w-64 border-r border-slate-800/80 bg-[#0a0f18] p-3 shrink-0">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-3 py-2">
            Operations & Analytics
          </div>

          <nav className="space-y-1">
            {NAV_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                    isActive
                      ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/70 shadow-sm font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span>{tab.label}</span>
                  </div>
                  {isActive && <ChevronRight className="h-3 w-3 text-cyan-400" />}
                </button>
              );
            })}
          </nav>

          {/* Safety Advisory Banner */}
          <div className="mt-8 p-3 bg-slate-950/90 border border-slate-800/90 rounded-xl text-[11px] text-slate-400 space-y-1.5">
            <div className="flex items-center gap-1.5 font-bold text-slate-300 text-[10px] uppercase tracking-wide">
              <ShieldAlert className="h-3.5 w-3.5 text-amber-400" /> Decision Support Mode
            </div>
            <p className="text-[10px] leading-tight text-slate-400">
              This analytics console evaluates synthetic events and decision heuristics. It does not replace certified SIL 3 / PLe certified hardware interlocks.
            </p>
          </div>
        </aside>

        {/* Content Viewport */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full overflow-x-hidden">
          {activeTab === 'overview' && <OverviewPage onNavigateToTab={setActiveTab} />}
          {activeTab === 'machines' && <PlantMachineExplorer />}
          {activeTab === 'alarms' && <AlarmExplorer />}
          {activeTab === 'incidents' && <IncidentIntelligence />}
          {activeTab === 'anomalies' && <AnomalyCenter />}
          {activeTab === 'actions' && <CorrectiveActionsPage />}
          {activeTab === 'quality' && <DataQualityEvaluation />}
          {activeTab === 'generator' && <DataGenerationExport />}
        </main>
      </div>
    </div>
  );
}

export default App;
