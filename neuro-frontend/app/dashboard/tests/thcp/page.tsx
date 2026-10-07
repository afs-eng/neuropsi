'use client'

import { Suspense, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Brain, Calculator, ChevronDown, ChevronRight, ClipboardList, Info, Loader2, MessageSquare, Pencil, RotateCcw, Save, ShieldCheck, Target, type LucideIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { THCPGroupFields } from '@/components/tests/THCPProtocolFields'
import { restoreTHCPItems, serializeTHCPItems, thcpGroupTotal, thcpItemScores, validTHCPItem, type THCPGroup, type THCPItemForm, type THCPProtocol } from '@/lib/thcp-protocol'
import { THCP_FIELDS, thcpErrorMessage, type THCPApplication, type THCPField, type THCPFormScores, type THCPNorm } from '@/types/tests/thcp'

interface EvaluationInfo {
  id: number
  patient_name: string
  start_date: string | null
}

const EMPTY_SCORES: THCPFormScores = { hpm: '', linguagem: '', pq: '', memoria: '', atencao_acertos: '', atencao_erros: '' }

const DOMAINS = [
  { key: 'hpm', shortLabel: 'HPM', label: 'Habilidades Percepto-Motoras (HPM)', max: THCP_FIELDS[0].max, icon: Pencil, tone: 'bg-indigo-50 text-indigo-800', iconTone: 'bg-indigo-100 text-indigo-700' },
  { key: 'linguagem', shortLabel: 'Linguagem', label: 'Linguagem', max: THCP_FIELDS[1].max, icon: MessageSquare, tone: 'bg-emerald-50 text-emerald-900', iconTone: 'bg-emerald-100 text-emerald-700' },
  { key: 'pq', shortLabel: 'Pensamento Quantitativo', label: 'Pensamento Quantitativo (PQ)', max: THCP_FIELDS[2].max, icon: Calculator, tone: 'bg-amber-50 text-amber-900', iconTone: 'bg-amber-100 text-amber-700' },
  { key: 'memoria', shortLabel: 'Memória', label: 'Memória', max: THCP_FIELDS[3].max, icon: Brain, tone: 'bg-sky-50 text-sky-900', iconTone: 'bg-sky-100 text-sky-700' },
  { key: 'atencao', shortLabel: 'Atenção', label: 'Atenção', max: THCP_FIELDS[4].max, icon: Target, tone: 'bg-rose-50 text-rose-900', iconTone: 'bg-rose-100 text-rose-700' },
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
  return <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${className}`}><Icon className="h-4 w-4" aria-hidden="true" /></span>
}

function ScoreValue({ value, max }: { value: number | null; max: number }) {
  return <span className="whitespace-nowrap tabular-nums"><span className="font-bold">{value ?? '—'}</span><span className="ml-1 text-sm font-normal text-slate-600">/ {max}</span></span>
}

function DomainPanel({ domain, value, children, title, maximum, progress, id = domain.key }: { domain: Domain; value: number | null; children: ReactNode; title?: string; maximum?: number; progress?: string; id?: string }) {
  return <section className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby={`${id}-title`}>
    <div className={`flex flex-wrap items-center gap-2 border-b border-slate-100 px-3 py-3 ${domain.tone}`}>
      <DomainIcon icon={domain.icon} className={domain.iconTone} />
      <h2 id={`${id}-title`} className="min-w-0 flex-1 text-sm font-semibold">{title || domain.label}</h2>
      <div className="text-right"><span className="text-base text-slate-900"><ScoreValue value={value} max={maximum ?? domain.max} /></span>{progress && <p className="mt-0.5 text-[10px] text-slate-500">{progress} itens</p>}</div>
    </div>
    <div className="px-3 py-2">{children}</div>
  </section>
}

const GROUP_PANELS: Record<THCPGroup, { domain: Domain; title: string }> = {
  hpm_i: { domain: DOMAINS[0], title: 'HPM · Exercício I' },
  hpm_ii: { domain: DOMAINS[0], title: 'HPM · Exercício II' },
  linguagem: { domain: DOMAINS[1], title: 'Linguagem' },
  memoria: { domain: DOMAINS[3], title: 'Memória' },
  pq: { domain: DOMAINS[2], title: 'Pensamento Quantitativo (PQ)' },
}

function ProtocolPanel({ group, protocol, items, onChange }: { group: THCPGroup; protocol: THCPProtocol; items: THCPItemForm; onChange: (group: THCPGroup, key: string, field: 'answer' | 'score', value: string) => void }) {
  const definitions = protocol[group]
  const completed = definitions.filter(item => validTHCPItem(item, items[group]?.[item.key])).length
  return <DomainPanel id={group} domain={GROUP_PANELS[group].domain} title={GROUP_PANELS[group].title} value={thcpGroupTotal(protocol, items, group)} maximum={definitions.reduce((sum, item) => sum + item.max_score, 0)} progress={`${completed}/${definitions.length}`}>
    <THCPGroupFields group={group} protocol={protocol} items={items} onChange={onChange} />
  </DomainPanel>
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
  const [protocol, setProtocol] = useState<THCPProtocol | null>(null)
  const [items, setItems] = useState<THCPItemForm>({})
  const [entryMode, setEntryMode] = useState<'items' | 'totals'>('items')
  const [legacyApplication, setLegacyApplication] = useState(false)
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
        const [application, initialEvaluation, definitions] = await Promise.all([
          applicationId ? api.get<THCPApplication>(`/api/tests/applications/${applicationId}`) : Promise.resolve(null),
          evaluationId ? api.get<EvaluationInfo>(`/api/evaluations/${evaluationId}`) : Promise.resolve(null),
          api.get<THCPProtocol>('/api/tests/thcp/protocol'),
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
        setProtocol(definitions)
        setItems(application?.raw_payload.item_responses ? restoreTHCPItems(application.raw_payload.item_responses) : {})
        setLegacyApplication(Boolean(application && !application.raw_payload.item_responses))
        setEntryMode(application && !application.raw_payload.item_responses ? 'totals' : 'items')
        setScores(EMPTY_SCORES)
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

  const effectiveScores = protocol && entryMode === 'items' ? thcpItemScores(protocol, items, scores) : scores

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!evaluation || saving || locked) return
    setError('')
    if (entryMode === 'items') {
      if (!protocol) return
      for (const [group, definitions] of Object.entries(protocol)) {
        const missing = definitions.find(item => !validTHCPItem(item, items[group as THCPGroup]?.[item.key]))
        if (missing) {
          setError(`${GROUP_PANELS[group as THCPGroup].title}, ${missing.label}: informe uma nota inteira entre 0 e ${missing.max_score}.`)
          document.getElementById(`thcp-${group}-${missing.key}-score`)?.focus()
          return
        }
      }
    }
    for (const field of THCP_FIELDS) {
      const score = Number(effectiveScores[field.key])
      if (effectiveScores[field.key] === '' || !Number.isInteger(score) || score < 0 || score > field.max) {
        setError(`${field.label}: informe um inteiro entre 0 e ${field.max}.`)
        return
      }
    }
    setSaving(true)
    try {
      const rawScores = Object.fromEntries(THCP_FIELDS.map(field => [field.key, Number(effectiveScores[field.key])]))
      const result = await api.post<{ application_id: number }>('/api/tests/thcp/submit', {
        evaluation_id: evaluation.id,
        application_id: applicationId ? Number(applicationId) : null,
        applied_on: appliedOn,
        norm_type: norm,
        ...rawScores,
        item_responses: entryMode === 'items' && protocol ? serializeTHCPItems(protocol, items) : null,
      })
      router.push(`/dashboard/tests/thcp/${result.application_id}/result`)
    } catch (err) {
      setError(thcpErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p role="status">Carregando THCP…</p>

  const values = DOMAINS.map(domain => domainScore(effectiveScores, domain))
  const total = values.every(value => value !== null) ? values.reduce<number>((sum, value) => sum + (value ?? 0), 0) : null
  const itemCount = protocol ? Object.values(protocol).reduce((sum, definitions) => sum + definitions.length, 0) : 0
  const completed = entryMode === 'items' && protocol ? Object.entries(protocol).reduce((sum, [group, definitions]) => sum + definitions.filter(item => validTHCPItem(item, items[group as THCPGroup]?.[item.key])).length, 0) : THCP_FIELDS.filter(field => validScore(scores, field.key) !== null).length
  const backHref = evaluation ? `/dashboard/evaluations/${evaluation.id}?tab=overview` : '/dashboard'

  function changeScore(key: THCPField, value: string) {
    setScores(current => ({ ...current, [key]: value }))
  }

  function changeItem(group: THCPGroup, key: string, field: 'answer' | 'score', value: string) {
    setItems(current => {
      const response = { answer: '', score: '', ...current[group]?.[key], [field]: value }
      if (field === 'score' && value !== current[group]?.[key]?.score) response.answer = ''
      return { ...current, [group]: { ...current[group], [key]: response } }
    })
  }

  const protocolProps = protocol ? { protocol, items, onChange: changeItem } : null
  const progressMaximum = entryMode === 'items' ? itemCount : THCP_FIELDS.length
  const progressPercent = progressMaximum ? Math.round(completed / progressMaximum * 100) : 0

  function clearForm() {
    if (locked || saving || !window.confirm('Limpar os campos deste formulário? Os dados já salvos não serão alterados até você salvar uma nova correção.')) return
    setItems({})
    setScores(EMPTY_SCORES)
    setError('')
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 px-0 pb-6 sm:px-4 lg:px-6">
      <nav aria-label="Navegação da correção" className="flex flex-wrap items-center gap-2 text-sm text-slate-500">
        <Link className="inline-flex min-h-11 items-center gap-2 rounded hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600" href={backHref}><ArrowLeft className="h-4 w-4" aria-hidden="true" />Avaliação</Link>
        <ChevronRight className="h-3 w-3" aria-hidden="true" /><span>THCP</span><ChevronRight className="h-3 w-3" aria-hidden="true" /><span aria-current="page" className="font-medium text-slate-900">Correção</span>
      </nav>
      <header className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 text-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-5 p-5 sm:p-6">
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-teal-300"><ClipboardList className="h-4 w-4" aria-hidden="true" />Protocolo de registro das respostas</p>
            <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">THCP · Correção</h1>
            <p className="mt-1 text-xs text-slate-300">Teste de Habilidades e Conhecimento Pré-Alfabetização</p>
            {evaluation && <p className="mt-3 break-words text-sm font-medium text-white">{evaluation.patient_name}</p>}
          </div>
          <div className="flex flex-wrap items-center gap-5">
            <div className="text-right"><p className="text-[10px] font-medium uppercase tracking-wider text-slate-300">Total THCP</p><p className="mt-1 text-4xl font-bold tabular-nums text-teal-300">{total ?? '—'}<span className="ml-1 text-sm font-normal text-slate-400">/ 91</span></p><p className="mt-1 text-[10px] text-slate-400">{total === null ? 'Preenchimento em andamento' : 'Escore bruto · não normatizado'}</p></div>
            <Button type="submit" form="thcp-correction" disabled={!evaluation || saving || locked} className="min-h-11 gap-2 bg-teal-600 px-4 text-white hover:bg-teal-500">{saving ? <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" /> : <Save className="h-4 w-4" aria-hidden="true" />}{saving ? 'Corrigindo…' : 'Salvar correção'}</Button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-white/10 bg-white/5 px-5 py-3 sm:px-6">
          <div className="min-w-40 flex-1"><div className="mb-1.5 flex justify-between gap-2 text-[11px] text-slate-300"><span>{completed} de {progressMaximum} {entryMode === 'items' ? 'itens' : 'campos'} preenchidos</span><span className="tabular-nums">{progressPercent}%</span></div><div role="progressbar" aria-label="Preenchimento do protocolo" aria-valuemin={0} aria-valuemax={progressMaximum || 1} aria-valuenow={completed} className="h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-teal-400" style={{ width: `${progressPercent}%` }} /></div></div>
          <Button type="button" variant="ghost" className="min-h-11 gap-2 text-xs text-slate-200 hover:bg-white/10 hover:text-white" aria-expanded={showInstructions} aria-controls="thcp-instructions" onClick={() => setShowInstructions(current => !current)}><Info className="h-4 w-4" aria-hidden="true" />Orientações<ChevronDown className={`h-4 w-4 ${showInstructions ? 'rotate-180' : ''}`} aria-hidden="true" /></Button>
          <Button type="button" variant="ghost" disabled={!evaluation || saving || locked} onClick={clearForm} className="min-h-11 gap-2 text-xs text-slate-200 hover:bg-white/10 hover:text-white"><RotateCcw className="h-4 w-4" aria-hidden="true" />Limpar campos</Button>
        </div>
      </header>
      <div id="thcp-instructions" hidden={!showInstructions} className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm leading-6 text-blue-900">
        Preencha somente a coluna Nota de cada item conforme o protocolo do THCP. Os números ao lado são referências fixas, sem seleção; os destaques não alteram os cálculos. O sistema soma as notas e aplica as normas ao salvar. Campos vazios não equivalem a zero.
      </div>
      {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">{error}</p>}
      {locked && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Esta aplicação está travada e não pode ser editada.</p>}
      {evaluation && <form id="thcp-correction" onSubmit={save} className="space-y-5" aria-busy={saving}>
        <fieldset disabled={saving || locked} className="min-w-0 space-y-5">
          <legend className="sr-only">Dados e pontuações da correção THCP</legend>
          <section aria-labelledby="application-title" className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="grid items-start gap-4 lg:grid-cols-[1fr_200px_240px]">
              <div><h2 id="application-title" className="text-sm font-semibold text-slate-900">Dados da aplicação</h2><p className="mt-2 max-w-lg text-xs leading-5 text-slate-600">A idade é calculada pela data de nascimento e de aplicação. Ambas as tabelas são restritas a crianças de 4 a 7 anos.</p></div>
              <div className="space-y-2"><label htmlFor="applied-on" className="text-sm font-medium text-slate-700">Data de aplicação</label><Input id="applied-on" name="applied_on" autoComplete="off" className="h-11 border-slate-300 bg-white" type="date" required value={appliedOn} onChange={e => setAppliedOn(e.target.value)} /></div>
              <div className="space-y-2"><label htmlFor="norm-type" className="text-sm font-medium text-slate-700">Tabela normativa</label><select id="norm-type" name="norm_type" className="h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:cursor-not-allowed disabled:opacity-50" value={norm} onChange={e => setNorm(e.target.value as THCPNorm)}><option value="idade">Idade (4 a 7 anos)</option><option value="geral">Amostra Geral</option></select></div>
            </div>
          </section>
          {legacyApplication && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <p>Esta aplicação possui apenas totais salvos. Eles foram preservados; nenhuma resposta por item foi inventada. Para preencher o protocolo completo, selecione “Por item”.</p>
            <div className="mt-3 flex flex-wrap gap-4"><label className="flex min-h-11 cursor-pointer items-center gap-2"><input type="radio" name="entry-mode" value="totals" checked={entryMode === 'totals'} onChange={() => setEntryMode('totals')} />Totais salvos</label><label className="flex min-h-11 cursor-pointer items-center gap-2"><input type="radio" name="entry-mode" value="items" checked={entryMode === 'items'} onChange={() => setEntryMode('items')} />Por item</label></div>
          </div>}
          {entryMode === 'items' && <p className="flex items-start gap-2 text-xs leading-5 text-slate-600"><Info className="mt-0.5 h-4 w-4 shrink-0 text-teal-700" aria-hidden="true" /><span>Digite os valores somente na coluna <strong>Nota</strong>. Os números de referência são fixos; os destaques são apenas visuais. As somas são automáticas.</span></p>}
          <div className="grid items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
            <div className="min-w-0 space-y-4">
              {entryMode === 'items' && protocolProps ? <><ProtocolPanel group="hpm_i" {...protocolProps} /><ProtocolPanel group="hpm_ii" {...protocolProps} /></> : <DomainPanel domain={DOMAINS[0]} value={values[0]}><div className="py-2"><ScoreInput fieldKey="hpm" scores={scores} onChange={changeScore} /></div></DomainPanel>}
            </div>
            <div className="min-w-0 space-y-4">
              {entryMode === 'items' && protocolProps ? <><ProtocolPanel group="linguagem" {...protocolProps} /><ProtocolPanel group="memoria" {...protocolProps} /></> : <><DomainPanel domain={DOMAINS[1]} value={values[1]}><div className="py-2"><ScoreInput fieldKey="linguagem" scores={scores} onChange={changeScore} /></div></DomainPanel><DomainPanel domain={DOMAINS[3]} value={values[3]}><div className="py-2"><ScoreInput fieldKey="memoria" scores={scores} onChange={changeScore} /></div></DomainPanel></>}
            </div>
            <div className="min-w-0 space-y-4 md:col-span-2 xl:col-span-1">
              {entryMode === 'items' && protocolProps ? <ProtocolPanel group="pq" {...protocolProps} /> : <DomainPanel domain={DOMAINS[2]} value={values[2]}><div className="py-2"><ScoreInput fieldKey="pq" scores={scores} onChange={changeScore} /></div></DomainPanel>}
              <DomainPanel domain={DOMAINS[4]} value={values[4]}>
                <div className="grid grid-cols-2 gap-3 py-2"><ScoreInput fieldKey="atencao_acertos" scores={scores} onChange={changeScore} /><ScoreInput fieldKey="atencao_erros" scores={scores} onChange={changeScore} /></div>
                <div className="mb-1 mt-2 flex items-center justify-between gap-3 rounded-lg bg-rose-50 px-3 py-3"><div><p className="text-xs font-medium text-rose-900">Resultado da atenção</p><p className="mt-1 text-[11px] text-slate-600">Acertos − erros · mínimo zero</p></div><output htmlFor="atencao_acertos atencao_erros" className="text-xl text-slate-900"><ScoreValue value={values[4]} max={DOMAINS[4].max} /></output></div>
              </DomainPanel>
              <section aria-labelledby="thcp-summary-title" className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 id="thcp-summary-title" className="flex items-center gap-2 text-sm font-semibold text-slate-900"><ClipboardList className="h-4 w-4 text-teal-700" aria-hidden="true" />Resumo</h2>
                <dl className="mt-3 space-y-2">
                  {entryMode === 'items' && protocol ? (['hpm_i', 'hpm_ii', 'linguagem', 'memoria', 'pq'] as const).map(group => <div key={group} className="flex items-center justify-between gap-2 text-xs"><dt className="text-slate-600">{GROUP_PANELS[group].title}</dt><dd className="font-semibold tabular-nums text-slate-900">{thcpGroupTotal(protocol, items, group) ?? '—'}</dd></div>) : DOMAINS.slice(0, 4).map((domain, index) => <div key={domain.key} className="flex items-center justify-between gap-2 text-xs"><dt className="text-slate-600">{domain.shortLabel}</dt><dd className="font-semibold tabular-nums text-slate-900">{values[index] ?? '—'}</dd></div>)}
                  <div className="flex items-center justify-between gap-2 text-xs"><dt className="text-slate-600">Atenção</dt><dd className="font-semibold tabular-nums text-slate-900">{values[4] ?? '—'}</dd></div>
                </dl>
                <div className="mt-4 flex items-center justify-between gap-3 border-t border-slate-100 pt-4"><div><p className="text-xs font-semibold text-slate-800">Total THCP</p><p className="mt-1 text-[10px] text-slate-500">HPM + Ling. + Mem. + Atenção + PQ</p></div><span className="text-3xl font-bold tabular-nums text-teal-700">{total ?? '—'}<span className="ml-1 text-xs font-normal text-slate-500">/ 91</span></span></div>
                <p className="mt-3 flex items-start gap-1.5 text-[10px] leading-4 text-slate-500"><ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600" aria-hidden="true" />As normas são aplicadas pelo sistema ao salvar. Totais incompletos não são tratados como zero.</p>
              </section>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 sm:p-5">
            <div><p className="text-sm font-semibold text-slate-900">Escore bruto total <span className="ml-2 text-xl"><ScoreValue value={total} max={DOMAINS.reduce((sum, domain) => sum + domain.max, 0)} /></span></p><p className="mt-1 text-xs text-slate-600">{completed} de {entryMode === 'items' ? itemCount : THCP_FIELDS.length} {entryMode === 'items' ? 'itens' : 'campos'} preenchidos{entryMode === 'items' ? ' · atenção: informe acertos e erros' : ''}. Campos vazios não equivalem a zero.</p></div>
            <Button type="submit" className="min-h-11 gap-2 bg-teal-700 px-5 hover:bg-teal-800"><Save className="h-4 w-4" aria-hidden="true" />{saving ? 'Corrigindo…' : 'Salvar e corrigir THCP'}</Button>
          </div>
        </fieldset>
      </form>}
    </div>
  )
}

export default function THCPPage() {
  return <Suspense fallback={<p role="status">Carregando THCP…</p>}><THCPForm /></Suspense>
}
