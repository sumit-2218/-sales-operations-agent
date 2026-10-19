import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { normalizeRole, useAuth } from "../hooks/useAuth";

const navItems = [
  { to: "/dashboard", label: "Overview", icon: "◫", end: true },
  { to: "/leads", label: "Leads", icon: "◎" },
  { to: "/import", label: "Import CSV", icon: "⇧" },
  { to: "/icp", label: "ICP settings", icon: "⌘" },
  { to: "/follow-ups", label: "Follow-ups", icon: "◷" },
  { to: "/profile", label: "Profile", icon: "◉" },
];
const link = ({ isActive }: { isActive: boolean }) => `app-nav-link ${isActive ? "app-nav-link-active" : ""}`;

export default function AppLayout() {
  const { user, signOut } = useAuth();
  const nav = useNavigate();
  const isAdmin = normalizeRole(user?.role) === "admin";
  const adminItems = [
    { to: "/admin", label: "Admin overview", icon: "▦", end: true },
    { to: "/admin/users", label: "User management", icon: "♙" },
    { to: "/admin/system", label: "System status", icon: "⌁" },
  ];
  return (
    <div className="app-shell flex min-h-screen flex-col md:flex-row">
      <aside className="app-sidebar z-10 w-full shrink-0 p-3 md:sticky md:top-0 md:h-screen md:w-64 md:p-5">
        <div className="app-brand mb-4 flex items-center gap-3 px-2 md:mb-9">
          <div className="app-brand-mark flex h-11 w-11 items-center justify-center rounded-2xl text-lg font-black text-white">S</div>
          <div><p className="font-bold tracking-tight text-slate-950">Sales Ops</p><p className="text-xs text-slate-500">Intelligence workspace</p></div>
        </div>
        <p className="app-nav-caption px-3 pb-2">WORKSPACE</p>
        <nav className="flex gap-1 md:block md:space-y-1" aria-label="Main">
          {navItems.map((item) => <NavLink key={item.to} to={item.to} end={item.end} className={link}><span className="app-nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span></NavLink>)}
          {isAdmin && <>
            <p className="app-nav-caption px-3 pb-2 pt-5">ADMINISTRATION</p>
            {adminItems.map((item) => <NavLink key={item.to} to={item.to} end={item.end} className={link}><span className="app-nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span></NavLink>)}
          </>}
        </nav>
        <div className="app-sidebar-note mt-6 hidden rounded-2xl p-4 md:block"><p className="text-sm font-semibold">A clearer view of your pipeline</p><p className="mt-1 text-xs leading-5">Qualify leads, personalise outreach, and keep every follow-up moving.</p></div>
        <div className="app-sidebar-footer mt-auto hidden items-center gap-3 px-2 pt-8 md:flex"><div className="app-avatar">{user?.name?.trim()?.charAt(0)?.toUpperCase() || "U"}</div><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-800">{user?.name ?? "Workspace user"}</p><p className="truncate text-xs text-slate-500">{user?.email ?? ""}</p></div></div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="app-topbar sticky top-0 z-20 flex min-h-20 items-center justify-between gap-3 px-4 py-3 md:px-8">
          <div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-[.16em] text-indigo-600">Sales workspace</p><p className="truncate text-lg font-bold tracking-tight text-slate-950">Welcome back, {user?.name?.split(" ")[0] ?? "there"}</p></div>
          <div className="flex items-center gap-3"><span className="app-status-pill hidden sm:inline-flex"><span className="app-status-dot" />Workspace active</span><button className="app-logout" onClick={async () => { await signOut(); nav("/login"); }}>Log out <span aria-hidden="true">↗</span></button></div>
        </header>
        <main className="app-main mx-auto max-w-[1440px] space-y-6 p-4 md:p-8"><Outlet /></main>
      </div>
    </div>
  );
}
