"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { openPrintRoute } from "@/lib/print";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { BFPApplicationData, BFPReportContent } from "@/components/tests/BFPReportContent";

function BFPResultPageContent() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const applicationId = params.id as string;
  const [application, setApplication] = useState<BFPApplicationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluationId, setEvaluationId] = useState(searchParams.get("evaluation_id") || "");

  useEffect(() => {
    async function fetchApplication() {
      try {
        const result = await api.get<BFPApplicationData>(`/api/tests/applications/${applicationId}`);
        setApplication(result);
        if (result?.evaluation_id && !evaluationId) {
          setEvaluationId(String(result.evaluation_id));
        }
      } catch (error) {
        console.error("Erro ao buscar resultado do BFP:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchApplication();
  }, [applicationId, evaluationId]);

  const backHref = useMemo(() => {
    return evaluationId ? `/dashboard/evaluations/${evaluationId}?tab=overview` : "/dashboard/evaluations?tab=overview";
  }, [evaluationId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-primary" />
          <p className="text-sm text-slate-500">Carregando resultado...</p>
        </div>
      </div>
    );
  }

  if (!application) {
    return <div className="py-12 text-center text-red-500">Resultado do BFP não encontrado.</div>;
  }

  return (
    <BFPReportContent
      application={application}
      applicationId={applicationId}
      evaluationId={evaluationId}
      onPrint={() => openPrintRoute(`/print/bfp-pdf/${applicationId}?autoprint=1`)}
      onEdit={() => router.push(`/dashboard/tests/bfp?application_id=${applicationId}&edit=true${evaluationId ? `&evaluation_id=${evaluationId}` : ""}`)}
      onBack={() => router.push(backHref)}
    />
  );
}

function BFPResultFallback() {
  return <div className="space-y-8" />;
}

export default function BFPResultPage() {
  return (
    <Suspense fallback={<BFPResultFallback />}>
      <BFPResultPageContent />
    </Suspense>
  );
}
