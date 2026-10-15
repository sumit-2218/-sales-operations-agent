import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import FollowUpPanel from "../components/FollowUpPanel";
import OutreachPanel from "../components/OutreachPanel";
import QualificationPanel from "../components/QualificationPanel";
import { Badge, Button, Card, Confirm, ErrorBox, Spinner, useToast } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { STATUSES, LeadStatus } from "../types";
import { apiErrorMessage } from "../utils/errors";
import { fmtDate, fmtNum, label } from "../utils/format";

type Tab = "qualification" | "outreach" | "followups" | "activity";

function ActivityTab({ id }: { id: number }) {
  const { data, loading, error, reload } = useAsync(() => api.leadActivity(id), [id]);
  return <Card title="Activity history">{loading ? <Spinner /> : error ? <ErrorBox problem={error} onRetry={reload} /> : !data?.items.length ? <p className="text-sm text-slate-500">No activity.</p> :
    <ul className="divide-y text-sm">{data.items.map((a) => <li key={a.id} className="flex justify-between py-1.5"><span>{label(a.action.replace(".", " "))}{a.meta && "from" in a.meta ? `: ${String(a.meta.from)} → ${String(a.meta.to)}` : ""}</span><span className="text-slate-500">{a.actor_email ?? "system"} · {fmtDate(a.created_at)}</span></li>)}</ul>}</Card>;
}

export default function LeadDetailPage() {
  const id = Number(useParams().id);
  const nav = useNavigate();
  const toast = useToast();
  const { data: lead, loading, error, reload } = useAsync(() => api.lead(id), [id]);
  const [tab, setTab] = useState<Tab>("qualification");
  const [confirm, setConfirm] = useState(false);

  if (loading && !lead) return <Spinner />;
  if (error || !lead) return <><ErrorBox problem={error} onRetry={reload} /><Link to="/leads" className="text-indigo-700 underline">Back to leads</Link></>;

  async function setStatus(s: LeadStatus) {
    try { await api.updateLead(id, { status: s }); toast("success", `Status changed to ${label(s)}`); await reload(); } catch (e) { toast("error", apiErrorMessage(e)); }
  }
  async function remove() {
    try { await api.deleteLead(id); toast("success", "Lead deleted"); nav("/leads"); } catch (e) { toast("error", apiErrorMessage(e)); setConfirm(false); }
  }
  const row = (k: string, v: string | number | null) => <div key={k}><dt className="text-xs uppercase text-slate-500">{k}</dt><dd className="text-sm">{v ?? <span className="text-slate-400">Not provided</span>}</dd></div>;
  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div><Link to="/leads" className="text-sm text-indigo-700 underline">← Leads</Link><h1 className="text-2xl font-bold">{lead.company_name}</h1>
          <p className="text-sm text-slate-600">Score {lead.score ?? "—"} · <Badge value={lead.qualification_category} /></p></div>
        <div className="flex items-end gap-2">
          <label className="text-sm"><span className="mb-1 block font-medium">Pipeline status</span>
            <select className="rounded-md border border-slate-300 px-2 py-1.5" value={lead.status} onChange={(e) => setStatus(e.target.value as LeadStatus)}>{STATUSES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select></label>
          <Link to={`/leads/${id}/edit`} className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100">Edit</Link>
          <Button variant="danger" onClick={() => setConfirm(true)}>Delete</Button>
        </div>
      </div>
      <Card title="Details"><dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {row("Contact", lead.contact_name)}{row("Email", lead.email)}{row("Job title", lead.job_title)}{row("Industry", lead.industry)}
        {row("Employees", lead.employee_count == null ? null : fmtNum(lead.employee_count))}{row("Location", lead.location)}{row("Website", lead.website)}
        {row("Annual revenue", lead.annual_revenue == null ? null : fmtNum(lead.annual_revenue))}{row("Source", lead.source)}{row("Updated", fmtDate(lead.updated_at))}
        <div className="col-span-2 md:col-span-4"><dt className="text-xs uppercase text-slate-500">Description</dt><dd className="text-sm">{lead.description ?? <span className="text-slate-400">Not provided</span>}</dd></div>
        <div className="col-span-2 md:col-span-4"><dt className="text-xs uppercase text-slate-500">Notes</dt><dd className="whitespace-pre-wrap text-sm">{lead.notes ?? <span className="text-slate-400">None</span>}</dd></div>
      </dl></Card>
      <div role="tablist" className="flex gap-1 border-b">
        {([["qualification", "Qualification"], ["outreach", "Outreach"], ["followups", "Follow-ups"], ["activity", "Activity"]] as const).map(([k, t]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={`px-4 py-2 text-sm ${tab === k ? "border-b-2 border-indigo-600 font-semibold" : "text-slate-600"}`}>{t}</button>))}
      </div>
      {tab === "qualification" && <QualificationPanel leadId={id} onChanged={reload} />}
      {tab === "outreach" && <OutreachPanel leadId={id} />}
      {tab === "followups" && <FollowUpPanel leadId={id} />}
      {tab === "activity" && <ActivityTab id={id} />}
      <Confirm open={confirm} title="Delete this lead?" message="This permanently deletes the lead together with its analyses, outreach drafts and follow-ups." onConfirm={remove} onCancel={() => setConfirm(false)} />
    </>
  );
}
