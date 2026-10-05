'use client'

import { Suspense, useEffect, useState, type FormEvent } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { THCP_FIELDS, thcpErrorMessage, type THCPApplication, type THCPFormScores, type THCPNorm } from '@/types/tests/thcp'

interface EvaluationInfo {
  id: number
  patient_name: string
  start_date: string | null
}

const EMPTY_SCORES: THCPFormScores = { hpm: '', linguagem: '', pq: '', memoria: '', atencao_acertos: '', atencao_erros: '' }

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

  if (loading) return <p role="status">Carregando THCP...</p>

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header>
        <Link className="text-sm text-slate-600 underline" href={evaluation ? `/dashboard/evaluations/${evaluation.id}?tab=overview` : '/dashboard'}>Voltar à avaliação</Link>
        <h1 className="mt-4 text-2xl font-semibold text-slate-900">THCP</h1>
        <p className="text-slate-600">Teste de Habilidades e Conhecimento Pré-Alfabetização</p>
        {evaluation && <p className="mt-2 font-medium">{evaluation.patient_name}</p>}
      </header>
      {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">{error}</p>}
      {locked && <p role="alert">Esta aplicação está travada e não pode ser editada.</p>}
      {evaluation && <form onSubmit={save}>
        <fieldset disabled={saving || locked}>
          <Card className="rounded-2xl border-slate-200">
            <CardHeader><CardTitle>Dados da aplicação</CardTitle><CardDescription>Informe os totais corrigidos de cada tarefa. Campos vazios não serão tratados como zero.</CardDescription></CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2"><label htmlFor="applied-on" className="text-sm font-medium">Data de aplicação</label><Input id="applied-on" type="date" required value={appliedOn} onChange={e => setAppliedOn(e.target.value)} /></div>
                <div className="space-y-2"><label htmlFor="norm-type" className="text-sm font-medium">Tabela normativa</label><select id="norm-type" className="h-10 w-full rounded-md border border-slate-300 bg-white px-3" value={norm} onChange={e => setNorm(e.target.value as THCPNorm)}><option value="idade">Idade (4 a 7 anos)</option><option value="geral">Amostra Geral</option></select></div>
              </div>
              <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-600">A idade será calculada a partir da data de nascimento e da aplicação. Ambas as tabelas são restritas a crianças de 4 a 7 anos.</p>
              <div className="grid gap-6 sm:grid-cols-2">
                {THCP_FIELDS.map(field => <div key={field.key} className="space-y-2">
                  <label htmlFor={field.key} className="text-sm font-medium text-slate-900">{field.label} (0–{field.max})</label>
                  <Input id={field.key} aria-describedby={`${field.key}-hint`} type="number" min={0} max={field.max} step={1} required value={scores[field.key]} onChange={e => setScores(current => ({ ...current, [field.key]: e.target.value }))} />
                  <p id={`${field.key}-hint`} className="text-xs text-slate-600">{field.hint}</p>
                </div>)}
              </div>
              <Button type="submit" className="min-h-11">{saving ? 'Corrigindo...' : 'Salvar e corrigir THCP'}</Button>
            </CardContent>
          </Card>
        </fieldset>
      </form>}
    </div>
  )
}

export default function THCPPage() {
  return <Suspense fallback={<p role="status">Carregando THCP...</p>}><THCPForm /></Suspense>
}
