import { Card, ErrorBox, Pagination, Spinner } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { useState } from "react";
import { fmtDate, label } from "../utils/format";

const Counts = ({ title, data }: { title: string; data: Record<string, number> }) => (
  <div><h3 className="mb-1 text-sm font-medium">{title}</h3><ul className="text-sm">{Object.entries(data).map(([k, v]) => <li key={k} className="flex justify-between"><span>{label(k)}</span><b>{v}</b></li>)}</ul></div>);

export default function AdminOverview() {
  const stats = useAsync(api.adminStats, []);
  const [page, setPage] = useState(1);
  const act = useAsync(() => api.adminActivity({ page, page_size: 20 }), [page]);
  return (
    <>
      <h1 className="text-2xl font-bold">Administration</h1>
      {stats.loading ? <Spinner /> : stats.error || !stats.data ? <ErrorBox problem={stats.error} onRetry={stats.reload} /> : (
        <div className="grid gap-4 md:grid-cols-4">
          <Card title="Users"><p className="text-2xl font-bold">{stats.data.users.total}</p><p className="text-sm text-slate-500">{stats.data.users.active} active</p><Counts title="By role" data={stats.data.users.by_role} /></Card>
          <Card title="Leads"><p className="text-2xl font-bold">{stats.data.leads.total}</p><Counts title="By qualification" data={stats.data.leads.by_category} /></Card>
          <Card title="Analyses"><p className="text-2xl font-bold">{stats.data.analyses.total}</p><Counts title="AI status" data={stats.data.analyses.by_ai_status} /></Card>
          <Card title="Work items"><p className="text-sm">Outreach drafts: <b>{stats.data.outreach_drafts}</b></p><Counts title="Follow-ups" data={stats.data.follow_ups.by_status} /></Card>
        </div>)}
      <Card title="Activity log (read-only)">
        {act.loading ? <Spinner /> : act.error || !act.data ? <ErrorBox problem={act.error} onRetry={act.reload} /> : (<>
          <table className="w-full text-left text-sm"><thead className="border-b text-slate-500"><tr><th className="p-1">When</th><th className="p-1">Actor</th><th className="p-1">Action</th><th className="p-1">Details</th></tr></thead>
            <tbody>{act.data.items.map((a) => <tr key={a.id} className="border-b last:border-0"><td className="p-1">{fmtDate(a.created_at)}</td><td className="p-1">{a.actor_email ?? "system"}</td>
              <td className={`p-1 ${a.action.includes("failed") ? "text-red-700" : ""}`}>{a.action}</td><td className="p-1 text-xs text-slate-500">{a.meta ? JSON.stringify(a.meta) : ""}</td></tr>)}</tbody></table>
          <Pagination page={act.data.page} pageSize={act.data.page_size} total={act.data.total} onChange={setPage} /></>)}
      </Card>
    </>
  );
}
