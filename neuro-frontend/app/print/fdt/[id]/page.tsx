"use client"

import { useEffect, useRef, useState } from "react"
import { useParams, useSearchParams } from "next/navigation"

import { resolveApiUrl } from "@/lib/api"

export default function FDTPrintPage() {
  const params = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const iframeRef = useRef<HTMLIFrameElement | null>(null)
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let currentUrl: string | null = null

    const readToken = () => {
      if (typeof window === "undefined") return ""
      return window.localStorage.getItem("token") || ""
    }

    const loadPdf = async () => {
      try {
        const requestPdf = async () => {
          const token = readToken()
          return fetch(resolveApiUrl(`/api/tests/fdt/${params.id}/export-pdf`), {
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
          throw new Error(`Falha ao carregar PDF (${response.status})`)
        }

        const blob = await response.blob()
        currentUrl = URL.createObjectURL(blob)
        setPdfUrl(currentUrl)
      } catch (fetchError: any) {
        setError(fetchError?.message || "Não foi possível carregar o PDF do FDT.")
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
    return <div className="flex min-h-screen items-center justify-center bg-white text-sm text-slate-500">Gerando PDF do FDT...</div>
  }

  if (error || !pdfUrl) {
    return <div className="flex min-h-screen items-center justify-center bg-white px-6 text-center text-sm text-rose-600">{error || "PDF do FDT indisponível."}</div>
  }

  return (
    <div className="h-screen bg-slate-100">
      <iframe
        ref={iframeRef}
        src={pdfUrl}
        title="PDF do FDT"
        className="h-full w-full border-0"
        onLoad={handleFrameLoad}
      />
    </div>
  )
}
