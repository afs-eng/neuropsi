"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import { FDTChart } from "@/components/charts/FDTChart";
import { openPrintRoute } from "@/lib/print";
import { TestReportSummaryCard } from "@/components/tests/TestReportSummaryCard";

const CLASSIFICATION_STYLES: Record<string, string> = {
  "Muito Superior": "bg-emerald-600 text-white",
  Superior: "bg-emerald-100 text-emerald-700",
  "Media Superior": "bg-teal-100 text-teal-700",
  Media: "bg-blue-100 text-blue-700",
  "Media Inferior": "bg-amber-100 text-amber-700",
  Inferior: "bg-orange-100 text-orange-700",
  "Muito Inferior": "bg-red-100 text-red-700",
  Deficitario: "bg-rose-100 text-rose-700",
};

const STAGE_LABELS: Record<string, string> = {
  leitura: "Leitura",
  contagem: "Contagem",
  escolha: "Escolha",
  alternancia: "Alternância",
};

const DOMAIN_LABELS: Record<string, string> = {
  ProcessosAutomaticos: "Processos Automáticos",
  ProcessosControlados: "Processos Controlados",
};

function formatClassification(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function toDomainKey(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, "");
}

export default function FDTResultPage() {
  const params = useParams();
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchResult = async () => {
      try {
        const { api } = await import("@/lib/api");
        const data = await api.get<any>(`/api/tests/applications/${params.id}`);
        setResult(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchResult();
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center">
        <div className="text-zinc-600">Carregando...</div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center">
        <div className="text-zinc-600">Resultado não encontrado</div>
      </div>
    );
  }

  const classified = result.classified_payload || {};
  const metricResults = classified.metric_results || [];
  const derivedScores = classified.derived_scores || {};
  const stageTotals = classified.stage_totals || {};
  const chartData = classified.charts || {};
  const errorResults = Object.entries(classified.erros || {}) as [string, any][];
  const interpretationParagraphs = String(result.interpretation_text || "")
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  const metricGroups = metricResults.reduce((acc: Record<string, any[]>, item: any) => {
    const key = toDomainKey(item.categoria || "");
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(item);
    return acc;
  }, {});
  const metricGroupEntries = Object.entries(metricGroups) as [string, any[]][];
  const handlePrint = () => {
    if (!params.id) return;
    const evaluationQuery = result.evaluation_id ? `?evaluation_id=${result.evaluation_id}&autoprint=1` : "?autoprint=1";
    openPrintRoute(`/print/fdt/${params.id}${evaluationQuery}`);
  };

  return (
    <div className="min-h-screen bg-slate-300 p-6 md:p-10 report-print-shell">
      <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7 report-print-card">
        <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6 report-print-content">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between print:hidden report-print-hide">
            <div className="flex items-center gap-4">
              <div className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium tracking-tight text-zinc-800 shadow-sm">
                Florescer
              </div>
            </div>
            <nav className="flex flex-wrap items-center gap-2 rounded-full bg-white/70 px-3 py-2 text-sm text-zinc-700 shadow-sm">
              <Link href="/dashboard" className="rounded-full px-4 py-2 hover:bg-black/5">Dashboard</Link>
              <Link href="/dashboard?tab=tests" className="rounded-full px-4 py-2 hover:bg-black/5">Testes</Link>
            </nav>
          </header>

          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-medium tracking-tight text-zinc-900">FDT - Resultado</h1>
              <p className="mt-1 text-sm text-zinc-600">
                {result.patient_name} • Faixa normativa {classified.faixa || "—"}
              </p>
            </div>
            <div className="flex gap-3 print:hidden report-print-hide">
              <Link href={`/dashboard/tests/fdt?evaluation_id=${result.evaluation_id}&application_id=${params.id}&edit=true`} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                Editar
              </Link>
              <button onClick={handlePrint} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                Imprimir / PDF
              </button>
              <Link href={`/dashboard/evaluations/${result.evaluation_id}?tab=overview`} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">
                Voltar
              </Link>
            </div>
          </div>

          <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text} className="mb-6 report-print-break-avoid" />

          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3 report-print-break-avoid">
            <div className="rounded-[28px] bg-blue-500 p-5 text-white shadow-lg">
              <div className="text-sm text-blue-100">Inibição</div>
              <div className="mt-2 text-4xl font-light">{derivedScores.inibicao ?? "—"}</div>
            </div>
            <div className="rounded-[28px] bg-teal-500 p-5 text-white shadow-lg">
              <div className="text-sm text-teal-100">Flexibilidade</div>
              <div className="mt-2 text-4xl font-light">{derivedScores.flexibilidade ?? "—"}</div>
            </div>
            <div className="rounded-[28px] bg-amber-500 p-5 text-white shadow-lg">
              <div className="text-sm text-amber-100">Erros totais</div>
              <div className="mt-2 text-4xl font-light">{derivedScores.total_erros ?? "—"}</div>
            </div>
          </div>

          <div className="mb-6 rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5 report-print-break-avoid">
            <h3 className="mb-4 text-lg font-semibold text-zinc-900">Métricas normativas</h3>
            <div className="mb-5 grid grid-cols-1 gap-4 md:grid-cols-2">
              {metricGroupEntries.map(([groupKey, items]) => (
                <div key={groupKey} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="text-sm font-semibold text-slate-900">{DOMAIN_LABELS[groupKey] || groupKey}</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {items.map((item: any) => (
                      <span
                        key={item.codigo}
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${CLASSIFICATION_STYLES[item.classificacao] || "bg-slate-100 text-slate-700"}`}
                      >
                        {item.nome}: {item.classificacao}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dashed border-black/10">
                    <th className="pb-3 text-left text-xs font-semibold uppercase text-zinc-500">Categoria</th>
                    <th className="pb-3 text-left text-xs font-semibold uppercase text-zinc-500">Subteste</th>
                    <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Tempo</th>
                    <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Média</th>
                    <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Pontos Ponderados</th>
                    <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Percentil</th>
                    <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Classificação</th>
                  </tr>
                </thead>
                <tbody>
                  {metricResults.map((item: any) => (
                    <tr key={item.codigo} className="border-b border-dashed border-black/5">
                      <td className="py-3 text-zinc-700">{item.categoria}</td>
                      <td className="py-3 text-zinc-900">{item.nome}</td>
                      <td className="py-3 text-center text-zinc-700">{item.valor}</td>
                      <td className="py-3 text-center text-zinc-700">{item.media}</td>
                      <td className="py-3 text-center text-zinc-700">{item.pontos_ponderados}</td>
                      <td className="py-3 text-center text-zinc-700">
                        {item.percentil_num ?? item.percentil_texto}
                      </td>
                      <td className="py-3 text-center">
                        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${CLASSIFICATION_STYLES[item.classificacao] || "bg-slate-100 text-slate-700"}`}>
                          {item.classificacao}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mb-6 rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5 report-print-break-avoid">
            <h3 className="mb-4 text-lg font-semibold text-zinc-900">Tempos e erros informados</h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              {Object.entries(stageTotals).map(([stage, values]: [string, any]) => (
                <div key={stage} className="rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="text-sm font-medium text-slate-900">{STAGE_LABELS[stage] || stage}</div>
                  <div className="mt-2 text-sm text-slate-600">Tempo: {values.tempo}</div>
                  <div className="text-sm text-slate-600">Erros: {values.erros}</div>
                </div>
              ))}
            </div>
          </div>

          {(chartData.automaticos || chartData.controlados) && (
            <div className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-2 report-print-break-avoid">
              <div>
                <h3 className="mb-3 text-lg font-semibold text-zinc-900">Processos automáticos</h3>
                <FDTChart data={chartData.automaticos} />
              </div>
              <div>
                <h3 className="mb-3 text-lg font-semibold text-zinc-900">Processos controlados</h3>
                <FDTChart data={chartData.controlados} />
              </div>
            </div>
          )}

          {errorResults.length > 0 && (
            <div className="mb-6 rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5 report-print-break-avoid">
              <div className="mb-5 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900">Análise de erros</h3>
                  <p className="text-sm text-zinc-600">Distribuição de erros por etapa com leitura normativa.</p>
                </div>
                <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700 ring-1 ring-rose-100">
                  Total de etapas analisadas: <span className="font-semibold">{errorResults.length}</span>
                </div>
              </div>

              <div className="mb-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
                {errorResults.map(([stage, errorData]) => (
                  <div key={stage} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{STAGE_LABELS[stage] || stage}</p>
                        <p className="text-xs text-slate-500">{errorData.categoria}</p>
                      </div>
                      <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${CLASSIFICATION_STYLES[formatClassification(errorData.classificacao_guilmette || "")] || "bg-slate-100 text-slate-700"}`}>
                        {errorData.classificacao_guilmette || "—"}
                      </span>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-xl bg-slate-50 px-3 py-2">
                        <div className="text-slate-500">Qtde erros</div>
                        <div className="mt-1 font-semibold text-slate-900">{errorData.qtde_erros ?? "—"}</div>
                      </div>
                      <div className="rounded-xl bg-slate-50 px-3 py-2">
                        <div className="text-slate-500">Percentil</div>
                        <div className="mt-1 font-semibold text-slate-900">{errorData.percentil_manual || "—"}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-dashed border-black/10">
                      <th className="pb-3 text-left text-xs font-semibold uppercase text-zinc-500">Etapa</th>
                      <th className="pb-3 text-left text-xs font-semibold uppercase text-zinc-500">Categoria</th>
                      <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Erros</th>
                      <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Média</th>
                      <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Pontos Ponderados</th>
                      <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Percentil</th>
                      <th className="pb-3 text-center text-xs font-semibold uppercase text-zinc-500">Classificação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {errorResults.map(([stage, errorData]) => (
                      <tr key={stage} className="border-b border-dashed border-black/5">
                        <td className="py-3 text-zinc-900">{STAGE_LABELS[stage] || stage}</td>
                        <td className="py-3 text-zinc-700">{errorData.categoria || "—"}</td>
                        <td className="py-3 text-center text-zinc-700">{errorData.qtde_erros ?? "—"}</td>
                        <td className="py-3 text-center text-zinc-700">{errorData.media ?? "—"}</td>
                        <td className="py-3 text-center text-zinc-700">{errorData.pontos_ponderados ?? "—"}</td>
                        <td className="py-3 text-center text-zinc-700">
                          {typeof errorData.percentil === "number" ? errorData.percentil : (errorData.percentil_manual || "—")}
                        </td>
                        <td className="py-3 text-center">
                          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${CLASSIFICATION_STYLES[formatClassification(errorData.classificacao_guilmette || "")] || "bg-slate-100 text-slate-700"}`}>
                            {errorData.classificacao_guilmette || "—"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {interpretationParagraphs.length > 0 && (
            <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5 report-print-break-avoid">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-zinc-900">Interpretação Clínica</h3>
                  <p className="text-sm text-zinc-600">Leitura estruturada do desempenho automático, controlado e do padrão de erros.</p>
                </div>
                <div className="rounded-2xl bg-slate-100 px-4 py-2 text-xs font-medium text-slate-600">
                  {interpretationParagraphs.length} blocos clínicos
                </div>
              </div>
              <div className="space-y-4">
                {interpretationParagraphs.map((paragraph, index) => (
                  <div key={index} className="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-sm leading-6 text-zinc-700 shadow-sm">
                    {paragraph}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
