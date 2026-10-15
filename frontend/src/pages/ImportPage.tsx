import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, ErrorBox, Spinner, useToast } from "../components/ui";
import { api, download } from "../services/api";
import type { ImportPreview } from "../types";
import { apiErrorMessage } from "../utils/errors";

const EDITABLE = ["company_name", "email", "employee_count"] as const;

export default function ImportPage() {
  const toast = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string | null>>({});
  const [fixes, setFixes] = useState<Record<string, Record<string, string>>>({});
  const [excluded, setExcluded] = useState<Set<number>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ imported: number; skipped_invalid: number; skipped_duplicates: number; excluded_by_user: number } | null>(null);

  async function runPreview(f: File, m?: Record<string, string | null>, c?: typeof fixes) {
    setBusy(true); setError(null); setResult(null);
    try { const p = await api.previewImport(f, m, c); setPreview(p); setMapping(p.mapping); }
    catch (e) { setPreview(null); setError(apiErrorMessage(e)); } finally { setBusy(false); }
  }
  function choose(f: File | null) {
    setFile(f); setPreview(null); setFixes({}); setExcluded(new Set()); setResult(null); setError(null);
    if (f) void runPreview(f);
  }
  async function confirm() {
    if (!file) return;
    setBusy(true); setError(null);
    try { const r = await api.confirmImport(file, mapping, fixes, [...excluded]); setResult(r); setPreview(null); toast("success", `${r.imported} leads imported`); }
    catch (e) { setError(apiErrorMessage(e)); } finally { setBusy(false); }
  }
  const importable = preview ? preview.rows.filter((r) => r.status !== "invalid" && !excluded.has(r.row_number) && r.status !== "duplicate").length : 0;

  return (
    <>
      <h1 className="text-2xl font-bold">Import leads from CSV</h1>
      <Card>
        <p className="mb-3 text-sm text-slate-600">Upload a UTF-8 CSV with at least a <code>company_name</code> column. You can review, fix or exclude rows before anything is saved.</p>
        <div className="flex flex-wrap items-center gap-3">
          <input aria-label="CSV file" type="file" accept=".csv,text/csv" onChange={(e) => choose(e.target.files?.[0] ?? null)} />
          <Button variant="secondary" onClick={() => download("/imports/template", "lead_import_template.csv").catch((e) => toast("error", apiErrorMessage(e)))}>Download template</Button>
        </div>
      </Card>
      {busy && <Spinner text="Processing…" />}
      <ErrorBox problem={error} />
      {result && <Card title="Import complete"><ul className="text-sm"><li>Imported: <b>{result.imported}</b></li><li>Skipped (invalid): {result.skipped_invalid}</li><li>Skipped (duplicates): {result.skipped_duplicates}</li><li>Excluded by you: {result.excluded_by_user}</li></ul>
        <Link to="/leads" className="mt-2 inline-block text-indigo-700 underline">View leads</Link></Card>}
      {preview && (<>
        <Card title="Column mapping">
          <div className="grid gap-2 md:grid-cols-3">{preview.headers.map((h) => (
            <label key={h} className="text-sm"><span className="mb-1 block font-medium">{h}</span>
              <select className="w-full rounded-md border border-slate-300 px-2 py-1.5" value={mapping[h] ?? ""} onChange={(e) => setMapping({ ...mapping, [h]: e.target.value || null })}>
                <option value="">(ignore)</option>{preview.fields.map((f) => <option key={f} value={f}>{f}</option>)}</select></label>))}</div>
          <Button className="mt-3" variant="secondary" onClick={() => file && runPreview(file, mapping, fixes)}>Re-validate with this mapping</Button>
        </Card>
        <Card title="Preview" actions={<Button disabled={busy || importable === 0} onClick={confirm}>Import {importable} lead{importable === 1 ? "" : "s"}</Button>}>
          <p className="mb-2 text-sm">{preview.total_rows} rows · <span className="text-green-700">{preview.valid_count} valid</span> · <span className="text-red-700">{preview.invalid_count} invalid</span> · <span className="text-amber-700">{preview.duplicate_count} duplicates</span> (duplicates are skipped)</p>
          <div className="overflow-x-auto"><table className="w-full text-left text-sm">
            <thead className="border-b text-slate-500"><tr><th className="p-1">Row</th><th className="p-1">Status</th><th className="p-1">Company</th><th className="p-1">Email</th><th className="p-1">Employees</th><th className="p-1">Problems</th><th className="p-1">Exclude</th></tr></thead>
            <tbody>{preview.rows.map((r) => (
              <tr key={r.row_number} className="border-b align-top last:border-0">
                <td className="p-1">{r.row_number}</td>
                <td className="p-1"><Badge value={r.status} danger={r.status === "invalid"} /></td>
                {EDITABLE.map((k) => <td key={k} className="p-1">{r.status === "invalid"
                  ? <input aria-label={`${k} row ${r.row_number}`} className="w-full rounded border border-red-300 px-1 py-0.5" defaultValue={String(r.data[k] ?? "")} onChange={(e) => setFixes({ ...fixes, [r.row_number]: { ...fixes[r.row_number], [k]: e.target.value } })} />
                  : String(r.data[k] ?? "—")}</td>)}
                <td className="p-1 text-xs text-red-700">{r.errors.join(" ")}{r.duplicate_of ? `Duplicate (${r.duplicate_of})` : ""}</td>
                <td className="p-1"><input type="checkbox" aria-label={`Exclude row ${r.row_number}`} checked={excluded.has(r.row_number)} onChange={(e) => { const n = new Set(excluded); e.target.checked ? n.add(r.row_number) : n.delete(r.row_number); setExcluded(n); }} /></td>
              </tr>))}</tbody></table></div>
          {preview.invalid_count > 0 && <Button className="mt-3" variant="secondary" onClick={() => file && runPreview(file, mapping, fixes)}>Re-validate corrections</Button>}
        </Card>
      </>)}
    </>
  );
}
