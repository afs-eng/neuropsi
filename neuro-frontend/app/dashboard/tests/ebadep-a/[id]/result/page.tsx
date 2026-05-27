'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Download, Edit, LayoutDashboard, Printer } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getToken, resolveApiUrl } from '@/lib/api'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'

const ITEM_LABELS: Record<number, string> = {
  1: 'Choro',
  2: 'Bem-estar',
  3: 'Tarefas',
  4: 'Problemas',
  5: 'Prazer',
  6: 'Choro recente',
  7: 'Solidão',
  8: 'Comportamento',
  9: 'Autonomia',
  10: 'Futuro',
  11: 'Atitudes',
  12: 'Planejamento',
  13: 'Crença em si',
  14: 'Decisão',
  15: 'Escolhas',
  16: 'Independência',
  17: 'Atividades',
  18: 'Vida',
  19: 'Situação atual',
  20: 'Utilidade',
  21: 'Convívio',
  22: 'Eventos sociais',
  23: 'Concentração',
  24: 'Ritmo de trabalho',
  25: 'Agitação',
  26: 'História de vida',
  27: 'Energia matinal',
  28: 'Vida atual',
  29: 'Ideias sobre morrer',
  30: 'Autoeficácia',
  31: 'Sono',
  32: 'Necessário do dia a dia',
  33: 'Valor da vida',
  34: 'Autoimagem',
  35: 'Finalização',
  36: 'Tranquilidade',
  37: 'Nervosismo',
  38: 'Disposição',
  39: 'Vontade de agir',
  40: 'Padrão de sono',
  41: 'Apetite',
  42: 'Desejo sexual',
  43: 'Peso',
  44: 'Medicação',
  45: 'Culpa',
}

const CLASSIFICATION_STYLES: Record<string, string> = {
  Mínimo: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Leve: 'bg-blue-50 text-blue-700 border-blue-200',
  Moderado: 'bg-amber-50 text-amber-700 border-amber-200',
  Grave: 'bg-red-50 text-red-700 border-red-200',
  Severo: 'bg-rose-50 text-rose-700 border-rose-200',
}

function getScoreLabel(value: number) {
  if (value === 0) return 'Primeiro círculo'
  if (value === 1) return 'Segundo círculo'
  if (value === 2) return 'Terceiro círculo'
  if (value === 3) return 'Quarto círculo'
  return '—'
}

function getClassificationStyle(classificacao: string) {
  return CLASSIFICATION_STYLES[classificacao] || 'bg-slate-100 text-slate-700 border-slate-200'
}

