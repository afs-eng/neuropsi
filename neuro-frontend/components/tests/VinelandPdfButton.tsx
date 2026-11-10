'use client'

import { useState } from 'react'
import { getToken, resolveApiUrl } from '@/lib/api'

export function VinelandPdfButton({ applicationId }: { applicationId: number }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function downloadPdf() {
    if (loading) return
    setLoading(true)
    setError('')
    try {
      const token = getToken()
      const response = await fetch(resolveApiUrl(`/api/tests/applications/${applicationId}/export-pdf`), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        cache: 'no-store',
      })
      if (!response.ok) {
        let message = `Não foi possível gerar o PDF (${response.status}).`
        try {
          const data = await response.json()
          if (data.message) message = String(data.message)
        } catch { /* Preserve the HTTP error if the response is not JSON. */ }
        throw new Error(message)
      }
      const url = URL.createObjectURL(await response.blob())
      const link = document.createElement('a')
      link.href = url
      link.download = `VINELAND3-${applicationId}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Não foi possível gerar o PDF. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return <div className="space-y-2 print:hidden">
    <button type="button" disabled={loading} aria-busy={loading} onClick={downloadPdf} className="rounded-lg border border-cyan-200 bg-white px-4 py-3 text-sm font-medium text-cyan-900 disabled:opacity-60">{loading ? 'Gerando PDF…' : 'Imprimir / PDF'}</button>
    {error && <p role="alert" className="text-sm text-red-800">{error}</p>}
  </div>
}
