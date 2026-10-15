import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Empty, ErrorBox, Pagination, Select, Spinner } from "../components/ui";
import { useAsync } from "../hooks/useAsync";
import { api, download } from "../services/api";
import { STATUSES } from "../types";
import { apiErrorMessage } from "../utils/errors";
import { fmtNum, label } from "../utils/format";
import { useToast } from "../components/ui";

const CATEGORIES = ["strong_match", "potential_match", "weak_match", "review_required", "excluded"];

export default function LeadsPage() {
  const [sp, setSp] = useSearchParams();
  const toast = useToast();
  const get = (k: string, d = "") => sp.get(k) ?? d;
  const [q, setQ] = useState(get("q"));
  const params = { q: get("q"), status: get("status"), category: get("category"), industry: get("industry"), location: get("location"),
    min_score: get("min_score"), sort_by: get("sort_by", "created_at"), sort_dir: get("sort_dir", "desc"), page: Number(get("page", "1")), page_size: 20 };
  const { data, error, loading, reload } = useAsync(() => api.leads(params), [sp.toString()]);
  const update = (patch: Record<string, string>) => { const n = new URLSearchParams(sp); Object.entries(patch).forEach(([k, v]) => (v ? n.set(k, v) : n.delete(k))); if (!("page" in patch)) n.delete("page"); setSp(n); };
  const sortBy = (col: string) => update({ sort_by: col, sort_dir: params.sort_by === col && params.sort_dir === "asc" ? "desc" : "asc" });
  const arrow = (col: string) => (params.sort_by === col ? (params.sort_dir === "asc" ? " ▲" : " ▼") : "");

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold">Leads</h1>
        <div className="space-x-2">
          <Button variant="secondary" onClick={() => download("/leads/export.csv", "leads_export.csv", { q: params.q, status: params.status, category: params.category }).catch((e) => toast("error", apiErrorMessage(e)))}>Export CSV</Button>
          <Link to="/import" className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-100">Import CSV</Link>
          <Link to="/leads/new" className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white">Add lead</Link>
        </div>
      </div>
      <Card>
        <form className="grid gap-3 md:grid-cols-6" onSubmit={(e) => { e.preventDefault(); update({ q }); }} role="search">
          <label className="text-sm md:col-span-2"><span className="mb-1 block font-medium">Search</span>
            <input className="w-full rounded-md border border-slate-300 px-2 py-1.5" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Company, contact, email…" /></label>
          <Select label="Status" value={params.status} onChange={(e) => update({ status: e.target.value })}><option value="">All</option>{STATUSES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</Select>
          <Select label="Qualification" value={params.category} onChange={(e) => update({ category: e.target.value })}><option value="">All</option>{CATEGORIES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</Select>
          <label className="text-sm"><span className="mb-1 block font-medium">Industry</span><input className="w-full rounded-md border border-slate-300 px-2 py-1.5" defaultValue={params.industry} onBlur={(e) => update({ industry: e.target.value })} /></label>
          <label className="text-sm"><span className="mb-1 block font-medium">Location</span><input className="w-full rounded-md border border-slate-300 px-2 py-1.5" defaultValue={params.location} onBlur={(e) => update({ location: e.target.value })} /></label>
          <label className="text-sm"><span className="mb-1 block font-medium">Min score</span><input type="number" min={0} max={100} className="w-full rounded-md border border-slate-300 px-2 py-1.5" defaultValue={params.min_score} onBlur={(e) => update({ min_score: e.target.value })} /></label>
          <div className="flex items-end"><Button type="submit">Search</Button></div>
        </form>
      </Card>
      {loading ? <Spinner /> : error ? <ErrorBox problem={error} onRetry={reload} /> : !data || data.total === 0 ? (
        <Empty title="No leads found" hint="Adjust the filters, add a lead, or import a CSV file."><Link to="/leads/new" className="text-indigo-700 underline">Add a lead</Link></Empty>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b text-slate-500"><tr>
                {([["company_name", "Company"], ["industry", "Industry"], ["location", "Location"]] as const).map(([c, t]) => <th key={c} className="cursor-pointer p-2" onClick={() => sortBy(c)} aria-sort={params.sort_by === c ? (params.sort_dir === "asc" ? "ascending" : "descending") : "none"}>{t}{arrow(c)}</th>)}
                <th className="p-2">Employees</th>
                <th className="cursor-pointer p-2" onClick={() => sortBy("score")}>Score{arrow("score")}</th><th className="p-2">Qualification</th>
                <th className="cursor-pointer p-2" onClick={() => sortBy("status")}>Status{arrow("status")}</th></tr></thead>
              <tbody>{data.items.map((l) => (
                <tr key={l.id} className="border-b last:border-0 hover:bg-slate-50">
                  <td className="p-2"><Link className="font-medium text-indigo-700 underline" to={`/leads/${l.id}`}>{l.company_name}</Link><div className="text-xs text-slate-500">{l.contact_name ?? ""}</div></td>
                  <td className="p-2">{l.industry ?? "—"}</td><td className="p-2">{l.location ?? "—"}</td><td className="p-2">{fmtNum(l.employee_count)}</td>
                  <td className="p-2">{l.score ?? "—"}</td><td className="p-2"><Badge value={l.qualification_category} /></td><td className="p-2">{label(l.status)}</td></tr>))}</tbody>
            </table>
          </div>
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onChange={(p) => update({ page: String(p) })} />
        </Card>
      )}
    </>
  );
}
