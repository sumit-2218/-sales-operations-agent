import { useState } from "react";
import { Button, Card, Confirm, ErrorBox, Field, Spinner, useToast } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import type { Icp, IcpConfig } from "../types";
import { apiErrorMessage } from "../utils/errors";
import { numOrNull, splitList } from "../utils/format";

const WEIGHTS = ["industry", "company_size", "location", "revenue", "keywords"];
const join = (a: string[]) => a.join(", ");

interface FormState { name: string; active: boolean; target_industries: string; excluded_industries: string; target_locations: string; keywords: string; excluded_keywords: string;
  min_employees: string; max_employees: string; min_revenue: string; max_revenue: string; strong: string; potential: string; minEval: string; weights: Record<string, string> }

const fromConfig = (name: string, active: boolean, c: IcpConfig): FormState => ({ name, active, target_industries: join(c.target_industries), excluded_industries: join(c.excluded_industries),
  target_locations: join(c.target_locations), keywords: join(c.keywords), excluded_keywords: join(c.excluded_keywords), min_employees: c.min_employees?.toString() ?? "", max_employees: c.max_employees?.toString() ?? "",
  min_revenue: c.min_revenue?.toString() ?? "", max_revenue: c.max_revenue?.toString() ?? "", strong: String(c.strong_threshold), potential: String(c.potential_threshold), minEval: String(c.min_evaluable_weight_pct),
  weights: Object.fromEntries(WEIGHTS.map((w) => [w, String(c.weights[w] ?? 0)])) });

export function toConfig(f: FormState): IcpConfig {
  return { target_industries: splitList(f.target_industries), excluded_industries: splitList(f.excluded_industries), target_locations: splitList(f.target_locations),
    keywords: splitList(f.keywords), excluded_keywords: splitList(f.excluded_keywords), min_employees: numOrNull(f.min_employees), max_employees: numOrNull(f.max_employees),
    min_revenue: numOrNull(f.min_revenue), max_revenue: numOrNull(f.max_revenue), strong_threshold: Number(f.strong), potential_threshold: Number(f.potential), min_evaluable_weight_pct: Number(f.minEval),
    weights: Object.fromEntries(WEIGHTS.map((w) => [w, Number(f.weights[w] || 0)])) };
}

export function validateIcp(f: FormState): string | null {
  if (!f.name.trim()) return "Give the profile a name.";
  const c = toConfig(f);
  if (c.min_employees != null && c.max_employees != null && c.min_employees > c.max_employees) return "Minimum employees cannot exceed maximum employees.";
  if (c.min_revenue != null && c.max_revenue != null && c.min_revenue > c.max_revenue) return "Minimum revenue cannot exceed maximum revenue.";
  if (Object.values(c.weights).some((w) => Number.isNaN(w) || w < 0)) return "Weights must be numbers of 0 or more.";
  if (Object.values(c.weights).reduce((a, b) => a + b, 0) <= 0) return "At least one weight must be greater than 0.";
  if (c.potential_threshold > c.strong_threshold) return "The potential threshold cannot exceed the strong threshold.";
  return null;
}

