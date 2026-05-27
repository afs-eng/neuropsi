'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Download, Edit, LayoutDashboard, Printer } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { printCurrentPage } from '@/lib/print'
import { TestReportSummaryCard } from '@/components/tests/TestReportSummaryCard'

const ITEM_LABELS: Record<number, string> = {
  1: 'Sinto-me estranho e não sei por quê',
  2: 'Sinto vontade de ficar longe das pessoas da minha casa',
  3: 'Sinto vontade de ficar longe dos meus amigos',
  4: 'Estou mais agressivo',
  5: 'Sinto-me culpado',
  6: 'Viver está sendo difícil para mim',
  7: 'Choro',
  8: 'Sinto-me triste',
  9: 'Tenho vontade de fazer as coisas que gosto',
  10: 'Sinto-me sozinho',
  11: 'Prefiro estar só',
  12: 'Acredito em um futuro bom',
  13: 'Meus dias têm sido bons',
  14: 'Tenho planos para o futuro',
  15: 'Tenho dormido bem',
  16: 'Acredito nas minhas capacidades',
  17: 'Estou feliz com minha vida',
  18: 'Consigo me concentrar nas minhas tarefas',
  19: 'Gosto de mim como eu sou',
  20: 'Tenho me sentido mal, sem estar doente',
  21: 'Penso em me machucar de propósito',
  22: 'Penso em me matar',
  23: 'Tenho comido normalmente',
  24: 'Sinto-me sem energia',
  25: 'Sou esperto',
  26: 'Sinto-me feio',
  27: 'Sinto que as pessoas não querem estar comigo',
}

const AUTHOR_NAME = "Dra. Claudette Maria Medeiros Baptista";

const CLASSIFICATION_STYLES: Record<string, string> = {
  Mínimo: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Leve: 'bg-blue-50 text-blue-700 border-blue-200',
  Moderado: 'bg-amber-50 text-amber-700 border-amber-200',
  Grave: 'bg-red-50 text-red-700 border-red-200',
  Severo: 'bg-rose-50 text-rose-700 border-rose-200',
}

function getClassificationStyle(classificacao: string) {
  return CLASSIFICATION_STYLES[classificacao] || 'bg-slate-100 text-slate-700 border-slate-200'
}

function getScoreLabel(value: number) {
  if (value === 0) return 'Nunca/Poucas vezes'
  if (value === 1) return 'Algumas vezes'
  if (value === 2) return 'Muitas vezes/Sempre'
  return '—'
}

