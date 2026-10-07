import type { TestReportPayload } from '@/lib/test-report'
import type { THCPItemResponses } from '@/lib/thcp-protocol'

export const THCP_FIELDS = [
  { key: 'hpm', label: 'Habilidades Percepto-Motoras', max: 30, hint: 'Total dos exercícios I (até 22) e II (até 8).' },
  { key: 'linguagem', label: 'Linguagem', max: 12, hint: 'Soma dos pontos de linguagem.' },
  { key: 'pq', label: 'Pensamento Quantitativo', max: 11, hint: 'Soma dos pontos de pensamento quantitativo.' },
  { key: 'memoria', label: 'Memória', max: 10, hint: 'Soma dos pontos de memória.' },
  { key: 'atencao_acertos', label: 'Atenção — acertos', max: 28, hint: 'Número de acertos na tarefa de atenção.' },
  { key: 'atencao_erros', label: 'Atenção — erros', max: 62, hint: 'O sistema calcula acertos − erros, com mínimo zero.' },
] as const

export type THCPField = typeof THCP_FIELDS[number]['key']
export type THCPFormScores = Record<THCPField, string>
export type THCPNorm = 'idade' | 'geral'

export interface THCPResultRow {
  code: string
  label: string
  raw_score: number
  max_score: number
  t_score: number | string
  z_score: number | null
  weighted_score: number | null
  percentile: number | null
  manual_percentile_band: string | null
  manual_classification: string | null
  classification: string | null
}

export interface THCPApplication {
  id: number
  application_id: number
  evaluation_id: number
  patient_name: string
  instrument_code: string
  applied_on: string | null
  is_validated: boolean
  status: string
  raw_payload: Partial<Record<THCPField, number>> & { norm_type?: THCPNorm; item_responses?: THCPItemResponses | null }
  computed_payload: { age: number; norm_label: string }
  classified_payload: { results?: THCPResultRow[]; summary?: THCPResultRow; warnings?: string[] }
  interpretation_text: string
  report_payload: TestReportPayload
}

export function thcpErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'message' in error) return String(error.message)
  return 'Não foi possível concluir a operação. Tente novamente.'
}

export function formatThcpScore(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return typeof value === 'number' ? value.toLocaleString('pt-BR', { maximumFractionDigits: 2 }) : value
}
