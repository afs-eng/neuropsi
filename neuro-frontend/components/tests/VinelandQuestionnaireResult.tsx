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
  clinical_review?: { eligible: boolean; validated: boolean; reason: string; fingerprint?: string; reviewer?: { name: string; crp: string }; reviewed_at?: string; clinical_note?: string } | null
  raw_payload: {
    form?: string
    form_level?: string
    entry_mode?: string
    respondent?: string
    birth_date?: string
    item_protocol_id?: string
    completion_status?: string
    general_observations?: string
    item_summary?: VinelandItemSummary
    item_responses?: Record<string, Record<string, { response: string; estimated?: boolean; observation?: string }>>
  }
}

export function VinelandQuestionnaireResult({ application }: { application: VinelandResultApplication }) {
  const [exportingPdf, setExportingPdf] = useState(false)
  const [pdfError, setPdfError] = useState('')
  const [review, setReview] = useState(application.clinical_review)
  const [reviewNote, setReviewNote] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [reviewing, setReviewing] = useState(false)
  const [reviewError, setReviewError] = useState('')
  const totals = application.raw_payload.entry_mode === 'totals' || application.normative_results?.form_level === 'extensivo' || Boolean(application.raw_payload.form && application.raw_payload.form_level !== 'niveis_dominio' && application.raw_payload.entry_mode !== 'items')
  const summary = application.raw_payload.item_summary || { sections: [], critical_items: [], answered: 0, applied_total: 0 }
  const adaptive = summary.sections.filter(section => section.kind === 'adaptive')
  const behavior = summary.sections.filter(section => section.kind === 'behavior')
  const critical = summary.sections.find(section => section.kind === 'critical')
  const evaluationUrl = `/dashboard/evaluations/${application.evaluation_id}/overview`
  const editUrl = `/dashboard/tests/vineland?evaluation_id=${application.evaluation_id}&application_id=${application.id}&edit=true`
  const historicalNotes = Object.entries(application.raw_payload.item_responses || {}).flatMap(([section, items]) =>
    Object.entries(items).filter(([, item]) => item.estimated || item.observation?.trim()).map(([id, item]) => ({ section, id, ...item })))

  async function revokeReview() {
    if (reviewing || !window.confirm('Retirar a validação para novos laudos? Laudos já finalizados não serão alterados.')) return
    setReviewing(true)
    setReviewError('')
    try {
      const token = getToken()
      const response = await fetch(resolveApiUrl(`/api/tests/vineland3/applications/${application.id}/review/revoke`), {
        method: 'POST', headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.message || 'Não foi possível retirar a validação.')
      setReview(data.clinical_review)
      setConfirmed(false)
    } catch (error) {
      setReviewError(error instanceof Error ? error.message : 'Não foi possível retirar a validação.')
    } finally { setReviewing(false) }
  }

  async function validateReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (reviewing || !confirmed || !review?.fingerprint) return
    setReviewing(true)
    setReviewError('')
    try {
      const token = getToken()
      const response = await fetch(resolveApiUrl(`/api/tests/vineland3/applications/${application.id}/review`), {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ fingerprint: review.fingerprint, confirmed: true, clinical_note: reviewNote.trim() }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.message || 'Não foi possível registrar a revisão.')
      setReview(data.clinical_review)
    } catch (error) {
      setReviewError(error instanceof Error ? error.message : 'Não foi possível registrar a revisão. Reabra o resultado e tente novamente.')
    } finally { setReviewing(false) }
  }

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
            <p className="mt-1 text-sm text-zinc-600">{application.patient_name} · {application.normative_results?.form_label || (totals ? `${application.raw_payload.form || 'Informante'} — ${application.raw_payload.form_level === 'niveis_dominio' ? 'Níveis de Domínio' : 'Extensivo'}` : 'Pais/Cuidadores — Níveis de Domínio')}</p>
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
          <p className="mt-4 font-medium text-slate-800">{totals ? 'Entrada por totais do protocolo. Não contém respostas item a item.' : `Preenchimento finalizado · ${summary.answered} de ${summary.applied_total} itens das seções aplicadas respondidos.`}</p>
        </section>
        {totals && <p className="rounded-xl border border-cyan-200 bg-cyan-50 p-4 text-sm">O questionário Pais/Cuidadores — Níveis de Domínio exige uma aplicação separada, sem copiar ou substituir este lançamento. <Link className="underline" href={`/dashboard/tests/vineland?evaluation_id=${application.evaluation_id}`}>Abrir formulário de 180 perguntas</Link></p>}
        {application.normative_results ? <VinelandNormativeResults result={application.normative_results} /> : totals ? <p role="alert">Correção normativa indisponível. Reabra os resultados ou confira as datas e os totais; cálculos antigos não são exibidos.</p> : <>
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
          {totals ? <p className="text-sm">Itens críticos não registrados neste lançamento por totais. Confira-os individualmente no protocolo original; não é possível inferir ausência de comportamentos críticos.</p> : !critical?.applied ? <p className="text-sm">Seção não aplicada.</p> : summary.critical_items.length === 0 ? <p className="text-sm">Nenhum item com resposta 1 ou 2 nesta seção.</p> :
            <ul className="space-y-3">{summary.critical_items.map(item => <li key={item.id} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950"><strong>Item {item.id} · Resposta {item.response}</strong><p className="mt-1">{item.text}</p></li>)}</ul>}
        </section>
        {application.raw_payload.general_observations && <section className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="mb-3 font-semibold text-slate-900">Observações gerais</h2><p className="whitespace-pre-wrap text-sm text-slate-700">{application.raw_payload.general_observations}</p></section>}
        {review && <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-5" aria-labelledby="vineland-review">
          <h2 id="vineland-review" className="font-semibold">Revisão profissional para o laudo</h2>
          <p role="status" className="text-sm">{review.reason}</p>
          {historicalNotes.length > 0 && <details className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm"><summary className="cursor-pointer font-medium">Estimativas e observações históricas por item ({historicalNotes.length})</summary><ul className="mt-3 space-y-2">{historicalNotes.map(item => <li key={`${item.section}-${item.id}`}><strong>{summary.sections.find(section => section.code === item.section)?.label || item.section} · Item {item.id}</strong> · Resposta {item.response || 'não preenchida'}{item.estimated ? ' · Estimativa registrada' : ''}{item.observation && <p className="whitespace-pre-wrap">{item.observation}</p>}</li>)}</ul></details>}
          {review.validated ? <div className="space-y-2 text-sm"><p>Revisado por {review.reviewer?.name}{review.reviewer?.crp ? ` · CRP ${review.reviewer.crp}` : ''}{review.reviewed_at ? ` · ${new Date(review.reviewed_at).toLocaleString('pt-BR')}` : ''}.</p><p className="whitespace-pre-wrap">{review.clinical_note}</p>{application.status !== 'locked' && <button type="button" disabled={reviewing} onClick={revokeReview} className="rounded-lg border border-red-200 px-4 py-3 text-red-800 print:hidden">Retirar validação</button>}</div> : review.eligible && application.status !== 'locked' ? <form onSubmit={validateReview} className="space-y-3 print:hidden">
            <p className="text-sm text-slate-600">Apenas profissionais autorizados podem validar. Confira respostas, datas, estimativas históricas, itens críticos e aplicabilidade das normas americanas. Alterações exigem nova revisão.</p>
            <label className="block text-sm font-medium" htmlFor="vineland-review-note">Nota da revisão profissional</label>
            <textarea id="vineland-review-note" required minLength={10} maxLength={10000} disabled={reviewing} value={reviewNote} onChange={event => setReviewNote(event.target.value)} className="w-full rounded-lg border border-slate-300 p-3 text-sm" rows={4} />
            <label className="flex items-start gap-3 text-sm"><input type="checkbox" checked={confirmed} disabled={reviewing} onChange={event => setConfirmed(event.target.checked)} className="mt-1" />Conferi os resultados e os itens críticos e autorizo sua inclusão no laudo, sem atribuição automática de diagnóstico.</label>
            <button type="submit" disabled={reviewing || !confirmed || reviewNote.trim().length < 10} aria-busy={reviewing} className="rounded-full bg-blue-800 px-5 py-3 text-sm font-medium text-white disabled:opacity-50">{reviewing ? 'Registrando revisão…' : 'Validar para inclusão no laudo'}</button>
          </form> : null}
          {reviewError && <p role="alert" className="text-sm text-red-800">{reviewError}</p>}
        </section>}
      </div>
    </div>
  </main>
}
