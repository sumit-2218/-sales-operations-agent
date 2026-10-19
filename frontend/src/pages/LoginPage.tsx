import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ErrorBox, Field } from "../components/ui";
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
  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs: typeof errors = {};
    if (!email.trim()) errs.email = "Email is required";
    else if (!EMAIL_RE.test(email.trim())) errs.email = "Enter a valid email address";
    if (!password) errs.password = "Password is required";
    setErrors(errs);
    if (Object.keys(errs).length) return;
    setBusy(true); setServerError(null);
    try { await signIn(email.trim(), password); nav("/dashboard"); } catch (err) { setServerError(apiErrorMessage(err)); } finally { setBusy(false); }
  }

  return (
    <div className="auth-page">
      <div className="auth-shell">
        <aside className="auth-visual">
          <div className="auth-brand"><span className="auth-brand-mark">S</span><span>Sales Ops<span className="auth-brand-sub">Intelligence workspace</span></span></div>
          <div className="auth-visual-content"><span className="auth-eyebrow"><span className="auth-live-dot" /> YOUR PIPELINE, IN FOCUS</span><h1>Make every lead<br />count.</h1><p>Turn raw prospects into clear next steps with lead qualification, thoughtful outreach, and a pipeline that stays organised.</p>
            <div className="auth-feature-list"><div><span>✓</span><p><b>Understand lead fit</b><small>See the signals behind every score.</small></p></div><div><span>↗</span><p><b>Move faster</b><small>Keep outreach and follow-ups together.</small></p></div><div><span>⌁</span><p><b>Stay in control</b><small>One workspace for your sales workflow.</small></p></div></div>
          </div>
          <div className="auth-visual-footer">Built for focused, evidence-led selling.</div>
          <div className="auth-orb auth-orb-one" /><div className="auth-orb auth-orb-two" />
        </aside>
        <section className="auth-panel">
          <div className="auth-mobile-brand"><span className="auth-brand-mark">S</span><b>Sales Ops</b></div>
          <div className="auth-form-wrap"><span className="auth-step">WELCOME BACK</span><h2>Sign in to your workspace</h2><p className="auth-subtitle">Enter your details to pick up where you left off.</p>
            <form onSubmit={submit} className="mt-7 space-y-5" noValidate>
              <Field label="Email address" type="email" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} autoComplete="username" placeholder="you@company.com" />
              <Field label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} autoComplete="current-password" placeholder="Enter your password" />
              <ErrorBox problem={serverError} />
              <button type="submit" disabled={busy} className="auth-submit">{busy ? <><span className="auth-button-spinner" /> Signing in…</> : <>Sign in <span aria-hidden="true">→</span></>}</button>
            </form>
            <div className="auth-divider"><span />or continue with<span /></div><GoogleSignIn />
            <p className="auth-switch">New to Sales Ops? <Link to="/register">Create an account <span aria-hidden="true">→</span></Link></p>
            <p className="auth-privacy">Secure access to your sales workspace</p>
          </div>
        </section>
      </div>
    </div>
  );
}
