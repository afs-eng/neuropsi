export interface TestReportResultItem {
  scale?: string
  raw_score?: string | number | null
  percentile?: string | number | null
  classification?: string | null
}

export interface TestReportPayload {
  test_code?: string
  test_name?: string
  domain?: string
  application_id?: number
  status?: string
  applied_on?: string | null
  raw_payload?: Record<string, unknown>
  computed_payload?: Record<string, unknown>
  classified_payload?: Record<string, unknown>
  interpretation?: string
  summary_for_report?: string
  results?: TestReportResultItem[]
  clinical_flags?: string[]
  chart_payload?: Record<string, unknown>
  technical_notes?: string[]
}

export function getTestWorkflowMeta(status?: string | null) {
  const key = String(status || "draft").toLowerCase()
  const mapping: Record<string, { label: string; className: string }> = {
    draft: { label: "Rascunho", className: "bg-slate-100 text-slate-700 border-slate-200" },
    completed: { label: "Aplicação concluída", className: "bg-blue-50 text-blue-700 border-blue-200" },
    scored: { label: "Corrigido", className: "bg-violet-50 text-violet-700 border-violet-200" },
    interpreted: { label: "Interpretado", className: "bg-amber-50 text-amber-700 border-amber-200" },
    reviewed: { label: "Revisado", className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    locked: { label: "Travado", className: "bg-rose-50 text-rose-700 border-rose-200" },
  }
  return mapping[key] || { label: status || "Status", className: "bg-slate-100 text-slate-700 border-slate-200" }
}

export function getPrimaryTechnicalSummary(payload?: TestReportPayload | null, fallback?: string | null) {
  return payload?.summary_for_report?.trim() || payload?.interpretation?.trim() || fallback?.trim() || ""
}
