import { useState } from "react";
import { api } from "../services/api";
import type { Analysis } from "../types";
import { apiProblem, ApiProblem } from "../utils/errors";
import { fmtDate, label } from "../utils/format";
import { Badge, Button, Card, ErrorBox, Spinner, useToast } from "./ui";
import { useAsync } from "../hooks/useAsync";

const statusTone: Record<string, string> = { match: "text-green-700", partial: "text-amber-700", mismatch: "text-red-700", missing: "text-slate-500" };

export function BreakdownTable({ a }: { a: Analysis }) {
  return (
    <div>
      <p className="mb-2 text-sm">Score <b>{a.score}</b> · <Badge value={a.category} /> · {a.breakdown.evaluable_weight_pct}% of criteria could be evaluated</p>
      {a.breakdown.exclusion_reasons.length > 0 && <ul className="mb-2 list-disc pl-5 text-sm text-red-700">{a.breakdown.exclusion_reasons.map((r) => <li key={r}>{r}</li>)}</ul>}
      <table className="w-full text-sm">
        <thead className="border-b text-left text-slate-500"><tr><th className="p-1">Criterion</th><th className="p-1">Result</th><th className="p-1">Points</th><th className="p-1">Explanation</th></tr></thead>
        <tbody>{a.breakdown.factors.map((f) => (
          <tr key={f.name} className="border-b last:border-0"><td className="p-1">{label(f.name)}</td>
            <td className={`p-1 font-medium ${statusTone[f.status]}`}>{label(f.status)}</td><td className="p-1">{f.status === "missing" ? "—" : `${f.earned}/${f.max_points}`}</td><td className="p-1">{f.detail}</td></tr>))}</tbody>
      </table>
      <p className="mt-1 text-xs text-slate-500">Missing data is excluded from the score; it is not counted as a mismatch.</p>
    </div>
  );
}

const List = ({ title, items }: { title: string; items: string[] }) => items.length === 0 ? null : (
  <div><h4 className="font-medium">{title}</h4><ul className="list-disc pl-5 text-sm">{items.map((x, i) => <li key={i}>{x}</li>)}</ul></div>);

export default function QualificationPanel({ leadId, onChanged }: { leadId: number; onChanged: () => void }) {
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(() => api.analyses(leadId), [leadId]);
  const [busy, setBusy] = useState<"score" | "ai" | null>(null);
  const [aiProblem, setAiProblem] = useState<ApiProblem | null>(null);
  const latest = data?.items[0];

  async function run(kind: "score" | "ai", retryId?: number) {
    setBusy(kind); setAiProblem(null);
    try {
      if (kind === "score") await api.score(leadId); else await api.analyze(leadId, retryId);
      toast("success", kind === "score" ? "Lead scored" : "AI explanation generated");
    } catch (e) {
      const p = apiProblem(e);
      if (kind === "ai") setAiProblem(p); else toast("error", p.message);
    } finally { setBusy(null); await reload(); onChanged(); }
  }
  return (
    <Card title="Qualification" actions={<div className="space-x-2">
      <Button variant="secondary" disabled={!!busy} onClick={() => run("score")}>{busy === "score" ? "Scoring…" : "Re-score"}</Button>
      <Button disabled={!!busy} onClick={() => run("ai")}>{busy === "ai" ? "Generating…" : "Generate AI explanation"}</Button></div>}>
      {busy === "ai" && <Spinner text="The local model is writing the explanation. This can take a while on a laptop…" />}
      {aiProblem && <div className="mb-3"><ErrorBox problem={aiProblem} onRetry={latest ? () => run("ai", latest.id) : undefined} /></div>}
      {loading ? <Spinner /> : error ? <ErrorBox problem={error} onRetry={reload} /> : !latest ? (
        <p className="text-sm text-slate-500">This lead has not been scored yet. Click “Re-score” to run the rule-based scoring.</p>
      ) : (<div className="space-y-4">
        <BreakdownTable a={latest} />
        <div className="rounded-md bg-slate-50 p-3">
          <h3 className="mb-1 font-semibold">AI explanation <span className="text-xs font-normal text-slate-500">(generated text, review before relying on it; the score above comes from rules, not the model)</span></h3>
          {latest.ai_status === "completed" && latest.ai_explanation ? (<div className="space-y-2">
            <p className="text-sm">{latest.ai_explanation.summary}</p>
            <List title="Matching factors" items={latest.ai_explanation.positive_factors} />
            <List title="Non-matching factors" items={latest.ai_explanation.negative_factors} />
            <List title="Missing information" items={latest.ai_explanation.missing_information} />
            <List title="Suggested next steps" items={latest.ai_explanation.recommended_next_steps} />
            <List title="Data limitations" items={latest.ai_explanation.data_limitations} />
            <p className="text-xs text-slate-500">Model: {latest.model_name} · {fmtDate(latest.created_at)}</p></div>
          ) : latest.ai_status === "failed" ? <p className="text-sm text-red-700">The last AI attempt failed: {latest.ai_error}</p>
            : <p className="text-sm text-slate-500">No AI explanation requested for the latest score.</p>}
        </div>
        {data && data.items.length > 1 && <details className="text-sm"><summary className="cursor-pointer">Scoring history ({data.total})</summary>
          <ul className="mt-1 space-y-1">{data.items.map((a) => <li key={a.id}>{fmtDate(a.created_at)} — {a.score} ({label(a.category)}){a.ai_status === "completed" ? " · AI explained" : ""}</li>)}</ul></details>}
      </div>)}
    </Card>
  );
}
