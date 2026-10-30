'use client'

import { Suspense, useEffect, useState, type FormEvent } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { VinelandItemFields, type VinelandItemProtocol, type VinelandItemResponses } from '@/components/tests/VinelandItemFields'

type FormCode = 'entrevista' | 'pais_cuidadores' | 'professores'
interface Scale { code: string; label: string; max: number; optional: boolean; min_months: number; max_months: number | null }
interface Protocol { forms: Record<FormCode, { label: string; scales: Scale[] }>; technical_notes: string[]; item_protocol: VinelandItemProtocol }
interface Evaluation { id: number; patient_name: string; patient_birth_date: string | null; start_date: string | null }
interface Subdomain { scale: string; label: string; raw_score: number; v_scale: number }
interface Domain { scale: string; label: string; standard_score: number; percentile: string }
interface Application {
  id: number; evaluation_id: number; instrument_code: string; status: string; is_validated: boolean; applied_on: string | null
  raw_payload: { form?: FormCode; respondent?: string; raw_scores?: Record<string, number>; entry_mode?: 'totals' | 'items'; item_responses?: VinelandItemResponses }
  computed_payload: { domains?: Domain[]; subdomains?: Subdomain[]; form_label?: string; respondent?: string; age_months?: number; norm_source?: { file: string; subdomain_pages: number[]; domain_pages: number[] } }
  interpretation_text: string
}

function errorMessage(error: unknown) {
  return error && typeof error === 'object' && 'message' in error ? String(error.message) : 'Não foi possível carregar ou salvar o Vineland-3.'
}

function completedMonths(birth: string | null | undefined, applied: string) {
  if (!birth || !applied || applied < birth) return -1
  const [by, bm, bd] = birth.split('-').map(Number)
  const [ay, am, ad] = applied.split('-').map(Number)
  const anniversaryDay = Math.min(bd, new Date(ay, am, 0).getDate())
  return (ay - by) * 12 + am - bm - (ad < anniversaryDay ? 1 : 0)
}

