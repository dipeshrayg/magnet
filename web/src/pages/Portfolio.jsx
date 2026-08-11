import { Link } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";

export default function Portfolio() {
  const { data, loading, error } = useApi("/portfolio");

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Portfolio</h1>
          <p className="text-slate-500 text-sm">Every product, one growth engine. Compare funnels side by side.</p>
        </div>
        <Link to="/add" className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium hover:bg-indigo-700">
          + Add Product
        </Link>
      </div>

      <StateBanner loading={loading} error={error} empty={data && data.length === 0}
        emptyText="No products yet. Add your first product to get started." />

      {data && data.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          {data.map(({ workspace, funnel }) => (
            <Link
              key={workspace.id}
              to={`/w/${workspace.id}`}
              className="rounded-lg border border-slate-200 dark:border-slate-800 p-4 hover:border-indigo-400 transition bg-white dark:bg-slate-900"
            >
              <div className="font-semibold text-lg">{workspace.name}</div>
              <dl className="mt-3 space-y-1 text-sm">
                {["visit", "lead", "signup", "activation", "revenue"].map((stage) => (
                  <div key={stage} className="flex justify-between">
                    <dt className="capitalize text-slate-500">{stage}</dt>
                    <dd className="font-medium">{funnel.counts[stage]}</dd>
                  </div>
                ))}
                <div className="flex justify-between border-t border-slate-200 dark:border-slate-800 pt-1 mt-1">
                  <dt className="text-slate-500">Revenue</dt>
                  <dd className="font-medium">${funnel.revenue}</dd>
                </div>
              </dl>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
