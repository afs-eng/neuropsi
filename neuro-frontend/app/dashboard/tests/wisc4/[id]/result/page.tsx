'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getToken, resolveApiUrl } from '@/lib/api'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'

export default function WISC4ResultPage() {
  const subtestOrder = ['CB', 'SM', 'DG', 'CN', 'CD', 'VC', 'SNL', 'RM', 'CO', 'PS']
  const params = useParams()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [exportingPdf, setExportingPdf] = useState(false)

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const { api } = await import('@/lib/api')
        const data = await api.get<any>(`/api/tests/applications/${params.id}`)
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

  const handleExportPdf = async () => {
    if (!params.id || exportingPdf) return
    setExportingPdf(true)
    try {
      const token = getToken() || ''
      const response = await fetch(resolveApiUrl(`/api/tests/applications/${params.id}/export-pdf`), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        cache: 'no-store',
      })

      if (!response.ok) {
        let message = `Falha ao gerar PDF (${response.status})`
        try {
          const payload = await response.json()
          if (payload?.message) message = `${message}: ${payload.message}`
        } catch {}
        throw new Error(message)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (error: any) {
      console.error(error)
      alert(error?.message || 'Não foi possível gerar o PDF do WISC-IV.')
    } finally {
      setExportingPdf(false)
    }
  }

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

  const rawPayload = result.raw_payload || {}
  const computed = result.computed_payload || {}
  const classified = result.classified_payload || {}
  const indices = classified.indices || []
  const subtestes = [...(classified.subtestes || [])].sort((a: any, b: any) => {
    const aIndex = subtestOrder.indexOf(a.codigo)
    const bIndex = subtestOrder.indexOf(b.codigo)

    if (aIndex === -1 && bIndex === -1) return 0
    if (aIndex === -1) return 1
    if (bIndex === -1) return -1

    return aIndex - bIndex
  })

  const getClassificationColor = (classificacao: string) => {
    if (classificacao?.includes('Baixo') || classificacao?.includes('Muito')) {
      return 'bg-red-50 text-red-700'
    }
    if (classificacao?.includes('Médio')) {
      return 'bg-green-50 text-green-700'
    }
    return 'bg-blue-50 text-blue-700'
  }

  return (
    <div className="min-h-screen bg-slate-300 p-6 md:p-10 report-print-shell">
      <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7 report-print-card">
        <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6 report-print-content">
          {/* Header */}
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between print:hidden report-print-hide">
            <div className="flex items-center gap-4">
              <div className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium tracking-tight text-zinc-800 shadow-sm">
                NeuroAvalia
              </div>
            </div>
            <nav className="flex flex-wrap items-center gap-2 rounded-full bg-white/70 px-3 py-2 text-sm text-zinc-700 shadow-sm">
              <Link href="/dashboard" className="rounded-full px-4 py-2 hover:bg-black/5">Dashboard</Link>
              <Link href="/dashboard/evaluations" className="rounded-full px-4 py-2 hover:bg-black/5">Avaliações</Link>
              <Link href="/dashboard/tests" className="rounded-full px-4 py-2 hover:bg-black/5">Testes</Link>
            </nav>
          </header>

          {/* Title */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-medium tracking-tight text-zinc-900">WISC-IV - Resultado</h1>
              <p className="mt-1 text-sm text-zinc-600">
                {result.patient_name} • {computed.faixa || '—'}
              </p>
            </div>
            <div className="flex gap-3 print:hidden report-print-hide">
              <Link href={`/dashboard/tests/wisc4?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                Editar
              </Link>
              <button onClick={handleExportPdf} disabled={exportingPdf} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60">
                {exportingPdf ? 'Gerando PDF...' : 'Imprimir / PDF'}
              </button>
              <Link href={`/dashboard/evaluations/${result.evaluation_id}?tab=overview`} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">
                Voltar
              </Link>
            </div>
          </div>

          <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text} className="mb-6" />

          {/* Resumo dos Índices */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
            <div className="px-5 py-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-900">Resumo dos Índices</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Escala</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Soma dos PP</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Escore Composto</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Percentil</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">IC 95%</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {indices.map((idx: any) => (
                    <tr key={idx.indice} className="hover:bg-slate-50">
                      <td className="px-5 py-3 text-sm font-medium text-slate-900">{idx.nome}</td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700">{idx.soma_ponderados}</td>
                      <td className="px-5 py-3 text-sm text-center font-bold text-blue-600">
                        {idx.indice === 'icv' ? 'ICV' : idx.indice === 'iop' ? 'IOP' : idx.indice === 'imt' ? 'IMO' : idx.indice === 'ivp' ? 'IVP' : idx.nome} {idx.escore_composto}
                      </td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700">{idx.percentil?.toFixed(1) || '—'}</td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700">{idx.intervalo_confianca?.[0]}-{idx.intervalo_confianca?.[1] || '—'}</td>
                    </tr>
                  ))}
                  {classified.qit_data && (
                    <tr className="bg-blue-50/50">
                      <td className="px-5 py-3 text-sm font-bold text-slate-900">QI Total</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.qit_data.soma_ponderados}</td>
                      <td className="px-5 py-3 text-sm text-center font-bold text-blue-700">QIT {classified.qit_data.escore_composto}</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.qit_data.percentil?.toFixed(1) || '—'}</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.qit_data.intervalo_confianca?.[0]}-{classified.qit_data.intervalo_confianca?.[1] || '—'}</td>
                    </tr>
                  )}
                  {classified.gai_data && (
                    <tr className="bg-purple-50/50">
                      <td className="px-5 py-3 text-sm font-medium text-slate-900">Habilidades Gerais (GAI)</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.gai_data.soma_ponderados}</td>
                      <td className="px-5 py-3 text-sm text-center font-semibold text-purple-700">GAI {classified.gai_data.escore_composto}</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.gai_data.percentil?.toFixed(1) || '—'}</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.gai_data.intervalo_confianca?.[0]}-{classified.gai_data.intervalo_confianca?.[1] || '—'}</td>
                    </tr>
                  )}
                  {classified.cpi_data && (
                    <tr className="bg-teal-50/50">
                      <td className="px-5 py-3 text-sm font-medium text-slate-900">Proficiência Cognitiva (CPI)</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.cpi_data.soma_ponderados}</td>
                      <td className="px-5 py-3 text-sm text-center font-semibold text-teal-700">CPI {classified.cpi_data.escore_composto}</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.cpi_data.percentil?.toFixed(1) || '—'}</td>
                      <td className="px-5 py-3 text-sm text-center font-medium text-slate-700">{classified.cpi_data.intervalo_confianca?.[0]}-{classified.cpi_data.intervalo_confianca?.[1] || '—'}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Subtestes */}
          {subtestes.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
              <div className="px-5 py-4 border-b border-slate-200">
                <h3 className="font-semibold text-slate-900">Subtestes</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-slate-50">
                      <th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Subteste</th>
                      <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Código</th>
                      <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">EB</th>
                      <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">PP</th>
                      <th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Classificação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {subtestes.map((st: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-sm text-slate-700">{st.subteste}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-500">{st.codigo}</td>
                        <td className="px-5 py-3 text-sm text-center font-medium text-slate-900">{st.escore_bruto}</td>
                        <td className="px-5 py-3 text-sm text-center font-medium text-slate-900">{st.escore_padrao}</td>
                        <td className="px-5 py-3 text-sm text-center">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getClassificationColor(st.classificacao)}`}>
                            {st.classificacao || '—'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Pontos Fortes e Frágeis */}
          {(classified.pontos_fortes?.length > 0 || classified.pontos_fragilizados?.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {classified.pontos_fortes?.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                  <h3 className="font-semibold text-green-700 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                    Pontos Fortes
                  </h3>
                  <ul className="space-y-1">
                    {classified.pontos_fortes.map((p: string, idx: number) => (
                      <li key={idx} className="text-sm text-slate-700">{p}</li>
                    ))}
                  </ul>
                </div>
              )}
              {classified.pontos_fragilizados?.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                  <h3 className="font-semibold text-red-700 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>
                    Pontos Frágeis
                  </h3>
                  <ul className="space-y-1">
                    {classified.pontos_fragilizados.map((p: string, idx: number) => (
                      <li key={idx} className="text-sm text-slate-700">{p}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Diferenças Significativas */}
          {classified.diferencas_significativas?.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
              <h3 className="font-semibold text-amber-700 mb-3 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Diferenças Significativas
              </h3>
              <ul className="space-y-1">
                {classified.diferencas_significativas.map((d: string, idx: number) => (
                  <li key={idx} className="text-sm text-slate-700">{d}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Interpretação */}
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
