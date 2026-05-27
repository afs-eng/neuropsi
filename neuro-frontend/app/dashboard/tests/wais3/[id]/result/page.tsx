'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getToken, resolveApiUrl } from '@/lib/api'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'
import { TestReportPayload } from '@/lib/test-report'

interface IndexData {
  nome: string
  soma_ponderada?: number | null
  pontuacao_composta?: number | null
  percentil?: number | null
  classificacao?: string | null
  ic_90?: string | null
  ic_95?: string | null
}

interface SubtestData {
  nome: string
  pontos_brutos?: number | null
  escore_ponderado?: number | null
  classificacao?: string | null
  dominio?: string | null
}

interface ResultData {
  id: number
  evaluation_id: number
  patient_name: string
  applied_on?: string
  report_payload?: TestReportPayload
  classified_payload?: {
    indices?: Record<string, IndexData>
    subtestes_ordenados?: SubtestData[]
    subtestes?: Record<string, SubtestData>
    gai_data?: any
    clusters?: Record<string, any>
  }
  computed_payload?: {
    idade?: { anos: number; meses: number }
    idade_normativa?: string
    indices?: Record<string, IndexData>
    subtestes_ordenados?: SubtestData[]
    subtestes?: Record<string, SubtestData>
    supplementary_tables?: Record<string, any>
    psychometrics_tables?: Record<string, any>
    facilidades_dificuldades?: any[]
    discrepancias?: any[]
    render_ready_tables?: any
    digitos?: any
  }
  interpretation_text?: string
}

// Ordem clínica dos subtestes WAIS-III
const SUBTEST_ORDER = [
  "Completar Figuras",
  "Vocabulário",
  "Códigos",
  "Semelhanças",
  "Cubos",
  "Aritmética",
  "Raciocínio Matricial",
  "Dígitos",
  "Informação",
  "Arranjo de Figuras",
  "Compreensão",
  "Procurar Símbolos",
  "Sequência de Números e Letras",
  "Armar Objetos",
]

const DIGIT_PROCESS_ROWS = [
  { key: 'ordem_direta', label: 'Dígitos - Ordem Direta' },
  { key: 'ordem_inversa', label: 'Dígitos - Ordem Inversa' },
  { key: 'maior_sequencia_direta', label: 'Maior Sequência de Dígitos OD' },
  { key: 'maior_sequencia_inversa', label: 'Maior Sequência de Dígitos OI' },
  { key: 'diferenca_maior_sequencia', label: 'Diferença OD - OI' },
]

const STATUS_AFFECTED_COLUMNS = new Set([
  'Significância Estatística - Nível',
  'Significância Estatística - nível',
  'Frequência da Diferença da Amostra de Padronização',
  'Frequência da Diferença na Amostra de Padronização',
  'Facilidade (+)',
  'Dificuldade (-)',
])

function getStatusPlaceholder(status?: string) {
  if (status === 'below_threshold') return 'NS'
  if (status === 'missing_norm') return 'N/D'
  if (status === 'missing_score') return 'Aus.'
  return '—'
}

function buildStatusSummary(...groups: Record<string, any>[][]) {
  const summary = {
    significant: 0,
    below_threshold: 0,
    missing_norm: 0,
    missing_score: 0,
  }

  for (const rows of groups) {
    for (const row of rows || []) {
      const status = row?.status
      if (status && status in summary) {
        summary[status as keyof typeof summary] += 1
      }
    }
  }

  return summary
}

