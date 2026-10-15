import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { FollowUp } from "../types";
import { apiErrorMessage } from "../utils/errors";
import { fmtDate } from "../utils/format";
import { Badge, Button, useToast } from "./ui";

export const toLocalInput = (iso: string) => { const d = new Date(iso); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 16); };

export default function FollowUpRow({ f, companyLink, onChanged }: { f: FollowUp; companyLink?: boolean; onChanged: () => void }) {
  const toast = useToast();
  const [edit, setEdit] = useState(false);
  const [title, setTitle] = useState(f.title);
  const [due, setDue] = useState(toLocalInput(f.due_at));
  const [priority, setPriority] = useState(f.priority);
  const [busy, setBusy] = useState(false);

  async function patch(b: Parameters<typeof api.updateFollowUp>[1], msg: string) {
    setBusy(true);
    try { await api.updateFollowUp(f.id, b); toast("success", msg); setEdit(false); onChanged(); } catch (e) { toast("error", apiErrorMessage(e)); } finally { setBusy(false); }
  }
  if (edit) return (
    <li className="flex flex-wrap items-end gap-2 py-2 text-sm">
      <input aria-label="Title" className="rounded-md border px-2 py-1" value={title} onChange={(e) => setTitle(e.target.value)} />
      <input aria-label="Due" type="datetime-local" className="rounded-md border px-2 py-1" value={due} onChange={(e) => setDue(e.target.value)} />
      <select aria-label="Priority" className="rounded-md border px-2 py-1" value={priority} onChange={(e) => setPriority(e.target.value as FollowUp["priority"])}><option>low</option><option>medium</option><option>high</option></select>
      <Button disabled={busy || !title.trim() || !due} onClick={() => patch({ title: title.trim(), due_at: new Date(due).toISOString(), priority }, "Follow-up updated")}>Save</Button>
      <Button variant="secondary" onClick={() => setEdit(false)}>Cancel</Button>
    </li>);
  return (
    <li className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
      <div>
        <span className="font-medium">{f.title}</span> {companyLink && <Link className="text-indigo-700 underline" to={`/leads/${f.lead_id}`}>(lead #{f.lead_id})</Link>}
        <div className="text-xs text-slate-500">Due <span className={f.is_overdue ? "font-semibold text-red-700" : ""}>{fmtDate(f.due_at)}{f.is_overdue ? " — overdue" : ""}</span>{f.completed_at ? ` · completed ${fmtDate(f.completed_at)}` : ""}</div>
      </div>
      <div className="flex items-center gap-2"><Badge value={f.priority} /><Badge value={f.status} />
        {f.status === "open" && <>
          <Button variant="secondary" disabled={busy} onClick={() => patch({ status: "completed" }, "Marked complete")}>Complete</Button>
          <Button variant="ghost" onClick={() => setEdit(true)}>Edit</Button>
          <Button variant="ghost" disabled={busy} onClick={() => patch({ status: "cancelled" }, "Follow-up cancelled")}>Cancel task</Button></>}
        {f.status !== "open" && <Button variant="ghost" disabled={busy} onClick={() => patch({ status: "open" }, "Follow-up reopened")}>Reopen</Button>}
      </div>
    </li>);
}
