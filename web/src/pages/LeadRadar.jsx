import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

export default function LeadRadar() {
  const { workspaceId } = useParams();
  const { data: leads, loading, error, reload } = useApi(`/workspaces/${workspaceId}/leads`);
  const [scanning, setScanning] = useState(false);

  async function scan() {
    setScanning(true);
    try {
      await api.post(`/workspaces/${workspaceId}/leads/scan`);
      reload();
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Lead Radar</h1>
        <button onClick={scan} disabled={scanning} className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
          {scanning ? "Scanning..." : "Scan community sources"}
        </button>
      </div>
      <p className="text-sm text-slate-500">
        High-opportunity leads get a helpful reply draft sent to the Approval Inbox. Nothing is posted automatically.
      </p>

      <StateBanner loading={loading} error={error} empty={leads && leads.length === 0} emptyText="No leads yet. Run a scan." />

      {leads && leads.length > 0 && (
        <table className="w-full text-sm bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-200 dark:border-slate-800">
              <th className="p-2">Source</th><th>Opportunity</th><th>Intent</th><th>Pain</th><th>Evidence</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((l) => (
              <tr key={l.id} className="border-t border-slate-100 dark:border-slate-800">
                <td className="p-2">{l.source}</td>
                <td><span className="font-semibold">{(l.opportunity_score * 100).toFixed(0)}%</span></td>
                <td>{(l.intent_score * 100).toFixed(0)}%</td>
                <td>{(l.pain_score * 100).toFixed(0)}%</td>
                <td className="max-w-md truncate">{l.evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
