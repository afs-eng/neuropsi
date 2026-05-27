'use client'

import { useEffect, useMemo, useState } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import Link from 'next/link'

import { api } from '@/lib/api'
import { printCurrentPage } from '@/lib/print'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'
import { TestReportPayload } from '@/lib/test-report'

import { WASI_COMPOSITE_LABELS, WASI_SUBTESTS, formatPtBrNumber, getCompositeBadgeColor } from '../../data'

type ApplicationData = {
  id: number
  evaluation_id: number
  patient_name: string
  applied_on?: string
  report_payload?: TestReportPayload
  computed_payload?: any
  classified_payload?: any
  interpretation_text?: string
}

type CompositeResult = {
  sum_t_scores?: number
  qi?: number
  percentile?: number | null
  percentile_display?: string
  confidence_interval?: string
  classification?: string
  interpretability?: {
    ok?: boolean
    warning?: string
  }
}

type SubtestResult = {
  name: string
  raw_score: number
  t_score: number
  z_score: number
  weighted_score: number
  percentile: number
  classification: string
  age_band: string
}

type IpsativeResult = {
  name: string
  weighted_score: number
  difference_from_mean: number
  trend: string
}

export default function WASIResultPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const [result, setResult] = useState<ApplicationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const evaluationId = searchParams.get('evaluation_id')

  useEffect(() => {
    async function fetchResult() {
      try {
        const data = await api.get<ApplicationData>(`/api/tests/applications/${params.id}`)
        setResult(data)
      } catch (err: any) {
        setError(err?.message || 'Erro ao carregar resultado')
      } finally {
        setLoading(false)
      }
    }

    if (params.id) {
      fetchResult()
    }
  }, [params.id])

  const subtestOrder = useMemo(() => WASI_SUBTESTS.map((subtest: (typeof WASI_SUBTESTS)[number]) => subtest.key), [])

  if (loading) {
    return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-zinc-600">Carregando...</div></div>
  }

  if (error || !result) {
    return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-red-600">{error || 'Resultado não encontrado'}</div></div>
  }

  const computed = result.computed_payload || {}
  const composites = (computed.composites || {}) as Record<string, CompositeResult>
  const subtests = (computed.subtests || {}) as Record<string, SubtestResult>
  const ipsative = (computed.ipsative || {}) as { subtests?: Record<string, IpsativeResult> }

  return (
    <div className="min-h-screen bg-slate-300 p-6 md:p-10 report-print-shell">
      <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7 report-print-card">
        <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6 report-print-content">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between print:hidden report-print-hide">
            <div className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium tracking-tight text-zinc-800 shadow-sm">NeuroAvalia</div>
            <div className="flex gap-3 print:hidden report-print-hide">
              <Link href={`/dashboard/tests/wasi?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">Editar</Link>
              <button onClick={printCurrentPage} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">Imprimir / PDF</button>
              <Link href={`/dashboard/evaluations/${evaluationId || result.evaluation_id}?tab=overview`} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">Voltar</Link>
            </div>
          </header>

          <div className="mb-6">
            <h1 className="text-3xl font-medium tracking-tight text-zinc-900">WASI - Resultado</h1>
            <p className="mt-1 text-sm text-zinc-600">{result.patient_name}</p>
            {result.applied_on ? <p className="mt-1 text-xs text-zinc-500">Avaliado em: {new Date(result.applied_on).toLocaleDateString('pt-BR')}</p> : null}
          </div>

          <TestReportSummaryCard reportPayload={result.report_payload as any} fallbackText={result.interpretation_text} className="mb-6" />

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
            <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Índices Compostos</h3></div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Escala</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Soma T</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">QI</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Percentil</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">IC</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Classificação</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Interpretável</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {Object.entries(WASI_COMPOSITE_LABELS).map(([key, label]: [string, string]) => {
                    const item = composites[key]
                    if (!item) return null
                    return (
                      <tr key={key} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-sm font-medium text-slate-900">{label}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{formatPtBrNumber(item.sum_t_scores, 0)}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{formatPtBrNumber(item.qi, 0)}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{item.percentile_display || '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{item.confidence_interval || '—'}</td>
                        <td className="px-5 py-3 text-sm text-center">
                          <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium ${getCompositeBadgeColor(item.classification)}`}>{item.classification || '—'}</span>
                        </td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{item.interpretability?.ok ? 'Sim' : 'Atenção'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
            <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Subtestes</h3></div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Subteste</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Bruto</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">T</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Z</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Ponderado</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Percentil</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Classificação</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Faixa Etária</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {subtestOrder.map((key: string) => {
                    const item = subtests[key]
                    if (!item) return null
                    return (
                      <tr key={key} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-sm font-medium text-slate-900">{item.name}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{formatPtBrNumber(item.raw_score, 0)}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{formatPtBrNumber(item.t_score, 0)}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{formatPtBrNumber(item.z_score, 3)}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{formatPtBrNumber(item.weighted_score, 0)}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{formatPtBrNumber(item.percentile, 1)}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{item.classification}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{item.age_band || '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
            <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Análise Ipsativa</h3></div>
            <div className="p-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              {subtestOrder.map((key: string) => {
                const item = ipsative.subtests?.[key]
                if (!item) return null
                return (
                  <div key={key} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-medium text-slate-900">{item.name}</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">{formatPtBrNumber(item.weighted_score, 0)}</p>
                    <p className="mt-1 text-xs text-slate-500">Dif. da média: {formatPtBrNumber(item.difference_from_mean, 2)}</p>
                    <p className="mt-1 text-xs text-slate-600">{item.trend}</p>
                  </div>
                )
              })}
            </div>
          </div>

          {Object.values(composites).some((item: any) => item?.interpretability?.warning) && (
            <div className="bg-amber-50 rounded-xl border border-amber-200 p-5 mb-6">
              <h3 className="font-semibold text-amber-900 mb-3">Alertas de Interpretabilidade</h3>
              <ul className="space-y-2 text-sm text-amber-800">
                {Object.entries(composites).map(([key, item]: [string, CompositeResult]) => item?.interpretability?.warning ? <li key={key}>{item.interpretability.warning}</li> : null)}
              </ul>
            </div>
          )}

          {result.interpretation_text && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-900 mb-3">Interpretação</h3>
              <div className="text-sm text-slate-700 whitespace-pre-line">{result.interpretation_text}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
