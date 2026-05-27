"use client";

import { useEffect, useState } from "react";

import { BFPReportContent, type BFPApplicationData } from "@/components/tests/BFPReportContent";
import { getToken, resolveApiUrl } from "@/lib/api";

interface BFPPrintPageClientProps {
  applicationId: string;
  autoprint?: boolean;
  apiMode?: "direct" | "proxy";
}

export default function BFPPrintPageClient({ applicationId, autoprint = false, apiMode = "direct" }: BFPPrintPageClientProps) {
  const [application, setApplication] = useState<BFPApplicationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchApplication() {
      try {
        const token = getToken() || "";
        const endpoint = `/api/tests/applications/${applicationId}`;
        const response = await fetch(apiMode === "proxy" ? endpoint : resolveApiUrl(endpoint), {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Falha ao carregar resultado do BFP (${response.status})`);
        }

        const result = (await response.json()) as BFPApplicationData;
        setApplication(result);
      } catch (fetchError: any) {
        setError(fetchError?.message || "Não foi possível carregar o resultado do BFP.");
      } finally {
        setLoading(false);
      }
    }

    fetchApplication();
  }, [apiMode, applicationId]);

  useEffect(() => {
    if (!autoprint || loading || !application) return;
    const timer = window.setTimeout(() => window.print(), 300);
    return () => window.clearTimeout(timer);
  }, [application, autoprint, loading]);

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-white text-sm text-slate-500">Preparando impressão do BFP...</div>;
  }

  if (error || !application) {
    return <div className="flex min-h-screen items-center justify-center bg-white px-6 text-center text-sm text-rose-600">{error || "Resultado do BFP indisponível."}</div>;
  }

  return (
    <div className="report-print-shell bg-white p-0">
      <div className="report-print-card mx-auto max-w-none bg-white p-0 shadow-none">
        <div className="report-print-content bg-white p-0">
          <BFPReportContent
            application={application}
            applicationId={applicationId}
            evaluationId={application.evaluation_id ? String(application.evaluation_id) : undefined}
            hideActions
          />
        </div>
      </div>
    </div>
  );
}
