import { useCallback, useEffect, useState } from "react";
import { api } from "./api";

export function useApi(path) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    api.get(path).then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [path]);

  // Data fetching on mount/path-change is exactly the "synchronize with an
  // external system" case the effect rule is meant to allow.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { reload(); }, [reload]);

  return { data, loading, error, reload };
}

export function StateBanner({ loading, error, empty, emptyText = "Nothing here yet." }) {
  if (loading) return <div className="text-sm text-slate-500 py-8 text-center">Loading...</div>;
  if (error) return <div className="text-sm text-red-600 py-8 text-center">Error: {error}</div>;
  if (empty) return <div className="text-sm text-slate-500 py-8 text-center border border-dashed rounded-lg border-slate-300 dark:border-slate-700">{emptyText}</div>;
  return null;
}
