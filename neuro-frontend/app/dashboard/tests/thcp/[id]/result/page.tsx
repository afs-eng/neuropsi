'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api, getToken, resolveApiUrl } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { formatThcpScore, thcpErrorMessage, type THCPApplication } from '@/types/tests/thcp'

export default function THCPResultPage() {
  const params = useParams<{ id: string }>()
  const [result, setResult] = useState<THCPApplication | null>(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    api.get<THCPApplication>(`/api/tests/thcp/result/${params.id}`)
      .then(data => { if (active) setResult(data) })
      .catch(err => { if (active) setError(thcpErrorMessage(err)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [params.id])

  async function exportPdf() {
    setExporting(true)
    setError('')
    try {
      const token = getToken()
      const response = await fetch(resolveApiUrl(`/api/tests/applications/${params.id}/export-pdf`), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        cache: 'no-store',
      })
      if (!response.ok) throw new Error(`Não foi possível gerar o PDF (${response.status}).`)
      const url = URL.createObjectURL(await response.blob())
      const link = document.createElement('a')
      link.href = url
      link.download = `THCP-${params.id}.pdf`
      link.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (err) {
      setError(thcpErrorMessage(err))
    } finally {
      setExporting(false)
    }
  }

  if (loading) return <p role="status">Carregando resultado...</p>
  if (!result) return <p role="alert">{error || 'Resultado não encontrado.'}</p>
  const rows = result.classified_payload.results || []

  return <div className="mx-auto max-w-7xl space-y-6">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div><h1 className="text-2xl font-semibold text-slate-900">THCP — Resultado</h1><p className="mt-2 text-slate-600">{result.patient_name} · {result.computed_payload.age} anos · Norma: {result.computed_payload.norm_label}</p><p className="text-sm text-slate-500">Aplicação: {result.applied_on?.split('-').reverse().join('/') || '—'}</p></div>
      <nav aria-label="Ações do resultado" className="flex flex-wrap items-center gap-4">
        {result.status !== 'locked' && <Link className="text-sm underline" href={`/dashboard/tests/thcp?application_id=${params.id}&edit=true`}>Editar</Link>}
        <Button onClick={exportPdf} disabled={exporting}>{exporting ? 'Gerando PDF...' : 'Baixar PDF'}</Button>
        <Link className="text-sm underline" href={`/dashboard/evaluations/${result.evaluation_id}?tab=overview`}>Voltar à avaliação</Link>
      </nav>
    </header>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800">{error}</p>}
    {(result.classified_payload.warnings || []).map(warning => <p key={warning} className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{warning}</p>)}
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="text-lg font-semibold">Resultados detalhados</h2>
      <p className="my-3 text-sm text-slate-600">A classificação do manual difere da classificação por Z-score. Percentis estimados não são os quartis do manual. “—” indica métrica indisponível.</p>
      <div className="overflow-x-auto"><table className="w-full text-sm">
        <caption className="sr-only">Escores e classificações do THCP</caption>
        <thead className="bg-slate-50 text-left"><tr>{['Escala', 'Bruto', 'T-score', 'Z-score', 'Ponderado', 'Manual / faixa percentil', 'Percentil estimado', 'Classificação Z'].map(label => <th key={label} scope="col" className="px-3 py-3">{label}</th>)}</tr></thead>
        <tbody>{rows.map(row => <tr key={row.code} className="border-b border-slate-100">
          <th scope="row" className="px-3 py-4 text-left font-medium">{row.label}</th>
          <td className="px-3 py-4">{row.raw_score}/{row.max_score}</td><td className="px-3 py-4 whitespace-nowrap">{formatThcpScore(row.t_score)}</td>
          <td className="px-3 py-4">{formatThcpScore(row.z_score)}</td><td className="px-3 py-4">{formatThcpScore(row.weighted_score)}</td>
          <td className="px-3 py-4">{row.manual_classification || '—'} / {row.manual_percentile_band || '—'}</td>
          <td className="px-3 py-4">{formatThcpScore(row.percentile)}</td><td className="px-3 py-4">{row.classification || 'Indisponível'}</td>
        </tr>)}</tbody>
      </table></div>
    </section>
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <h2 className="mb-4 text-lg font-semibold">Perfil de percentis estimados (0–100)</h2>
      <div className="space-y-4">{rows.map(row => <div key={row.code} className="grid gap-2 sm:grid-cols-[220px_1fr_70px] sm:items-center">
        <span className="text-sm">{row.label}</span><div className="h-3 rounded bg-slate-100" aria-hidden="true">{row.percentile !== null && <div className="h-3 rounded bg-cyan-700" style={{ width: `${row.percentile}%` }} />}</div><span className="text-sm tabular-nums">{formatThcpScore(row.percentile)}</span>
      </div>)}</div>
    </section>
    <section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="mb-4 text-lg font-semibold">Interpretação</h2><p className="whitespace-pre-line text-sm leading-7 text-slate-700">{result.interpretation_text}</p></section>
    <section className="rounded-2xl border border-slate-200 bg-white p-5"><h2 className="mb-3 text-lg font-semibold">Notas técnicas</h2><ul className="list-inside list-disc space-y-2 text-sm text-slate-600">{(result.report_payload.technical_notes || []).map(note => <li key={note}>{note}</li>)}</ul></section>
  </div>
}
