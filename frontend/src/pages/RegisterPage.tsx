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
  const [busy, setBusy] = useState(false);
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    const x: Record<string, string> = {};
    if (!f.name.trim()) x.name = "Name is required";
    if (!EMAIL_RE.test(f.email.trim())) x.email = "Enter a valid email address";
    if (f.password.length < 8) x.password = "Use at least 8 characters";
    setErrs(x);
    if (Object.keys(x).length) return;
    setBusy(true); setServer(null);
    try { await api.register(f.name.trim(), f.email.trim(), f.password); toast("success", "Account created. Please sign in."); nav("/login"); }
    catch (err) { setServer(apiErrorMessage(err)); } finally { setBusy(false); }
  }
  return (
    <div className="auth-page">
      <div className="auth-shell auth-shell-register">
        <aside className="auth-visual">
          <div className="auth-brand"><span className="auth-brand-mark">S</span><span>Sales Ops<span className="auth-brand-sub">Intelligence workspace</span></span></div>
          <div className="auth-visual-content"><span className="auth-eyebrow"><span className="auth-live-dot" /> A BETTER WAY TO SELL</span><h1>Build a pipeline<br />with purpose.</h1><p>Bring your leads, qualification signals, and next steps into one clear workspace—so the important work never gets lost.</p>
            <div className="auth-highlight-card"><div className="auth-highlight-top"><span>PIPELINE SNAPSHOT</span><span className="auth-mini-pill">LIVE WORKSPACE</span></div><div className="auth-highlight-number">One place. <em>More clarity.</em></div><div className="auth-highlight-bars"><span /><span /><span /><span /><span /><span /><span /><span /><span /><span /><span /><span /></div><div className="auth-highlight-caption"><span>Lead fit</span><span>Outreach</span><span>Follow-ups</span></div></div>
          </div>
          <div className="auth-visual-footer">Thoughtful workflows. Better conversations.</div><div className="auth-orb auth-orb-one" /><div className="auth-orb auth-orb-two" />
        </aside>
        <section className="auth-panel">
          <div className="auth-mobile-brand"><span className="auth-brand-mark">S</span><b>Sales Ops</b></div>
          <div className="auth-form-wrap"><span className="auth-step">GET STARTED</span><h2>Create your account</h2><p className="auth-subtitle">Set up your workspace and get your pipeline organised.</p>
            <form onSubmit={submit} className="mt-7 space-y-4" noValidate>
              <Field label="Full name" value={f.name} onChange={set("name")} error={errs.name} autoComplete="name" placeholder="Your name" />
              <Field label="Work email" type="email" value={f.email} onChange={set("email")} error={errs.email} autoComplete="email" placeholder="you@company.com" />
              <Field label="Create password" type="password" value={f.password} onChange={set("password")} error={errs.password} hint="Use at least 8 characters" autoComplete="new-password" placeholder="At least 8 characters" />
              <ErrorBox problem={server} />
              <button type="submit" disabled={busy} className="auth-submit">{busy ? <><span className="auth-button-spinner" /> Creating account…</> : <>Create account <span aria-hidden="true">→</span></>}</button>
            </form>
            <div className="auth-divider"><span />or sign up with<span /></div><GoogleSignIn />
            <p className="auth-switch">Already have an account? <Link to="/login">Sign in <span aria-hidden="true">→</span></Link></p>
            <p className="auth-privacy">Your workspace access is managed securely.</p>
          </div>
        </section>
      </div>
    </div>
  );
}
