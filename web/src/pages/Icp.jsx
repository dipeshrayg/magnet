import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";

export default function Icp() {
  const { workspaceId } = useParams();
  const { data: icps, loading, error } = useApi(`/workspaces/${workspaceId}/icp`);
  const { data: profile } = useApi(`/workspaces/${workspaceId}/profile`);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">ICP Builder</h1>
      <StateBanner loading={loading} error={error} empty={icps && icps.length === 0} />

      {icps?.map((icp) => (
        <div key={icp.id} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-3">
          <div>
            <div className="text-xs uppercase text-slate-500">Segment</div>
            <div className="text-lg font-semibold">{icp.segment_name}</div>
            <div className="text-sm text-slate-500">{icp.description}</div>
          </div>
          <div>
            <div className="text-xs uppercase text-slate-500 mb-1">Pain points</div>
            <ul className="text-sm list-disc list-inside">{icp.pain_points.map((p) => <li key={p}>{p}</li>)}</ul>
          </div>
          <div>
            <div className="text-xs uppercase text-slate-500 mb-1">Buying triggers</div>
            <ul className="text-sm list-disc list-inside">{icp.buying_triggers.map((p) => <li key={p}>{p}</li>)}</ul>
          </div>
          <div>
            <div className="text-xs uppercase text-slate-500 mb-1">Firmographics</div>
            <div className="text-sm">{JSON.stringify(icp.firmographics)}</div>
          </div>
        </div>
      ))}

      {profile && (
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
          <div className="text-xs uppercase text-slate-500 mb-1">Source: Product Profile keywords</div>
          <div className="flex flex-wrap gap-1">
            {profile.keywords.map((k) => (
              <span key={k} className="text-xs bg-slate-100 dark:bg-slate-800 rounded px-2 py-0.5">{k}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
