import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

export default function Reputation() {
  const { workspaceId } = useParams();
  const { data: reviews, loading, error, reload } = useApi(`/workspaces/${workspaceId}/reviews`);
  const [scanning, setScanning] = useState(false);

  async function scan() {
    setScanning(true);
    try {
      await api.post(`/workspaces/${workspaceId}/reputation/scan`);
      reload();
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Reputation</h1>
        <button onClick={scan} disabled={scanning} className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
          {scanning ? "Scanning..." : "Draft responses to negative reviews"}
        </button>
      </div>

      <StateBanner loading={loading} error={error} empty={reviews && reviews.length === 0} />

      <div className="grid gap-2">
        {reviews?.map((r) => (
          <div key={r.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">{r.source} -- {r.subject}</div>
              <div className="text-sm font-semibold">{r.rating.toFixed(1)}/5</div>
            </div>
            <div className="text-sm text-slate-500">{r.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