export default function EBADEPAResultPage() {
  const params = useParams()
  const router = useRouter()
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
      alert(exportError?.message || 'Não foi possível gerar o PDF do EBADEP-A.')
    } finally {
      setExportingPdf(false)
    }
  }

  if (loading) {
    return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-zinc-600">Carregando...</div></div>
  }

  if (!result) {
    return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-zinc-600">Resultado não encontrado</div></div>
  }

  const classified = result.classified_payload || {}
  const detailItems = classified.result?.detalhe_itens || []
  const criticalItems = classified.items_criticos || []
  const responseRows = []

  for (let i = 0; i < 9; i++) {
    responseRows.push([i + 1, i + 10, i + 19, i + 28, i + 37].filter((item) => item <= 45))
  }

  return (
    <div className="space-y-6 report-print-shell">
      <div className="flex items-center justify-between print:hidden report-print-hide">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push(`/dashboard/evaluations/${result.evaluation_id}?tab=overview`)} className="rounded-full">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">EBADEP-A - Resultado</h2>
            <p className="text-sm text-slate-500">Escala Baptista de Depressão - Versão Adulto</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="rounded-xl gap-2" onClick={() => router.push('/dashboard')}>
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Button>
          <Button variant="outline" className="rounded-xl gap-2" onClick={() => router.push(`/dashboard/tests/ebadep-a?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`)}>
            <Edit className="h-4 w-4" />
            Editar
          </Button>
          <Button variant="outline" className="rounded-xl gap-2" onClick={() => router.push(`/dashboard/evaluations/${result.evaluation_id}?tab=overview`)}>
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Button>
          <Button variant="outline" className="rounded-xl gap-2" onClick={handleExportPdf} disabled={exportingPdf}>
            <Printer className="h-4 w-4" />
            {exportingPdf ? 'Gerando...' : 'Imprimir'}
          </Button>
          <Button className="rounded-xl gap-2" onClick={handleExportPdf} disabled={exportingPdf}>
            <Download className="h-4 w-4" />
            {exportingPdf ? 'Gerando...' : 'Salvar em PDF'}
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 space-y-8 report-print-content">
        <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text} className="mb-6" />

        <div className="text-center border-b pb-6">
          <h1 className="text-2xl font-bold text-slate-900">EBADEP-A</h1>
          <p className="text-lg text-slate-600">Escala Baptista de Depressão - Versão Adulto</p>
          <p className="text-sm text-slate-500 mt-1">Relatório estruturado do protocolo</p>
        </div>

        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">DADOS DA APLICAÇÃO</h2>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b"><td className="py-3 px-4 font-medium text-slate-700 w-1/3">Paciente</td><td className="py-3 px-4 text-slate-900">{result.patient_name}</td></tr>
                <tr className="border-b"><td className="py-3 px-4 font-medium text-slate-700">Aplicação</td><td className="py-3 px-4 text-slate-900">{result.applied_on || '—'}</td></tr>
                <tr className="border-b"><td className="py-3 px-4 font-medium text-slate-700">Total de itens</td><td className="py-3 px-4 text-slate-900">45</td></tr>
                <tr><td className="py-3 px-4 font-medium text-slate-700">Itens críticos</td><td className="py-3 px-4 text-slate-900">{criticalItems.length}</td></tr>
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">SÍNTESE DOS RESULTADOS</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-200 p-5 bg-slate-50">
              <p className="text-sm text-slate-500">Escore total</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{classified.escore_total ?? '—'}</p>
            </div>
            <div className="rounded-xl border border-slate-200 p-5 bg-slate-50">
              <p className="text-sm text-slate-500">Percentil</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{classified.percentil ?? '—'}</p>
            </div>
            <div className="rounded-xl border border-slate-200 p-5 bg-slate-50">
              <p className="text-sm text-slate-500">Classificação</p>
              <div className="mt-3"><Badge className={getClassificationStyle(classified.classificacao || '')}>{classified.classificacao || '—'}</Badge></div>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">LEITURA CLÍNICA</h2>
          <div className="space-y-4">
            <div className="border rounded-xl p-4">
              <h3 className="font-semibold text-slate-900 mb-2">Síntese interpretativa</h3>
              <p className="text-sm text-slate-600">{classified.sintese || 'Sem síntese disponível.'}</p>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-sm text-amber-800">Este resultado deve ser integrado com entrevista clínica, observação e demais instrumentos do processo avaliativo.</p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">ITENS CRÍTICOS</h2>
          {criticalItems.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {criticalItems.map((item: any) => (
                <Badge key={item.item} className="bg-red-50 text-red-700 border-red-200">Item {item.item}</Badge>
              ))}
            </div>
          ) : (
            <div className="border rounded-xl p-4 text-sm text-slate-600">Nenhum item com intensidade máxima.</div>
          )}
        </section>

        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">REGISTRO DE RESPOSTAS</h2>
          <p className="text-sm text-slate-600 mb-4">Legenda: 0 = Primeiro círculo | 1 = Segundo | 2 = Terceiro | 3 = Quarto</p>
          <div className="border rounded-xl overflow-hidden">
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
                      const item = detailItems.find((entry: any) => entry.item === itemNumber)
                      return (
                        <>
                          <td className="py-1 px-2 text-center text-slate-700 font-medium">{String(itemNumber).padStart(2, '0')}</td>
                          <td className="py-1 px-2 text-center">
                            <span className={`inline-block w-8 h-6 leading-6 rounded font-bold ${item?.resposta === 3 ? 'bg-red-100 text-red-800' : item?.resposta === 2 ? 'bg-amber-100 text-amber-800' : item?.resposta === 1 ? 'bg-blue-100 text-blue-800' : item?.resposta === 0 ? 'bg-slate-200 text-slate-700' : 'bg-slate-100 text-slate-400'}`}>
                              {item?.resposta ?? '-'}
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
        </section>

        {result.interpretation_text && (
          <section>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">INTERPRETAÇÃO</h2>
            <div className="border rounded-xl p-4 whitespace-pre-wrap text-sm text-slate-600 leading-relaxed">
              {result.interpretation_text}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
