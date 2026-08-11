import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

export default function CompetitorWatch() {
  const { workspaceId } = useParams();
  const { data: competitors } = useApi(`/workspaces/${workspaceId}/competitors`);
  const { data: events, loading, error, reload } = useApi(`/workspaces/${workspaceId}/competitor-events`);
  const [scanning, setScanning] = useState(false);
  const nameById = Object.fromEntries((competitors || []).map((c) => [c.id, c.name]));

  async function scan() {
    setScanning(true);
    try {
      await api.post(`/workspaces/${workspaceId}/competitors/scan`);
      reload();
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Competitor Watch</h1>
        <button onClick={scan} disabled={scanning} className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
          {scanning ? "Scanning..." : "Scan for switch opportunities"}
        </button>
      </div>

      <StateBanner loading={loading} error={error} empty={events && events.length === 0} />

      <div className="grid gap-2">
        {events?.map((e) => (
          <div key={e.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 flex items-start justify-between">
            <div>
              <div className="font-medium">{nameById[e.competitor_id] || "Competitor"} -- {e.type.replace("_", " ")}</div>
              <div className="text-sm text-slate-500">{e.description}</div>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded font-semibold ${e.severity === "high" ? "bg-red-100 text-red-700" : e.severity === "medium" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-700"}`}>
              {e.severity}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
