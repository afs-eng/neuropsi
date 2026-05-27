import { AlertTriangle, ClipboardList, FileBarChart2 } from "lucide-react"

import { TestReportPayload, getPrimaryTechnicalSummary } from "@/lib/test-report"

function renderValue(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "-"
  return String(value)
}

export function TestReportSummaryCard({
  reportPayload,
  fallbackText,
  className = "",
}: {
  reportPayload?: TestReportPayload | null
  fallbackText?: string | null
  className?: string
}) {
  const summary = getPrimaryTechnicalSummary(reportPayload, fallbackText)
  const results = (reportPayload?.results || []).filter((item) => item?.scale).slice(0, 4)
  const flags = (reportPayload?.clinical_flags || []).filter(Boolean)
  const notes = (reportPayload?.technical_notes || []).filter(Boolean).slice(0, 3)

  if (!summary && results.length === 0 && flags.length === 0 && notes.length === 0) {
    return null
  }

  return (
    <section className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm report-print-break-avoid ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-400">
            <FileBarChart2 className="h-4 w-4 text-primary" />
            Resumo Técnico Estruturado
          </div>
          {summary ? <p className="mt-3 text-sm leading-6 text-slate-700">{summary}</p> : null}
        </div>
      </div>

      {results.length > 0 ? (
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {results.map((item, index) => (
            <div key={`${item.scale}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-xs font-bold uppercase tracking-wide text-slate-500">{item.scale}</div>
              <div className="mt-2 text-lg font-semibold text-slate-900">{renderValue(item.raw_score)}</div>
              <div className="mt-2 text-xs text-slate-500">Percentil: {renderValue(item.percentile)}</div>
              <div className="mt-1 text-xs font-medium text-slate-700">{renderValue(item.classification)}</div>
            </div>
          ))}
        </div>
      ) : null}

      {flags.length > 0 ? (
        <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-amber-700">
            <AlertTriangle className="h-4 w-4" />
            Alertas Clínicos
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {flags.map((flag) => (
              <span key={flag} className="rounded-full border border-amber-200 bg-white px-3 py-1 text-xs font-medium text-amber-800">
                {flag}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {notes.length > 0 ? (
        <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-slate-500">
            <ClipboardList className="h-4 w-4" />
            Notas Técnicas
          </div>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {notes.map((note, index) => (
              <li key={`${note}-${index}`}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}
