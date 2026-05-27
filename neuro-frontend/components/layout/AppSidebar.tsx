"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { NeuroavaliaLogo } from "@/components/brand/NeuroavaliaLogo";
import {
  LayoutDashboard,
  Users,
  ClipboardList,
  FlaskConical,
  FileText,
  FolderOpen,
  Brain,
  ShieldCheck,
  Settings,
  Plus,
  ChevronRight,
  FileQuestion,
  Stethoscope,
  LogOut,
  X,
} from "lucide-react";

interface NavItem {
  key: string;
  label: string;
  icon: React.ElementType;
  href: string;
  badge?: number;
}

const NAV_ITEMS: NavItem[] = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
  { key: "patients", label: "Pacientes", icon: Users, href: "/dashboard/patients" },
  { key: "evaluations", label: "Avaliações", icon: ClipboardList, href: "/dashboard/evaluations" },
  { key: "tests", label: "Testes", icon: FlaskConical, href: "/dashboard/tests" },
  { key: "anamnesis", label: "Anamnese", icon: Stethoscope, href: "/dashboard/evaluations" },
  { key: "reports", label: "Laudos", icon: FileText, href: "/dashboard/reports" },
  { key: "documents", label: "Documentos", icon: FolderOpen, href: "/dashboard/documents" },
  { key: "ai", label: "IA Clínica", icon: Brain, href: "/dashboard/ai" },
  { key: "accounts", label: "Usuários", icon: ShieldCheck, href: "/dashboard/accounts" },
  { key: "settings", label: "Configurações", icon: Settings, href: "/dashboard/settings" },
];

export function AppSidebar({ 
  collapsed, 
  onNewEvaluation,
  hidden,
  onHide,
  isMobile,
  onNavClick,
}: { 
  collapsed: boolean; 
  onNewEvaluation?: () => void;
  hidden?: boolean;
  onHide?: () => void;
  isMobile?: boolean;
  onNavClick?: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = React.useState<any>(null);

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const savedUser = localStorage.getItem("user");
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch (e) {
          console.error("Error parsing user data");
        }
      }
    }
  }, []);

  const getUserInitials = (userObj: any) => {
    if (!userObj) return "Dr.";
    const rawName = userObj.full_name || userObj.username || "Profissional";
    const cleanName = rawName.replace(/^(Dr\.|Dra\.|Dr|Dra)\s+/i, "").trim();
    const firstName = cleanName.split(/\s+/)[0];
    const isFemale = userObj.sex === "F" || 
                     (firstName.toLowerCase().endsWith("a") && !["luca", "joshua"].includes(firstName.toLowerCase()));
    return isFemale ? "Dra." : "Dr.";
  };

  const getDisplayName = () => {
    if (!user) return "Dr. André";
    if (user.display_name) return user.display_name;
    const rawName = user.full_name || user.username || "Profissional";
    const cleanName = rawName.replace(/^(Dr\.|Dra\.|Dr|Dra)\s+/i, "").trim();
    const firstName = cleanName.split(/\s+/)[0];
    const isFemale = user.sex === "F" || (firstName.toLowerCase().endsWith("a") && !["luca", "joshua"].includes(firstName.toLowerCase()));
    return `${isFemale ? "Dra. " : "Dr. "}${firstName}`;
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    sessionStorage.clear();
    router.push("/login");
  };

  return (
    <aside className={`fixed left-0 top-0 z-50 flex h-screen flex-col border-r border-slate-200 bg-white transition-all duration-300 app-shell-sidebar ${
        isMobile
          ? hidden
            ? "-translate-x-full w-[260px] shadow-xl"
            : "translate-x-0 w-[260px] shadow-2xl"
          : hidden
            ? "-translate-x-full w-0 overflow-hidden"
            : collapsed
              ? "w-[72px]"
              : "w-[260px]"
      }`}>
      <div className="flex h-[118px] items-center justify-between px-1.5">
        <Link href="/dashboard" className="flex min-w-0 flex-1 items-center" onClick={onNavClick} aria-label="Ir para dashboard Neuroavalia">
          {collapsed ? (
            <NeuroavaliaLogo compact className="h-12 w-12 shrink-0" />
          ) : (
            <NeuroavaliaLogo className="h-[114px] w-full" />
          )}
        </Link>
        {isMobile ? (
          <button onClick={onHide} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors" title="Fechar menu">
            <X className="h-5 w-5" />
          </button>
        ) : null}
      </div>

      <div className="p-4">
        <Link href="/dashboard/evaluations/new" className={`flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-spike transition-all hover:opacity-90 active:scale-95 ${collapsed ? "px-0 h-10 w-10 mx-auto" : ""}`}>
          <Plus className="h-5 w-5 shrink-0" />
          {!collapsed && <span>Nova avaliação</span>}
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 custom-scrollbar">
        <ul className="space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href || ""));
            return (
              <li key={item.key}>
                <Link href={item.href} onClick={onNavClick} className={`group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${isActive ? "bg-primary/5 text-primary" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"} ${collapsed ? "justify-center px-0 h-11 w-11 mx-auto" : ""}`}>
                  <div className={`flex shrink-0 items-center justify-center rounded-lg transition-colors ${isActive ? "h-8 w-8 bg-primary text-primary-foreground shadow-sm" : "h-8 w-8 text-slate-400 group-hover:text-slate-600"}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  {!collapsed && <span className="flex-1 truncate">{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mt-auto border-t border-slate-100 p-4">
        <div className={`flex items-center gap-3 rounded-xl bg-slate-50 p-2 border border-slate-100 ${collapsed ? "justify-center p-1" : ""}`}>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white border border-slate-200 text-primary text-sm font-bold shadow-sm whitespace-nowrap">
            {getUserInitials(user)}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-bold text-slate-900">{getDisplayName()}</p>
              <p className="truncate text-[11px] font-medium text-slate-500 uppercase tracking-wider">{user?.specialty || "Neuropsicólogo"}</p>
            </div>
          )}
          {!collapsed && (
            <button onClick={handleLogout} className="text-slate-400 hover:text-primary transition-colors" title="Sair do sistema">
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}

export { NAV_ITEMS };
