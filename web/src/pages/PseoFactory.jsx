import { useState } from "react";
import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

export default function PseoFactory() {
  const { workspaceId } = useParams();
  const { data: pages, loading, error, reload } = useApi(`/workspaces/${workspaceId}/pages`);
  const [generating, setGenerating] = useState(false);

  async function generate() {
    setGenerating(true);
    try {
      await api.post(`/workspaces/${workspaceId}/pages/generate`);
      reload();
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">pSEO Factory</h1>
          <p className="text-sm text-slate-500">{pages?.length || 0} pages generated for this product</p>
        </div>
        <button onClick={generate} disabled={generating} className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
          {generating ? "Generating..." : "Regenerate pages"}
        </button>
      </div>

      <StateBanner loading={loading} error={error} empty={pages && pages.length === 0} emptyText="No pages yet. Generate the pSEO dataset." />

      <div className="grid gap-2 max-h-[70vh] overflow-y-auto">
        {pages?.map((p) => (
          <details key={p.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
            <summary className="cursor-pointer font-medium text-sm">{p.title} <span className="text-xs text-slate-400 ml-2">{p.template}</span></summary>
            <p className="text-sm text-slate-500 mt-2">{p.body}</p>
            <div className="text-xs text-slate-400 mt-1">canonical: {p.canonical_url}</div>
          </details>
        ))}
      </div>
    </div>
  );
}
