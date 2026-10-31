import React, { useEffect, useState } from 'react';
import {
  Download, Database, Sliders, CheckCircle2, AlertTriangle,
  FileText, Shield, Hash, RefreshCw, Layers, ExternalLink
} from 'lucide-react';
import { api } from '../services/api';

const EXPORTABLE_ENTITIES = [
  { name: 'plants', label: 'Plants (Facilities)' },
  { name: 'machines', label: 'Machines & Assets' },
  { name: 'safety-zones', label: 'Safety Zones' },
  { name: 'interlocks', label: 'Hardware Interlocks' },
  { name: 'alarm-definitions', label: 'Alarm Definitions' },
  { name: 'alarms', label: 'Alarm Telemetry Events' },
  { name: 'acknowledgements', label: 'Operator Acknowledgements' },
  { name: 'incidents', label: 'Safety Incidents' },
  { name: 'corrective-actions', label: 'Corrective Actions' }
];

export const DataGenerationExport: React.FC = () => {
  const [seed, setSeed] = useState<number>(20261022);
  const [profile, setProfile] = useState<string>('starter');
  const [customEvents, setCustomEvents] = useState<string>('');
  const [generating, setGenerating] = useState<boolean>(false);
  const [genResult, setGenResult] = useState<any | null>(null);
  const [manifest, setManifest] = useState<any | null>(null);
  const [runs, setRuns] = useState<any[]>([]);

  const loadRunsAndManifest = async () => {
    try {
      const [m, r] = await Promise.all([
        api.getManifest(),
        api.getGenerationRuns()
      ]);
      setManifest(m);
      setRuns(r);
    } catch (err) {
      console.error('Failed to load generation metadata', err);
    }
  };

  useEffect(() => {
    loadRunsAndManifest();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setGenResult(null);
    try {
      const evtCount = customEvents ? parseInt(customEvents, 10) : undefined;
      const res = await api.generateData(seed, profile, evtCount);
      setGenResult(res);
      await loadRunsAndManifest();
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Database className="h-6 w-6 text-cyan-400" />
          Deterministic Synthetic Generator & Data Exports
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Configurable seeded telemetry generator, canonical reproducibility hashes, and multi-format exports
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generator Controls Form */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm space-y-5">
          <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-slate-800 pb-3">
            <Sliders className="h-4 w-4 text-cyan-400" />
            Generator Configuration Profile
          </div>

          <form onSubmit={handleGenerate} className="space-y-4 text-xs">
            {/* Seed input */}
            <div>
              <label className="block text-slate-400 font-semibold mb-1">
                Deterministic Seed (RNG)
              </label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(parseInt(e.target.value, 10) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono outline-none focus:border-cyan-500 transition"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Identical seeds produce 100% equivalent canonical hashes.
              </span>
            </div>

            {/* Profile Selection */}
            <div>
              <label className="block text-slate-400 font-semibold mb-1">
                Dataset Scale Profile
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setProfile('starter')}
                  className={`py-2 px-3 rounded-lg border text-left font-medium transition ${
                    profile === 'starter'
                      ? 'bg-cyan-950/60 border-cyan-500 text-cyan-300'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold">Starter</div>
                  <div className="text-[10px] opacity-80">~2,500 Alarms (Instant)</div>
                </button>

                <button
                  type="button"
                  onClick={() => setProfile('full')}
                  className={`py-2 px-3 rounded-lg border text-left font-medium transition ${
                    profile === 'full'
                      ? 'bg-cyan-950/60 border-cyan-500 text-cyan-300'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold">Full Profile</div>
                  <div className="text-[10px] opacity-80">50,000 Alarms (30 Days)</div>
                </button>
              </div>
            </div>

            {/* Target Events override */}
            <div>
              <label className="block text-slate-400 font-semibold mb-1">
                Custom Event Count (Optional Override)
              </label>
              <input
                type="number"
                placeholder="Leave blank for profile default"
                value={customEvents}
                onChange={(e) => setCustomEvents(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 font-mono outline-none focus:border-cyan-500 transition"
              />
            </div>

            {/* Controlled Anomaly Categories Injected Note */}
            <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg text-[11px] text-slate-400 space-y-1">
              <span className="font-bold text-slate-300 block">Controlled Anomaly Fixtures Included:</span>
              <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                <li>Acknowledgement Before Alarm (Rule 3)</li>
                <li>Impossible Interlock State (Rule 6)</li>
                <li>Incident Missing Trigger Context (Rule 7)</li>
                <li>Duplicate Alarm Replay (Rule 4)</li>
                <li>Action Closed Without Verification (Rule 8)</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={generating}
              className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-bold text-xs transition shadow-md flex items-center justify-center gap-2 cursor-pointer"
            >
              <RefreshCw className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />
              {generating ? 'Generating Synthetics...' : 'Execute Deterministic Generation'}
            </button>
          </form>

          {/* Success summary callout */}
          {genResult && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Generation Successful!
              </div>
              <p className="text-[11px] text-emerald-400/80">{genResult.message}</p>
              <div className="font-mono text-[10px] break-all pt-1 text-slate-300">
                SHA-256: {genResult.canonical_checksum}
              </div>
            </div>
          )}
        </div>

        {/* Entity Downloads & Evaluation Ground Truth */}
        <div className="lg:col-span-2 space-y-6">
          {/* Export Table Downloads */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <Download className="h-4 w-4 text-cyan-400" />
                Standard Dataset Downloads (CSV & JSON)
              </div>
              <span className="text-[11px] text-slate-400">Database & Streaming Exports</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {EXPORTABLE_ENTITIES.map((ent) => (
                <div
                  key={ent.name}
                  className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg flex items-center justify-between"
                >
                  <span className="text-xs font-medium text-slate-200">{ent.label}</span>
                  <div className="flex items-center gap-2">
                    <a
                      href={api.getExportUrl(ent.name, 'csv')}
                      download
                      className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-slate-700 rounded text-[10px] font-mono font-bold transition flex items-center gap-1"
                    >
                      <Download className="h-2.5 w-2.5" /> CSV
                    </a>
                    <a
                      href={api.getExportUrl(ent.name, 'json')}
                      download
                      className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-purple-400 border border-slate-700 rounded text-[10px] font-mono font-bold transition flex items-center gap-1"
                    >
                      <Download className="h-2.5 w-2.5" /> JSON
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Isolated Ground Truth Download Box */}
          <div className="bg-gradient-to-r from-red-950/30 to-amber-950/20 border border-red-900/50 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-red-400">
                <Shield className="h-5 w-5 text-red-400" />
                Evaluation Ground Truth (Strictly Isolated)
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-bold uppercase">
                Evaluation Only
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Ground-truth labels are generated into an isolated directory (<code className="text-cyan-400 font-mono">data/evaluation/</code>). The operational anomaly engine never reads these files during prediction. Download to audit benchmark test fixtures:
            </p>

            <div className="flex items-center gap-3 pt-1">
              <a
                href={api.getGroundTruthExportUrl('csv')}
                download
                className="px-4 py-2 bg-red-900/80 hover:bg-red-800 text-white font-bold rounded-lg text-xs transition flex items-center gap-2 shadow-sm"
              >
                <Download className="h-3.5 w-3.5" /> Download ground_truth.csv
              </a>
              <a
                href={api.getGroundTruthExportUrl('json')}
                download
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-lg text-xs transition flex items-center gap-2 border border-slate-700"
              >
                <Download className="h-3.5 w-3.5" /> Download ground_truth.json
              </a>
            </div>
          </div>

          {/* Dataset Manifest & Canonical Checksum */}
          {manifest && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-white">
                  <Hash className="h-4 w-4 text-cyan-400" />
                  Active Dataset Manifest & Canonical Hash
                </div>
                <span className="text-[10px] font-mono text-cyan-400">
                  Schema v{manifest.schema_version || '1.0.0'}
                </span>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300">
                <div>Origin: <span className="text-white">{manifest.origin}</span></div>
                <div>Seed: <span className="text-cyan-400">{manifest.seed}</span> | Profile: <span className="text-cyan-400">{manifest.profile}</span></div>
                <div className="break-all pt-1">Canonical SHA-256: <span className="text-emerald-400 font-bold">{manifest.canonical_checksum}</span></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
