import { AnimatePresence, motion } from "framer-motion";
import {
  BarChart3,
  BookOpen,
  Brain,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageCircle,
  NotebookPen,
  Search,
  Settings,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Brand } from "@/components/layout/Brand";
import { Avatar } from "@/components/ui/Feedback";
import { useAuth } from "@/context/AuthContext";
import { healthApi } from "@/services/endpoints";
import type { Health } from "@/types/api";
import { cn } from "@/utils/format";

const NAV = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/app/chat", label: "Mentor Chat", icon: MessageCircle },
  { to: "/app/knowledge", label: "Knowledge Vault", icon: BookOpen },
  { to: "/app/experiences", label: "Experiences", icon: NotebookPen },
  { to: "/app/personality", label: "Personality", icon: SlidersHorizontal },
  { to: "/app/memory", label: "Memory Inspector", icon: Search },
  { to: "/app/insights", label: "Insights", icon: BarChart3 },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    healthApi.get().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="flex h-full flex-col">
      <div className="px-5 pb-4 pt-5">
        <Brand to="/app" light />
      </div>
      <nav aria-label="Main" className="flex-1 space-y-1 overflow-y-auto px-3">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                isActive ? "bg-cream text-brown shadow-paper" : "text-cream/80 hover:bg-white/10 hover:text-cream",
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={cn("h-[18px] w-[18px]", isActive ? "text-mustard-dark" : "text-gold/80")} aria-hidden />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="space-y-3 border-t border-white/10 p-4">
        {health && (
          <div className="rounded-xl bg-white/5 px-3 py-2 text-xs text-cream/70">
            <div className="flex items-center gap-2">
              <Brain className="h-3.5 w-3.5 text-gold" aria-hidden />
              {health.ai.mode === "live" ? (
                <span>
                  AI: <span className="text-cream">{health.ai.model}</span>
                </span>
              ) : (
                <span>
                  AI: <span className="text-gold">demo mode</span> (no API key)
                </span>
              )}
            </div>
          </div>
        )}
        <div className="flex items-center gap-3">
          <Avatar name={user?.full_name} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-cream">{user?.full_name}</p>
            <p className="truncate text-xs text-cream/60">{user?.email}</p>
          </div>
          <button
            type="button"
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
            className="rounded-lg p-2 text-cream/70 hover:bg-white/10 hover:text-cream"
            aria-label="Sign out"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AppLayout() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => setOpen(false), [location.pathname]);

  return (
    <div className="min-h-screen lg:pl-64">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <aside className="fixed inset-y-0 left-0 hidden w-64 bg-brown lg:block" aria-label="Sidebar">
        <Sidebar />
      </aside>

      <div className="sticky top-0 z-40 flex items-center justify-between border-b border-line bg-cream/90 px-4 py-3 backdrop-blur lg:hidden">
        <Brand to="/app" />
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="rounded-lg p-2 text-brown hover:bg-paper"
            aria-label="Open navigation"
            aria-expanded={open}
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <motion.div
              className="absolute inset-0 bg-ink/50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.aside
              className="absolute inset-y-0 left-0 w-72 max-w-[85%] bg-brown shadow-lift"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "tween", duration: 0.22 }}
              aria-label="Mobile navigation"
            >
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="absolute right-3 top-4 rounded-lg p-2 text-cream/80 hover:bg-white/10"
                aria-label="Close navigation"
              >
                <X className="h-5 w-5" />
              </button>
              <Sidebar onNavigate={() => setOpen(false)} />
            </motion.aside>
          </div>
        )}
      </AnimatePresence>

      <main id="main" className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-10 lg:py-10">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: "easeOut" }}
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  );
}
