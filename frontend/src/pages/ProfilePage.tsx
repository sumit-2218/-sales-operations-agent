import { FormEvent, useState } from "react";
import { Card, ErrorBox, Field, useToast } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { apiErrorMessage } from "../utils/errors";
import { label } from "../utils/format";

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const toast = useToast();
  const [name, setName] = useState(user?.name ?? "");
  const [cur, setCur] = useState(""); const [next, setNext] = useState("");
  const [err, setErr] = useState<string | null>(null);
  async function save(e: FormEvent) {
    e.preventDefault(); setErr(null);
    if (!name.trim()) { setErr("Name is required."); return; }
    if (next && next.length < 8) { setErr("The new password must have at least 8 characters."); return; }
    try { await api.updateMe({ name: name.trim(), ...(next ? { current_password: cur, new_password: next } : {}) }); toast("success", "Profile updated"); setCur(""); setNext(""); await refresh(); }
    catch (x) { setErr(apiErrorMessage(x)); }
  }
  return (
    <>
      <div className="mb-2"><p className="page-eyebrow">YOUR ACCOUNT</p><h1 className="text-2xl font-bold">Profile & settings</h1><p className="mt-1 text-sm text-slate-500">Manage your personal details and sign-in security.</p></div>
      <Card className="profile-card">
        <div className="profile-summary"><div className="profile-large-avatar">{user?.name?.trim()?.charAt(0)?.toUpperCase() || "U"}</div><div className="min-w-0"><h2 className="truncate text-lg font-bold text-slate-900">{user?.name}</h2><p className="mt-1 truncate text-sm text-slate-500">{user?.email}</p><span className="profile-role-pill">{label(user?.role)} account</span></div></div>
        <div className="profile-section-heading"><h3>Personal information</h3><p>Update the name associated with your workspace.</p></div>
        <form onSubmit={save} className="profile-form max-w-xl space-y-4" noValidate>
          <Field label="Full name" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
          <div className="profile-section-heading profile-security-heading"><h3>Security</h3><p>Leave password fields blank if you don't want to change your password.</p></div>
          <Field label="Current password" type="password" value={cur} onChange={(e) => setCur(e.target.value)} hint="Required when changing your password" autoComplete="current-password" />
          <Field label="New password" type="password" value={next} onChange={(e) => setNext(e.target.value)} hint="Use at least 8 characters" autoComplete="new-password" />
          <ErrorBox problem={err} /><button type="submit" className="ui-button ui-button-primary">Save changes <span aria-hidden="true">→</span></button>
        </form>
      </Card>
    </>
  );
}
