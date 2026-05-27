"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
}

export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <div className={cn("min-h-[calc(100vh-4rem)] bg-background p-8 lg:p-10 print:min-h-0 print:bg-white print:p-0 report-print-shell", className)}>
      <div className="mx-auto max-w-7xl animate-in fade-in slide-in-from-bottom-2 duration-500 print:max-w-none report-print-card">
        {children}
      </div>
    </div>
  );
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  breadcrumbs?: React.ReactNode;
}

export function PageHeader({ title, subtitle, actions, breadcrumbs }: PageHeaderProps) {
  return (
    <div className="mb-8 print:mb-4">
      {breadcrumbs && <div className="mb-4 print:hidden">{breadcrumbs}</div>}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{title}</h1>
          {subtitle && (
            <p className="text-base font-medium text-slate-500 max-w-2xl">
              {subtitle}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3 print:hidden report-print-hide">{actions}</div>}
      </div>
    </div>
  );
}

interface SectionCardProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  icon?: React.ReactNode;
}

export function SectionCard({ title, description, children, actions, className, icon }: SectionCardProps) {
  return (
    <div className={cn("spike-card overflow-hidden print:break-inside-avoid print:shadow-none report-print-break-avoid", className)}>
      {(title || actions || icon) && (
        <div className="flex items-center justify-between border-b border-slate-50 px-6 py-5 bg-slate-50/30 print:bg-white">
          <div className="flex items-center gap-3">
            {icon && <div className="shrink-0">{icon}</div>}
            <div>
              {title && <h3 className="text-lg font-bold text-slate-900">{title}</h3>}
              {description && <p className="mt-1 text-sm font-medium text-slate-500">{description}</p>}
            </div>
          </div>
          {actions && <div className="flex items-center gap-2 print:hidden report-print-hide">{actions}</div>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ElementType;
  trend?: {
    value: number;
    label: string;
  };
  className?: string;
}

export function StatCard({ title, value, description, icon: Icon, trend, className }: StatCardProps) {
  return (
    <div className={cn("spike-card p-6 transition-all hover:shadow-md hover:border-primary/10 group", className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-bold text-slate-500 uppercase tracking-wider">{title}</p>
          <div className="flex items-baseline gap-2">
            <h4 className="text-3xl font-black tracking-tight text-slate-900">{value}</h4>
            {trend && (
              <span
                className={cn(
                  "flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full",
                  trend.value >= 0
                    ? "text-primary bg-primary/10"
                    : "text-red-600 bg-red-100"
                )}
              >
                {trend.value >= 0 ? "+" : ""}
                {trend.value}%
              </span>
            )}
          </div>
          {(description || trend) && (
            <p className="text-xs font-medium text-slate-400 mt-1">
              {description || trend?.label}
            </p>
          )}
        </div>
        {Icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-50 text-slate-400 transition-colors group-hover:bg-primary/5 group-hover:text-primary">
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
    </div>
  );
}

interface InfoCardProps {
  label: string;
  value: string | React.ReactNode;
  icon?: React.ElementType;
  className?: string;
}

export function InfoCard({ label, value, icon: Icon, className }: InfoCardProps) {
  return (
    <div className={cn("flex items-center gap-4 rounded-xl border border-slate-100 bg-white p-4 shadow-sm transition-all hover:border-primary/20", className)}>
      {Icon && (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-50 text-slate-400">
          <Icon className="h-5 w-5" />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest leading-tight">{label}</p>
        <p className="mt-1 text-sm font-bold text-slate-900 truncate">{value}</p>
      </div>
    </div>
  );
}

interface SummaryCardProps {
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function SummaryCard({ title, children, className }: SummaryCardProps) {
  return (
    <div className={cn("spike-card p-5", className)}>
      <h4 className="mb-4 text-xs font-black text-slate-400 uppercase tracking-[0.2em]">{title}</h4>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center spike-card bg-slate-50/50 border-dashed">
      {icon && <div className="mb-6 text-slate-200">{icon}</div>}
      <h3 className="text-xl font-bold text-slate-900">{title}</h3>
      {description && <p className="mt-2 max-w-sm text-base font-medium text-slate-500">{description}</p>}
      {action && <div className="mt-8">{action}</div>}
    </div>
  );
}