export default function IcpPage() {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(api.icps, []);
  const [form, setForm] = useState<FormState | null>(null);
  const [editId, setEditId] = useState<number | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [del, setDel] = useState<Icp | null>(null);

  async function startNew() { try { const d = await api.defaultIcp(); setEditId(null); setForm(fromConfig("My ICP", !data?.length, d.config)); setProblem(null); } catch (e) { toast("error", apiErrorMessage(e)); } }
  const startEdit = (i: Icp) => { setEditId(i.id); setForm(fromConfig(i.name, i.is_active, i.config)); setProblem(null); };
  async function save() {
    if (!form) return;
    const v = validateIcp(form);
    if (v) { setProblem(v); return; }
    try {
      if (editId) await api.updateIcp(editId, { name: form.name.trim(), config: toConfig(form), is_active: form.active });
      else await api.createIcp({ name: form.name.trim(), config: toConfig(form), is_active: form.active });
      toast("success", "ICP saved; lead scores were recalculated"); setForm(null); await reload();
    } catch (e) { setProblem(apiErrorMessage(e)); }
  }
  const set = (k: keyof Omit<FormState, "weights" | "active">) => (e: React.ChangeEvent<HTMLInputElement>) => form && setForm({ ...form, [k]: e.target.value });
  return (
    <>
      <div className="flex items-center justify-between"><h1 className="text-2xl font-bold">Ideal Customer Profile</h1><Button onClick={startNew}>New profile</Button></div>
      <p className="text-sm text-slate-600">Your <b>active</b> profile is used to score all of your leads. Changing it recalculates scores. Without any profile, a built-in demo ICP is used.</p>
      {loading ? <Spinner /> : error ? <ErrorBox problem={error} onRetry={reload} /> : (data ?? []).map((i) => (
        <Card key={i.id} title={`${i.name}${i.is_active ? " (active)" : ""}`} actions={<div className="space-x-2">
          {!i.is_active && <Button variant="secondary" onClick={async () => { try { await api.updateIcp(i.id, { is_active: true }); toast("success", "Profile activated; scores recalculated"); await reload(); } catch (e) { toast("error", apiErrorMessage(e)); } }}>Make active</Button>}
          <Button variant="secondary" onClick={() => startEdit(i)}>Edit</Button><Button variant="danger" onClick={() => setDel(i)}>Delete</Button></div>}>
          <ul className="list-disc space-y-1 pl-5 text-sm">{i.explanations.map((x, n) => <li key={n}>{x}</li>)}</ul>
        </Card>))}
      {!loading && !error && !data?.length && !form && <p className="text-sm text-slate-500">No profile yet. Create one to customise scoring.</p>}
      {form && (
        <Card title={editId ? "Edit profile" : "New profile"}>
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Profile name" value={form.name} onChange={set("name")} />
            <label className="flex items-end gap-2 pb-2 text-sm"><input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} /> Use as my active profile</label>
            <Field label="Target industries" value={form.target_industries} onChange={set("target_industries")} hint="Comma-separated" />
            <Field label="Excluded industries" value={form.excluded_industries} onChange={set("excluded_industries")} hint="Leads in these industries are always 'excluded'" />
            <Field label="Target locations" value={form.target_locations} onChange={set("target_locations")} hint="Matched against the lead's location text" />
            <Field label="Keywords" value={form.keywords} onChange={set("keywords")} hint="Matched against the business description" />
            <Field label="Excluded keywords" value={form.excluded_keywords} onChange={set("excluded_keywords")} />
            <div />
            <Field label="Min employees" inputMode="numeric" value={form.min_employees} onChange={set("min_employees")} /><Field label="Max employees" inputMode="numeric" value={form.max_employees} onChange={set("max_employees")} />
            <Field label="Min revenue" inputMode="numeric" value={form.min_revenue} onChange={set("min_revenue")} /><Field label="Max revenue" inputMode="numeric" value={form.max_revenue} onChange={set("max_revenue")} />
            <Field label="Strong match from score" inputMode="numeric" value={form.strong} onChange={set("strong")} /><Field label="Potential match from score" inputMode="numeric" value={form.potential} onChange={set("potential")} />
            <Field label="Min % of criteria that must be evaluable" inputMode="numeric" value={form.minEval} onChange={set("minEval")} hint="Below this, a lead is marked 'review required'" />
          </div>
          <h3 className="mt-4 font-medium">Scoring weights</h3>
          <div className="grid gap-3 md:grid-cols-5">{WEIGHTS.map((w) => <Field key={w} label={w.replace("_", " ")} inputMode="numeric" value={form.weights[w]} onChange={(e) => setForm({ ...form, weights: { ...form.weights, [w]: e.target.value } })} />)}</div>
          <div className="mt-3"><ErrorBox problem={problem} /></div>
          <div className="mt-3 space-x-2"><Button onClick={save}>Save profile</Button><Button variant="secondary" onClick={() => setForm(null)}>Cancel</Button></div>
        </Card>)}
      <Confirm open={!!del} title="Delete this profile?" message="Lead scores will be recalculated with your next active profile (or the built-in default)." onCancel={() => setDel(null)}
        onConfirm={async () => { try { await api.deleteIcp(del!.id); toast("success", "Profile deleted"); setDel(null); await reload(); } catch (e) { toast("error", apiErrorMessage(e)); } }} />
    </>
  );
}
