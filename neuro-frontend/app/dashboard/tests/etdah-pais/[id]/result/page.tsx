'use client'

import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { printCurrentPage } from '@/lib/print'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'

const FACTOR_NAMES: Record<string, string> = {
  fator_1: "Fator 1 - Regulação Emocional (RE)",
  fator_2: "Fator 2 - Hiperatividade / Impulsividade (HI)",
  fator_3: "Fator 3 - Comportamento Adaptativo (CA)",
  fator_4: "Fator 4 - Atenção (A)",
  escore_geral: "Escore Geral",
}

const CLINICAL_BADGE_STYLES: Record<string, string> = {
  Superior: 'bg-red-100 text-red-700 border-red-200',
  'Média Superior': 'bg-amber-100 text-amber-700 border-amber-200',
  Média: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'Média Inferior': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  Inferior: 'bg-emerald-100 text-emerald-700 border-emerald-200',
}

function getClinicalBadgeStyle(classification: string) {
  return CLINICAL_BADGE_STYLES[classification] || 'bg-slate-100 text-slate-700 border-slate-200'
}

function formatAppliedOn(value: string) {
  if (!value) return '—'
  const date = new Date(value)
  if (isNaN(date.getTime())) return value
  return date.toLocaleDateString('pt-BR')
}

