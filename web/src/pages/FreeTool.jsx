import { useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";

export default function FreeTool() {
  const { workspaceId } = useParams();
  const [email, setEmail] = useState("");
  const [situation, setSituation] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  async function run(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await api.post(`/workspaces/${workspaceId}/freetool/run`, { email, input_value: situation });
      setResult(res);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Free Tool: ICP-Fit Calculator</h1>
      <p className="text-sm text-slate-500">
        A real, working lead magnet: describe your situation, get a fit score against this
        product&apos;s ICP. Captures the email as an attributed lead.
      </p>

      <form onSubmit={run} className="space-y-3">
        <input required type="email" placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm" />
        <textarea required rows={3} placeholder="Describe your current situation / pain..." value={situation}
          onChange={(e) => setSituation(e.target.value)}
          className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm" />
        <button disabled={busy} className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium disabled:opacity-50">
          {busy ? "Scoring..." : "Get my fit score"}
        </button>
      </form>

      {result && (
        <div className="rounded-lg border border-indigo-200 dark:border-indigo-900 bg-indigo-50 dark:bg-indigo-950 p-4">
          <div className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">{result.fit_score}%</div>
          <div className="text-sm text-slate-600 dark:text-slate-300">{result.summary}</div>
        </div>
      )}
    </div>
  );
}
