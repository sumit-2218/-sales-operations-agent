import { useSearchParams } from "react-router-dom";
import FollowUpRow from "../components/FollowUpRow";
import { Card, Empty, ErrorBox, Pagination, Select, Spinner } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";

export default function FollowUpsPage() {
  const [sp, setSp] = useSearchParams();
  const g = (k: string) => sp.get(k) ?? "";
  const params = { status: g("status"), priority: g("priority"), overdue: g("overdue"), page: Number(g("page") || 1), page_size: 20 };
  const { data, loading, error, reload } = useAsync(() => api.followUps(params), [sp.toString()]);
  const upd = (k: string, v: string) => { const n = new URLSearchParams(sp); v ? n.set(k, v) : n.delete(k); if (k !== "page") n.delete("page"); setSp(n); };
  return (
    <>
      <h1 className="text-2xl font-bold">Follow-ups</h1>
      <p className="text-sm text-slate-600">Create follow-ups from a lead's page. They are tracked here only — no emails or notifications are sent.</p>
      <Card><div className="grid gap-3 md:grid-cols-4">
        <Select label="Status" value={params.status} onChange={(e) => upd("status", e.target.value)}><option value="">All</option><option value="open">Open</option><option value="completed">Completed</option><option value="cancelled">Cancelled</option></Select>
        <Select label="Priority" value={params.priority} onChange={(e) => upd("priority", e.target.value)}><option value="">All</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></Select>
        <Select label="Due" value={params.overdue} onChange={(e) => upd("overdue", e.target.value)}><option value="">Any</option><option value="true">Overdue only</option><option value="false">Not overdue</option></Select>
      </div></Card>
      {loading ? <Spinner /> : error ? <ErrorBox problem={error} onRetry={reload} /> : !data?.items.length ? <Empty title="No follow-ups match" hint="Open a lead and add a follow-up task." /> : (
        <Card><ul className="divide-y">{data.items.map((f) => <FollowUpRow key={`${f.id}-${f.status}`} f={f} companyLink onChanged={reload} />)}</ul>
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onChange={(p) => upd("page", String(p))} /></Card>)}
    </>
  );
}