export default function ETDAHPAISResultPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const { api } = await import('@/lib/api')
        const data = await api.get<any>(`/api/tests/etdah-pais/result/${params.id}`)
        setResult(data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    if (params.id) {
      fetchResult()
    }
  }, [params.id])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center">
        <div className="text-zinc-600">Carregando...</div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center">
        <div className="text-zinc-600">Resultado não encontrado</div>
      </div>
    )
  }

  const raw = result.raw_payload || {}
  const classified = result.classified_payload || {}

  const rawScores = result.raw_scores || {}
  const results = result.results || {}

  const itemKeys = Object.keys(raw).filter(k => k.startsWith('item_'))
  const items: { number: number, value: any }[] = []
  
  if (raw.responses) {
    Object.keys(raw.responses).forEach(key => {
      items.push({ number: parseInt(key), value: raw.responses[key] })
    })
  } else {
    itemKeys.forEach(key => {
      items.push({ number: parseInt(key.replace('item_', '')), value: raw[key] })
    })
  }
  items.sort((a, b) => a.number - b.number)

  const responseRows = []
  for (let i = 0; i < 12; i++) {
    responseRows.push([i + 1, i + 13, i + 25, i + 37, i + 49].filter((item) => item <= 58))
  }

  const factorOrder = ["fator_1", "fator_2", "fator_3", "fator_4", "escore_geral"]
  const interpretationText = result.interpretation || ''
  const interpretationParagraphs = interpretationText
    .split(/\n\s*\n/)
    .map((paragraph: string) => paragraph.trim())
    .filter(Boolean)

  const evaluationId = searchParams.get("evaluation_id")

  return (
    <div className="min-h-screen bg-slate-300 p-6 md:p-10 report-print-shell">
      <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7 report-print-card">
        <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6 report-print-content">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between print:hidden report-print-hide">
            <div className="flex items-center gap-4">
              <div className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium tracking-tight text-zinc-800 shadow-sm">
                Florescer
              </div>
            </div>
            <nav className="flex flex-wrap items-center gap-2 rounded-full bg-white/70 px-3 py-2 text-sm text-zinc-700 shadow-sm">
              <Link href="/dashboard" className="rounded-full px-4 py-2 hover:bg-black/5">Dashboard</Link>
              <Link href="/dashboard?tab=tests" className="rounded-full px-4 py-2 hover:bg-black/5">Testes</Link>
            </nav>
          </header>

          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-medium tracking-tight text-zinc-900">ETDAH-PAIS - Resultado</h1>
              <p className="mt-1 text-sm text-zinc-600">
                {result.patient_name} • Aplicado em {formatAppliedOn(result.applied_on)}
              </p>
            </div>
            <div className="flex gap-3 print:hidden report-print-hide">
              <Link href={`/dashboard/tests/etdah-pais?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                Editar
              </Link>
              <button onClick={printCurrentPage} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm">
                Imprimir / PDF
              </button>
              <Link href={`/dashboard/evaluations/${result.evaluation_id}?tab=overview`} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">
                Voltar
              </Link>
            </div>
          </div>

          <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5 mb-6">
            <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation || ''} className="mb-4" />
            <h3 className="mb-4 text-lg font-semibold text-zinc-900">Escores por Fator</h3>
            <div className="mb-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
              {factorOrder.map((factor) => {
                const r = results[factor] || {}
                const classification = r.classification || '—'
                return (
                    <div key={factor} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                      <div className="text-sm font-semibold text-slate-900">{FACTOR_NAMES[factor]}</div>
                      <div className="mt-3 text-3xl font-bold text-slate-900">{r.raw_score ?? rawScores[factor] ?? '—'}</div>
                    <div className="mt-2 text-sm text-slate-500">Percentil Guilmette: {typeof r.percentile_guilmette === 'number' ? r.percentile_guilmette.toFixed(1) : '—'}</div>
                    <div className="mt-3">
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium ${getClinicalBadgeStyle(classification)}`}>
                        {classification}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dashed border-black/10">
                    <th className="pb-3 text-left text-xs font-semibold text-zinc-500 uppercase">Fator</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Pontos Brutos</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Média</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Percentil Guilmette</th>
                    <th className="pb-3 text-left text-xs font-semibold text-zinc-500 uppercase">Classificação Clínica</th>
                  </tr>
                </thead>
                <tbody>
                  {factorOrder.map((factor) => {
                    const r = results[factor] || {}
                    return (
                      <tr key={factor} className="border-b border-dashed border-black/5">
                        <td className="py-3 text-zinc-900 font-medium">{FACTOR_NAMES[factor]}</td>
                        <td className="py-3 text-center font-medium text-zinc-900">{r.raw_score ?? rawScores[factor] ?? '—'}</td>
                        <td className="py-3 text-center text-zinc-600">{r.mean ?? '—'}</td>
                        <td className="py-3 text-center text-zinc-600">{typeof r.percentile_guilmette === 'number' ? r.percentile_guilmette.toFixed(1) : '—'}</td>
                        <td className="py-3 text-zinc-600">{r.classification ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5 mb-6">
            <h3 className="mb-4 text-lg font-semibold text-zinc-900">REGISTRO DE RESPOSTAS</h3>
            <p className="text-sm text-slate-600 mb-4">Escala: 1 = Nunca | 2-3 = Raramente | 4 = Às vezes | 5 = Frequentemente | 6 = Sempre</p>
            <p className="text-sm text-slate-600 mb-4">* Itens invertidos (Fator 3 completo + item 1 do Fator 4)</p>
            <div className="border rounded-xl overflow-hidden bg-white">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-100">
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                    <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                  </tr>
                </thead>
                <tbody>
                  {responseRows.map((row, idx) => (
                    <tr key={idx} className={`border-t ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}>
                      {row.map((itemNumber) => {
                        const item = items.find((entry) => entry.number === itemNumber)
                        const value = item?.value
                        const isReversed = (itemNumber >= 33 && itemNumber <= 46) || itemNumber === 47
                        const style =
                          value === 6 ? 'bg-red-100 text-red-800 font-bold' :
                          value >= 4 ? 'bg-amber-100 text-amber-800 font-bold' :
                          value >= 2 ? 'bg-blue-100 text-blue-800 font-bold' :
                          value === 1 ? 'bg-slate-200 text-slate-700 font-bold' :
                          'bg-slate-100 text-slate-400'

                        return (
                          <>
                            <td className="py-1 px-2 text-center text-slate-700 font-medium">
                              {String(itemNumber).padStart(2, '0')}
                              {isReversed && <span className="text-red-500 ml-1">*</span>}
                            </td>
                            <td className="py-1 px-2 text-center">
                              <span className={`inline-block w-8 h-6 leading-6 rounded ${style}`}>
                                {value ?? '-'}
                              </span>
                            </td>
                          </>
                        )
                      })}
                      {Array.from({ length: 5 - row.length }).map((_, emptyIdx) => (
                        <>
                          <td key={`empty-item-${idx}-${emptyIdx}`} className="py-1 px-2" />
                          <td key={`empty-resp-${idx}-${emptyIdx}`} className="py-1 px-2" />
                        </>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {results && Object.keys(results).length > 0 && (
            <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900">Interpretação Clínica</h3>
                  <p className="text-sm text-zinc-600">Interpretação técnica do ETDAH-PAIS por fator, escore geral e análise integrada.</p>
                </div>
                <div className="rounded-2xl bg-slate-100 px-4 py-2 text-xs font-medium text-slate-600">
                  {interpretationParagraphs.length} blocos clínicos
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
                <p className="text-sm text-amber-800">
                  <strong>Sexo:</strong> {raw.sex === 'M' ? 'Masculino' : 'Feminino'}
                </p>
                <p className="text-sm text-amber-800">
                  <strong>Faixa etária:</strong> {(() => {
                    const age = result.computed_payload?.age || result.classified_payload?.age
                    if (age >= 2 && age <= 5) return '2 a 5 anos'
                    if (age >= 6 && age <= 9) return '6 a 9 anos'
                    if (age >= 10 && age <= 13) return '10 a 13 anos'
                    if (age >= 14 && age <= 17) return '14 a 17 anos'
                    return 'Não informada'
                  })()}
                </p>
              </div>

              <div className="space-y-4">
                {interpretationParagraphs.map((paragraph: string, index: number) => (
                  <div key={index} className="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-sm leading-6 text-zinc-700 shadow-sm whitespace-pre-wrap">
                    {paragraph}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
