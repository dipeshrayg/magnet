import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";
import { api } from "../lib/api";

const COLUMNS = ["requested", "planned", "in_progress", "shipped"];

export default function Voc() {
  const { workspaceId } = useParams();
  const { data: items, loading, error, reload } = useApi(`/workspaces/${workspaceId}/voc`);

  async function move(item, status) {
    await api.put(`/workspaces/${workspaceId}/voc/${item.id}/status`, { status });
    reload();
  }

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Voice of Customer</h1>
      <StateBanner loading={loading} error={error} empty={items && items.length === 0} />

      <div className="grid grid-cols-4 gap-3">
        {COLUMNS.map((col) => (
          <div key={col}>
            <h2 className="text-sm font-semibold capitalize mb-2">{col.replace("_", " ")}</h2>
            <div className="space-y-2">
              {items?.filter((i) => i.roadmap_status === col).map((i) => (
                <div key={i.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 text-xs">
                  <div className="font-medium">{i.cluster}</div>
                  <div className="text-slate-500">{i.evidence}</div>
                  <select value={i.roadmap_status} onChange={(e) => move(i, e.target.value)}
                    className="mt-1 w-full text-xs border border-slate-300 dark:border-slate-700 rounded bg-white dark:bg-slate-900">
                    {COLUMNS.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
