import { Link, Navigate } from "react-router-dom";
import { Spinner } from "../components/ui";
import { useAuth } from "../hooks/useAuth";

const features = [
  { icon: "◈", title: "Qualify with context", text: "Review lead-fit signals and see why a prospect may match your ideal customer profile." },
  { icon: "✳", title: "Create thoughtful outreach", text: "Draft personalised messages grounded in the lead details you actually have." },
  { icon: "⌁", title: "Keep momentum", text: "Organise follow-ups and next steps so promising conversations do not go cold." },
];

export default function HomePage() {
  const { user, loading } = useAuth();
  if (loading) return <Spinner text="Opening your workspace…" />;
  if (user) return <Navigate to="/dashboard" replace />;

  return (
    <div className="landing-page">
      <div className="landing-grid" aria-hidden="true" />
      <header className="landing-nav">
        <Link to="/" className="landing-brand" aria-label="Sales Ops home">
          <span className="landing-brand-mark">S<span>+</span></span>
          <span>SALES<span className="landing-brand-light">OPS</span><small>INTELLIGENCE PLATFORM</small></span>
        </Link>
        <nav className="landing-nav-actions" aria-label="Main navigation">
          <a href="#platform">Platform</a><a href="#workflow">How it works</a>
          <Link to="/login" className="landing-login">Log in <span>↗</span></Link>
          <Link to="/register" className="landing-register">Get started <span>→</span></Link>
        </nav>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-hero-copy">
            <div className="landing-kicker"><span className="landing-pulse" /> INTELLIGENCE FOR THE NEXT SALES MOVE</div>
            <h1>Turn your leads<br />into <span>clear next moves.</span></h1>
            <p className="landing-lede">One focused workspace to understand lead fit, prepare relevant outreach, and keep every follow-up moving—with AI assistance where it helps.</p>
            <div className="landing-cta-row"><Link to="/register" className="landing-primary-cta">Explore your workspace <span>↗</span></Link><Link to="/login" className="landing-secondary-cta">I already have an account</Link></div>
            <div className="landing-trust-row"><span><i>✓</i> Evidence-led lead scoring</span><span><i>✓</i> AI-assisted workflows</span><span><i>✓</i> One organised pipeline</span></div>
          </div>
          <div className="landing-visual" aria-label="Illustration of a sales intelligence dashboard">
            <div className="landing-visual-orbit orbit-a"/><div className="landing-visual-orbit orbit-b"/>
            <div className="landing-float-label label-top"><span className="signal-dot"/> SIGNAL DETECTED <b>+24%</b></div>
            <div className="landing-dashboard-card">
              <div className="landing-card-head"><div><span className="mini-label">PIPELINE INTELLIGENCE</span><h3>Lead overview</h3></div><span className="live-chip">● LIVE VIEW</span></div>
              <div className="landing-metric-row"><div><small>Qualified leads</small><strong>68<span>.4%</span></strong><em>↗ 12.8% this month</em></div><div className="landing-ring"><span>FIT<br/><b>84</b></span></div></div>
              <div className="landing-chart-label"><span>Qualification signals</span><span>LAST 7 DAYS</span></div>
              <div className="landing-chart" aria-hidden="true"><span style={{height:"34%"}}/><span style={{height:"48%"}}/><span style={{height:"42%"}}/><span style={{height:"66%"}}/><span style={{height:"57%"}}/><span style={{height:"78%"}}/><span style={{height:"69%"}}/><span style={{height:"91%"}}/><span style={{height:"75%"}}/><span style={{height:"100%"}}/><span style={{height:"86%"}}/><span style={{height:"96%"}}/></div>
              <div className="landing-lead-row"><span className="lead-avatar">N</span><span className="lead-company"><b>Northstar Digital</b><small>Strong match · SaaS</small></span><span className="lead-score">94 / 100</span></div>
            </div>
            <div className="landing-float-card"><span className="float-icon">✳</span><span><b>Outreach drafted</b><small>Personalised to lead context</small></span><span className="float-check">✓</span></div>
            <div className="landing-visual-caption">A clearer signal in every conversation.</div>
          </div>
        </section>

        <section className="landing-proof-strip" aria-label="Platform workflow"><div><span className="proof-number">01</span><span><b>Import</b><small>Bring in your lead list</small></span></div><span className="proof-line"/><div><span className="proof-number">02</span><span><b>Understand</b><small>Review fit and context</small></span></div><span className="proof-line"/><div><span className="proof-number">03</span><span><b>Engage</b><small>Plan outreach and follow-ups</small></span></div></section>

        <section id="platform" className="landing-features-section">
          <div className="landing-section-intro"><span className="landing-kicker">THE WORKFLOW, CONNECTED</span><h2>Less tab-switching.<br/><span>More meaningful selling.</span></h2><p>Move from a spreadsheet of names to a practical, organised sales workflow.</p></div>
          <div className="landing-feature-grid">{features.map((feature, i) => <article className="landing-feature-card" key={feature.title}><div className="feature-icon">{feature.icon}</div><span className="feature-index">0{i + 1} / CAPABILITY</span><h3>{feature.title}</h3><p>{feature.text}</p><span className="feature-arrow">↗</span></article>)}</div>
        </section>

        <section id="workflow" className="landing-workflow"><div><span className="landing-kicker">FROM RAW DATA TO NEXT STEP</span><h2>A simple flow.<br/><span>A sharper process.</span></h2><p>Sales Ops helps you keep the work connected, while you stay in control of decisions and customer conversations.</p><Link to="/register" className="landing-primary-cta">Start with your leads <span>→</span></Link></div><div className="workflow-steps"><div className="workflow-step"><span>01</span><div><b>Bring your data</b><p>Import a CSV or add leads to your workspace.</p></div><i>↘</i></div><div className="workflow-step"><span>02</span><div><b>Review the fit</b><p>Inspect scoring signals and missing information.</p></div><i>↘</i></div><div className="workflow-step"><span>03</span><div><b>Take the next action</b><p>Draft outreach and track follow-ups in one place.</p></div><i>✓</i></div></div></section>
      </main>
      <footer className="landing-footer"><Link to="/" className="landing-brand"><span className="landing-brand-mark">S<span>+</span></span><span>SALES<span className="landing-brand-light">OPS</span><small>INTELLIGENCE PLATFORM</small></span></Link><p>Built for clearer decisions and better sales conversations.</p><div><Link to="/login">Log in</Link><Link to="/register">Create account</Link></div></footer>
    </div>
  );
}
