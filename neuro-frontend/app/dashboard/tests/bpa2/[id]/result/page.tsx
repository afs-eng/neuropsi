'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'
import { getToken, resolveApiUrl } from '@/lib/api'

export default function BPA2ResultPage() {
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
      alert(error?.message || 'Não foi possível gerar o PDF do BPA-2.')
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

  const classified = result.classified_payload || {}
  const subtestes = classified.subtestes || []

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
              <h1 className="text-3xl font-medium tracking-tight text-zinc-900">BPA-2 - Resultado</h1>
              <p className="mt-1 text-sm text-zinc-600">
                {result.patient_name} • Aplicado em {result.applied_on}
              </p>
            </div>
            <div className="flex gap-3 print:hidden report-print-hide">
              <Link href={`/dashboard/tests/bpa2?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                Editar
              </Link>
              <button onClick={handleExportPdf} disabled={exportingPdf} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm disabled:cursor-not-allowed disabled:opacity-60">
                {exportingPdf ? 'Gerando PDF...' : 'Imprimir / PDF'}
              </button>
              <Link href={`/dashboard/evaluations/${result.evaluation_id}?tab=overview`} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">
                Voltar
              </Link>
            </div>
          </div>

          <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text} className="mb-6" />

          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-[28px] bg-blue-500 p-5 text-white shadow-lg">
              <div className="text-sm text-blue-100">Atenção Concentrada</div>
              <div className="mt-2 text-4xl font-light">
                {subtestes.find((s: any) => s.codigo === 'ac')?.classificacao || '—'}
              </div>
              <div className="mt-2 text-sm text-blue-100">
                Pctl {subtestes.find((s: any) => s.codigo === 'ac')?.percentil || '—'}
              </div>
            </div>
            <div className="rounded-[28px] bg-purple-500 p-5 text-white shadow-lg">
              <div className="text-sm text-purple-100">Atenção Dividida</div>
              <div className="mt-2 text-4xl font-light">
                {subtestes.find((s: any) => s.codigo === 'ad')?.classificacao || '—'}
              </div>
              <div className="mt-2 text-sm text-purple-100">
                Pctl {subtestes.find((s: any) => s.codigo === 'ad')?.percentil || '—'}
              </div>
            </div>
            <div className="rounded-[28px] bg-teal-500 p-5 text-white shadow-lg">
              <div className="text-sm text-teal-100">Atenção Alternada</div>
              <div className="mt-2 text-4xl font-light">
                {subtestes.find((s: any) => s.codigo === 'aa')?.classificacao || '—'}
              </div>
              <div className="mt-2 text-sm text-teal-100">
                Pctl {subtestes.find((s: any) => s.codigo === 'aa')?.percentil || '—'}
              </div>
            </div>
          </div>

          <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5">
            <h3 className="mb-4 text-lg font-semibold text-zinc-900">Subtestes Detalhados</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dashed border-black/10">
                    <th className="pb-3 text-left text-xs font-semibold text-zinc-500 uppercase">Subteste</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Brutos</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Erros</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Omissões</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Total</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Percentil</th>
                    <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Classificação</th>
                  </tr>
                </thead>
                <tbody>
                  {subtestes.map((st: any) => (
                    <tr key={st.codigo} className="border-b border-dashed border-black/5">
                      <td className="py-3 text-zinc-900">{st.subteste}</td>
                      <td className="py-3 text-center text-zinc-700">{st.brutos}</td>
                      <td className="py-3 text-center text-zinc-700">{st.erros}</td>
                      <td className="py-3 text-center text-zinc-700">{st.omissoes}</td>
                      <td className="py-3 text-center font-medium text-zinc-900">{st.total}</td>
                      <td className="py-3 text-center text-zinc-700">{st.percentil}</td>
                      <td className="py-3 text-center">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                          st.classificacao?.includes('Muito Superior') ? 'bg-green-600 text-white' :
                          st.classificacao?.includes('Superior') ? 'bg-green-400 text-green-900' :
                          st.classificacao?.includes('Médio') ? 'bg-green-100 text-green-700' :
                          st.classificacao?.includes('Inferior') ? 'bg-orange-100 text-orange-700' :
                          st.classificacao?.includes('Muito Inferior') ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {st.classificacao || '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {result.interpretation_text && (
            <div className="mt-6 rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5">
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Interpretação</h3>
              <div className="whitespace-pre-wrap text-sm text-zinc-700">
                {result.interpretation_text}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
