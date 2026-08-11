import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export default function AddProduct() {
  const [mode, setMode] = useState("manual");
  const [name, setName] = useState("");
  const [rawText, setRawText] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const navigate = useNavigate();

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const res = mode === "manual"
        ? await api.post("/workspaces/onboard/manual", { name, raw_text: rawText })
        : await api.post("/workspaces/onboard/url", { name, url });
      navigate(`/w/${res.workspace.id}`);
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Add Product</h1>
      <p className="text-slate-500 text-sm mb-6">
        Adding a product creates a new workspace. MAGNET derives a ProductProfile and ICP
        from what you give it here -- every module downstream reads from that profile.
      </p>

      <div className="flex gap-2 mb-4">
        <button onClick={() => setMode("manual")} className={`px-3 py-1.5 text-sm rounded ${mode === "manual" ? "bg-indigo-600 text-white" : "bg-slate-100 dark:bg-slate-800"}`}>
          Manual / Demo (no API keys needed)
        </button>
        <button onClick={() => setMode("url")} className={`px-3 py-1.5 text-sm rounded ${mode === "url" ? "bg-indigo-600 text-white" : "bg-slate-100 dark:bg-slate-800"}`}>
          From URL
        </button>
      </div>

      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Product name</label>
          <input required value={name} onChange={(e) => setName(e.target.value)}
            className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm" />
        </div>

        {mode === "manual" ? (
          <div>
            <label className="block text-sm font-medium mb-1">Describe the product</label>
            <textarea required rows={6} value={rawText} onChange={(e) => setRawText(e.target.value)}
              placeholder="Paste a description, product.yaml contents, or a short pitch..."
              className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm" />
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium mb-1">Landing page URL</label>
            <input required type="url" value={url} onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-sm" />
            <p className="text-xs text-slate-500 mt-1">MAGNET respects robots.txt and only reads public pages.</p>
          </div>
        )}

        {err && <div className="text-sm text-red-600">{err}</div>}

        <button disabled={busy} type="submit" className="rounded bg-indigo-600 text-white px-4 py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
          {busy ? "Creating..." : "Create workspace"}
        </button>
      </form>
    </div>
  );
}
