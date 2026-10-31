import React, { useEffect, useState } from 'react';
import {
  CheckCircle2, AlertTriangle, ShieldCheck, Clock, User,
  Check, X, RefreshCw, ChevronLeft, ChevronRight, AlertOctagon
} from 'lucide-react';
import { api } from '../services/api';
import { CorrectiveAction } from '../types';

export const CorrectiveActionsPage: React.FC = () => {
  const [actions, setActions] = useState<CorrectiveAction[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [verificationFilter, setVerificationFilter] = useState<string>('');

  // Action update feedback
  const [alertMessage, setAlertMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadActions = async () => {
    setLoading(true);
    try {
      const res = await api.getCorrectiveActions({
        action_status: statusFilter || undefined,
        verification_status: verificationFilter || undefined,
        page,
        page_size: 20
      });
      setActions(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to load corrective actions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActions();
  }, [statusFilter, verificationFilter, page]);

  // Workflow Action 1: Transition Status (e.g. IN_PROGRESS or COMPLETED)
  const handleTransitionStatus = async (actionId: string, newStatus: string) => {
    setAlertMessage(null);
    try {
      await api.updateCorrectiveAction(actionId, {
        action_status: newStatus,
        actor: 'OPERATIONS_SUPERVISOR',
        notes: `Transitioned status to ${newStatus}`
      });
      setAlertMessage({ type: 'success', text: `Action ${actionId} successfully updated to ${newStatus}.` });
      loadActions();
    } catch (err: any) {
      setAlertMessage({ type: 'error', text: err.message || 'Workflow transition rejected' });
    }
  };

  // Workflow Action 2: Audit Sign-off Verification Gate
  const handleVerifyAction = async (actionId: string) => {
    setAlertMessage(null);
    try {
      await api.verifyCorrectiveAction(actionId, 'SAFETY_AUDITOR_CERTIFIED', 'Independent physical inspection signed off.');
      setAlertMessage({ type: 'success', text: `Action ${actionId} verified and safely closed with audit log.` });
      loadActions();
    } catch (err: any) {
      setAlertMessage({ type: 'error', text: err.message || 'Verification sign-off failed' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <CheckCircle2 className="h-6 w-6 text-emerald-400" />
          Corrective Actions & Safety Verification
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Remediation tracking, independent verification gate enforcement, and compliance audit trail
        </p>
      </div>

      {/* Alert Banner */}
      {alertMessage && (
        <div className={`p-4 rounded-xl border text-xs flex items-center justify-between ${
          alertMessage.type === 'success'
            ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
            : 'bg-red-950/40 border-red-800 text-red-300'
        }`}>
          <div className="flex items-center gap-2">
            {alertMessage.type === 'success' ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
            <span>{alertMessage.text}</span>
          </div>
          <button onClick={() => setAlertMessage(null)} className="text-slate-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Lifecycle Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="IN_PROGRESS">IN_PROGRESS</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="CLOSED">CLOSED</option>
          </select>

          <select
            value={verificationFilter}
            onChange={(e) => { setVerificationFilter(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="">All Verification Gates</option>
            <option value="PENDING">PENDING</option>
            <option value="VERIFIED">VERIFIED</option>
          </select>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>{total} total remediation items</span>
          <button onClick={loadActions} className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Actions Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Action ID</th>
                <th className="py-3 px-4">Parent Incident</th>
                <th className="py-3 px-4">Action Type & Narrative</th>
                <th className="py-3 px-4">Assigned Team</th>
                <th className="py-3 px-4">Action Status</th>
                <th className="py-3 px-4">Verification Gate</th>
                <th className="py-3 px-4 text-center">Audit Anomaly</th>
                <th className="py-3 px-4 text-right">Workflow Transition</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    Loading corrective actions...
                  </td>
                </tr>
              ) : actions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    No corrective action records.
                  </td>
                </tr>
              ) : (
                actions.map((act) => {
                  const isUnverifiedClosed =
                    act.action_status === 'CLOSED' && (act.verification_status !== 'VERIFIED' || !act.verified_at);

                  return (
                    <tr
                      key={act.corrective_action_id}
                      className={`hover:bg-slate-800/40 transition ${
                        isUnverifiedClosed ? 'bg-red-950/20' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-cyan-400 whitespace-nowrap">
                        {act.corrective_action_id}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300 whitespace-nowrap">
                        {act.incident_id}
                      </td>
                      <td className="py-3 px-4 max-w-xs">
                        <div className="font-semibold text-slate-200">{act.action_type}</div>
                        <div className="text-[11px] text-slate-400 truncate">{act.description}</div>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-300">
                        {act.assigned_team}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          act.action_status === 'CLOSED' ? 'bg-slate-800 text-slate-300 border border-slate-700' :
                          act.action_status === 'COMPLETED' ? 'bg-blue-950 text-blue-400 border border-blue-800' :
                          act.action_status === 'IN_PROGRESS' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                          'bg-purple-950 text-purple-300 border border-purple-800'
                        }`}>
                          {act.action_status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          act.verification_status === 'VERIFIED'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-yellow-950 text-yellow-400 border border-yellow-800'
                        }`}>
                          {act.verification_status === 'VERIFIED' ? <ShieldCheck className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                          {act.verification_status}
                        </span>
                        {act.verified_at && (
                          <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                            {new Date(act.verified_at).toLocaleDateString()}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {isUnverifiedClosed ? (
                          <span className="inline-block px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-mono text-[9px] font-bold">
                            CLOSED_UNVERIFIED
                          </span>
                        ) : (
                          <span className="text-slate-600">-</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {act.action_status === 'OPEN' && (
                            <button
                              onClick={() => handleTransitionStatus(act.corrective_action_id, 'IN_PROGRESS')}
                              className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-200 px-2 py-1 rounded transition border border-slate-700"
                            >
                              Start
                            </button>
                          )}
                          {act.action_status === 'IN_PROGRESS' && (
                            <button
                              onClick={() => handleTransitionStatus(act.corrective_action_id, 'COMPLETED')}
                              className="text-[11px] bg-slate-800 hover:bg-slate-700 text-blue-300 px-2 py-1 rounded transition border border-slate-700"
                            >
                              Complete Work
                            </button>
                          )}
                          {act.verification_status !== 'VERIFIED' && (
                            <button
                              onClick={() => handleVerifyAction(act.corrective_action_id)}
                              className="text-[11px] bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-800 px-2 py-1 rounded font-semibold transition flex items-center gap-1"
                            >
                              <ShieldCheck className="h-3 w-3" /> Verify & Close
                            </button>
                          )}
                          {/* Test Rule 8 Gate Button: Attempt premature close */}
                          {act.action_status !== 'CLOSED' && act.verification_status !== 'VERIFIED' && (
                            <button
                              onClick={() => handleTransitionStatus(act.corrective_action_id, 'CLOSED')}
                              title="Test Rule 8 Gate (Expected 422 Rejection)"
                              className="text-[10px] bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-900 px-1.5 py-1 rounded font-mono"
                            >
                              Try Bypass
                            </button>
                          )}
                        </div>
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
    </div>
  );
};
