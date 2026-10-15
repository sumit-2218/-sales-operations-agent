import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ErrorBox, Field, useToast } from "../components/ui";
import { api } from "../services/api";
import { apiErrorMessage } from "../utils/errors";
import { EMAIL_RE } from "./LoginPage";
import GoogleSignIn from "../components/GoogleSignIn";

export default function RegisterPage() {
  const nav = useNavigate();
  const toast = useToast();
  const [f, setF] = useState({ name: "", email: "", password: "" });
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [server, setServer] = useState<string | null>(null);
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    const x: Record<string, string> = {};
    if (!f.name.trim()) x.name = "Name is required";
    if (!EMAIL_RE.test(f.email.trim())) x.email = "Enter a valid email address";
    if (f.password.length < 8) x.password = "Use at least 8 characters";
    setErrs(x);
    if (Object.keys(x).length) return;
    try { await api.register(f.name.trim(), f.email.trim(), f.password); toast("success", "Account created. Please sign in."); nav("/login"); }
    catch (err) { setServer(apiErrorMessage(err)); }
  }
  return (
    <div className="mx-auto mt-24 max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="mb-4 text-xl font-bold">Create account</h1>
      <form onSubmit={submit} className="space-y-3" noValidate>
        <Field label="Name" value={f.name} onChange={set("name")} error={errs.name} />
        <Field label="Email" type="email" value={f.email} onChange={set("email")} error={errs.email} />
        <Field label="Password" type="password" value={f.password} onChange={set("password")} error={errs.password} hint="At least 8 characters" />
        <ErrorBox problem={server} />
        <button type="submit" className="w-full rounded-md bg-indigo-600 py-2 text-sm font-medium text-white">Register</button>
      </form>
      <div className="my-5 flex items-center gap-3 text-xs text-slate-400"><span className="h-px flex-1 bg-slate-200" />OR<span className="h-px flex-1 bg-slate-200" /></div>
      <GoogleSignIn />
      <p className="mt-4 text-sm">Already registered? <Link to="/login" className="text-indigo-700 underline">Sign in</Link></p>
    </div>
  );
}
