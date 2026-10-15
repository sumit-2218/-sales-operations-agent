import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button, Card, ErrorBox, Field, Spinner, useToast } from "../components/ui";
import { api } from "../services/api";
import { apiErrorMessage } from "../utils/errors";
import { emptyToNull, numOrNull } from "../utils/format";

const BLANK = { company_name: "", contact_name: "", email: "", job_title: "", industry: "", employee_count: "", location: "", website: "", annual_revenue: "", description: "", notes: "" };
type Form = typeof BLANK;

export function validateLead(f: Form): Record<string, string> {
  const e: Record<string, string> = {};
  if (!f.company_name.trim()) e.company_name = "Company name is required";
  if (f.email.trim() && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f.email.trim())) e.email = "Enter a valid email address";
  for (const k of ["employee_count", "annual_revenue"] as const) {
    if (f[k].trim() && (!/^\d+$/.test(f[k].trim()))) e[k] = "Enter a whole number (0 or more)";
  }
  return e;
}

export default function LeadFormPage() {
  const { id } = useParams();
  const editing = !!id;
  const nav = useNavigate();
  const toast = useToast();
  const [f, setF] = useState<Form>(BLANK);
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [server, setServer] = useState<string | null>(null);
  const [loading, setLoading] = useState(editing);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.lead(Number(id)).then((l) => setF({ ...BLANK, ...Object.fromEntries(Object.entries(l).filter(([k]) => k in BLANK).map(([k, v]) => [k, v == null ? "" : String(v)])) } as Form))
      .catch((e) => setServer(apiErrorMessage(e))).finally(() => setLoading(false));
  }, [id]);

  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setF({ ...f, [k]: e.target.value });
  async function submit(e: FormEvent) {
    e.preventDefault();
    const v = validateLead(f);
    setErrs(v);
    if (Object.keys(v).length) return;
    const body = { company_name: f.company_name.trim(), contact_name: emptyToNull(f.contact_name), email: emptyToNull(f.email), job_title: emptyToNull(f.job_title),
      industry: emptyToNull(f.industry), employee_count: numOrNull(f.employee_count), location: emptyToNull(f.location), website: emptyToNull(f.website),
      annual_revenue: numOrNull(f.annual_revenue), description: emptyToNull(f.description), notes: emptyToNull(f.notes) };
    setBusy(true); setServer(null);
    try {
      const l = editing ? await api.updateLead(Number(id), body) : await api.createLead(body);
      toast("success", editing ? "Lead updated" : "Lead created");
      nav(`/leads/${l.id}`);
    } catch (err) { setServer(apiErrorMessage(err)); } finally { setBusy(false); }
  }
  if (loading) return <Spinner />;
  return (
    <>
      <h1 className="text-2xl font-bold">{editing ? "Edit lead" : "Add lead"}</h1>
      <Card>
        <form onSubmit={submit} noValidate className="grid gap-3 md:grid-cols-2">
          <Field label="Company name *" value={f.company_name} onChange={set("company_name")} error={errs.company_name} />
          <Field label="Contact name" value={f.contact_name} onChange={set("contact_name")} />
          <Field label="Email" type="email" value={f.email} onChange={set("email")} error={errs.email} />
          <Field label="Job title" value={f.job_title} onChange={set("job_title")} />
          <Field label="Industry" value={f.industry} onChange={set("industry")} />
          <Field label="Employees" inputMode="numeric" value={f.employee_count} onChange={set("employee_count")} error={errs.employee_count} />
          <Field label="Location" value={f.location} onChange={set("location")} />
          <Field label="Website" value={f.website} onChange={set("website")} />
          <Field label="Annual revenue" inputMode="numeric" value={f.annual_revenue} onChange={set("annual_revenue")} error={errs.annual_revenue} hint="Leave blank if unknown — missing data is not treated as a negative signal." />
          <label className="block text-sm md:col-span-2"><span className="mb-1 block font-medium">Business description</span>
            <textarea className="w-full rounded-md border border-slate-300 px-2 py-1.5" rows={3} value={f.description} onChange={set("description")} /></label>
          <label className="block text-sm md:col-span-2"><span className="mb-1 block font-medium">Notes</span>
            <textarea className="w-full rounded-md border border-slate-300 px-2 py-1.5" rows={2} value={f.notes} onChange={set("notes")} /></label>
          <div className="md:col-span-2"><ErrorBox problem={server} /></div>
          <div className="space-x-2 md:col-span-2"><button type="submit" disabled={busy} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{busy ? "Saving…" : "Save lead"}</button>
            <Button variant="secondary" onClick={() => nav(-1)}>Cancel</Button></div>
        </form>
      </Card>
    </>
  );
}
