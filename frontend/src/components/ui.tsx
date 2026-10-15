import { createContext, ReactNode, useCallback, useContext, useState, ButtonHTMLAttributes, InputHTMLAttributes } from "react";
import { ApiProblem } from "../utils/errors";
import { label } from "../utils/format";

export function Button({ variant = "primary", className = "", ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" | "ghost" }) {
  const v = { primary: "bg-indigo-600 text-white hover:bg-indigo-700", secondary: "bg-white border border-slate-300 hover:bg-slate-100",
    danger: "bg-red-600 text-white hover:bg-red-700", ghost: "text-indigo-700 hover:bg-indigo-50" }[variant];
  return <button type="button" className={`rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed ${v} ${className}`} {...p} />;
}
export const Card = ({ title, children, actions, className = "" }: { title?: string; children: ReactNode; actions?: ReactNode; className?: string }) => (
  <section className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
    {(title || actions) && <div className="mb-3 flex items-center justify-between gap-2"><h2 className="font-semibold">{title}</h2>{actions}</div>}
    {children}
  </section>
);
export const Spinner = ({ text = "Loading…" }: { text?: string }) => <p role="status" className="p-4 text-sm text-slate-500">{text}</p>;
export const Empty = ({ title, hint, children }: { title: string; hint?: string; children?: ReactNode }) => (
  <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center"><p className="font-medium">{title}</p>{hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}<div className="mt-3">{children}</div></div>
);
export function ErrorBox({ problem, onRetry }: { problem: ApiProblem | string | null; onRetry?: () => void }) {
  if (!problem) return null;
  const p = typeof problem === "string" ? { message: problem } : problem;
  return (
    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      <p className="font-medium">{p.message}</p>
      {p.hint && <p className="mt-1">{p.hint}</p>}
      {onRetry && <Button variant="secondary" className="mt-2" onClick={onRetry}>Retry</Button>}
    </div>
  );
}
const tone: Record<string, string> = { strong_match: "bg-green-100 text-green-800", potential_match: "bg-lime-100 text-lime-800", weak_match: "bg-slate-200 text-slate-700",
  excluded: "bg-red-100 text-red-800", review_required: "bg-amber-100 text-amber-800", high: "bg-red-100 text-red-800", medium: "bg-amber-100 text-amber-800",
  low: "bg-slate-200 text-slate-700", open: "bg-blue-100 text-blue-800", completed: "bg-green-100 text-green-800", cancelled: "bg-slate-200 text-slate-600" };
export const Badge = ({ value, danger }: { value: string | null; danger?: boolean }) =>
  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${danger ? "bg-red-100 text-red-800" : tone[value ?? ""] ?? "bg-indigo-50 text-indigo-800"}`}>{value ? label(value) : "Not scored"}</span>;

export function Field({ label: l, error, hint, ...p }: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium">{l}</span>
      <input className="w-full rounded-md border border-slate-300 px-2 py-1.5 focus:border-indigo-500 focus:outline-none" aria-invalid={!!error} {...p} />
      {hint && <span className="text-xs text-slate-500">{hint}</span>}
      {error && <span className="block text-xs text-red-700" role="alert">{error}</span>}
    </label>
  );
}
export const Select = ({ label: l, children, ...p }: { label: string; children: ReactNode } & React.SelectHTMLAttributes<HTMLSelectElement>) => (
  <label className="block text-sm"><span className="mb-1 block font-medium">{l}</span>
    <select className="w-full rounded-md border border-slate-300 px-2 py-1.5" {...p}>{children}</select></label>
);

export function Pagination({ page, pageSize, total, onChange }: { page: number; pageSize: number; total: number; onChange: (p: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="mt-3 flex items-center justify-between text-sm">
      <span>{total} result{total === 1 ? "" : "s"} · page {page} of {pages}</span>
      <div className="space-x-2">
        <Button variant="secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</Button>
        <Button variant="secondary" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</Button>
      </div>
    </div>
  );
}
export function Confirm({ open, title, message, confirmLabel = "Delete", onConfirm, onCancel }: { open: boolean; title: string; message: string; confirmLabel?: string; onConfirm: () => void; onCancel: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-modal="true" aria-label={title}>
      <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl">
        <h3 className="font-semibold">{title}</h3><p className="mt-2 text-sm text-slate-600">{message}</p>
        <div className="mt-4 flex justify-end gap-2"><Button variant="secondary" onClick={onCancel}>Cancel</Button><Button variant="danger" onClick={onConfirm}>{confirmLabel}</Button></div>
      </div>
    </div>
  );
}

type Toast = { id: number; kind: "success" | "error"; text: string };
const ToastCtx = createContext<(kind: Toast["kind"], text: string) => void>(() => {});
export const useToast = () => useContext(ToastCtx);
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((kind: Toast["kind"], text: string) => {
    const id = Date.now() + Math.random();
    setItems((x) => [...x, { id, kind, text }]);
    setTimeout(() => setItems((x) => x.filter((t) => t.id !== id)), 5000);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div aria-live="polite" className="fixed bottom-4 right-4 z-50 space-y-2">
        {items.map((t) => <div key={t.id} className={`rounded-md px-4 py-2 text-sm text-white shadow ${t.kind === "success" ? "bg-green-700" : "bg-red-700"}`}>{t.text}</div>)}
      </div>
    </ToastCtx.Provider>
  );
}
