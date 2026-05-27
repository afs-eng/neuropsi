'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'

interface Subtest {
  code: string
  name: string
  maxScore: number
  optional: boolean
}

const subtests: Subtest[] = [
  { code: 'CB', name: 'Cubos', maxScore: 68, optional: false },
  { code: 'SM', name: 'Semelhanças', maxScore: 44, optional: false },
  { code: 'DG', name: 'Dígitos', maxScore: 32, optional: false },
  { code: 'CN', name: 'Conceitos Figurativos', maxScore: 28, optional: false },
  { code: 'CD', name: 'Código', maxScore: 119, optional: false },
  { code: 'VC', name: 'Vocabulário', maxScore: 68, optional: false },
  { code: 'SNL', name: 'Seq. de Núm. e Letras', maxScore: 30, optional: false },
  { code: 'RM', name: 'Raciocínio Matricial', maxScore: 41, optional: false },
  { code: 'CO', name: 'Compreensão', maxScore: 47, optional: false },
  { code: 'PS', name: 'Procurar Símbolos', maxScore: 60, optional: false },
  { code: 'CF', name: 'Completar Figuras', maxScore: 38, optional: true },
  { code: 'CA', name: 'Cancelamento', maxScore: 60, optional: true },
  { code: 'IN', name: 'Informação', maxScore: 30, optional: true },
  { code: 'AR', name: 'Aritmética', maxScore: 34, optional: true },
  { code: 'RP', name: 'Raciocínio com Palavras', maxScore: 32, optional: true },
]

const indices = [
  { code: 'ICV', name: 'Compreensão Verbal', subtests: ['SM', 'VC', 'CO'] },
  { code: 'IOP', name: 'Organização Perceptual', subtests: ['CB', 'CN', 'RM'] },
  { code: 'IMO', name: 'Memória Operacional', subtests: ['DG', 'SNL'] },
  { code: 'IVP', name: 'Velocidade de Processamento', subtests: ['CD', 'PS'] },
]

const processScores: Subtest[] = [
  { code: 'CUSB', name: 'Cubos sem Tempo de Bônus', maxScore: 50, optional: true },
  { code: 'DIOD', name: 'Dígitos Ordem Direta', maxScore: 16, optional: true },
  { code: 'DIOI', name: 'Dígitos Ordem Inversa', maxScore: 16, optional: true },
  { code: 'CAA', name: 'Cancelamento Aleatório', maxScore: 68, optional: true },
  { code: 'CAE', name: 'Cancelamento Estruturado', maxScore: 69, optional: true },
  { code: 'UDIOD', name: 'Seq. Maior Dígitos Ordem Direta', maxScore: 11, optional: true },
  { code: 'UDIOI', name: 'Seq. Maior Dígitos Ordem Inversa', maxScore: 11, optional: true },
]

