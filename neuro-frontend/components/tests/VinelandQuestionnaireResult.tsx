'use client'

import Link from 'next/link'
import { useState } from 'react'
import { getToken, resolveApiUrl } from '@/lib/api'
import { VinelandNormativeResults, type VinelandNormativeResultsData } from './VinelandNormativeResults'

const dateFormatter = new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' })

interface SectionSummary {
  code: string
  label: string
  kind: 'adaptive' | 'behavior' | 'critical'
  applied: boolean
  answered: number
  total: number
  raw_score: number | null
  max_score: number | null
  response_counts: Record<string, number>
}

export interface VinelandItemSummary {
  protocol_id: string
  normative_scoring: false
  answered: number
  applied_total: number
  sections: SectionSummary[]
  critical_items: { id: string; text: string; response: string }[]
}

export interface VinelandResultApplication {
  id: number
  evaluation_id: number
  instrument_code: string
  patient_name?: string
  applied_on: string | null
  status: string
  normative_results?: VinelandNormativeResultsData | null
  raw_payload: {
    respondent?: string
    birth_date?: string
    item_protocol_id?: string
    completion_status?: string
    general_observations?: string
    item_summary?: VinelandItemSummary
  }
}

export function VinelandQuestionnaireResult({ application }: { application: VinelandResultApplication }) {
  const [exportingPdf, setExportingPdf] = useState(false)
  const [pdfError, setPdfError] = useState('')
  const summary = application.raw_payload.item_summary!
  const adaptive = summary.sections.filter(section => section.kind === 'adaptive')
  const behavior = summary.sections.filter(section => section.kind === 'behavior')
  const critical = summary.sections.find(section => section.kind === 'critical')
  const evaluationUrl = `/dashboard/evaluations/${application.evaluation_id}/overview`
  const editUrl = `/dashboard/tests/vineland?evaluation_id=${application.evaluation_id}&application_id=${application.id}&edit=true`

  async function exportPdf() {
    if (exportingPdf) return
    setExportingPdf(true)
    setPdfError('')
    try {
      const token = getToken()
      const response = await fetch(resolveApiUrl(`/api/tests/applications/${application.id}/export-pdf`), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        cache: 'no-store',
      })
      if (!response.ok) {
        let message = `Não foi possível gerar o PDF (${response.status}).`
        try {
          const payload = await response.json()
          if (payload.message) message = String(payload.message)
        } catch { /* Keep the HTTP error message if the server did not return JSON. */ }
        throw new Error(message)
      }
      const url = URL.createObjectURL(await response.blob())
      const download = document.createElement('a')
      download.href = url
      download.download = `VINELAND3-${application.id}.pdf`
      document.body.appendChild(download)
      download.click()
      download.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (error) {
      setPdfError(error instanceof Error ? error.message : 'Não foi possível gerar o PDF. Tente novamente.')
    } finally {
      setExportingPdf(false)
    }
  }

  function dateLabel(value?: string | null) {
    return value ? dateFormatter.format(new Date(`${value}T00:00:00Z`)) : '—'
  }

  function sectionTable(rows: SectionSummary[]) {
    return <div className="overflow-x-auto"><table className="w-full text-left text-sm tabular-nums">
      <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600"><tr>
        <th scope="col" className="px-5 py-3">Área</th>
        <th scope="col" className="px-5 py-3 text-center">Respostas</th>
        <th scope="col" className="px-5 py-3 text-center">Soma bruta</th>
        <th scope="col" className="px-5 py-3 text-center">Máximo possível</th>
        <th scope="col" className="px-5 py-3">Situação</th>
      </tr></thead>
      <tbody className="divide-y divide-slate-200">{rows.map(section => <tr key={section.code}>
        <th scope="row" className="px-5 py-3 font-medium text-slate-900">{section.label}</th>
        <td className="px-5 py-3 text-center">{section.applied ? `${section.answered}/${section.total}` : '—'}</td>
        <td className="px-5 py-3 text-center font-bold text-blue-700">{section.raw_score ?? '—'}</td>
        <td className="px-5 py-3 text-center">{section.applied ? section.max_score : '—'}</td>
        <td className="px-5 py-3">{section.applied ? 'Preenchida' : 'Não aplicada'}</td>
      </tr>)}</tbody>
    </table></div>
  }

  return <main className="min-h-screen break-words bg-slate-300 p-4 md:p-10 report-print-shell">
    <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7 report-print-card">
      <div className="space-y-6 rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6 report-print-content">
        <header className="flex flex-wrap items-center justify-between gap-4 print:hidden report-print-hide">
          <span className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium text-zinc-800">NeuroAvalia</span>
          <nav aria-label="Navegação dos resultados" className="flex flex-wrap gap-2 rounded-full bg-white/70 px-3 py-2 text-sm text-zinc-700">
            <Link href="/dashboard" className="rounded-full px-4 py-3 hover:bg-black/5">Dashboard</Link>
            <Link href="/dashboard/evaluations" className="rounded-full px-4 py-3 hover:bg-black/5">Avaliações</Link>
            <Link href="/dashboard/tests" className="rounded-full px-4 py-3 hover:bg-black/5">Testes</Link>
          </nav>
        </header>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div><h1 className="text-3xl font-medium tracking-tight text-zinc-900">Vineland-3 - Resultado</h1>
            <p className="mt-1 text-sm text-zinc-600">{application.patient_name} · Pais/Cuidadores — Níveis de Domínio</p>
          </div>
          <div className="flex flex-wrap gap-3 print:hidden report-print-hide">
            {application.status !== 'locked' && <Link href={editUrl} className="rounded-full border border-black/10 bg-white px-4 py-3 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">Editar</Link>}
            <button type="button" onClick={exportPdf} disabled={exportingPdf} aria-busy={exportingPdf} className="rounded-full border border-black/10 bg-white px-4 py-3 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50 disabled:cursor-wait disabled:opacity-60">{exportingPdf ? 'Gerando PDF…' : 'Imprimir / PDF'}</button>
            <Link href={evaluationUrl} className="rounded-full bg-zinc-900 px-4 py-3 text-sm font-medium text-white shadow-lg">Voltar à avaliação</Link>
          </div>
        </div>
        {pdfError && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 print:hidden">{pdfError}</p>}
        <section aria-labelledby="vineland-identification" className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 id="vineland-identification" className="mb-3 font-semibold text-slate-900">Identificação e preenchimento</h2>
          <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div><dt className="text-slate-500">Avaliado</dt><dd className="font-medium">{application.patient_name || '—'}</dd></div>
            <div><dt className="text-slate-500">Respondente / informante</dt><dd className="font-medium">{application.raw_payload.respondent || '—'}</dd></div>
            <div><dt className="text-slate-500">Aplicação</dt><dd className="font-medium">{dateLabel(application.applied_on)}</dd></div>
            <div><dt className="text-slate-500">Nascimento</dt><dd className="font-medium">{dateLabel(application.raw_payload.birth_date)}</dd></div>
          </dl>
          <p className="mt-4 font-medium text-slate-800">Preenchimento finalizado · {summary.answered} de {summary.applied_total} itens das seções aplicadas respondidos.</p>
        </section>
        {application.normative_results ? <VinelandNormativeResults result={application.normative_results} /> : <>
        <aside className="space-y-2 rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
          <h2 className="font-semibold">Resultado descritivo — sem correção normativa</h2>
          <p>As somas abaixo são das respostas registradas. Não são escores padrão, percentis, classificação clínica ou CCA. A conversão normativa deste formulário ainda não está habilitada.</p>
          <p>A finalização não equivale à revisão clínica e não inclui automaticamente este registro no laudo.</p>
        </aside>
        <section aria-labelledby="vineland-adaptive-summary" className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <h2 id="vineland-adaptive-summary" className="border-b border-slate-200 px-5 py-4 font-semibold text-slate-900">Resumo das áreas adaptativas</h2>
          {sectionTable(adaptive)}
        </section>
        <section aria-labelledby="vineland-raw-profile" className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
          <h2 id="vineland-raw-profile" className="font-semibold text-slate-900">Perfil das somas brutas</h2>
          <p className="text-sm text-slate-600">Barras proporcionais ao máximo de cada seção, sem comparação normativa ou classificação de desempenho.</p>
          {adaptive.filter(section => section.applied).map(section => <div key={section.code}>
            <div className="mb-1 flex justify-between gap-4 text-sm"><span>{section.label}</span><span className="font-semibold">{section.raw_score} / {section.max_score}</span></div>
            <div aria-hidden="true" className="h-3 rounded-full bg-slate-100"><div className="h-3 rounded-full bg-blue-600" style={{ width: `${(section.raw_score ?? 0) / (section.max_score || 1) * 100}%` }} /></div>
          </div>)}
        </section>
        <section aria-labelledby="vineland-behavior-summary" className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <h2 id="vineland-behavior-summary" className="border-b border-slate-200 px-5 py-4 font-semibold text-slate-900">Problemas de comportamento — A e B</h2>
          <p className="px-5 py-3 text-sm text-slate-600">Nestas seções, maior soma indica maior frequência dos comportamentos relatados, não melhor habilidade. Sem escala-v ou classificação automática.</p>
          {sectionTable(behavior)}
        </section>
        </>}
        <section aria-labelledby="vineland-critical-items" className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 id="vineland-critical-items" className="mb-3 font-semibold text-slate-900">Itens críticos — Seção C</h2>
          <p className="mb-3 text-sm text-slate-600">Itens com resposta 1 ou 2 são apresentados individualmente para revisão profissional. Esta seção não recebe soma ou diagnóstico automático.</p>
          {!critical?.applied ? <p className="text-sm">Seção não aplicada.</p> : summary.critical_items.length === 0 ? <p className="text-sm">Nenhum item com resposta 1 ou 2 nesta seção.</p> :
            <ul className="space-y-3">{summary.critical_items.map(item => <li key={item.id} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950"><strong>Item {item.id} · Resposta {item.response}</strong><p className="mt-1">{item.text}</p></li>)}</ul>}
        </section>
        {application.raw_payload.general_observations && <section className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="mb-3 font-semibold text-slate-900">Observações gerais</h2><p className="whitespace-pre-wrap text-sm text-slate-700">{application.raw_payload.general_observations}</p></section>}
      </div>
    </div>
  </main>
}
