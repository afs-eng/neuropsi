"use client";

import { FileText } from "lucide-react";

type Section = { id: number; title: string };

export function ReportEditorNavigation({ sections, activeSectionId, onSelect }: {
  sections: Section[]; activeSectionId: number | null; onSelect: (id: number) => void;
}) {
  return (
    <aside className="min-w-0 lg:sticky lg:top-24 lg:self-start">
      <div className="rounded-xl border border-slate-200 bg-white p-4 lg:p-3">
        <div className="mb-3 flex items-center justify-between px-1">
          <h2 className="text-sm font-semibold text-slate-900">Capítulos do laudo</h2>
          <span className="text-xs tabular-nums text-slate-500">{sections.length}</span>
        </div>
        <div className="lg:hidden">
          <label htmlFor="report-chapter" className="sr-only">Capítulo em edição</label>
          <select id="report-chapter" name="chapter" value={activeSectionId ?? ""} onChange={(event) => onSelect(Number(event.target.value))}
            className="min-h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <option value="" disabled>Selecione um capítulo</option>
            {sections.map((section) => <option key={section.id} value={section.id}>{section.title}</option>)}
          </select>
        </div>
        <nav aria-label="Capítulos do laudo" className="hidden max-h-[calc(100vh-15rem)] space-y-1 overflow-y-auto lg:block">
          {sections.map((section, index) => (
            <button key={section.id} type="button" onClick={() => onSelect(section.id)} aria-current={activeSectionId === section.id ? "true" : undefined}
              className={`flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${activeSectionId === section.id ? "bg-primary/10 font-medium text-primary" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"}`}>
              <span aria-hidden="true" className={`mt-0.5 min-w-5 text-xs tabular-nums ${activeSectionId === section.id ? "text-primary" : "text-slate-400"}`}>{String(index + 1).padStart(2, "0")}</span>
              <span className="min-w-0 break-words">{section.title}</span>
            </button>
          ))}
        </nav>
        {sections.length === 0 && <p className="flex gap-2 px-1 py-3 text-sm text-slate-500"><FileText aria-hidden="true" className="h-4 w-4 shrink-0" />Nenhum capítulo disponível.</p>}
        <p className="mt-4 hidden border-t border-slate-100 px-1 pt-3 text-xs leading-5 text-slate-500 lg:block">Selecione um capítulo para revisar. As alterações são salvas pelo botão “Salvar seção”.</p>
      </div>
    </aside>
  );
}
