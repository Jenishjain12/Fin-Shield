import { NavLink, Outlet } from "react-router-dom";
import { Bell, GitFork, LayoutDashboard, ScanSearch, Shield, Table2 } from "lucide-react";

const links = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/analyze", label: "Analyze Advertisement", icon: ScanSearch },
  { to: "/investigations", label: "Investigations", icon: Table2 },
  { to: "/campaigns", label: "Campaign Intelligence", icon: GitFork },
  { to: "/alerts", label: "Alerts", icon: Bell },
];

export function AppLayout() {
  return (
    <div className="min-h-screen bg-ink text-paper">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r border-line bg-panel">
        <div className="flex items-center gap-3 border-b border-line px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded border border-accent/40 text-accent">
            <Shield size={18} />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-[0.18em]">FIN-SHIELD</p>
            <p className="text-[11px] text-mute">Ad intelligence</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
                  isActive ? "bg-white/5 text-paper" : "text-mute hover:bg-white/5 hover:text-paper"
                }`
              }
            >
              <link.icon size={16} />
              {link.label}
            </NavLink>
          ))}
        </nav>
        <p className="px-5 pb-5 text-[11px] leading-relaxed text-mute">
          Scores are configured triage indicators, not a probability of fraud and not proof of a crime.
        </p>
      </aside>
      <div className="ml-64 min-h-screen">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-ink/90 px-6 py-3 backdrop-blur">
          <p className="text-xs uppercase tracking-[0.2em] text-mute">Investigation console</p>
          <p className="text-xs text-mute">Synthetic demo data is labeled in-product</p>
        </header>
        <main className="px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