function WISC4FormPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [scores, setScores] = useState<Record<string, number | null>>({})
  const [evaluation, setEvaluation] = useState<any>(null)
  const [loadingEvaluation, setLoadingEvaluation] = useState(true)

  const evaluationId = searchParams.get("evaluation_id");
  const applicationId = searchParams.get("application_id");
  const isEditMode = searchParams.get("edit") === "true";

  useEffect(() => {
    async function fetchEvaluation() {
      if (applicationId) {
        try {
          const result = await api.get<any>(`/api/tests/applications/${applicationId}`)
          if (result && result.evaluation_id && !evaluationId) {
            const newEvalId = result.evaluation_id.toString();
            router.replace(`/dashboard/tests/wisc4?application_id=${applicationId}&evaluation_id=${newEvalId}&edit=true`)
            return
          }
          if (result && result.is_validated && !isEditMode) {
            const resultEvaluationId = result.evaluation_id ? `?evaluation_id=${result.evaluation_id}` : ""
            router.push(`/dashboard/tests/wisc4/${applicationId}/result${resultEvaluationId}`)
            return
          }
          if (result && result.raw_payload) {
            const raw = result.raw_payload
            const existingScores: Record<string, number> = {}
            const codes = ['CB', 'SM', 'DG', 'CN', 'CD', 'VC', 'SNL', 'RM', 'CO', 'PS', 'CF', 'CA', 'IN', 'AR', 'RP', 'CUSB', 'DIOD', 'DIOI', 'CAA', 'CAE', 'UDIOD', 'UDIOI']
            const keys = ['cubos', 'semelhancas', 'digitos', 'conceitos', 'codigos', 'vocabulario', 'sequencias', 'matricial', 'compreensao', 'procura_simbolos', 'cf', 'ca', 'in', 'ar', 'rp', 'cusb', 'diod', 'dioi', 'caa', 'cae', 'udiod', 'udioi']
            keys.forEach((key, idx) => {
              if (raw[key] !== undefined) {
                existingScores[codes[idx]] = raw[key]
              }
            })
            setScores(existingScores)
          }
        } catch (error) {
          console.log("Teste não encontrado, redirecionando para formulário...")
        }
      }

      if (!evaluationId) {
        setLoadingEvaluation(false);
        return;
      }

      try {
        const data = await api.get<any>(`/api/evaluations/${evaluationId}`)
        setEvaluation(data)
      } catch (error: any) {
        console.error("Erro ao buscar avaliação:", error)
      } finally {
        setLoadingEvaluation(false)
      }
    }
    fetchEvaluation()
  }, [evaluationId, applicationId, isEditMode, router])

  const handleScoreChange = (code: string, value: string) => {
    if (value === '') {
      setScores(prev => ({ ...prev, [code]: null }))
      return
    }

    const numValue = parseInt(value, 10)
    if (!Number.isNaN(numValue)) {
      setScores(prev => ({ ...prev, [code]: numValue }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!evaluationId) {
      alert('ID da avaliação não encontrado. Acesse este teste através de uma avaliação.')
      return
    }

    const payload = {
      evaluation_id: parseInt(evaluationId),
      cb: scores['CB'] == null ? '' : String(scores['CB']),
      sm: scores['SM'] == null ? '' : String(scores['SM']),
      dg: scores['DG'] == null ? '' : String(scores['DG']),
      cn: scores['CN'] == null ? '' : String(scores['CN']),
      cd: scores['CD'] == null ? '' : String(scores['CD']),
      vc: scores['VC'] == null ? '' : String(scores['VC']),
      snl: scores['SNL'] == null ? '' : String(scores['SNL']),
      rm: scores['RM'] == null ? '' : String(scores['RM']),
      co: scores['CO'] == null ? '' : String(scores['CO']),
      ps: scores['PS'] == null ? '' : String(scores['PS']),
      cf: scores['CF'] == null ? '' : String(scores['CF']),
      ca: scores['CA'] == null ? '' : String(scores['CA']),
      in_: scores['IN'] == null ? '' : String(scores['IN']),
      ar: scores['AR'] == null ? '' : String(scores['AR']),
      rp: scores['RP'] == null ? '' : String(scores['RP']),
      cusb: scores['CUSB'] == null ? '' : String(scores['CUSB']),
      diod: scores['DIOD'] == null ? '' : String(scores['DIOD']),
      dioi: scores['DIOI'] == null ? '' : String(scores['DIOI']),
      caa: scores['CAA'] == null ? '' : String(scores['CAA']),
      cae: scores['CAE'] == null ? '' : String(scores['CAE']),
      udiod: scores['UDIOD'] == null ? '' : String(scores['UDIOD']),
      udioi: scores['UDIOI'] == null ? '' : String(scores['UDIOI']),
    }

    console.log('Payload WISC-IV:', payload)

    try {
      const result = await api.post<{ application_id: number }>('/api/tests/wisc4/submit', payload)
      alert('WISC-IV salvo com sucesso!')
      router.push(`/dashboard/tests/wisc4/${result.application_id}/result?evaluation_id=${evaluationId}`)
    } catch (error: any) {
      console.error('Erro completo:', error)
      alert('Erro ao salvar. Ver console para detalhes.')
    }
  }

  return (
    <div className="min-h-screen w-full bg-slate-300 p-6 md:p-10">
      <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7">
        <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6">
          {/* Header */}
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium tracking-tight text-zinc-800 shadow-sm">
                NeuroAvalia
              </div>
            </div>

            <nav className="flex flex-wrap items-center gap-2 rounded-full bg-white/70 px-3 py-2 text-sm text-zinc-700 shadow-sm">
              <Link href="/dashboard" className="rounded-full px-4 py-2 hover:bg-black/5">Dashboard</Link>
              <Link href="/dashboard/patients" className="rounded-full px-4 py-2 hover:bg-black/5">Pacientes</Link>
              <Link href="/dashboard/evaluations" className="rounded-full px-4 py-2 hover:bg-black/5">Avaliações</Link>
              <Link href="/dashboard/tests" className="rounded-full px-4 py-2 bg-zinc-900 text-white shadow">Testes</Link>
              <Link href="/dashboard/reports" className="rounded-full px-4 py-2 hover:bg-black/5">Laudos</Link>
            </nav>
          </header>

          {/* Page Title */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-medium tracking-tight text-zinc-900">WISC-IV</h1>
              <p className="mt-1 text-sm text-zinc-600">Escala de Inteligência Wechsler para Crianças</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Patient Selection */}
            <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5">
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Informações</h3>
              {loadingEvaluation ? (
                <div className="text-center py-4 text-zinc-500">Carregando dados do paciente...</div>
              ) : evaluation ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-zinc-700">Paciente</label>
                    <div className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm shadow-sm">
                      {evaluation.patient_name}
                    </div>
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-zinc-700">Data de nascimento</label>
                    <div className="w-full rounded-2xl border border-black/10 bg-slate-50 px-4 py-3 text-sm shadow-sm">
                      {evaluation.patient_birth_date || "—"}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4 text-red-500">Avaliação não encontrada</div>
              )}
            </div>

            {/* Subtests */}
            <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5">
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Escores Brutos</h3>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {subtests.map((subtest) => (
                  <div key={subtest.code} className={`rounded-2xl border p-4 shadow-sm ${subtest.optional ? 'border-dashed border-amber-200 bg-amber-50/50' : 'border-black/10 bg-white'}`}>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-medium text-zinc-900">{subtest.name}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${subtest.optional ? 'bg-amber-100 text-amber-700' : 'bg-zinc-100 text-zinc-500'}`}>
                        {subtest.code}
                      </span>
                    </div>
                    <input
                      type="number"
                      min="0"
                      max={subtest.maxScore}
                      value={scores[subtest.code] ?? ''}
                      onChange={(e) => handleScoreChange(subtest.code, e.target.value)}
                      placeholder={`0 - ${subtest.maxScore}`}
                      className="w-full rounded-xl border border-black/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900/20"
                    />
                    {subtest.optional && (
                      <span className="mt-1 block text-xs text-amber-600">Opcional</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5">
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Escores de Processo</h3>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {processScores.map((score) => (
                  <div key={score.code} className="rounded-2xl border border-dashed border-blue-200 bg-blue-50/50 p-4 shadow-sm">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="font-medium text-zinc-900">{score.name}</span>
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                        {score.code}
                      </span>
                    </div>
                    <input
                      type="number"
                      min="0"
                      max={score.maxScore}
                      value={scores[score.code] ?? ''}
                      onChange={(e) => handleScoreChange(score.code, e.target.value)}
                      placeholder={`0 - ${score.maxScore}`}
                      className="w-full rounded-xl border border-black/10 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900/20"
                    />
                    <span className="mt-1 block text-xs text-blue-600">Opcional / análise de processo</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Indexes Preview */}
            <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5">
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Índices</h3>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {indices.map((idx) => {
                  const subtestScores = idx.subtests.map(code => scores[code])
                  const hasMissingScores = subtestScores.some(score => score == null)
                  const presentScores = subtestScores.filter((score): score is number => score != null)
                  const sum = hasMissingScores ? null : presentScores.reduce((total, score) => total + score, 0)
                  return (
                    <div key={idx.code} className="rounded-2xl border border-black/10 bg-white p-4 shadow-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-zinc-900">{idx.name}</span>
                        <span className="text-sm text-zinc-500">({idx.code})</span>
                      </div>
                      <div className="mt-2 text-2xl font-semibold text-zinc-900">
                        {sum != null ? sum : '—'}
                      </div>
                      <div className="mt-1 text-xs text-zinc-500">
                        Soma dos escores: {subtestScores.map(score => score ?? '—').join(' + ')}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-4">
              <Link
                href="/patients"
                className="rounded-full border border-black/10 bg-white px-6 py-3 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50"
              >
                Cancelar
              </Link>
              <button
                type="submit"
                className="rounded-full bg-zinc-900 px-8 py-3 text-sm font-medium text-white shadow-lg hover:bg-zinc-800"
              >
                Calcular Resultado
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

function WISC4FormPageFallback() {
  return <div className="min-h-screen w-full bg-slate-300 p-6 md:p-10" />
}

export default function WISC4FormPage() {
  return (
    <Suspense fallback={<WISC4FormPageFallback />}>
      <WISC4FormPageContent />
    </Suspense>
  )
}
