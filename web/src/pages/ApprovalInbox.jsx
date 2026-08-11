import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

const STATUS_COLOR = {
  PENDING_APPROVAL: "bg-amber-100 text-amber-800",
  APPROVED: "bg-blue-100 text-blue-800",
  REJECTED: "bg-red-100 text-red-800",
  SENT: "bg-green-100 text-green-800",
  EXPORTED: "bg-green-100 text-green-800",
};

export default function ApprovalInbox() {
  const { workspaceId } = useParams();
  const { data: items, loading, error, reload } = useApi(`/workspaces/${workspaceId}/approvals`);
  const [editing, setEditing] = useState({});
  const [busyId, setBusyId] = useState(null);

  async function act(id, action) {
    setBusyId(id);
    try {
      await api.post(`/workspaces/${workspaceId}/approvals/${id}/${action}`);
      reload();
    } finally {
      setBusyId(null);
    }
  }

  async function saveEdit(id) {
    await api.post(`/workspaces/${workspaceId}/approvals/${id}/edit`, { content: editing[id] });
    setEditing((e) => ({ ...e, [id]: undefined }));
    reload();
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Approval Inbox</h1>
      <div className="rounded-lg bg-indigo-50 dark:bg-indigo-950 border border-indigo-200 dark:border-indigo-900 px-4 py-3 text-sm text-indigo-800 dark:text-indigo-200">
        Nothing leaves MAGNET without human approval. Approve first, then Send/Export -- every decision is audit-logged.
      </div>

      <StateBanner loading={loading} error={error} empty={items && items.length === 0} emptyText="Nothing pending. Run a scan in any module to generate drafts." />

      <div className="space-y-2">
        {items?.map((item) => (
          <div key={item.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
            <div className="flex items-center justify-between mb-1">
              <div className="text-xs text-slate-500">{item.source_module} -- {item.type} -- target: {item.target}</div>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded ${STATUS_COLOR[item.status]}`}>{item.status}</span>
            </div>
            <div className="text-xs text-slate-400 mb-1">Reason: {item.reason}</div>

            {editing[item.id] !== undefined ? (
              <textarea value={editing[item.id]} onChange={(e) => setEditing((s) => ({ ...s, [item.id]: e.target.value }))}
                rows={3} className="w-full text-sm rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2" />
            ) : (
              <p className="text-sm whitespace-pre-wrap">{item.draft_content}</p>
            )}

            <div className="flex gap-2 mt-2">
              {item.status === "PENDING_APPROVAL" && editing[item.id] === undefined && (
                <>
                  <button onClick={() => act(item.id, "approve")} disabled={busyId === item.id} className="text-xs rounded bg-green-600 text-white px-3 py-1.5">Approve</button>
                  <button onClick={() => setEditing((s) => ({ ...s, [item.id]: item.draft_content }))} className="text-xs rounded border border-slate-300 dark:border-slate-700 px-3 py-1.5">Edit</button>
                  <button onClick={() => act(item.id, "reject")} disabled={busyId === item.id} className="text-xs rounded bg-red-600 text-white px-3 py-1.5">Reject</button>
                </>
              )}
              {editing[item.id] !== undefined && (
                <>
                  <button onClick={() => saveEdit(item.id)} className="text-xs rounded bg-indigo-600 text-white px-3 py-1.5">Save edit</button>
                  <button onClick={() => setEditing((s) => ({ ...s, [item.id]: undefined }))} className="text-xs rounded border border-slate-300 dark:border-slate-700 px-3 py-1.5">Cancel</button>
                </>
              )}
              {item.status === "APPROVED" && (
                <button onClick={() => act(item.id, "export")} disabled={busyId === item.id} className="text-xs rounded bg-indigo-600 text-white px-3 py-1.5">Send / Export</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
