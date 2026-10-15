import { Button, Card, ErrorBox, Spinner } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";

const Dot = ({ ok }: { ok: boolean }) => <span className={`mr-2 inline-block h-3 w-3 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`} aria-hidden />;

export default function AdminSystem() {
  const { data, loading, error, reload } = useAsync(api.adminStatus, []);
  return (
    <>
      <div className="flex items-center justify-between"><h1 className="text-2xl font-bold">System status</h1><Button variant="secondary" onClick={reload}>Refresh</Button></div>
      {loading && !data ? <Spinner /> : error || !data ? <ErrorBox problem={error} onRetry={reload} /> : (
        <div className="grid gap-4 md:grid-cols-3">
          <Card title="Application"><p><Dot ok={data.application.status === "ok"} />API running</p><p className="mt-1 text-xs text-slate-500">Independent of the database and the AI model.</p></Card>
          <Card title="Database (MySQL)"><p><Dot ok={data.database.status === "ok"} />{data.database.message}</p></Card>
          <Card title="Local AI (Ollama)"><p><Dot ok={data.ai.reachable && data.ai.model_available} />{data.ai.message}</p>
            <p className="mt-2 text-sm">Model: <code>{data.config.model}</code></p><p className="text-sm">Server: <code>{data.ai.base_url}</code></p>
            <p className="mt-1 text-xs text-slate-500">If AI is down, scoring, leads, follow-ups and imports keep working.</p></Card>
        </div>)}
    </>
  );
}
