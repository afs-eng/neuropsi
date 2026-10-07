import type { THCPFormScores } from '@/types/tests/thcp'

export type THCPGroup = 'hpm_i' | 'hpm_ii' | 'linguagem' | 'pq' | 'memoria'
export interface THCPItemDefinition {
  key: string
  label: string
  max_score: number
  options: number[]
  score_options: number[] | null
}
export type THCPProtocol = Record<THCPGroup, THCPItemDefinition[]>
export type THCPItemResponses = Partial<Record<THCPGroup, Record<string, { answer: number | null; score: number }>>>
export type THCPItemForm = Partial<Record<THCPGroup, Record<string, { answer: string; score: string }>>>

export function restoreTHCPItems(responses: THCPItemResponses): THCPItemForm {
  return Object.fromEntries(Object.entries(responses).map(([group, entries]) => [group,
    Object.fromEntries(Object.entries(entries).map(([key, response]) => [key, { answer: response.answer == null ? '' : String(response.answer), score: String(response.score) }])),
  ]))
}

export function validTHCPItem(item: THCPItemDefinition, response?: { answer: string; score: string }): boolean {
  if (!response || response.score === '') return false
  const score = Number(response.score)
  if (!Number.isInteger(score) || score < 0 || score > item.max_score) return false
  return true
}

export function thcpGroupTotal(protocol: THCPProtocol, items: THCPItemForm, group: THCPGroup): number | null {
  if (!protocol[group].every(item => validTHCPItem(item, items[group]?.[item.key]))) return null
  return protocol[group].reduce((sum, item) => sum + Number(items[group]![item.key].score), 0)
}

export function thcpItemScores(protocol: THCPProtocol, items: THCPItemForm, scores: THCPFormScores): THCPFormScores {
  const hpmI = thcpGroupTotal(protocol, items, 'hpm_i')
  const hpmII = thcpGroupTotal(protocol, items, 'hpm_ii')
  return {
    ...scores,
    hpm: hpmI !== null && hpmII !== null ? String(hpmI + hpmII) : '',
    ...Object.fromEntries((['linguagem', 'pq', 'memoria'] as const).map(group => {
      const total = thcpGroupTotal(protocol, items, group)
      return [group, total === null ? '' : String(total)]
    })),
  }
}

export function serializeTHCPItems(protocol: THCPProtocol, items: THCPItemForm): THCPItemResponses {
  return Object.fromEntries(Object.entries(protocol).map(([group, definitions]) => [group,
    Object.fromEntries(definitions.map(item => {
      const response = items[group as THCPGroup]![item.key]
      return [item.key, { answer: item.options.length && response.answer !== '' ? Number(response.answer) : null, score: Number(response.score) }]
    })),
  ]))
}
