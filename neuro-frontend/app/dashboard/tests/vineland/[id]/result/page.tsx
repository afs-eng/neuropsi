'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { VinelandQuestionnaireResult, type VinelandResultApplication } from '@/components/tests/VinelandQuestionnaireResult'

export default function VinelandResultPage() {
  const params = useParams<{ id: string }>()
  const [application, setApplication] = useState<VinelandResultApplication | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    api.get<VinelandResultApplication>(`/api/tests/applications/${params.id}`).then(data => {
      if (!active) return
      const extensive = data.normative_results?.form_level === 'extensivo' || data.raw_payload.form && data.raw_payload.form_level !== 'niveis_dominio' && data.raw_payload.entry_mode !== 'items'
      if (data.instrument_code !== 'vineland3' || !extensive && (data.raw_payload.completion_status !== 'finalized' || (!data.raw_payload.item_summary && !(data.raw_payload.form_level === 'niveis_dominio' && data.raw_payload.entry_mode === 'totals')))) {
        setError('Este registro não possui um questionário Vineland finalizado.')
        setApplication(null)
      } else {
        setApplication(data)
      }
    }).catch(() => {
      if (active) { setApplication(null); setError('Não foi possível carregar o resultado do Vineland. Tente novamente.') }
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [params.id])

  if (loading) return <p role="status" className="p-8">Carregando resultado do Vineland…</p>
  if (error || !application) return <main className="space-y-4 p-8"><p role="alert">{error || 'Resultado não encontrado.'}</p><Link className="inline-block py-3 underline" href={`/dashboard/tests/vineland?application_id=${params.id}&edit=true`}>Voltar ao registro</Link></main>
  return <VinelandQuestionnaireResult application={application} />
}
