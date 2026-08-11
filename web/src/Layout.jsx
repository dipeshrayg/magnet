import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import { api } from "./lib/api";

const NAV = [
  { to: "", label: "Dashboard", end: true },
  { to: "icp", label: "ICP" },
  { to: "leads", label: "Lead Radar" },
  { to: "competitors", label: "Competitor Watch" },
  { to: "pseo", label: "pSEO Factory" },
  { to: "reputation", label: "Reputation" },
  { to: "freetool", label: "Free Tool" },
  { to: "content", label: "Content Studio" },
  { to: "outreach", label: "Outreach" },
  { to: "lifecycle", label: "Lifecycle" },
  { to: "voc", label: "Voice of Customer" },
  { to: "referrals", label: "Referrals" },
  { to: "analytics", label: "Analytics" },
  { to: "approvals", label: "Approval Inbox" },
];

export default function Layout() {
  const { workspaceId } = useParams();
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState([]);
  const [mode, setMode] = useState("DEMO");
  const [dark, setDark] = useState(() => localStorage.getItem("magnet-dark") === "1");

  useEffect(() => {
    api.get("/workspaces").then(setWorkspaces).catch(() => {});
    api.get("/system/mode").then((r) => setMode(r.mode)).catch(() => {});
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("magnet-dark", dark ? "1" : "0");
  }, [dark]);

  return (
    <div className="flex h-full">
      <aside className="w-64 shrink-0 border-r border-slate-200 dark:border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <div className="font-bold text-lg tracking-tight">MAGNET</div>
          <div className="text-xs text-slate-500">One growth engine, every product</div>
        </div>
        <div className="p-3 border-b border-slate-200 dark:border-slate-800 space-y-2">
          <NavLink to="/" className="block text-sm font-medium text-indigo-600 dark:text-indigo-400">
            &larr; Portfolio
          </NavLink>
          <select
            className="w-full text-sm rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-1.5"
            value={workspaceId || ""}
            onChange={(e) => navigate(`/w/${e.target.value}`)}
          >
            <option value="" disabled>Select product...</option>
            {workspaces.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>
        <nav className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {workspaceId && NAV.map((item) => (
            <NavLink
              key={item.to}
              to={`/w/${workspaceId}/${item.to}`}
              end={item.end}
              className={({ isActive }) =>
                `block rounded px-3 py-1.5 text-sm ${isActive
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <span className={`text-xs font-semibold px-2 py-1 rounded ${mode === "LIVE" ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"}`}>
            {mode}
          </span>
          <button onClick={() => setDark((d) => !d)} className="text-xs px-2 py-1 rounded border border-slate-300 dark:border-slate-700">
            {dark ? "Light" : "Dark"}
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
