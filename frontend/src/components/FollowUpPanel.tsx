import { FormEvent, useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { apiErrorMessage } from "../utils/errors";
import FollowUpRow from "./FollowUpRow";
import { Card, ErrorBox, Field, Select, Spinner, useToast } from "./ui";

export default function FollowUpPanel({ leadId }: { leadId: number }) {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(() => api.followUps({ lead_id: leadId, page_size: 50 }), [leadId]);
  const [f, setF] = useState({ title: "", due: "", priority: "medium", description: "" });
  const [err, setErr] = useState<string | null>(null);

  async function add(e: FormEvent) {
    e.preventDefault();
    if (!f.title.trim() || !f.due) { setErr("A title and a due date/time are required."); return; }
    setErr(null);
    try { await api.createFollowUp({ lead_id: leadId, title: f.title.trim(), description: f.description || null, due_at: new Date(f.due).toISOString(), priority: f.priority });
      toast("success", "Follow-up created (no reminder is sent automatically)"); setF({ title: "", due: "", priority: "medium", description: "" }); await reload(); }
    catch (x) { setErr(apiErrorMessage(x)); }
  }
  return (
    <Card title="Follow-ups">
      <form onSubmit={add} className="grid gap-3 md:grid-cols-5" noValidate>
        <div className="md:col-span-2"><Field label="Task" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></div>
        <Field label="Due" type="datetime-local" value={f.due} onChange={(e) => setF({ ...f, due: e.target.value })} />
        <Select label="Priority" value={f.priority} onChange={(e) => setF({ ...f, priority: e.target.value })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></Select>
        <div className="flex items-end"><button type="submit" className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white">Add follow-up</button></div>
      </form>
      <div className="mt-2"><ErrorBox problem={err} /></div>
      {loading ? <Spinner /> : error ? <ErrorBox problem={error} onRetry={reload} /> : !data?.items.length ? <p className="mt-3 text-sm text-slate-500">No follow-ups for this lead.</p>
        : <ul className="mt-3 divide-y">{data.items.map((x) => <FollowUpRow key={`${x.id}-${x.status}`} f={x} onChanged={reload} />)}</ul>}
    </Card>
  );
}
