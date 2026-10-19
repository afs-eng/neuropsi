"use client";

import type { KeyboardEvent, ReactNode } from "react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { BookOpen, FlaskConical, MoreHorizontal, Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export type ReportWorkspace = "editor" | "tests" | "specialists";

export function parseReportWorkspace(value: string | null): ReportWorkspace {
  return value === "tests" || value === "specialists" ? value : "editor";
}

const workspaces = [
  { key: "editor", label: "Editor do laudo", shortLabel: "Editor", icon: BookOpen },
  { key: "tests", label: "Dados dos testes", shortLabel: "Testes", icon: Table2 },
  { key: "specialists", label: "Especialistas de IA", shortLabel: "Especialistas", icon: FlaskConical },
] as const;

export function ReportWorkspaceTabs({ value, onChange }: { value: ReportWorkspace; onChange: (value: ReportWorkspace) => void }) {
  function navigate(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const next = event.key === "ArrowRight" ? (index + 1) % workspaces.length
      : event.key === "ArrowLeft" ? (index + workspaces.length - 1) % workspaces.length
        : event.key === "Home" ? 0 : event.key === "End" ? workspaces.length - 1 : null;
    if (next === null) return;
    event.preventDefault();
    onChange(workspaces[next].key);
    event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[next]?.focus();
  }

  return (
    <div role="tablist" aria-label="Áreas do laudo" className="mb-6 grid grid-cols-3 gap-1 border-b border-slate-200 lg:flex">
      {workspaces.map(({ key, label, shortLabel, icon: Icon }, index) => (
        <button key={key} id={`report-tab-${key}`} type="button" role="tab" aria-label={label} aria-selected={value === key} aria-controls={`report-panel-${key}`} tabIndex={value === key ? 0 : -1}
          onClick={() => onChange(key)} onKeyDown={(event) => navigate(event, index)}
          className={`inline-flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 border-b-2 px-2 py-3 text-xs font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary lg:flex-row lg:gap-2 lg:px-4 lg:text-sm ${value === key ? "border-primary text-primary" : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-900"}`}>
          <Icon aria-hidden="true" className="h-4 w-4 shrink-0" /><span className="hidden lg:inline">{label}</span><span className="min-w-0 break-words lg:hidden">{shortLabel}</span>
        </button>
      ))}
    </div>
  );
}

export type ReportAction = { label: string; onSelect: () => void; disabled?: boolean; icon?: ReactNode };

export function ReportActionsMenu({ actions, disabled, label = "Mais ações" }: { actions: ReportAction[]; disabled?: boolean; label?: string }) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button type="button" variant="outline" disabled={disabled} className="gap-2 bg-white"><MoreHorizontal aria-hidden="true" className="h-4 w-4" />{label}</Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content align="end" sideOffset={8} collisionPadding={12} className="z-50 w-64 max-w-[calc(100vw-2rem)] rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg">
          {actions.map((action) => (
            <DropdownMenu.Item key={action.label} disabled={action.disabled} onSelect={action.onSelect}
              className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2.5 text-sm text-slate-700 outline-none focus:bg-slate-100 focus:text-slate-900 data-[disabled]:pointer-events-none data-[disabled]:opacity-40">
              {action.icon}{action.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

export function ReportStatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = { draft: "Rascunho", generating: "Em geração", in_review: "Em revisão", finalized: "Aprovado", sent: "Enviado" };
  const tone = status === "finalized" || status === "sent" ? "border-emerald-200 bg-emerald-50 text-emerald-800"
    : status === "generating" ? "border-amber-200 bg-amber-50 text-amber-900" : "border-slate-200 bg-slate-100 text-slate-600";
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${tone}`}>{labels[status] || status}</span>;
}
