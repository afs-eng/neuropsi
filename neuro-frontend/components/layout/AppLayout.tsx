"use client";

import React, { useState, useEffect, useCallback } from "react";
import { AppSidebar } from "./AppSidebar";
import { AppHeader } from "./AppHeader";

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarHidden, setSidebarHidden] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia("(max-width: 767px)");
    const handler = (e: MediaQueryListEvent | MediaQueryList) => {
      const mobile = e.matches;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarHidden(true);
      } else {
        setSidebarHidden(false);
      }
    };
    handler(mql);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  const toggleSidebar = useCallback(() => {
    if (isMobile) {
      setSidebarHidden(!sidebarHidden);
    }
  }, [isMobile, sidebarHidden]);

  const sidebarVisible = !sidebarHidden;

  return (
    <div className="min-h-screen bg-slate-50 app-shell">
      <AppSidebar
        collapsed={false}
        onHide={() => setSidebarHidden(true)}
        hidden={sidebarHidden}
        isMobile={isMobile}
        onNavClick={() => isMobile && setSidebarHidden(true)}
      />
      <AppHeader
        onToggleSidebar={toggleSidebar}
        isMobile={isMobile}
      />

      {isMobile && sidebarVisible && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300 app-shell-overlay"
          onClick={() => setSidebarHidden(true)}
          aria-hidden="true"
        />
      )}

      <main
        className={`pt-16 transition-all duration-300 app-shell-main ${
          isMobile
            ? "px-4"
            : "pl-[260px]"
        }`}
      >
        <div className="mx-auto max-w-7xl py-4 app-shell-content">
          {children}
        </div>
      </main>
    </div>
  );
}
