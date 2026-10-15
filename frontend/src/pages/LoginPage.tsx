import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Button, ErrorBox, Field } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { apiErrorMessage } from "../utils/errors";
import GoogleSignIn from "../components/GoogleSignIn";

export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function LoginPage() {
  const { user, signIn } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs: typeof errors = {};
    if (!email.trim()) errs.email = "Email is required";
    else if (!EMAIL_RE.test(email.trim())) errs.email = "Enter a valid email address";
    if (!password) errs.password = "Password is required";
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setBusy(true); setServerError(null);
    try { await signIn(email.trim(), password); nav("/"); } catch (err) { setServerError(apiErrorMessage(err)); } finally { setBusy(false); }
  }
  return (
    <div className="mx-auto mt-24 max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="mb-4 text-xl font-bold">Sign in</h1>
      <form onSubmit={submit} className="space-y-3" noValidate>
        <Field label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} autoComplete="username" />
        <Field label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} autoComplete="current-password" />
        <ErrorBox problem={serverError} />
        <button type="submit" disabled={busy} className="w-full rounded-md bg-indigo-600 py-2 text-sm font-medium text-white disabled:opacity-50">{busy ? "Signing in…" : "Sign in"}</button>
      </form>
      <div className="my-5 flex items-center gap-3 text-xs text-slate-400"><span className="h-px flex-1 bg-slate-200" />OR<span className="h-px flex-1 bg-slate-200" /></div>
      <GoogleSignIn />
      <p className="mt-4 text-sm">No account? <Link to="/register" className="text-indigo-700 underline">Register</Link></p>
    </div>
  );
}