function Vineland3Form() {
  const router = useRouter()
  const params = useSearchParams()
  const evaluationId = params.get('evaluation_id')
  const applicationId = params.get('application_id')
  const isEdit = params.get('edit') === 'true'
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [application, setApplication] = useState<Application | null>(null)
  const [protocol, setProtocol] = useState<Protocol | null>(null)
  const [form, setForm] = useState<FormCode>('entrevista')
  const [respondent, setRespondent] = useState('')
  const [appliedOn, setAppliedOn] = useState('')
  const [scores, setScores] = useState<Record<string, string>>({})
  const [entryMode, setEntryMode] = useState<'totals' | 'items'>('items')
  const [itemResponses, setItemResponses] = useState<VinelandItemResponses>({})
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const [definitions, existing, initialEvaluation] = await Promise.all([
          api.get<Protocol>('/api/tests/vineland3/protocol'),
          applicationId ? api.get<Application>(`/api/tests/applications/${applicationId}`) : Promise.resolve(null),
          evaluationId ? api.get<Evaluation>(`/api/evaluations/${evaluationId}`) : Promise.resolve(null),
        ])
        if (existing && existing.instrument_code !== 'vineland3') throw new Error('Esta aplicação não é Vineland-3.')
        if (existing && evaluationId && existing.evaluation_id !== Number(evaluationId)) throw new Error('Aplicação de outra avaliação.')
        const data = initialEvaluation || (existing ? await api.get<Evaluation>(`/api/evaluations/${existing.evaluation_id}`) : null)
        if (!data) throw new Error('Abra o Vineland-3 a partir de uma avaliação.')
        if (!active) return
        setProtocol(definitions)
        setEvaluation(data)
        setApplication(existing)
        setEntryMode(existing?.raw_payload.entry_mode || (existing ? 'totals' : 'items'))
        setItemResponses(existing?.raw_payload.item_responses || {})
        setForm(existing?.raw_payload.form || 'entrevista')
        setRespondent(existing?.raw_payload.respondent || '')
        setScores(Object.fromEntries(Object.entries(existing?.raw_payload.raw_scores || {}).map(([key, value]) => [key, String(value)])))
        setAppliedOn(existing?.applied_on || data.start_date || new Date().toLocaleDateString('en-CA'))
      } catch (err) {
        if (active) setError(errorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [applicationId, evaluationId, isEdit])

  const months = completedMonths(evaluation?.patient_birth_date, appliedOn)
  const activeScales = protocol?.forms[form].scales.filter(scale => months >= scale.min_months && (scale.max_months === null || months <= scale.max_months)) || []
  const locked = application?.status === 'locked'
  const viewResult = Boolean(application?.computed_payload.domains?.length && !isEdit)

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!evaluation || saving || locked) return
    setError('')
    setSuccess('')
    const raw: Record<string, number> = {}
    for (const scale of entryMode === 'totals' ? activeScales : []) {
      const value = scores[scale.code] || ''
      if (scale.optional && value === '') continue
      if (value === '' || !Number.isInteger(Number(value)) || Number(value) < 0 || Number(value) > scale.max) {
        setError(`${scale.label}: informe um inteiro entre 0 e ${scale.max}.`)
        return
      }
      raw[scale.code] = Number(value)
    }
    if (entryMode === 'items' && Object.values(itemResponses).some(items => Object.values(items).some(item => item.response !== '' && !/^[210ND]$/.test(item.response)))) {
      setError('Há respostas inválidas. Digite somente 2, 1, 0, N ou D em todos os domínios.')
      return
    }
    setSaving(true)
    try {
      const result = await api.post<Application & { application_id: number }>('/api/tests/vineland3/submit', {
        evaluation_id: evaluation.id, application_id: applicationId ? Number(applicationId) : null,
        applied_on: appliedOn, form: entryMode === 'totals' ? form : null, respondent, entry_mode: entryMode, raw_scores: raw,
        ...(entryMode === 'items' ? { item_protocol_id: protocol?.item_protocol.id, item_responses: itemResponses } : {}),
      })
      setApplication(result)
      setSuccess(entryMode === 'items' ? 'Registro parcial salvo. Respostas e observações preservadas; sem cálculo normativo ou laudo.' : 'Pontuações salvas para revisão.')
      router.replace(`/dashboard/tests/vineland3?evaluation_id=${evaluation.id}&application_id=${result.application_id}`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p role="status" className="p-8">Carregando Vineland-3…</p>
  return <main className="mx-auto max-w-5xl space-y-6 p-4 sm:p-8">
    <Link className="text-sm text-cyan-800 underline" href={evaluation ? `/dashboard/evaluations/${evaluation.id}/overview` : '/dashboard/evaluations'}>Voltar à avaliação</Link>
    <header><h1 className="text-2xl font-semibold text-slate-900">{!viewResult && entryMode === 'items' ? 'Vineland · Registro item a item' : `Vineland-3 · ${viewResult ? 'Resultados' : 'Correção'}`}</h1><p className="mt-2 text-slate-600">{evaluation?.patient_name}</p></header>
    {error && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error}</p>}
    {success && <p role="status" className="rounded-lg border border-green-200 bg-green-50 p-4 text-green-900">{success}</p>}
    <aside className="space-y-2 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
      {entryMode === 'items' ? <p><strong>Banco parcial · edição não confirmada.</strong> Respostas e observações para conferência, sem escores ou interpretação clínica automática.</p> : <p><strong>Normas americanas.</strong> Correção quantitativa por pontuações brutas, com revisão clínica obrigatória.</p>}
      <p>Item a item: registro do banco parcial fornecido, com edição não confirmada e sem conversão normativa. Classificação qualitativa ainda não habilitada.</p>
    </aside>
    {viewResult && application ? <>
      <section className="space-y-3 rounded-xl border bg-white p-5">
        <h2 className="text-lg font-semibold">{application.computed_payload.form_label}</h2>
        <p>Respondente: {application.computed_payload.respondent} · Aplicação: {application.applied_on}</p>
        <p>Idade: {Math.floor((application.computed_payload.age_months || 0) / 12)} anos e {(application.computed_payload.age_months || 0) % 12} meses.</p>
        <p className="font-medium">{application.is_validated ? 'Revisado pelo profissional.' : 'Aguardando revisão clínica; ainda não incluído no laudo.'}</p>
        {!locked && <Link className="inline-block text-cyan-800 underline" href={`/dashboard/tests/vineland3?evaluation_id=${evaluation?.id}&application_id=${application.id}&edit=true`}>Editar lançamento</Link>}
      </section>
      <section className="overflow-x-auto rounded-xl border bg-white p-5">
        <h2 className="mb-4 text-lg font-semibold">Subdomínios</h2>
        <table className="w-full text-left text-sm"><thead><tr><th scope="col" className="p-2">Subdomínio</th><th scope="col" className="p-2">Bruto</th><th scope="col" className="p-2">Escala-v</th></tr></thead>
          <tbody>{application.computed_payload.subdomains?.map(row => <tr key={row.scale} className="border-t"><th scope="row" className="p-2 font-normal">{row.label}</th><td className="p-2">{row.raw_score}</td><td className="p-2">{row.v_scale}</td></tr>)}</tbody></table>
      </section>
      <section className="space-y-4 rounded-xl border bg-white p-5">
        <h2 className="text-lg font-semibold">Domínios e CCA · escores padrão</h2>
        <p className="text-sm text-slate-600">Escala do gráfico: 0–140. Tabela normativa: 20–140. Não comparar diretamente com escala-v.</p>
        {application.computed_payload.domains?.map(row => <div key={row.scale}>
          <div className="mb-1 flex justify-between gap-4 text-sm"><span>{row.label}</span><span className="shrink-0 font-semibold">{row.standard_score} · Percentil {row.percentile}</span></div>
          <div aria-hidden="true" className="h-3 bg-slate-100"><div className="h-3 bg-cyan-700" style={{ width: `${row.standard_score / 140 * 100}%` }} /></div>
        </div>)}
      </section>
      <section className="rounded-xl border bg-white p-5"><h2 className="mb-3 text-lg font-semibold">Síntese quantitativa</h2><p className="whitespace-pre-line leading-7">{application.interpretation_text}</p></section>
      <p className="text-sm text-slate-600">Fonte: {application.computed_payload.norm_source?.file}; páginas PDF: {application.computed_payload.norm_source?.subdomain_pages.join(', ')} (subdomínios), {application.computed_payload.norm_source?.domain_pages.join(', ')} (domínios).</p>
    </> : evaluation && protocol ? <form onSubmit={save} className="space-y-6">
      <fieldset disabled={saving || locked} className="space-y-5 rounded-xl border bg-white p-5">
        <legend className="px-2 font-semibold">Identificação do protocolo</legend>
        {locked && <p role="status">Aplicação travada para edição.</p>}
        <div><label htmlFor="vineland-entry-mode" className="mb-2 block text-sm font-medium">Modo de entrada</label>
          <select id="vineland-entry-mode" disabled={Boolean(application)} className="h-12 w-full rounded-md border border-slate-300 px-3" value={entryMode} onChange={event => { setEntryMode(event.target.value as 'totals' | 'items'); setSuccess('') }}>
            <option value="items">Item a item — banco parcial, edição não confirmada (somente registro)</option>
            <option value="totals">Pontuações brutas — correção normativa Vineland-3</option>
          </select>
          {application && <p className="mt-1 text-xs text-slate-600">Para usar outro modo, crie uma aplicação separada e preserve o registro original.</p>}
        </div>
        {entryMode === 'totals' && <div><label htmlFor="vineland-form" className="mb-2 block text-sm font-medium">Formulário extensivo</label>
          <select id="vineland-form" className="h-12 w-full rounded-md border border-slate-300 px-3" value={form} onChange={event => {
            if (Object.keys(scores).length && !window.confirm('Trocar o formulário limpará as pontuações lançadas. Continuar?')) return
            setForm(event.target.value as FormCode); setScores({})
          }}>{Object.entries(protocol.forms).map(([code, definition]) => <option key={code} value={code}>{definition.label}</option>)}</select></div>}
        <div><label htmlFor="vineland-respondent" className="mb-2 block text-sm font-medium">Nome do respondente</label><Input id="vineland-respondent" required maxLength={200} value={respondent} onChange={event => setRespondent(event.target.value)} /></div>
        <div><label htmlFor="vineland-date" className="mb-2 block text-sm font-medium">Data da aplicação</label><Input id="vineland-date" type="date" required value={appliedOn} onChange={event => setAppliedOn(event.target.value)} /></div>
      </fieldset>
      {entryMode === 'items' ? <VinelandItemFields protocol={protocol.item_protocol} responses={itemResponses} onChange={responses => { setItemResponses(responses); setSuccess('') }} disabled={saving || locked} /> : <fieldset disabled={saving || locked} className="space-y-4 rounded-xl border bg-white p-5">
        <legend className="px-2 font-semibold">Pontuações brutas por subdomínio</legend>
        <p className="text-sm text-slate-600">Use os totais corrigidos no protocolo. Campos vazios não são zero. Motor é opcional; se utilizado, preencha os dois subdomínios.</p>
        {activeScales.length === 0 && <p role="status" className="text-amber-900">Verifique a data de nascimento e aplicação. Professores possui normas dos 3 anos aos 18 anos e 11 meses.</p>}
        <div className="grid gap-4 sm:grid-cols-2">{activeScales.map(scale => <div key={scale.code}>
          <label htmlFor={`vineland-${scale.code}`} className="mb-2 block text-sm font-medium">{scale.label}{scale.optional ? ' (opcional)' : ''}</label>
          <Input id={`vineland-${scale.code}`} type="number" min={0} max={scale.max} step={1} required={!scale.optional} inputMode="numeric" value={scores[scale.code] ?? ''} onChange={event => setScores(previous => ({ ...previous, [scale.code]: event.target.value }))} aria-describedby={`vineland-${scale.code}-hint`} />
          <p id={`vineland-${scale.code}-hint`} className="mt-1 text-xs text-slate-600">De 0 a {scale.max}.</p>
        </div>)}</div>
      </fieldset>}
      <Button type="submit" disabled={saving || locked || (entryMode === 'totals' && activeScales.length === 0)}>{saving ? 'Salvando…' : entryMode === 'items' ? 'Salvar registro parcial (sem cálculo)' : 'Calcular e salvar para revisão'}</Button>
    </form> : null}
    <details className="rounded-lg border p-4 text-sm"><summary className="cursor-pointer font-medium">Notas técnicas e limitações</summary><ul className="mt-3 list-disc space-y-2 pl-5">{protocol?.technical_notes.map(note => <li key={note}>{note}</li>)}</ul></details>
  </main>
}

export default function Vineland3Page() {
  return <Suspense fallback={<p role="status">Carregando Vineland-3…</p>}><Vineland3Form /></Suspense>
}