export default function EBADEPIJResultPage() {
  const params = useParams()
  const router = useRouter()
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(true)

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

  if (loading) {
    return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-zinc-600">Carregando...</div></div>
  }

  if (!result) {
    return <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center"><div className="text-zinc-600">Resultado não encontrado</div></div>
  }

  const classified = result.classified_payload || {}
  const protocol = classified.result || {}
  const detailItems = protocol.detalhe_itens || []
  const norms = classified.normas || protocol.normas || {}
  const criticalItems = classified.items_criticos || []
  const responseRows = []

  for (let i = 0; i < 7; i++) {
    responseRows.push([i + 1, i + 8, i + 15, i + 22].filter((item) => item <= 27))
  }

  return (
    <div className="space-y-6 report-print-shell">
      <div className="flex items-center justify-between print:hidden report-print-hide">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push(`/dashboard/evaluations/${result.evaluation_id}?tab=overview`)} className="rounded-full">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">EBADEP-IJ - Resultado</h2>
            <p className="text-sm text-slate-500">Escala Baptista de Depressão - Infantojuvenil</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="rounded-xl gap-2 border-emerald-200 text-emerald-700 hover:bg-emerald-50" onClick={() => router.push('/dashboard')}>
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Button>
          <Button variant="outline" className="rounded-xl gap-2 border-emerald-200 text-emerald-700 hover:bg-emerald-50" onClick={() => router.push(`/dashboard/tests/ebadep-ij?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`)}>
            <Edit className="h-4 w-4" />
            Editar
          </Button>
          <Button variant="outline" className="rounded-xl gap-2 border-emerald-200 text-emerald-700 hover:bg-emerald-50" onClick={() => router.push(`/dashboard/evaluations/${result.evaluation_id}?tab=overview`)}>
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Button>
          <Button variant="outline" className="rounded-xl gap-2 border-emerald-200 text-emerald-700 hover:bg-emerald-50" onClick={printCurrentPage}>
            <Printer className="h-4 w-4" />
            Imprimir
          </Button>
          <Button className="rounded-xl gap-2 bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-100 transition-all font-bold" onClick={printCurrentPage}>
            <Download className="h-4 w-4" />
            Salvar em PDF
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 space-y-10 print:shadow-none print:border-none print:p-0 report-print-content">
        <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text || result.interpretation} className="mb-6" />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           <section>
              <h2 className="text-[10px] font-black uppercase tracking-widest text-emerald-600 mb-4 flex items-center gap-2">
                 <div className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                 Dados de Identificação
              </h2>
              <div className="border border-slate-100 rounded-2xl overflow-hidden bg-slate-50/30">
                <table className="w-full text-xs">
                  <tbody>
                    <tr className="border-b border-slate-100"><td className="py-3 px-4 font-black text-slate-400 uppercase w-1/3">Paciente</td><td className="py-3 px-4 text-slate-900 font-bold">{result.patient_name}</td></tr>
                    <tr className="border-b border-slate-100"><td className="py-3 px-4 font-black text-slate-400 uppercase">Aplicação</td><td className="py-3 px-4 text-slate-900 font-bold">{result.applied_on || '—'}</td></tr>
                    <tr className="border-b border-slate-100"><td className="py-3 px-4 font-black text-slate-400 uppercase">Examinador</td><td className="py-3 px-4 text-slate-900 font-bold">{result.examiner_name && result.examiner_name !== '—' ? result.examiner_name : 'Dr. André'}</td></tr>
                    <tr><td className="py-3 px-4 font-black text-slate-400 uppercase">Protocolo</td><td className="py-3 px-4 text-slate-900 font-bold">{params.id}</td></tr>
                  </tbody>
                </table>
              </div>
           </section>

           <section>
              <h2 className="text-[10px] font-black uppercase tracking-widest text-emerald-600 mb-4 flex items-center gap-2">
                 <div className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
                 Escore Geral e Normas
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                 <div className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Pontos Brutos</p>
                    <p className="text-3xl font-black text-slate-900 leading-none">{classified.pontuacao_total ?? '—'}</p>
                 </div>
                 <div className={`rounded-2xl p-4 border flex flex-col justify-center ${getClassificationStyle(classified.classificacao || '')}`}>
                    <p className="text-[9px] font-black uppercase tracking-widest opacity-60 mb-1">Classificação</p>
                    <p className="text-sm font-black tracking-tight leading-tight uppercase">{classified.classificacao || '—'}</p>
                 </div>
                 <div className="bg-slate-50 rounded-2xl p-3 border border-slate-100">
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Percentil</p>
                    <p className="text-3xl font-black text-slate-900 leading-none">{norms.percentil ?? '—'}</p>
                 </div>
                 <div className="bg-slate-50 rounded-2xl p-3 border border-slate-100">
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Escore T</p>
                    <p className="text-3xl font-black text-slate-900 leading-none">{norms.T ?? '—'}</p>
                 </div>
                 <div className="bg-slate-50 rounded-2xl p-3 border border-slate-100">
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-1">Estanino</p>
                    <p className="text-3xl font-black text-slate-900 leading-none">{norms.estanino ?? '—'}</p>
                 </div>
              </div>
           </section>
        </div>

        <section className="relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-emerald-600 rounded-full" />
          <div className="bg-slate-50/50 rounded-3xl p-8 border border-slate-100 shadow-inner group transition-all hover:bg-white hover:border-emerald-100">
            <h2 className="text-[10px] font-black uppercase tracking-widest text-emerald-600 mb-8 flex items-center gap-3">
               <div className="h-4 w-4 rounded bg-emerald-100 flex items-center justify-center">
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
               </div>
               Síntese de Interpretação Clínica do Especialista
            </h2>
            <div className="prose prose-slate max-w-none">
               <div className="text-sm text-slate-700 font-medium leading-relaxed whitespace-pre-wrap print:text-black">
                 {/* Design para o título ## Resultado se presente no texto */}
                 {(result.interpretation_text || result.interpretation || '').split('\n').map((line: string, i: number) => {
                   if (line.startsWith('## ')) {
                     return <h3 key={i} className="text-xl font-black text-slate-900 mt-6 mb-4 uppercase tracking-tight">{line.replace('## ', '')}</h3>
                   }
                   if (line.includes('**')) {
                     const parts = line.split('**');
                     return (
                       <p key={i} className="mb-4">
                         {parts.map((p, j) => (j % 2 === 1 ? <strong key={j} className="font-black text-emerald-700 bg-emerald-50 px-1 rounded">{p}</strong> : p))}
                       </p>
                     )
                   }
                   return line.trim() ? <p key={i} className="mb-4">{line}</p> : <div key={i} className="h-2" />
                 })}
               </div>
            </div>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between mb-4">
             <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-400">Análise de Itens Críticos</h2>
             <span className="text-[10px] font-black text-red-500 uppercase">{criticalItems.length} identificados</span>
          </div>
          {criticalItems.length > 0 ? (
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-9 gap-2">
              {criticalItems.map((item: any) => (
                <div key={item.item} className="h-10 w-full flex flex-col items-center justify-center rounded-xl bg-red-50 border border-red-100">
                   <span className="text-[9px] font-black text-red-400 uppercase leading-none">Item</span>
                   <span className="text-sm font-black text-red-700 leading-none">{item.item}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="border border-dashed border-slate-200 rounded-2xl p-4 text-center">
               <p className="text-[10px] font-black text-slate-400 uppercase">Nenhum item de alerta clínica máxima identificado</p>
            </div>
          )}
        </section>

        <section>
          <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4">Registro de Respostas (27 Itens)</h2>
          <div className="border border-slate-100 rounded-3xl overflow-hidden shadow-sm">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-12">Item</th>
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-16">Resp.</th>
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-12">Item</th>
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-16">Resp.</th>
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-12">Item</th>
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-16">Resp.</th>
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-12">Item</th>
                  <th className="py-2 px-2 text-center font-black text-slate-400 uppercase w-16">Resp.</th>
                </tr>
              </thead>
              <tbody>
                {responseRows.map((row, idx) => (
                  <tr key={idx} className={`border-t border-slate-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}>
                    {row.map((itemNumber) => {
                      const item = detailItems.find((entry: any) => entry.item === itemNumber)
                      return (
                        <>
                          <td className="py-1.5 px-2 text-center text-slate-700 font-bold">{String(itemNumber).padStart(2, '0')}</td>
                          <td className="py-1.5 px-2 text-center">
                            <span className={`inline-flex items-center justify-center w-8 h-6 rounded-lg font-black text-[10px] ${item?.resposta === 2 ? 'bg-red-500 text-white' : item?.resposta === 1 ? 'bg-amber-400 text-white' : item?.resposta === 0 ? 'bg-slate-200 text-slate-700' : 'bg-slate-100 text-slate-400'}`}>
                              {item?.resposta ?? '-'}
                            </span>
                          </td>
                        </>
                      )
                    })}
                    {Array.from({ length: 4 - row.length }).map((_, emptyIdx) => (
                      <>
                        <td key={`empty-item-${idx}-${emptyIdx}`} className="py-1.5 px-2" />
                        <td key={`empty-resp-${idx}-${emptyIdx}`} className="py-1.5 px-2" />
                      </>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-[9px] font-bold text-slate-400 uppercase tracking-widest text-center">Legenda: 0 = Nunca/Poucas vezes | 1 = Algumas vezes | 2 = Muitas vezes/Sempre</p>
        </section>

      </div>
    </div>
  )
}
