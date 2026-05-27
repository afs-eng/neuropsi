import { api } from '@/lib/api'
import type { Report } from '@/types/shared'

export const reportService = {
  list: (evaluationId?: number) =>
    api.get<Report[]>(evaluationId ? `/api/reports?evaluation_id=${evaluationId}` : '/api/reports'),

  getByEvaluation: (evaluationId: number | string) =>
    api.get<Report[]>(`/api/reports/by-evaluation/${evaluationId}`),

  get: (reportId: number | string) =>
    api.get<Report>(`/api/reports/${reportId}`),

  create: (data: Record<string, unknown>) =>
    api.post<Report>('/api/reports/', data),

  generateFromEvaluation: (evaluationId: number | string, mode: 'full' | 'tests_only' = 'full') =>
    api.post<Report>(`/api/reports/generate-from-evaluation/${evaluationId}?mode=${mode}`, {}),

  regenerateReport: (reportId: number | string) =>
    api.post<Record<string, unknown>>(`/api/reports/${reportId}/regenerate`, {}),

  regenerateTests: (reportId: number | string) =>
    api.post<Record<string, unknown>>(`/api/reports/${reportId}/regenerate-tests`, {}),

  build: (reportId: number | string) =>
    api.post<Record<string, unknown>>(`/api/reports/${reportId}/build`, {}),

  regenerateSection: (reportId: number | string, sectionKey: string) =>
    api.post<Record<string, unknown>>(`/api/reports/${reportId}/regenerate-section/${sectionKey}`, {}),

  saveSection: (sectionId: number | string, editedText: string) =>
    api.patch<Record<string, unknown>>(`/api/reports/sections/${sectionId}`, { edited_text: editedText }),

  finalize: (reportId: number | string) =>
    api.post<Record<string, unknown>>(`/api/reports/${reportId}/finalize`, {}),

  exportHtml: (reportId: number | string) =>
    api.post<{ html: string }>(`/api/reports/${reportId}/export-html`, {}),
}
