'use client'

import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { PageContainer, PageHeader, SectionCard } from '@/components/ui/page'
import { Button } from '@/components/ui/button'
import { RAVLTChart } from '@/components/charts/RAVLTChart'
import { ArrowLeft, Edit2, FileText, Activity, Brain, Target, Calendar, User, Clock } from 'lucide-react'
import { openPrintRoute } from '@/lib/print'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'

export default function RAVLTResultPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const evaluationId = searchParams.get('evaluation_id')
  
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const data = await api.get<any>(`/api/tests/ravlt/result/${params.id}`)
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
      <PageContainer>
        <div className="py-20 text-center animate-pulse text-slate-300 font-bold uppercase tracking-widest text-xs">
          Aguarde... Carregando resultados do RAVLT
        </div>
      </PageContainer>
    )
  }

  if (!result) {
    return (
      <PageContainer>
        <div className="py-20 text-center text-slate-400 font-bold uppercase tracking-widest text-xs">
          Resultado não encontrado
        </div>
      </PageContainer>
    )
  }

  const rawPayload = result.raw_payload || {}
  const resultsData = result.results || {}
  const items = resultsData.resultados || []
  const chartData = resultsData.chart || result.classified_payload?.chart || null
  const handlePrint = () => {
    if (!params.id) return
    openPrintRoute(`/print/ravlt/${params.id}?autoprint=1`)
  }
  
  const formatNumber = (num: any) => {
    if (num === null || num === undefined) return '-'
    const n = Number(num)
    return Number.isInteger(n) ? n.toString() : n.toFixed(2)
  }

  const getClassificationColor = (classification: string) => {
    if (!classification) return 'text-slate-500 bg-slate-50 border-slate-100'
    const lower = classification.toLowerCase()
    if (lower.includes('superior')) return 'text-emerald-700 bg-emerald-50 border-emerald-200'
    if (lower.includes('médio')) return 'text-blue-700 bg-blue-50 border-blue-200'
    if (lower.includes('inferior') || lower.includes('déficit')) return 'text-rose-700 bg-rose-50 border-rose-200'
    if (lower.includes('limítrofe')) return 'text-amber-700 bg-amber-50 border-amber-200'
    return 'text-slate-600 bg-slate-50 border-slate-200'
  }

  return (
    <PageContainer>
      <PageHeader
        title="Resultados: RAVLT"
        subtitle={`Teste de Aprendizagem Auditivo-Verbal de Rey para: ${result.patient_name}`}
        actions={
          <div className="flex gap-2">
            <Link href={`/dashboard/evaluations/${result.evaluation_id}`}>
              <Button variant="ghost" className="gap-2 font-bold text-slate-500">
                <ArrowLeft className="h-4 w-4" />
                Voltar para Avaliação
              </Button>
            </Link>
            <Button variant="outline" className="gap-2 border-slate-200 text-slate-700 font-bold" onClick={handlePrint}>
              <FileText className="h-4 w-4" /> Imprimir / PDF
            </Button>
            <Link href={`/dashboard/tests/ravlt/${params.id}?evaluation_id=${result.evaluation_id}&edit=true`}>
              <Button variant="outline" className="gap-2 border-slate-200 text-slate-700 font-bold">
                <Edit2 className="h-4 w-4" /> Editar Aplicação
              </Button>
            </Link>
          </div>
        }
      />

      <TestReportSummaryCard reportPayload={result.report_payload as any} fallbackText={result.interpretation} className="mb-8" />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="md:col-span-2 space-y-8">
          
          {/* Main Interpretation Table */}
          <SectionCard 
            title="Tabela de Normatização e Interpretação" 
            description={`Resultados normativos comparados com a faixa etária do paciente: ${resultsData.faixa_etaria || '-'}`}
          >
            <div className="overflow-x-auto rounded-[24px] border border-slate-200 bg-white shadow-sm">
              <table className="w-full min-w-[800px] border-collapse text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-4 border-b border-slate-200 font-black text-slate-400 text-[10px] uppercase tracking-widest text-left">Itens</th>
                    <th className="px-3 py-4 border-b border-slate-200 font-black text-slate-400 text-[10px] uppercase tracking-widest text-center">Pts. Brutos</th>
                    <th className="px-3 py-4 border-b border-slate-200 font-black text-slate-400 text-[10px] uppercase tracking-widest text-center">Média</th>
                    <th className="px-3 py-4 border-b border-slate-200 font-black text-slate-400 text-[10px] uppercase tracking-widest text-center">Desvio Padrão</th>
                    <th className="px-3 py-4 border-b border-slate-200 font-black text-slate-400 text-[10px] uppercase tracking-widest text-center">Pts. Ponderados</th>
                    <th className="px-3 py-4 border-b border-slate-200 font-black text-slate-400 text-[10px] uppercase tracking-widest text-center">Percentil</th>
                    <th className="px-4 py-4 border-b border-slate-200 font-black text-slate-400 text-[10px] uppercase tracking-widest text-left w-48">Classificação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {items.map((item: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-4 py-3 font-bold text-slate-700 text-left whitespace-nowrap">{item.variavel}</td>
                      <td className="px-3 py-3 font-bold text-slate-900 text-center">{formatNumber(item.bruto)}</td>
                      <td className="px-3 py-3 font-medium text-slate-500 text-center">{formatNumber(item.media)}</td>
                      <td className="px-3 py-3 font-medium text-slate-500 text-center">{formatNumber(item.dp)}</td>
                      <td className="px-3 py-3 font-bold text-primary text-center">{formatNumber(item.ponderado)}</td>
                      <td className="px-3 py-3 font-black text-slate-700 text-center">{formatNumber(item.percentil)}</td>
                      <td className="px-4 py-3 text-left">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[9px] font-black uppercase tracking-widest border ${getClassificationColor(item.classificacao)}`}>
                          {item.classificacao || '-'}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-slate-400 font-bold uppercase text-[10px] tracking-widest">
                        Nenhum dado normativo encontrado
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </SectionCard>

          {/* Computed Analysis Overview */}
          <SectionCard title="Análise Rápida de Desempenho" description="Principais marcadores de aprendizado e memória.">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="rounded-[24px] bg-blue-50 p-6 border border-blue-100 relative overflow-hidden">
                <Brain className="absolute -right-4 -bottom-4 h-24 w-24 text-blue-500/10" />
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-blue-600 mb-2">Curva de Aprendizado</div>
                <div className="text-3xl font-black text-blue-800 tracking-tight">
                  {rawPayload.a1 + rawPayload.a2 + rawPayload.a3 + rawPayload.a4 + rawPayload.a5 || '-'}
                  <span className="text-sm font-bold text-blue-400 ml-1">/ 75</span>
                </div>
                <p className="text-[11px] font-medium text-blue-600 mt-2">Soma total das tentativas A1-A5</p>
              </div>

              <div className="rounded-[24px] bg-amber-50 p-6 border border-amber-100 relative overflow-hidden">
                <Target className="absolute -right-4 -bottom-4 h-24 w-24 text-amber-500/10" />
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-600 mb-2">Velocidade de Esquecimento</div>
                <div className="text-3xl font-black text-amber-800 tracking-tight">
                  {items.find((i: any) => i.variavel === "Velocidade de Esquecimento")?.bruto !== undefined 
                    ? formatNumber(items.find((i: any) => i.variavel === "Velocidade de Esquecimento")?.bruto * 100) + '%'
                    : '-'}
                </div>
                <p className="text-[11px] font-medium text-amber-600 mt-2">Retenção após intervalo (A7/A6)</p>
              </div>

              <div className="rounded-[24px] bg-purple-50 p-6 border border-purple-100 relative overflow-hidden">
                <Activity className="absolute -right-4 -bottom-4 h-24 w-24 text-purple-500/10" />
                <div className="text-[10px] font-black uppercase tracking-[0.2em] text-purple-600 mb-2">Interferência Proativa</div>
                <div className="text-3xl font-black text-purple-800 tracking-tight">
                  {items.find((i: any) => i.variavel === "Interferência Proativa")?.bruto !== undefined 
                    ? formatNumber(items.find((i: any) => i.variavel === "Interferência Proativa")?.bruto) 
                    : '-'}
                </div>
                <p className="text-[11px] font-medium text-purple-600 mt-2">Razão B1/A1</p>
              </div>
            </div>
          </SectionCard>

          {chartData && (
            <SectionCard title="Curva de Aprendizagem" description="Séries esperada, mínima e obtida no formato gráfico do RAVLT.">
              <RAVLTChart data={chartData} />
            </SectionCard>
          )}
          
          {/* Summary Text (If provided by backend) */}
          {result.interpretation && (
            <SectionCard 
              title="Texto para o Laudo (Súmula)" 
              description="Resumo textual gerado automaticamente para você copiar e colar no seu documento final."
            >
               <div className="relative rounded-2xl bg-white p-6 md:p-8 border-2 border-slate-100 shadow-sm overflow-hidden group">
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(result.interpretation)
                      alert("Súmula copiada para a área de transferência!")
                    }}
                    className="absolute top-4 right-4 text-[10px] font-black uppercase tracking-widest text-primary bg-primary/10 hover:bg-primary/20 hover:scale-105 active:scale-95 px-4 py-2.5 rounded-xl transition-all flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover:opacity-100"
                  >
                    📋 Copiar Original
                  </button>
                  
                  <div className="space-y-1">
                    {result.interpretation.split('\n').map((line: string, idx: number) => {
                      if (line.includes('RAVLT - Resultados')) {
                        return <h4 key={idx} className="text-sm font-black uppercase tracking-widest text-slate-400 border-b-2 border-slate-100 pb-4 mb-6">{line}</h4>
                      }
                      if (!line.trim()) return <div key={idx} className="h-2" />
                      
                      const match = line.match(/^(.*?):\s*(.*?)\s*\((.*?)\)$/);
                      if (match) {
                        const classificacao = match[3].toLowerCase();
                        let badgeClass = "border-slate-200 text-slate-500 bg-slate-50";
                        if (classificacao.includes('inferior') || classificacao.includes('déficit')) badgeClass = "border-rose-200 text-rose-600 bg-rose-50";
                        else if (classificacao.includes('superior')) badgeClass = "border-emerald-200 text-emerald-600 bg-emerald-50";
                        else if (classificacao.includes('média')) badgeClass = "border-blue-200 text-blue-600 bg-blue-50";
                        else if (classificacao.includes('limítrofe')) badgeClass = "border-amber-200 text-amber-600 bg-amber-50";

                        return (
                          <div key={idx} className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-2 sm:py-3 border-b border-dashed border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors px-2 rounded-lg">
                             <div className="flex items-center gap-3">
                               <div className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                               <span className="font-bold text-slate-700 text-sm">{match[1]}</span>
                             </div>
                             <div className="flex items-center gap-4 mt-2 sm:mt-0 ml-4 sm:ml-0">
                               <span className="text-xs font-medium text-slate-400">Score bruto: <strong className="text-slate-900 ml-1">{match[2]}</strong></span>
                               <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded-md border ${badgeClass}`}>
                                 {match[3]}
                               </span>
                             </div>
                          </div>
                        )
                      }
                      
                      return <div key={idx} className="text-sm font-medium text-slate-600">{line}</div>
                    })}
                  </div>
               </div>
            </SectionCard>
          )}

        </div>

        {/* Sidebar Context */}
        <div className="space-y-6">
          <SectionCard>
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary font-black text-lg">
                  {result.patient_name.charAt(0)}
                </div>
                <div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Paciente</div>
                  <div className="font-bold text-slate-900">{result.patient_name}</div>
                </div>
              </div>
              
              <div className="h-px w-full bg-slate-100" />
              
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400">
                  <Calendar className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Data de Aplicação</div>
                  <div className="font-bold text-slate-700">{result.applied_on || '-'}</div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-xl bg-slate-50 flex items-center justify-center text-slate-400">
                  <User className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Idade Calculada</div>
                  <div className="font-bold text-slate-700">{resultsData.idade || '-'} anos</div>
                </div>
              </div>

            </div>
          </SectionCard>

          <SectionCard title="Escores Brutos da Aplicação">
            <div className="space-y-3">
              {[
                { label: 'Tentativas A1-A5', value: `${rawPayload.a1}, ${rawPayload.a2}, ${rawPayload.a3}, ${rawPayload.a4}, ${rawPayload.a5}` },
                { label: 'Matriz B (Interferência)', value: rawPayload.b },
                { label: 'A6 (Intervalo Imediato)', value: rawPayload.a6 },
                { label: 'A7 (30 Minutos)', value: rawPayload.a7 },
                { label: 'Escore de Reconhecimento', value: rawPayload.reconhecimento },
              ].map((item, idx) => (
                <div key={idx} className="flex justify-between items-center p-3 rounded-xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-colors">
                  <span className="text-xs font-bold text-slate-500">{item.label}</span>
                  <span className="text-xs font-black text-slate-900">{item.value}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    </PageContainer>
  )
}
