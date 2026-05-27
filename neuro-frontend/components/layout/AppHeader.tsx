"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Bell,
  Settings,
  ChevronDown,
  LogOut,
  User,
  HelpCircle,
  PanelLeftOpen,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { NeuroavaliaLogo } from "@/components/brand/NeuroavaliaLogo";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function AppHeader({ onToggleSidebar, isMobile }: { onToggleSidebar?: () => void; isMobile?: boolean }) {
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

  const getUserInitials = () => {
    if (!user) return "DR";
    const fullName = user.full_name || user.username || "";
    const parts = fullName.trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return "DR";
  };

  const getDisplayName = () => {
    if (!user) return "Profissional";
    return user.full_name || user.username || "Profissional";
  };

  const getRole = () => {
    if (!user) return "";
    return user.role || user.specialty || "Neuropsicólogo";
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    sessionStorage.clear();
    router.push("/login");
  };

  return (
    <header
      className={`fixed top-0 right-0 z-40 h-16 border-b border-slate-100 bg-white/80 backdrop-blur-md transition-all duration-300 app-shell-header ${
        isMobile ? "left-0" : "left-[260px]"
      }`}
    >
      <div className="flex h-full items-center justify-between px-4 md:px-8">
        <div className="flex items-center gap-2 md:gap-3 flex-1 md:max-w-xl md:pr-8">
          {isMobile && (
            <button onClick={onToggleSidebar} className="group flex shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-slate-50/80 h-10 w-10 text-slate-400 shadow-inner shadow-slate-50 hover:bg-white hover:text-slate-700 hover:border-slate-200 hover:shadow-sm transition-all duration-200 ease-out active:scale-95" title="Mostrar menu">
              <PanelLeftOpen className="h-4 w-4 group-hover:text-primary transition-colors duration-200" />
            </button>
          )}
          {isMobile && (
            <NeuroavaliaLogo className="h-12 w-[176px] shrink-0" />
          )}
          {/* Search */}
          <div className="group relative flex-1 md:block hidden">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 group-focus-within:text-primary transition-colors" />
            <Input
              placeholder="Pesquisar..."
              className="h-10 w-full max-w-[400px] border-transparent bg-slate-50 pl-10 text-sm transition-all focus:bg-white focus:border-slate-200 focus:ring-4 focus:ring-primary/5"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border border-slate-200 bg-white px-1.5 font-mono text-[10px] font-medium text-slate-400 opacity-100">
                <span className="text-xs">⌘</span>K
              </kbd>
            </div>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-0 md:gap-1">
          {/* Support */}
          <Button variant="ghost" size="icon" className="hidden sm:inline-flex h-10 w-10 text-slate-400 hover:text-primary hover:bg-primary/5">
            <HelpCircle className="h-5 w-5" />
          </Button>

          {/* Notifications */}
          <Button variant="ghost" size="icon" className="relative hidden sm:inline-flex h-10 w-10 text-slate-400 hover:text-primary hover:bg-primary/5">
            <Bell className="h-5 w-5" />
            <span className="absolute right-2.5 top-2.5 flex h-2 w-2">
              <span className="relative inline-flex h-2 w-2 rounded-full bg-primary"></span>
            </span>
          </Button>

          {/* Divider */}
          <div className="mx-1 md:mx-3 h-6 w-px bg-slate-100 hidden sm:block"></div>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="group flex items-center gap-3 rounded-xl p-1 pr-2 transition-all hover:bg-slate-50">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white border border-slate-200 text-primary text-xs font-bold shadow-sm transition-all group-hover:border-primary/20">
                  {getUserInitials()}
                </div>
                <div className="text-left hidden lg:block">
                  <p className="text-sm font-bold text-slate-900 leading-tight">{getDisplayName()}</p>
                  <p className="text-[10px] font-semibold text-primary uppercase tracking-widest opacity-80">{getRole()}</p>
                </div>
                <ChevronDown className="h-4 w-4 text-slate-400 group-hover:text-primary transition-colors" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 mt-2">
              <DropdownMenuLabel className="font-semibold text-slate-900">Minha Conta</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer">
                <User className="mr-2 h-4 w-4 text-slate-400" />
                <span>Perfil</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer">
                <Settings className="mr-2 h-4 w-4 text-slate-400" />
                <span>Configurações</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600 cursor-pointer focus:bg-red-50 focus:text-red-600" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Sair</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
