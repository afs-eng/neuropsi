'use client'

import { Suspense, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Brain, Calculator, ChevronDown, ChevronRight, Eye, Info, Loader2, MessageSquare, Pencil, Save, Target, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { THCP_FIELDS, thcpErrorMessage, type THCPApplication, type THCPField, type THCPFormScores, type THCPNorm } from '@/types/tests/thcp'

interface EvaluationInfo {
  id: number
  patient_name: string
  start_date: string | null
}

const EMPTY_SCORES: THCPFormScores = { hpm: '', linguagem: '', pq: '', memoria: '', atencao_acertos: '', atencao_erros: '' }

const DOMAINS = [
  { key: 'hpm', shortLabel: 'HPM', label: 'Habilidades Percepto-Motoras (HPM)', max: THCP_FIELDS[0].max, icon: Pencil, tone: 'border-blue-200 bg-blue-50/60', iconTone: 'bg-blue-100 text-blue-700', barTone: 'bg-blue-500', trackTone: 'bg-blue-100' },
  { key: 'linguagem', shortLabel: 'Linguagem', label: 'Linguagem', max: THCP_FIELDS[1].max, icon: MessageSquare, tone: 'border-violet-200 bg-violet-50/60', iconTone: 'bg-violet-100 text-violet-700', barTone: 'bg-violet-500', trackTone: 'bg-violet-100' },
  { key: 'pq', shortLabel: 'Pensamento Quantitativo', label: 'Pensamento Quantitativo (PQ)', max: THCP_FIELDS[2].max, icon: Calculator, tone: 'border-emerald-200 bg-emerald-50/60', iconTone: 'bg-emerald-100 text-emerald-700', barTone: 'bg-emerald-500', trackTone: 'bg-emerald-100' },
  { key: 'memoria', shortLabel: 'Memória', label: 'Memória', max: THCP_FIELDS[3].max, icon: Brain, tone: 'border-rose-200 bg-rose-50/60', iconTone: 'bg-rose-100 text-rose-700', barTone: 'bg-rose-500', trackTone: 'bg-rose-100' },
  { key: 'atencao', shortLabel: 'Atenção', label: 'Atenção', max: THCP_FIELDS[4].max, icon: Target, tone: 'border-orange-200 bg-orange-50/60', iconTone: 'bg-orange-100 text-orange-700', barTone: 'bg-orange-500', trackTone: 'bg-orange-100' },
] as const

type Domain = typeof DOMAINS[number]

function validScore(scores: THCPFormScores, key: THCPField): number | null {
  const field = THCP_FIELDS.find(field => field.key === key)!
  const value = Number(scores[key])
  return scores[key] !== '' && Number.isInteger(value) && value >= 0 && value <= field.max ? value : null
}

function domainScore(scores: THCPFormScores, domain: Domain): number | null {
  if (domain.key !== 'atencao') return validScore(scores, domain.key)
  const hits = validScore(scores, 'atencao_acertos')
  const errors = validScore(scores, 'atencao_erros')
  return hits !== null && errors !== null ? Math.max(0, hits - errors) : null
}

function DomainIcon({ icon: Icon, className }: { icon: LucideIcon; className: string }) {
  return <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${className}`}><Icon className="h-5 w-5" aria-hidden="true" /></span>
}

function ScoreValue({ value, max }: { value: number | null; max: number }) {
  return <span className="whitespace-nowrap tabular-nums"><span className="font-bold">{value ?? '—'}</span><span className="ml-1 text-sm font-normal text-slate-600">/ {max}</span></span>
}

function DomainPanel({ domain, value, children, className = '' }: { domain: Domain; value: number | null; children: ReactNode; className?: string }) {
  return <section className={`min-w-0 overflow-hidden rounded-xl border bg-white ${domain.tone.split(' ')[0]} ${className}`} aria-labelledby={`${domain.key}-title`}>
    <div className={`flex items-center gap-3 border-b px-4 py-4 ${domain.tone}`}>
      <DomainIcon icon={domain.key === 'hpm' ? Eye : domain.icon} className={domain.iconTone} />
      <h2 id={`${domain.key}-title`} className="min-w-0 flex-1 text-sm font-semibold text-slate-900 sm:text-base">{domain.label}</h2>
      <span className="text-lg text-slate-900"><ScoreValue value={value} max={domain.max} /></span>
    </div>
    <div className="p-4 sm:p-5">{children}</div>
  </section>
}

function ScoreInput({ fieldKey, scores, onChange }: { fieldKey: THCPField; scores: THCPFormScores; onChange: (key: THCPField, value: string) => void }) {
  const field = THCP_FIELDS.find(field => field.key === fieldKey)!
  return <div className="space-y-2">
    <label htmlFor={field.key} className="text-sm font-medium text-slate-900">{field.key === 'atencao_acertos' ? 'Nº de acertos' : field.key === 'atencao_erros' ? 'Nº de erros' : 'Pontuação total'}</label>
    <div className="flex items-center gap-3">
      <Input id={field.key} name={field.key} autoComplete="off" aria-describedby={`${field.key}-hint`} type="number" min={0} max={field.max} step={1} required inputMode="numeric" className="h-12 max-w-32 border-slate-300 bg-white text-center text-lg tabular-nums" value={scores[field.key]} onChange={e => onChange(field.key, e.target.value)} />
      <span className="text-sm text-slate-500">/ {field.max}</span>
    </div>
    <p id={`${field.key}-hint`} className="text-xs leading-5 text-slate-600">{field.hint} Informe um inteiro de 0 a {field.max}.</p>
  </div>
}

function THCPForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const evaluationId = searchParams.get('evaluation_id')
  const applicationId = searchParams.get('application_id')
  const isEdit = searchParams.get('edit') === 'true'
  const [evaluation, setEvaluation] = useState<EvaluationInfo | null>(null)
  const [scores, setScores] = useState<THCPFormScores>(EMPTY_SCORES)
  const [norm, setNorm] = useState<THCPNorm>('idade')
  const [appliedOn, setAppliedOn] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [locked, setLocked] = useState(false)
  const [showInstructions, setShowInstructions] = useState(false)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const [application, initialEvaluation] = await Promise.all([
          applicationId ? api.get<THCPApplication>(`/api/tests/applications/${applicationId}`) : Promise.resolve(null),
          evaluationId ? api.get<EvaluationInfo>(`/api/evaluations/${evaluationId}`) : Promise.resolve(null),
        ])
        if (!active) return
        if (application && application.instrument_code !== 'thcp') throw new Error('A aplicação selecionada não é THCP.')
        if (application && evaluationId && application.evaluation_id !== Number(evaluationId)) throw new Error('A aplicação pertence a outra avaliação.')
        if (application?.is_validated && !isEdit) {
          router.replace(`/dashboard/tests/thcp/${applicationId}/result`)
          return
        }
        const data = initialEvaluation || (application ? await api.get<EvaluationInfo>(`/api/evaluations/${application.evaluation_id}`) : null)
        if (!active) return
        if (!data) throw new Error('Abra o THCP através de uma avaliação.')
        setEvaluation(data)
        setLocked(application?.status === 'locked')
        if (application) {
          const restored = { ...EMPTY_SCORES }
          for (const field of THCP_FIELDS) restored[field.key] = String(application.raw_payload[field.key] ?? '')
          setScores(restored)
          setNorm(application.raw_payload.norm_type || 'idade')
        }
        setAppliedOn(application?.applied_on || data.start_date || new Date().toLocaleDateString('en-CA'))
      } catch (err) {
        if (active) setError(thcpErrorMessage(err))
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [applicationId, evaluationId, isEdit, router])

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!evaluation || saving || locked) return
    setError('')
    for (const field of THCP_FIELDS) {
      const score = Number(scores[field.key])
      if (scores[field.key] === '' || !Number.isInteger(score) || score < 0 || score > field.max) {
        setError(`${field.label}: informe um inteiro entre 0 e ${field.max}.`)
        return
      }
    }
    setSaving(true)
    try {
      const rawScores = Object.fromEntries(THCP_FIELDS.map(field => [field.key, Number(scores[field.key])]))
      const result = await api.post<{ application_id: number }>('/api/tests/thcp/submit', {
        evaluation_id: evaluation.id,
        application_id: applicationId ? Number(applicationId) : null,
        applied_on: appliedOn,
        norm_type: norm,
        ...rawScores,
      })
      router.push(`/dashboard/tests/thcp/${result.application_id}/result`)
    } catch (err) {
      setError(thcpErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p role="status">Carregando THCP…</p>

  const values = DOMAINS.map(domain => domainScore(scores, domain))
  const total = values.every(value => value !== null) ? values.reduce<number>((sum, value) => sum + (value ?? 0), 0) : null
  const completed = THCP_FIELDS.filter(field => validScore(scores, field.key) !== null).length
  const backHref = evaluation ? `/dashboard/evaluations/${evaluation.id}?tab=overview` : '/dashboard'

  function changeScore(key: THCPField, value: string) {
    setScores(current => ({ ...current, [key]: value }))
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-0 pb-6 sm:px-4 lg:px-6">
      <nav aria-label="Navegação da correção" className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
        <Link className="inline-flex min-h-11 items-center gap-2 rounded hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600" href={backHref}><ArrowLeft className="h-4 w-4" aria-hidden="true" />Avaliação</Link>
        <ChevronRight className="h-3 w-3" aria-hidden="true" /><span>THCP</span><ChevronRight className="h-3 w-3" aria-hidden="true" /><span aria-current="page" className="font-medium text-slate-900">Correção</span>
      </nav>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">THCP</h1>
          <p className="mt-1 text-sm text-slate-600 sm:text-base">Correção do Teste de Habilidades e Conhecimento Pré-Alfabetização</p>
          {evaluation && <p className="mt-2 break-words text-sm font-medium text-slate-800">{evaluation.patient_name}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" className="min-h-11 gap-2 border-slate-200 bg-white" aria-expanded={showInstructions} aria-controls="thcp-instructions" onClick={() => setShowInstructions(current => !current)}><Info className="h-4 w-4" aria-hidden="true" />Orientações<ChevronDown className={`h-4 w-4 ${showInstructions ? 'rotate-180' : ''}`} aria-hidden="true" /></Button>
          <Button type="submit" form="thcp-correction" disabled={!evaluation || saving || locked} className="min-h-11 gap-2 bg-blue-700 px-5 hover:bg-blue-800">{saving ? <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" /> : <Save className="h-4 w-4" aria-hidden="true" />}{saving ? 'Corrigindo…' : 'Salvar correção'}</Button>
        </div>
      </header>
      <div id="thcp-instructions" hidden={!showInstructions} className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm leading-6 text-blue-900">
        Informe os totais corrigidos no protocolo. Em HPM, some os exercícios I (até 22 pontos) e II (até 8 pontos). A atenção é calculada como acertos − erros, com mínimo zero. Campos vazios não equivalem a zero. As normas e classificações serão aplicadas pelo sistema ao salvar.
      </div>
      {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">{error}</p>}
      {locked && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Esta aplicação está travada e não pode ser editada.</p>}
      {evaluation && <form id="thcp-correction" onSubmit={save} className="space-y-5" aria-busy={saving}>
        <section aria-label="Resumo das pontuações" className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
          {DOMAINS.map((domain, index) => <div key={domain.key} className={`rounded-xl border p-4 ${domain.tone} ${domain.key === 'atencao' ? 'col-span-2 sm:col-span-1' : ''}`}>
            <div className="flex items-center gap-3">
              <DomainIcon icon={domain.icon} className={domain.iconTone} />
              <div className="min-w-0"><h2 className="text-xs font-semibold leading-5 text-slate-900 sm:text-sm">{domain.shortLabel}</h2><div className="mt-1 text-2xl text-slate-900"><ScoreValue value={values[index]} max={domain.max} /></div></div>
            </div>
            <div className={`mt-4 h-1.5 overflow-hidden rounded-full ${domain.trackTone}`} aria-hidden="true"><div className={`h-full rounded-full ${domain.barTone}`} style={{ width: `${((values[index] ?? 0) / domain.max) * 100}%` }} /></div>
          </div>)}
        </section>
        <fieldset disabled={saving || locked} className="min-w-0 space-y-5">
          <legend className="sr-only">Dados e pontuações da correção THCP</legend>
          <section aria-labelledby="application-title" className="rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
            <div className="grid items-start gap-4 lg:grid-cols-[1fr_200px_240px]">
              <div><h2 id="application-title" className="text-sm font-semibold text-slate-900">Dados da aplicação</h2><p className="mt-2 max-w-lg text-xs leading-5 text-slate-600">A idade é calculada pela data de nascimento e de aplicação. Ambas as tabelas são restritas a crianças de 4 a 7 anos.</p></div>
              <div className="space-y-2"><label htmlFor="applied-on" className="text-sm font-medium text-slate-700">Data de aplicação</label><Input id="applied-on" name="applied_on" autoComplete="off" className="h-11 border-slate-300 bg-white" type="date" required value={appliedOn} onChange={e => setAppliedOn(e.target.value)} /></div>
              <div className="space-y-2"><label htmlFor="norm-type" className="text-sm font-medium text-slate-700">Tabela normativa</label><select id="norm-type" name="norm_type" className="h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:cursor-not-allowed disabled:opacity-50" value={norm} onChange={e => setNorm(e.target.value as THCPNorm)}><option value="idade">Idade (4 a 7 anos)</option><option value="geral">Amostra Geral</option></select></div>
            </div>
          </section>
          <DomainPanel domain={DOMAINS[0]} value={values[0]}>
            <div className="grid gap-5 md:grid-cols-[1fr_1fr]">
              <div className="space-y-4"><p className="text-sm leading-6 text-slate-600">Informe a soma dos dois exercícios, conforme a correção do protocolo.</p><ScoreInput fieldKey="hpm" scores={scores} onChange={changeScore} /></div>
              <div className="grid content-start gap-3 sm:grid-cols-2 md:border-l md:border-slate-100 md:pl-5">
                <div className="rounded-lg border border-blue-100 bg-blue-50/60 p-4"><h3 className="text-sm font-semibold text-blue-900">Exercício I</h3><p className="mt-1 text-xs leading-5 text-slate-600">Labirinto, cópia e figura complexa</p><p className="mt-3 text-sm font-medium text-blue-800">Até 22 pontos</p></div>
                <div className="rounded-lg border border-blue-100 bg-blue-50/60 p-4"><h3 className="text-sm font-semibold text-blue-900">Exercício II</h3><p className="mt-1 text-xs leading-5 text-slate-600">Pontuação corrigida no protocolo</p><p className="mt-3 text-sm font-medium text-blue-800">Até 8 pontos</p></div>
              </div>
            </div>
          </DomainPanel>
          <div className="grid items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
            <DomainPanel domain={DOMAINS[1]} value={values[1]}><ScoreInput fieldKey="linguagem" scores={scores} onChange={changeScore} /></DomainPanel>
            <DomainPanel domain={DOMAINS[2]} value={values[2]}><ScoreInput fieldKey="pq" scores={scores} onChange={changeScore} /></DomainPanel>
            <div className="space-y-4 md:col-span-2 xl:col-span-1">
              <DomainPanel domain={DOMAINS[3]} value={values[3]}><ScoreInput fieldKey="memoria" scores={scores} onChange={changeScore} /></DomainPanel>
              <DomainPanel domain={DOMAINS[4]} value={values[4]}>
                <div className="grid grid-cols-2 gap-3"><ScoreInput fieldKey="atencao_acertos" scores={scores} onChange={changeScore} /><ScoreInput fieldKey="atencao_erros" scores={scores} onChange={changeScore} /></div>
                <div className="mt-4 flex items-center justify-between gap-3 rounded-lg bg-orange-50 px-4 py-3"><div><p className="text-xs font-medium text-orange-900">Resultado da atenção</p><p className="mt-1 text-xs text-slate-600">Acertos − erros · mínimo zero</p></div><output htmlFor="atencao_acertos atencao_erros" className="text-xl text-slate-900"><ScoreValue value={values[4]} max={DOMAINS[4].max} /></output></div>
              </DomainPanel>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
            <div><p className="text-sm font-semibold text-slate-900">Escore bruto total <span className="ml-2 text-xl"><ScoreValue value={total} max={DOMAINS.reduce((sum, domain) => sum + domain.max, 0)} /></span></p><p className="mt-1 text-xs text-slate-600">{completed} de {THCP_FIELDS.length} campos preenchidos. Campos vazios não equivalem a zero.</p></div>
            <Button type="submit" className="min-h-11 gap-2 bg-blue-700 px-5 hover:bg-blue-800"><Save className="h-4 w-4" aria-hidden="true" />{saving ? 'Corrigindo…' : 'Salvar e corrigir THCP'}</Button>
          </div>
        </fieldset>
      </form>}
    </div>
  )
}

export default function THCPPage() {
  return <Suspense fallback={<p role="status">Carregando THCP…</p>}><THCPForm /></Suspense>
}
