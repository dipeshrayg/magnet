import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

export default function Lifecycle() {
  const { workspaceId } = useParams();
  const { data: messages, loading, error, reload } = useApi(`/workspaces/${workspaceId}/lifecycle`);
  const [scanning, setScanning] = useState(false);

  async function scan() {
    setScanning(true);
    try {
      await api.post(`/workspaces/${workspaceId}/lifecycle/scan`);
      reload();
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Lifecycle</h1>
        <button onClick={scan} disabled={scanning} className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
          {scanning ? "Scanning..." : "Find stalled signups"}
        </button>
      </div>
      <p className="text-sm text-slate-500">Users who signed up but never activated get a draft rescue email, routed to the Approval Inbox.</p>

      <StateBanner loading={loading} error={error} empty={messages && messages.length === 0} />

      <div className="grid gap-2">
        {messages?.map((m) => (
          <div key={m.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
            <div className="text-xs text-slate-500 uppercase">{m.kind} -- {m.status}</div>
            <p className="text-sm mt-1">{m.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