function RenderReadyTable({
  title,
  columns,
  rows,
}: {
  title: string
  columns: string[]
  rows: Record<string, any>[]
}) {
  if (!rows.length) return null

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
      <div className="px-5 py-4 border-b border-slate-200">
        <h3 className="font-semibold text-slate-900">{title}</h3>
        <p className="mt-1 text-xs text-slate-500">NS = não significativo. N/D = norma indisponível.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50">
              {columns.map((column) => (
                <th key={column} className="px-5 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wide first:min-w-[240px]">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((row, index) => (
              <tr key={index} className="hover:bg-slate-50">
                {columns.map((column) => {
                  const value = row[column]
                  const status = row.status as string | undefined
                  const reason = row.reason as string | undefined
                  const shouldUseStatusPlaceholder = value == null && STATUS_AFFECTED_COLUMNS.has(column) && status
                  const displayValue = shouldUseStatusPlaceholder ? getStatusPlaceholder(status) : (value ?? '—')

                  return (
                    <td
                      key={column}
                      title={reason || undefined}
                      className={`px-5 py-3 text-sm text-slate-700 ${column === columns[0] ? 'font-medium text-slate-900' : 'text-center'} ${shouldUseStatusPlaceholder ? 'text-slate-500' : ''}`}
                    >
                      {displayValue}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function cleanWAIS3InterpretationText(text?: string) {
  return (text || '')
    .replace(/^\s*Interpretação e Observações Clínicas\s*:?\s*/i, '')
    .replace(/\n\s*\n\s*Interpretação e Observações Clínicas\s*:?\s*/gi, '\n\n')
    .replace(/(?:^|(?<=[.!?])\s+)\S*\s*CPI\b[^.!?]*(?:[.!?]|$)/gi, ' ')
    .replace(/(?:^|(?<=[.!?])\s+)\S*\s*Índice de Produtividade Cognitiva[^.!?]*(?:[.!?]|$)/gi, ' ')
    .replace(/[ \t]+/g, ' ')
    .trim()
}

export default function WAIS3ResultPage() {
  const params = useParams()
  const [result, setResult] = useState<ResultData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exportingPdf, setExportingPdf] = useState(false)

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const { api } = await import('@/lib/api')
        const data = await api.get<ResultData>(`/api/tests/applications/${params.id}`)
        if (!data) {
          setError('Resultado não encontrado')
        } else {
          setResult(data)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao carregar resultado')
      } finally {
        setLoading(false)
      }
    }
    if (params.id) fetchResult()
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
    } catch (exportError: any) {
      console.error(exportError)
      alert(exportError?.message || 'Não foi possível gerar o PDF do WAIS-III.')
    } finally {
      setExportingPdf(false)
    }
  }

  if (loading) return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-zinc-600">Carregando...</div></div>
  if (error || !result) return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-red-600">{error || 'Resultado não encontrado'}</div></div>

  const classified = result.classified_payload || {}
  const computed = result.computed_payload || {}
  const renderReadyTables = computed.render_ready_tables || {}
  const statusSummary = buildStatusSummary(
    renderReadyTables.facilidades_dificuldades?.linhas || [],
    renderReadyTables.discrepancias?.linhas || [],
  )
  const interpretationText = cleanWAIS3InterpretationText(result.interpretation_text)
  const indices = classified.indices || computed.indices || {}
  const subtestes = (classified.subtestes_ordenados && classified.subtestes_ordenados.length > 0)
    ? classified.subtestes_ordenados
    : (computed.subtestes_ordenados && computed.subtestes_ordenados.length > 0)
      ? computed.subtestes_ordenados
      : classified.subtestes
        ? Object.values(classified.subtestes)
        : computed.subtestes
          ? Object.values(computed.subtestes)
          : []

  return (
    <div className="min-h-screen bg-slate-300 p-6 md:p-10 report-print-shell">
      <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7 report-print-card">
        <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6 report-print-content">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between print:hidden report-print-hide">
            <div className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium tracking-tight text-zinc-800 shadow-sm">NeuroAvalia</div>
            <div className="flex gap-3 print:hidden report-print-hide">
              <Link href={`/dashboard/tests/wais3?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">Editar</Link>
              <button onClick={handleExportPdf} disabled={exportingPdf} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60">{exportingPdf ? 'Gerando PDF...' : 'Imprimir / PDF'}</button>
              <Link href={`/dashboard/evaluations/${result.evaluation_id}?tab=overview`} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">Voltar</Link>
            </div>
          </header>

          <div className="mb-6">
            <h1 className="text-3xl font-medium tracking-tight text-zinc-900">WAIS-III - Resultado</h1>
            <p className="mt-1 text-sm text-zinc-600">{result.patient_name}</p>
            {result.applied_on && <p className="mt-1 text-xs text-zinc-500">Avaliado em: {new Date(result.applied_on).toLocaleDateString('pt-BR')}</p>}
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4 mb-6">
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Significativas</div>
              <div className="mt-1 text-2xl font-semibold text-emerald-900">{statusSummary.significant}</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-600">Abaixo do Corte</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{statusSummary.below_threshold}</div>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-amber-700">Sem Norma</div>
              <div className="mt-1 text-2xl font-semibold text-amber-900">{statusSummary.missing_norm}</div>
            </div>
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-wide text-rose-700">Escore Ausente</div>
              <div className="mt-1 text-2xl font-semibold text-rose-900">{statusSummary.missing_score}</div>
            </div>
          </div>
          <TestReportSummaryCard reportPayload={result.report_payload as any} fallbackText={interpretationText} className="mb-6" />

          {/* Índices Principais */}
          {Object.keys(indices).length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
              <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Índices Fatoriais e QI</h3></div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr className="bg-slate-50"><th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Índice</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Soma Ponderada</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Escore Composto</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Percentil</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Classificação</th></tr></thead>
                  <tbody className="divide-y divide-slate-200">
                    {Object.entries(indices).map(([key, item]) => (
                      <tr key={key} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-sm font-medium text-slate-900">{item.nome || key}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{item.soma_ponderada ?? '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{item.pontuacao_composta ?? '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{item.percentil ?? '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{item.classificacao ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Subtestes - ordem clínica do WAIS-III */}
          {Array.isArray(subtestes) && subtestes.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
              <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Subtestes</h3></div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr className="bg-slate-50"><th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Subteste</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Bruto</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Ponderado</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Classificação</th></tr></thead>
                  <tbody className="divide-y divide-slate-200">
                    {SUBTEST_ORDER.map((nome) => {
                      const item = subtestes.find((s: SubtestData) => s.nome === nome)
                      if (!item) return null
                      return (
                        <tr key={nome} className="hover:bg-slate-50">
                          <td className="px-5 py-3 text-sm text-slate-700">{item.nome}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{item.pontos_brutos ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{item.escore_ponderado ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.classificacao ?? '—'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* GAI */}
          {classified.gai_data && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
              <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Índice de Aptidão Geral (GAI)</h3></div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr className="bg-slate-50"><th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Índice</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Soma Ponderada</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Escore Composto</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Percentil</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">IC 95%</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Status</th></tr></thead>
                  <tbody className="divide-y divide-slate-200">
                    <tr className="hover:bg-slate-50">
                      <td className="px-5 py-3 text-sm font-medium text-slate-900">GAI (Índice de Aptidão Geral)</td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{classified.gai_data.soma_ponderados ?? '—'}</td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{classified.gai_data.escore_composto ?? '—'}</td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700">{classified.gai_data.percentil ?? '—'}</td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700">{classified.gai_data.intervalo_confianca?.join?.(' - ') ?? '—'}</td>
                      <td className="px-5 py-3 text-sm text-center text-slate-700">{classified.gai_data.interpretavel ? classified.gai_data.classificacao : classified.gai_data.alerta || 'Atenção'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Clusters Clínicos */}
          {classified.clusters && Object.keys(classified.clusters).length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
              <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Clusters Clínicos</h3></div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr className="bg-slate-50"><th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Cluster</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Soma</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Escore</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Percentil</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">IC 95%</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Classificação</th></tr></thead>
                  <tbody className="divide-y divide-slate-200">
                    {Object.entries(classified.clusters).map(([key, cluster]: [string, any]) => (
                      <tr key={key} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-sm font-medium text-slate-900">{cluster.nome}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{cluster.soma ?? '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700 font-semibold">{cluster.escore ?? '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{cluster.percentil ?? '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{cluster.ic_95 ?? '—'}</td>
                        <td className="px-5 py-3 text-sm text-center text-slate-700">{cluster.classificacao ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Facilidades e Dificuldades */}
          {renderReadyTables.facilidades_dificuldades && (
            <>
              <RenderReadyTable
                title={renderReadyTables.facilidades_dificuldades.titulo}
                columns={renderReadyTables.facilidades_dificuldades.colunas || []}
                rows={renderReadyTables.facilidades_dificuldades.linhas || []}
              />
              <div className="bg-white rounded-xl border border-slate-200 p-5 mb-6">
                <h4 className="font-semibold text-slate-900 mb-3">Determinação das Facilidades e Dificuldades</h4>
                <div className="grid gap-3 md:grid-cols-2 text-sm text-slate-700">
                  <div className={`rounded-xl border px-4 py-3 ${renderReadyTables.facilidades_dificuldades.determinacao?.diferenca_media_total?.checked ? 'border-sky-300 bg-sky-50' : 'border-slate-200 bg-slate-50'}`}>
                    <div className="font-medium text-slate-900">{renderReadyTables.facilidades_dificuldades.determinacao?.diferenca_media_total?.label || 'Diferença da Média Total'}</div>
                    <div className="mt-1">{renderReadyTables.facilidades_dificuldades.determinacao?.diferenca_media_total?.checked ? 'Selecionado' : 'Não selecionado'}</div>
                  </div>
                  <div className={`rounded-xl border px-4 py-3 ${renderReadyTables.facilidades_dificuldades.determinacao?.diferenca_media_verbal_execucao?.checked ? 'border-sky-300 bg-sky-50' : 'border-slate-200 bg-slate-50'}`}>
                    <div className="font-medium text-slate-900">{renderReadyTables.facilidades_dificuldades.determinacao?.diferenca_media_verbal_execucao?.label || 'Diferença da Média Verbal e da Média de Execução'}</div>
                    <div className="mt-1">{renderReadyTables.facilidades_dificuldades.determinacao?.diferenca_media_verbal_execucao?.checked ? 'Selecionado' : 'Não selecionado'}</div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Discrepâncias entre Índices */}
          {renderReadyTables.discrepancias && (
            <RenderReadyTable
              title={renderReadyTables.discrepancias.titulo}
              columns={renderReadyTables.discrepancias.colunas || []}
              rows={renderReadyTables.discrepancias.linhas || []}
            />
          )}

          {renderReadyTables.digitos && (
            <RenderReadyTable
              title={renderReadyTables.digitos.titulo}
              columns={renderReadyTables.digitos.colunas || []}
              rows={renderReadyTables.digitos.linhas || []}
            />
          )}

          {/* Análise de Dígitos */}
          {computed.digitos && Object.keys(computed.digitos).length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden mb-6">
              <div className="px-5 py-4 border-b border-slate-200"><h3 className="font-semibold text-slate-900">Análise de Dígitos</h3></div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr className="bg-slate-50"><th className="text-left px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Medida</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Bruto</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Freq. Acumulada</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Média</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">DP</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Z</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Ponder</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Percentil</th><th className="text-center px-5 py-3 text-xs font-semibold text-slate-600 uppercase tracking-wide">Classificação</th></tr></thead>
                  <tbody className="divide-y divide-slate-200">
                    {DIGIT_PROCESS_ROWS.map(({ key, label }) => {
                      const item = computed.digitos[key]
                      if (!item) return null
                      return (
                        <tr key={key} className="hover:bg-slate-50">
                          <td className="px-5 py-3 text-sm font-medium text-slate-900">{label}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.difference ?? item.raw_score ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.cumulative_frequency ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.mean ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.sd ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.z_score ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.scaled_score ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.percentile ?? '—'}</td>
                          <td className="px-5 py-3 text-sm text-center text-slate-700">{item.classification ?? '—'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Interpretação */}
          {interpretationText && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-900 mb-3">Interpretação</h3>
              <p className="text-sm leading-7 text-slate-700 whitespace-pre-wrap">{interpretationText}</p>
            </div>
          )}

          {/* Sem dados */}
          {Object.keys(indices).length === 0 && !Array.isArray(subtestes) && !interpretationText && (
            <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-5">
              <p className="text-sm text-yellow-800">Nenhum resultado disponível para exibir. Verifique se o teste foi processado corretamente.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
