import { Link } from "react-router-dom";
import { Badge, Card, Empty, ErrorBox, Spinner } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { fmtDate, label } from "../utils/format";

const Stat = ({ title, value, to, danger }: { title: string; value: number; to?: string; danger?: boolean }) => {
  const body = <div className={`dashboard-stat rounded-2xl border bg-white p-4 shadow-sm ${danger && value > 0 ? "dashboard-stat-danger border-red-300" : "border-slate-200"}`}><div className="flex items-start justify-between gap-2"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p><span className="dashboard-stat-mark" aria-hidden="true">{danger ? "!" : "↗"}</span></div><p className={`mt-3 text-3xl font-bold tracking-tight ${danger && value > 0 ? "text-red-700" : "text-slate-900"}`}>{value.toLocaleString()}</p><p className="mt-1 text-xs text-slate-400">{danger && value > 0 ? "Needs attention" : "Current total"}</p></div>;
  return to ? <Link to={to}>{body}</Link> : body;
};

export default function DashboardPage() {
  const s = useAsync(api.summary, []);
  const a = useAsync(api.recentActivity, []);
  if (s.loading) return <Spinner text="Loading dashboard…" />;
  if (s.error || !s.data) return <ErrorBox problem={s.error} onRetry={s.reload} />;
  const d = s.data;
  const cats = Object.entries(d.by_category);
  const max = Math.max(1, ...cats.map(([, v]) => v));
  return (
    <>
      <section className="dashboard-hero relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-violet-900 p-6 text-white shadow-lg sm:p-8">
        <div className="relative z-10 max-w-2xl"><p className="text-xs font-bold uppercase tracking-[.2em] text-indigo-200">Sales intelligence</p><h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">Your pipeline, at a glance.</h1><p className="mt-2 max-w-xl text-sm leading-6 text-indigo-100/80">Track lead quality, keep outreach moving, and stay ahead of every follow-up.</p><div className="mt-5 flex flex-wrap gap-2"><Link to="/leads" className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-950 transition hover:bg-indigo-50">View leads →</Link><Link to="/import" className="rounded-xl border border-white/25 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/20">Import leads</Link></div></div>
        <div aria-hidden="true" className="pointer-events-none absolute -right-8 -top-16 h-64 w-64 rounded-full border-[32px] border-white/5 sm:right-8 sm:top-[-4rem]"/><div aria-hidden="true" className="pointer-events-none absolute -bottom-28 right-24 h-64 w-64 rounded-full bg-violet-400/10 blur-2xl"/>
      </section>
      {d.total_leads === 0 && <Empty title="No leads yet" hint="Import a CSV or add a lead to get started."><Link to="/import" className="text-indigo-700 underline">Import leads</Link></Empty>}
      <div className="grid grid-cols-1 gap-3 min-[420px]:grid-cols-2 md:grid-cols-4">
        <Stat title="Total leads" value={d.total_leads} to="/leads" />
        <Stat title="New imports (7 days)" value={d.new_imported_leads} />
        <Stat title="Qualified" value={d.qualified_leads} to="/leads?category=strong_match" />
        <Stat title="Needs review" value={d.review_required_leads} to="/leads?category=review_required" />
        <Stat title="Unqualified" value={d.unqualified_leads} />
        <Stat title="Outreach drafts" value={d.outreach_drafts} />
        <Stat title="Pending follow-ups" value={d.pending_follow_ups} to="/follow-ups?status=open" />
        <Stat title="Overdue follow-ups" value={d.overdue_follow_ups} to="/follow-ups?overdue=true" danger />
      </div>
      <div className="grid min-w-0 gap-4 lg:grid-cols-2">
        <Card title="Leads by qualification">
          {cats.length === 0 ? <p className="text-sm text-slate-500">No data.</p> : (
            <ul className="space-y-2">{cats.map(([k, v]) => (
              <li key={k} className="text-sm"><div className="flex justify-between"><span>{label(k)}</span><span>{v}</span></div>
                <div className="h-2 rounded bg-slate-100"><div className="h-2 rounded bg-indigo-500" style={{ width: `${(v / max) * 100}%` }} /></div></li>))}</ul>)}
        </Card>
        <Card title="Next follow-ups" actions={<Link className="text-sm text-indigo-700 underline" to="/follow-ups">All</Link>}>
          {d.upcoming_follow_ups.length === 0 ? <p className="text-sm text-slate-500">No open follow-ups.</p> : (
            <ul className="divide-y text-sm">{d.upcoming_follow_ups.map((f) => (
              <li key={f.id} className="flex items-center justify-between py-2"><span><Link className="underline" to={`/leads/${f.lead_id}`}>{f.company_name}</Link> — {f.title}</span>
                <span className={f.is_overdue ? "font-medium text-red-700" : ""}>{fmtDate(f.due_at)}{f.is_overdue ? " (overdue)" : ""}</span></li>))}</ul>)}
        </Card>
      </div>
      <Card title="Pipeline">
        <div className="flex flex-wrap gap-2">{Object.entries(d.by_status).map(([k, v]) => <span key={k} className="rounded-full bg-slate-100 px-3 py-1 text-sm">{label(k)}: <b>{v}</b></span>)}</div>
      </Card>
      <Card title="Recent activity">
        {a.loading ? <Spinner /> : a.error ? <ErrorBox problem={a.error} /> : !a.data?.length ? <p className="text-sm text-slate-500">No activity yet.</p> : (
          <ul className="divide-y text-sm">{a.data.map((x) => <li key={x.id} className="flex justify-between py-1.5"><span>{label(x.action.replace(".", " "))}{x.meta && "company" in x.meta ? ` — ${String(x.meta.company)}` : ""}</span><span className="text-slate-500">{fmtDate(x.created_at)}</span></li>)}</ul>)}
      </Card>
    </>
  );
}
