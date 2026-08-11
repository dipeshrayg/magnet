import { useParams } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useApi, StateBanner } from "../lib/useApi";

export default function Dashboard() {
  const { workspaceId } = useParams();
  const { data: report, loading, error } = useApi(`/workspaces/${workspaceId}/analytics/report`);
  const { data: profile } = useApi(`/workspaces/${workspaceId}/profile`);

  const chartData = report ? Object.entries(report.funnel.counts).map(([stage, count]) => ({ stage, count })) : [];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="rounded-lg bg-indigo-50 dark:bg-indigo-950 border border-indigo-200 dark:border-indigo-900 px-4 py-3 text-sm text-indigo-800 dark:text-indigo-200">
        MAGNET never publishes or sends automatically. Every outward action requires human approval in the Approval Inbox.
      </div>

      <div>
        <h1 className="text-2xl font-bold">{profile?.name || "Dashboard"}</h1>
        <p className="text-slate-500 text-sm">{profile?.positioning}</p>
      </div>

      <StateBanner loading={loading} error={error} empty={false} />

      {report && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {Object.entries(report.funnel.counts).map(([stage, count]) => (
              <div key={stage} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3">
                <div className="text-xs uppercase text-slate-500">{stage}</div>
                <div className="text-xl font-bold">{count}</div>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
            <h2 className="font-semibold mb-3">Funnel</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
            <h2 className="font-semibold mb-2">ROI by module</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="py-1">Module</th><th>Events</th><th>Leads</th><th>Revenue</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(report.roi_by_module).map(([mod, r]) => (
                  <tr key={mod} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="py-1">{mod}</td><td>{r.events}</td><td>{r.leads}</td><td>${r.revenue.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
