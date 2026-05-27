"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Edit3, Printer } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { printCurrentPage } from "@/lib/print";
import { TestReportSummaryCard } from "@/components/tests/TestReportSummaryCard";

const CRITICAL_ITEMS = new Set([2, 7, 9, 13, 14, 15]);

const ITEM_LABELS: Record<string, string> = {
  gosta_de_balancar: "Gosta de balançar",
  interesse_outras_criancas: "Interesse por outras crianças",
  gosta_de_subir: "Gosta de subir",
  brinca_esconder_mostrar: "Brinca de esconder e mostrar",
  brinca_faz_de_conta: "Brinca de faz-de-conta",
  aponta_para_pedir: "Aponta para pedir",
  aponta_para_mostrar_interesse: "Aponta para mostrar interesse",
  brinca_corretamente_com_objetos: "Brinca corretamente com objetos",
  traz_objetos_para_mostrar: "Traz objetos para mostrar",
  contato_visual: "Contato visual",
  hipersensibilidade_a_ruido: "Hipersensibilidade a ruído",
  sorri_em_resposta: "Sorri em resposta",
  imita_o_adulto: "Imita o adulto",
  responde_ao_nome: "Responde ao nome",
  segue_apontar: "Segue apontar",
  ja_sabe_andar: "Já sabe andar",
  olha_para_o_que_o_adulto_olha: "Olha para o que o adulto olha",
  movimentos_estranhos_dedos_rosto: "Movimentos estranhos com dedos",
  busca_atencao_para_atividade: "Busca atenção para a atividade",
  suspeita_de_surdez: "Suspeita de surdez",
  entende_o_que_dizem: "Entende o que dizem",
  fica_aereo_ou_deambula: "Fica aéreo / deambula",
  checa_reacao_facial: "Checa reação facial",
};

export default function MCHATResultPage() {
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

  const itemResults = useMemo(() => result?.computed_payload?.item_results || {}, [result]);
  const failedItems = [...(result?.computed_payload?.failed_items || [])].sort((a, b) => a - b);
  const criticalFailures = [...(result?.computed_payload?.failed_critical_items || [])].sort((a, b) => a - b);
  const orderedItemResults = useMemo(
    () =>
      Object.entries(itemResults).sort(
        ([, left]: [string, any], [, right]: [string, any]) => left.item_number - right.item_number,
      ),
    [itemResults],
  );

  if (loading) {
    return <div className="py-16 text-center text-slate-500">Carregando resultado...</div>;
  }

  if (!result) {
    return <div className="py-16 text-center text-red-500">Resultado não encontrado.</div>;
  }

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
            onClick={() => router.push(`/dashboard/tests/mchat?evaluation_id=${evaluationId}&application_id=${params.id}&edit=true`)}
            className="gap-2"
          >
            <Edit3 className="h-4 w-4" />
            Editar
          </Button>
        </div>
      </div>

      <Card className="rounded-2xl border-slate-200 shadow-sm report-print-content">
        <CardHeader>
          <CardTitle className="text-2xl font-semibold text-slate-900">M-CHAT - Resultado</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm text-slate-500">Falhas totais</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">{result.computed_payload?.total_failures ?? "—"}</div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm text-slate-500">Falhas críticas</div>
              <div className="mt-1 text-3xl font-semibold text-slate-900">{result.computed_payload?.critical_failures ?? "—"}</div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm text-slate-500">Triagem</div>
              <div className={`mt-1 text-lg font-semibold ${classified.screen_code === "positive" ? "text-rose-600" : "text-emerald-700"}`}>
                {classified.screen_result || "—"}
              </div>
            </div>
          </div>

          <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text || result.interpretation} />

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="text-sm font-medium text-slate-900">Interpretação técnica</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">{result.interpretation_text || result.interpretation || "—"}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="text-sm font-medium text-slate-900">Itens com falha</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {failedItems.length ? failedItems.map((item: number) => <Badge key={item} className="rounded-full bg-rose-50 text-rose-700 border border-rose-200">{item}</Badge>) : <span className="text-sm text-slate-500">Nenhuma falha</span>}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <div className="text-sm font-medium text-slate-900">Falhas críticas</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {criticalFailures.length ? criticalFailures.map((item: number) => <Badge key={item} className="rounded-full bg-amber-50 text-amber-700 border border-amber-200">{item}</Badge>) : <span className="text-sm text-slate-500">Nenhuma falha crítica</span>}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="text-sm font-medium text-slate-900">Resumo por item</div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {orderedItemResults.map(([key, value]: [string, any]) => (
                <div key={key} className={`rounded-xl border p-3 ${value.is_critical ? "border-amber-200 bg-amber-50/60" : "border-slate-200 bg-slate-50"}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium text-slate-900">{ITEM_LABELS[key] || key}</div>
                      <div className="text-xs text-slate-500">Item {value.item_number}</div>
                    </div>
                    <Badge className={`rounded-full ${value.result === "Falha" ? "bg-rose-50 text-rose-700 border border-rose-200" : "bg-emerald-50 text-emerald-700 border border-emerald-200"}`}>
                      {value.result}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
