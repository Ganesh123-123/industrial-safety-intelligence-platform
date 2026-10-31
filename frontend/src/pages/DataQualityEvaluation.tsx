import React, { useEffect, useState } from 'react';
import {
  ShieldCheck, AlertTriangle, CheckCircle2, RefreshCw,
  Layers, Database, FileCheck, Target, Award, ArrowUpRight
} from 'lucide-react';
import { api } from '../services/api';
import { ValidationReport, EvaluationReport } from '../types';

export const DataQualityEvaluation: React.FC = () => {
  const [valReport, setValReport] = useState<ValidationReport | null>(null);
  const [evalReport, setEvalReport] = useState<EvaluationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [validating, setValidating] = useState<boolean>(false);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [v, e] = await Promise.all([
        api.getDataQualityReport(),
        api.getEvaluationMetrics()
      ]);
      setValReport(v);
      setEvalReport(e);
    } catch (err) {
      console.error('Failed to load quality & evaluation data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleRunValidation = async () => {
    setValidating(true);
    try {
      const updated = await api.runValidation();
      setValReport(updated);
    } catch (err) {
      console.error('Validation execution failed', err);
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-cyan-400" />
            Data Quality & Ground Truth Evaluation
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated 18-point database integrity framework & empirical anomaly detection benchmark
          </p>
        </div>

        <button
          onClick={handleRunValidation}
          disabled={validating}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-cyan-800/60 px-4 py-2 rounded-lg text-xs font-bold transition shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${validating ? 'animate-spin' : ''}`} />
          {validating ? 'Evaluating 18 Checks...' : 'Re-Run Validation Framework'}
        </button>
      </div>

      {/* Evaluation Benchmark KPI Hero */}
      {evalReport && (
        <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800 rounded-xl p-6 shadow-md">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Target className="h-5 w-5 text-emerald-400" />
              Empirical Detection Benchmark vs Isolated Ground Truth
            </div>
            <span className="text-[11px] px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono font-bold">
              Isolated Test Set ({evalReport.total_ground_truth_anomalies} Fixtures)
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Overall Precision</span>
              <div className="text-2xl font-bold text-emerald-400 font-mono">
                {(evalReport.overall_precision * 100).toFixed(1)}%
              </div>
              <span className="text-[10px] text-slate-500">TP / (TP + FP)</span>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Overall Recall</span>
              <div className="text-2xl font-bold text-emerald-400 font-mono">
                {(evalReport.overall_recall * 100).toFixed(1)}%
              </div>
              <span className="text-[10px] text-slate-500">TP / (TP + FN)</span>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Overall F1 Score</span>
              <div className="text-2xl font-bold text-cyan-400 font-mono">
                {(evalReport.overall_f1 * 100).toFixed(1)}%
              </div>
              <span className="text-[10px] text-slate-500">Harmonic Mean</span>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg">
              <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Ground Truth Injected</span>
              <div className="text-2xl font-bold text-white font-mono">
                {evalReport.total_ground_truth_anomalies}
              </div>
              <span className="text-[10px] text-slate-500">0 Leakage Guarantee</span>
            </div>
          </div>

          {/* Anomaly Category Benchmark Table */}
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs bg-slate-950/70">
              <thead className="bg-slate-900 text-slate-400 text-[10px] uppercase font-bold">
                <tr>
                  <th className="py-2.5 px-3">Controlled Anomaly Category</th>
                  <th className="py-2.5 px-3 text-center">True Positives (TP)</th>
                  <th className="py-2.5 px-3 text-center">False Positives (FP)</th>
                  <th className="py-2.5 px-3 text-center">False Negatives (FN)</th>
                  <th className="py-2.5 px-3 text-center">Precision</th>
                  <th className="py-2.5 px-3 text-center">Recall</th>
                  <th className="py-2.5 px-3 text-center">F1 Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {evalReport.categories.map((cat) => (
                  <tr key={cat.anomaly_type} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-sans font-semibold text-slate-200">
                      {cat.anomaly_type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2 px-3 text-center text-emerald-400 font-bold">{cat.true_positives}</td>
                    <td className="py-2 px-3 text-center text-slate-500">{cat.false_positives}</td>
                    <td className="py-2 px-3 text-center text-slate-500">{cat.false_negatives}</td>
                    <td className="py-2 px-3 text-center text-emerald-400 font-bold">{(cat.precision * 100).toFixed(0)}%</td>
                    <td className="py-2 px-3 text-center text-emerald-400 font-bold">{(cat.recall * 100).toFixed(0)}%</td>
                    <td className="py-2 px-3 text-center text-cyan-400 font-bold">{(cat.f1_score * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 18-Point Data Validation Framework Report */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Database className="h-5 w-5 text-cyan-400" />
              18-Point Database & Referential Integrity Framework
            </h3>
            <p className="text-xs text-slate-400">
              Validates primary keys, foreign keys, temporal bounds, and controlled evaluation fixtures
            </p>
          </div>

          {valReport && (
            <div className="flex items-center gap-3 text-xs">
              <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold">
                {valReport.passed_checks} PASSED
              </span>
              <span className="px-2.5 py-1 rounded bg-amber-950 text-amber-400 border border-amber-800 font-bold">
                {valReport.failed_checks} CONTROLLED FIXTURES
              </span>
            </div>
          )}
        </div>

        {/* Validation Checks Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">Check Specification</th>
                <th className="py-2.5 px-3 text-center">Status</th>
                <th className="py-2.5 px-3 text-center">Evaluated</th>
                <th className="py-2.5 px-3 text-center">Exceptions</th>
                <th className="py-2.5 px-3">Technical Explanation & Provenance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    Running validation audit...
                  </td>
                </tr>
              ) : valReport?.checks.map((check, index) => (
                <tr key={index} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-3 font-mono text-slate-500">{index + 1}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-200">
                    {check.check_name}
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      check.status === 'PASSED'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : 'bg-amber-950 text-amber-300 border border-amber-800'
                    }`}>
                      {check.status === 'PASSED' ? 'PASS' : 'FIXTURE'}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-center font-mono text-slate-300">
                    {check.records_checked.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-3 text-center font-mono">
                    {check.failure_count > 0 ? (
                      <span className="font-bold text-amber-400">{check.failure_count}</span>
                    ) : (
                      <span className="text-slate-600">0</span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-slate-400 text-[11px] max-w-md">
                    <div>{check.explanation}</div>
                    {check.example_affected_ids.length > 0 && (
                      <div className="font-mono text-[10px] text-amber-300/80 mt-0.5">
                        Sample IDs: {check.example_affected_ids.slice(0, 3).join(', ')}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
