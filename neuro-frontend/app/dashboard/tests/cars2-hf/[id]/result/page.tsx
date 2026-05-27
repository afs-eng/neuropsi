"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Edit3, Printer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { printCurrentPage } from "@/lib/print";
import { TestReportSummaryCard } from "@/components/tests/TestReportSummaryCard";

const ITEM_LABELS: Record<string, string> = {
  compreensao_socio_emocional: "Compreensão sócio-emocional",
  expressao_emocional_regulacao: "Expressão emocional e regulação das emoções",
  relacionamento_com_pessoas: "Relacionamento com pessoas",
  uso_do_corpo: "Uso do corpo",
  uso_objetos_brincadeiras: "Uso de objetos nas brincadeiras",
  adaptacao_mudancas_interesses_restritos: "Adaptação a mudanças / interesses restritos",
  resposta_visual: "Resposta visual",
  resposta_auditiva: "Resposta auditiva",
  resposta_sensorial: "Resposta a, ou uso de, sabor, cheiro e toque",
  medo_ou_ansiedade: "Medo ou ansiedade",
  comunicacao_verbal: "Comunicação verbal",
  comunicacao_nao_verbal: "Comunicação não verbal",
  integracao_pensamento_cognicao: "Habilidades de integração de pensamento/cognitiva",
  resposta_intelectual: "Leve e consistente resposta intelectual",
  impressoes_gerais: "Impressões gerais",
};

export default function CARS2HFResultPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const evaluationId = searchParams.get("evaluation_id") || result?.evaluation_id;

  useEffect(() => {
    async function loadResult() {
      try {
        const data = await api.get<any>(`/api/tests/applications/${params.id}`);
        setResult(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }

    if (params.id) loadResult();
  }, [params.id]);

  const topDomains = useMemo(() => {
    const scores = result?.computed_payload?.domain_scores || {};
    return Object.entries(scores)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
      .slice(0, 3);
  }, [result]);

  if (loading) {
    return <div className="py-16 text-center text-slate-500">Carregando resultado...</div>;
  }

  if (!result) {
    return <div className="py-16 text-center text-red-500">Resultado não encontrado.</div>;
  }

  const computed = result.computed_payload || {};
  const classified = result.classified_payload || {};

  return (
    <div className="space-y-6 report-print-shell">
      <div className="flex items-center justify-between gap-4 print:hidden report-print-hide">
        <Button variant="ghost" onClick={() => router.push(`/dashboard/evaluations/${evaluationId}/overview?tab=tests`)} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Voltar
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" onClick={printCurrentPage} className="gap-2">
            <Printer className="h-4 w-4" />
            Imprimir / PDF
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push(`/dashboard/tests/cars2-hf?evaluation_id=${evaluationId}&application_id=${params.id}&edit=true`)}
            className="gap-2"
          >
            <Edit3 className="h-4 w-4" />
            Editar
          </Button>
        </div>
      </div>

      <Card className="rounded-2xl border-slate-200 shadow-sm report-print-content">
        <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text || result.interpretation} className="mb-4" />

        <CardHeader>
          <CardTitle className="text-2xl font-semibold text-slate-900">CARS2 – HF - Resultado</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm text-slate-500">Escore bruto</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">{computed.raw_total ?? "—"}</div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm text-slate-500">T-escore</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">{computed.t_score ?? "—"}</div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm text-slate-500">Percentil</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">{computed.percentile ?? "—"}</div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="text-sm text-slate-500">Classificação</div>
            <div className="mt-1 text-lg font-medium text-slate-900">{classified.severity_group || "—"}</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="text-sm font-medium text-slate-900">Domínios mais elevados</div>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              {topDomains.map(([key, value]) => (
                <div key={key} className="rounded-xl bg-slate-50 p-3">
                  <div className="text-sm text-slate-700">{ITEM_LABELS[key] || key}</div>
                  <div className="mt-1 text-xl font-semibold text-slate-900">{String(value)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="text-sm font-medium text-slate-900">Interpretação técnica</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">{result.interpretation_text || result.interpretation || "—"}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
