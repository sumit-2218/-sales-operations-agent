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
      <h1 className="text-2xl font-bold">Profile</h1>
      <Card><p className="mb-3 text-sm">{user?.email} · {label(user?.role)}</p>
        <form onSubmit={save} className="max-w-sm space-y-3" noValidate>
          <Field label="Name" value={name} onChange={(e) => setName(e.target.value)} />
          <Field label="Current password" type="password" value={cur} onChange={(e) => setCur(e.target.value)} hint="Only needed to change your password" autoComplete="current-password" />
          <Field label="New password" type="password" value={next} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" />
          <ErrorBox problem={err} /><button type="submit" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white">Save</button></form></Card>
    </>
  );
}
