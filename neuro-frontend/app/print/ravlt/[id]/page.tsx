"use client"

import { useEffect, useRef, useState } from "react"
import { useParams, useSearchParams } from "next/navigation"

import { getToken, resolveApiUrl } from "@/lib/api"

export default function RAVLTPrintPage() {
  const params = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const iframeRef = useRef<HTMLIFrameElement | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let currentUrl: string | null = null

    const loadPdf = async () => {
      try {
        const requestPdf = async () => {
          const token = getToken() || ""
          return fetch(resolveApiUrl(`/api/tests/applications/${params.id}/export-pdf`), {
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
            cache: "no-store",
          })
        }

        let response = await requestPdf()
        if (response.status === 401) {
          await new Promise((resolve) => window.setTimeout(resolve, 250))
          response = await requestPdf()
        }

        if (!response.ok) {
          let message = `Falha ao carregar PDF (${response.status})`
          try {
            const payload = await response.json()
            if (payload?.message) {
              message = `${message}: ${payload.message}`
            }
          } catch {}
          throw new Error(message)
        }

        const blob = await response.blob()
        currentUrl = URL.createObjectURL(blob)
        setPdfUrl(currentUrl)
      } catch (fetchError: any) {
        setError(fetchError?.message || "Não foi possível carregar o PDF do RAVLT.")
      } finally {
        setLoading(false)
      }
    }

    if (params.id) {
      loadPdf()
    }

    return () => {
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl)
      }
    }
  }, [params.id])

  const handleFrameLoad = () => {
    if (searchParams.get("autoprint") !== "1") return
    const frameWindow = iframeRef.current?.contentWindow
    if (!frameWindow) return
    window.setTimeout(() => frameWindow.print(), 300)
  }

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-white text-sm text-slate-500">Gerando PDF do RAVLT...</div>
  }

  if (error || !pdfUrl) {
    return <div className="flex min-h-screen items-center justify-center bg-white px-6 text-center text-sm text-rose-600">{error || "PDF do RAVLT indisponível."}</div>
  }

  return (
    <div className="h-screen bg-slate-100">
      <iframe
        ref={iframeRef}
        src={pdfUrl}
        title="PDF do RAVLT"
        className="h-full w-full border-0"
        onLoad={handleFrameLoad}
      />
    </div>
  )
}
