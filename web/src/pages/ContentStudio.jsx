import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

export default function ContentStudio() {
  const { workspaceId } = useParams();
  const { data: pieces, loading, error, reload } = useApi(`/workspaces/${workspaceId}/content`);
  const [idea, setIdea] = useState("");
  const [busy, setBusy] = useState(false);

  async function generate(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post(`/workspaces/${workspaceId}/content/generate`, { idea });
      setIdea("");
      reload();
    } finally {
      setBusy(false);
    }
  }

  async function schedule(id) {
    await api.post(`/workspaces/${workspaceId}/content/${id}/schedule`);
    alert("Sent to Approval Inbox for review -- MAGNET never posts automatically.");
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Content Studio</h1>
      <form onSubmit={generate} className="flex gap-2">
        <input required value={idea} onChange={(e) => setIdea(e.target.value)} placeholder="One content idea..."
          className="flex-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm" />
        <button disabled={busy} className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
          {busy ? "Generating..." : "Generate variants"}
        </button>
      </form>

      <StateBanner loading={loading} error={error} empty={pieces && pieces.length === 0} />

      <div className="grid gap-2">
        {pieces?.map((p) => (
          <div key={p.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-semibold text-indigo-600 dark:text-indigo-400">{p.channel}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">hook {(p.hook_score * 100).toFixed(0)}% / virality {(p.virality_score * 100).toFixed(0)}%</span>
                <button onClick={() => schedule(p.id)} className="text-xs rounded border border-slate-300 dark:border-slate-700 px-2 py-1">Schedule (via Approval)</button>
              </div>
            </div>
            <p className="text-sm mt-1">{p.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
