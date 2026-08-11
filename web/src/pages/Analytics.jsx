import { useParams } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useApi, StateBanner } from "../lib/useApi";

export default function Analytics() {
  const { workspaceId } = useParams();
  const { data: report, loading, error } = useApi(`/workspaces/${workspaceId}/analytics/report`);

  const roiData = report ? Object.entries(report.roi_by_module).map(([mod, r]) => ({ module: mod, revenue: r.revenue })) : [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Growth Analytics</h1>
      <StateBanner loading={loading} error={error} empty={false} />

      {report && (
        <>
          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 text-sm">
            {report.summary}
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
            <h2 className="font-semibold mb-2">Conversion rates by stage</h2>
            <table className="w-full text-sm">
              <tbody>
                {Object.entries(report.funnel.conversion_rates).map(([stage, rate]) => (
                  <tr key={stage} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="py-1 capitalize">{stage}</td>
                    <td className="text-right font-medium">{(rate * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
            <h2 className="font-semibold mb-3">Revenue by module (ROI)</h2>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={roiData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="module" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="revenue" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
