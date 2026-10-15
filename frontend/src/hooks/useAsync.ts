import { useCallback, useEffect, useState } from "react";
import { apiProblem, ApiProblem } from "../utils/errors";

/** Loads data with loading/error state; `reload()` refetches. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiProblem | null>(null);
  const [loading, setLoading] = useState(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fn, deps);
  const reload = useCallback(async () => {
    setLoading(true);
    try { setData(await run()); setError(null); } catch (e) { setError(apiProblem(e)); } finally { setLoading(false); }
  }, [run]);
  useEffect(() => { void reload(); }, [reload]);
  return { data, error, loading, reload, setData };
}
