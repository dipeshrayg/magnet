import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

export default function Outreach() {
  const { workspaceId } = useParams();
  const { data: leads } = useApi(`/workspaces/${workspaceId}/leads`);
  const { data: messages, loading, error, reload } = useApi(`/workspaces/${workspaceId}/outreach`);
  const [busyId, setBusyId] = useState(null);

  async function generate(leadId) {
    setBusyId(leadId);
    try {
      await api.post(`/workspaces/${workspaceId}/outreach/${leadId}/generate`);
      reload();
      alert("Sequence generated, step 1 sent to Approval Inbox.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Outreach</h1>

      <div>
        <h2 className="font-semibold mb-2">Generate a sequence for a lead</h2>
        <div className="grid gap-2">
          {(leads || []).slice(0, 8).map((l) => (
            <div key={l.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 flex items-center justify-between">
              <div className="text-sm max-w-lg truncate">{l.evidence}</div>
              <button onClick={() => generate(l.id)} disabled={busyId === l.id}
                className="text-xs rounded bg-indigo-600 text-white px-3 py-1.5 disabled:opacity-50">
                {busyId === l.id ? "Generating..." : "Generate outreach"}
              </button>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="font-semibold mb-2">Drafted messages</h2>
        <StateBanner loading={loading} error={error} empty={messages && messages.length === 0} />
        <div className="grid gap-2">
          {messages?.map((m) => (
            <div key={m.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
              <div className="text-xs text-slate-500">Step {m.step} -- {m.subject} -- {m.status}</div>
              <p className="text-sm mt-1">{m.body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
