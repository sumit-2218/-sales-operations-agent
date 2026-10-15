import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { label } from "../utils/format";

const link = ({ isActive }: { isActive: boolean }) => `block rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${isActive ? "bg-indigo-600 text-white shadow-sm" : "text-slate-600 hover:bg-indigo-50 hover:text-indigo-700"}`;

export default function AppLayout() {
  const { user, signOut } = useAuth();
  const nav = useNavigate();
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="z-10 w-full shrink-0 border-b border-slate-200/80 bg-white p-3 md:sticky md:top-0 md:h-screen md:w-60 md:border-b-0 md:border-r md:p-5">
        <div className="mb-4 flex items-center gap-3 px-2 md:mb-8"><div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-500 text-lg font-black text-white shadow-md">S</div><div><p className="font-bold tracking-tight text-slate-900">Sales Ops</p><p className="text-xs text-slate-500">Intelligence workspace</p></div></div>
        <nav className="flex gap-1 md:block md:space-y-1" aria-label="Main">
          <NavLink to="/" end className={link}>Overview</NavLink><NavLink to="/leads" className={link}>Leads</NavLink><NavLink to="/import" className={link}>Import CSV</NavLink><NavLink to="/icp" className={link}>ICP settings</NavLink><NavLink to="/follow-ups" className={link}>Follow-ups</NavLink><NavLink to="/profile" className={link}>Profile</NavLink>
          {user?.role === "admin" && <><p className="hidden px-3 pt-5 text-xs font-bold uppercase tracking-wider text-slate-400 md:block">Administration</p><NavLink to="/admin" end className={link}>Admin overview</NavLink><NavLink to="/admin/users" className={link}>Users</NavLink><NavLink to="/admin/system" className={link}>System status</NavLink></>}
        </nav>
        <div className="mt-5 hidden rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-50 p-4 md:block"><p className="text-sm font-semibold text-indigo-950">Work smarter</p><p className="mt-1 text-xs leading-5 text-indigo-800/80">Qualify leads, personalise outreach, and keep every follow-up on track.</p></div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-5 flex min-h-16 items-center justify-between gap-3 border-b border-slate-200/80 bg-white/90 px-4 py-3 backdrop-blur md:px-8"><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">Welcome back, {user?.name?.split(" ")[0] ?? "there"}</p><p className="text-xs text-slate-500">Your sales workspace</p></div><div className="flex items-center gap-3"><span className="hidden rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 sm:inline-flex">● Workspace active</span><button className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-indigo-200 hover:bg-indigo-50" onClick={async () => { await signOut(); nav("/login"); }}>Log out</button></div></header>
        <main className="mx-auto max-w-7xl space-y-5 p-4 md:p-8"><Outlet /></main>
      </div>
    </div>
  );
}
