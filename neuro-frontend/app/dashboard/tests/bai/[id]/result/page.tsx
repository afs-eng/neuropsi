"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, LayoutDashboard } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { printCurrentPage } from "@/lib/print";
import { TestReportSummaryCard } from "@/components/tests/TestReportSummaryCard";

function ReportSection({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[28px] border border-slate-200 bg-white px-5 py-6 shadow-sm sm:px-8 sm:py-8">
      {eyebrow ? <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">{eyebrow}</p> : null}
      <h3 className="font-serif text-[2.3rem] font-semibold leading-none tracking-[-0.03em] text-slate-950 sm:text-[3.2rem]">
        {title}
      </h3>
      <div className="mt-6">{children}</div>
    </section>
  );
}

function getClassificationColor(classificacao: string) {
  const key = classificacao.toLowerCase();
  if (key === "mínimo" || key === "minimo") return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (key === "leve") return "bg-blue-50 text-blue-700 border-blue-200";
  if (key === "moderado") return "bg-yellow-50 text-yellow-700 border-yellow-200";
  if (key === "grave") return "bg-red-50 text-red-700 border-red-200";
  return "bg-slate-100 text-slate-700 border-slate-200";
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function ProfileScale({ rawScore, tScore }: { rawScore: number; tScore: number }) {
  const min = 20;
  const max = 80;
  const ticks = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80];
  const specialLabels: Record<number, string> = {
    20: "min",
    40: "-s",
    50: "m",
    60: "+s",
    80: "max",
  };
  const safeT = Math.max(min, Math.min(max, tScore));
  const width = 920;
  const height = 190;
  const leftLabelCol = 40;
  const leftValueCol = 40;
  const chartX = leftLabelCol + leftValueCol * 2;
  const chartWidth = 680;
  const rightBoxWidth = 200;
  const rulerY = 72;
  const tickBottomY = 86;
  const barY = 108;
  const barHeight = 74;
  const topLabelY = barY - 24;
  const rawLabelY = topLabelY;
  const step = chartWidth / (ticks.length - 1);
  const markerX = chartX + ((safeT - min) / (max - min)) * chartWidth;

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-[13px] leading-5 text-slate-700">
        <p className="font-semibold text-slate-900">Inventário de Ansiedade · Padrão</p>
        <p className="font-semibold">Amostra Geral · Escore T (50+10z)</p>
      </div>

      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-[190px] min-w-[920px] w-full">
          <text
            x={leftLabelCol + leftValueCol / 2}
            y={rawLabelY}
            transform={`rotate(-90 ${leftLabelCol + leftValueCol / 2} ${rawLabelY})`}
            textAnchor="start"
            className="fill-black text-[11px] font-bold"
          >
            Dados brutos
          </text>
          <text
            x={leftLabelCol + leftValueCol + leftValueCol / 2}
            y={topLabelY}
            transform={`rotate(-90 ${leftLabelCol + leftValueCol + leftValueCol / 2} ${topLabelY})`}
            textAnchor="start"
            className="fill-black text-[11px] font-bold"
          >
            Normas
          </text>

          <line x1={chartX} y1={rulerY} x2={chartX + chartWidth} y2={rulerY} stroke="#000000" strokeWidth="1" />

          {ticks.map((tick, index) => {
            const x = chartX + index * step;
            return (
              <g key={tick}>
                {specialLabels[tick] ? (
                  <text x={x} y="36" textAnchor="middle" className="fill-black text-[13px] font-medium">
                    {specialLabels[tick]}
                  </text>
                ) : null}
                <text x={x} y="56" textAnchor="middle" className="fill-[#4d626c] text-[11px]">
                  {tick}
                </text>
                <line x1={x} y1={rulerY} x2={x} y2={tickBottomY} stroke="#000000" strokeWidth="1" />
              </g>
            );
          })}

          <rect x={leftLabelCol} y={barY} width={leftValueCol} height={barHeight} fill="#e9fdff" />
          <rect x={leftLabelCol + leftValueCol} y={barY} width={leftValueCol} height={barHeight} fill="#e9fdff" />

          <text
            x={leftLabelCol + leftValueCol / 2}
            y={barY + barHeight / 2 + 5}
            textAnchor="middle"
            className="fill-[#4d626c] text-[14px]"
          >
            {rawScore}
          </text>
          <text
            x={leftLabelCol + leftValueCol + leftValueCol / 2}
            y={barY + barHeight / 2 + 5}
            textAnchor="middle"
            className="fill-[#4d626c] text-[14px]"
          >
            {formatNumber(safeT)}
          </text>

          <rect x={chartX} y={barY} width={chartWidth} height={barHeight} fill="#cccccc" />

          {ticks.map((_, index) => {
            const x = chartX + index * step;
            return <line key={index} x1={x} y1={barY} x2={x} y2={barY + barHeight} stroke="#ffffff" strokeWidth="2" />;
          })}

          <circle cx={markerX} cy={barY + barHeight / 2} r="8" fill="#c0000e" />

          <rect x={chartX + chartWidth} y={barY} width={rightBoxWidth} height={barHeight} fill="#e9fdff" />
          <text x={chartX + chartWidth + 16} y={barY + barHeight / 2 + 6} className="fill-black text-[14px] font-bold">
            Escore Total
          </text>
        </svg>
      </div>
    </div>
  );
}

function NormalCurve({ tScore, confidenceInterval }: { tScore: number; confidenceInterval: number[] }) {
  const width = 380;
  const height = 180;
  const paddingX = 28;
  const baselineY = 145;
  const xToSvg = (value: number) => paddingX + ((value - 20) / 60) * (width - paddingX * 2);
  const pdf = (x: number, mean: number, std: number) => {
    const coefficient = 1 / (std * Math.sqrt(2 * Math.PI));
    const exponent = Math.exp(-0.5 * ((x - mean) / std) ** 2);
    return coefficient * exponent;
  };

  const maxY = pdf(50, 50, 10);
  const points = Array.from({ length: 241 }, (_, index) => {
    const value = 20 + index * 0.25;
    const y = pdf(value, 50, 10);
    const svgY = baselineY - (y / maxY) * 88;
    return `${xToSvg(value)},${svgY}`;
  }).join(" ");

  const tScoreY = baselineY - (pdf(tScore, 50, 10) / maxY) * 88;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-[220px] w-full">
      <polyline fill="none" stroke="#8faab1" strokeWidth="1.5" points={points} />
      <polygon fill="rgba(165, 243, 252, 0.35)" points={`${xToSvg(20)},${baselineY} ${points} ${xToSvg(80)},${baselineY}`} />
      <line x1={xToSvg(20)} y1={baselineY} x2={xToSvg(80)} y2={baselineY} stroke="#111827" strokeWidth="1" />
      <line x1={xToSvg(tScore)} y1={baselineY} x2={xToSvg(tScore)} y2={tScoreY} stroke="#e11d48" strokeWidth="2" />
      <circle cx={xToSvg(tScore)} cy={tScoreY} r="4" fill="#e11d48" />
      <line
        x1={xToSvg(confidenceInterval[0])}
        y1={baselineY + 10}
        x2={xToSvg(confidenceInterval[1])}
        y2={baselineY + 10}
        stroke="#99f6e4"
        strokeWidth="6"
        strokeLinecap="round"
      />
      {[20, 30, 40, 50, 60, 70, 80].map((tick) => (
        <g key={tick}>
          <line x1={xToSvg(tick)} y1={baselineY} x2={xToSvg(tick)} y2={baselineY + 6} stroke="#475569" strokeWidth="1" />
          <text x={xToSvg(tick)} y={baselineY + 22} textAnchor="middle" className="fill-slate-500 text-[10px]">
            {tick}
          </text>
        </g>
      ))}
    </svg>
  );
}

function BAIResultPageContent() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const [applicationData, setApplicationData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [evaluationId, setEvaluationId] = useState(searchParams.get("evaluation_id") || "");

  const applicationId = params.id as string;

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await api.get<any>(`/api/tests/applications/${applicationId}`);
        setApplicationData(result);
        if (result?.evaluation_id && !evaluationId) {
          setEvaluationId(String(result.evaluation_id));
        }
      } catch (error) {
        console.error("Erro ao buscar dados da aplicação:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [applicationId, evaluationId]);

  const backHref = evaluationId ? `/dashboard/evaluations/${evaluationId}?tab=overview` : "/dashboard/evaluations?tab=overview";

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-primary"></div>
          <p className="text-sm text-slate-500">Carregando resultado...</p>
        </div>
      </div>
    );
  }

  if (!applicationData) {
    return (
      <div className="py-12 text-center">
        <p className="text-red-500">Dados da aplicação não encontrados</p>
      </div>
    );
  }

  const computed = applicationData.computed_payload || {};
  const classified = applicationData.classified_payload || {};
  const interpretation = applicationData.interpretation_text || "";
  const summary = computed.tables?.summary_table?.[0] || {};
  const detailTable = computed.tables?.detail_table || [];
  const classificationTable = computed.tables?.classification_table || [];
  const itemsTable = computed.tables?.items_table || [];
  const distributionTable = computed.tables?.distribution_table || [];

  const totalScore = computed.total_raw_score || 0;
  const classificacao = classified.classificacao?.label || computed.faixa_normativa || "Não classificado";
  const interpretationLabel = classified.classificacao?.interpretation || computed.interpretacao_faixa || "";
  const tScore = computed.t_score || 0;
  const confidenceInterval = computed.confidence_interval || [Math.max(20, tScore - 5), Math.min(80, tScore + 5)];

  return (
    <div className="mx-auto max-w-5xl space-y-8 report-print-shell">
      <div className="flex items-center justify-between gap-4 print:hidden report-print-hide">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push(backHref)} className="rounded-full">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">BAI - Resultado</h2>
            <p className="text-sm text-slate-500">Inventário de Ansiedade de Beck</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2 rounded-xl" onClick={printCurrentPage}>
            Imprimir / PDF
          </Button>
          <Button variant="outline" className="gap-2 rounded-xl" onClick={() => router.push(backHref)}>
            <LayoutDashboard className="h-4 w-4" />
            Voltar à Avaliação
          </Button>
        </div>
      </div>

      <div className="rounded-[30px] border border-slate-200 bg-white px-6 py-6 shadow-sm sm:px-8 report-print-content">
        <div className="flex flex-col gap-5 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Visão Geral</p>
            <h1 className="mt-2 font-serif text-[2.6rem] font-semibold leading-none tracking-[-0.04em] text-slate-950 sm:text-[4rem]">
              BAI
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              O Inventário de Ansiedade de Beck mede a intensidade de sintomas ansiosos a partir de 21 itens e permite classificar o resultado em níveis de intensidade da ansiedade.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm text-slate-600 sm:text-right">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Escala</p>
              <p className="mt-1 font-medium text-slate-800">Amostra Geral · Escore T</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">Faixa</p>
              <p className="mt-1 font-medium text-slate-800">18-90 anos</p>
            </div>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card className="rounded-2xl border-slate-200 shadow-none">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-500">Pontuação bruta</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-slate-900">{totalScore}</div>
            <p className="mt-2 text-xs text-slate-500">Escala de 0 a 63 pontos</p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-none">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-500">Valor da norma</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-slate-900">{formatNumber(tScore)}</div>
            <p className="mt-2 text-xs text-slate-500">Amostra Geral · Escore T</p>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-none">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-500">Classificação</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge className={`px-4 py-2 text-lg ${getClassificationColor(classificacao)}`}>{classificacao}</Badge>
            {interpretationLabel ? <p className="mt-2 text-xs text-slate-500">{interpretationLabel}</p> : null}
          </CardContent>
        </Card>
        </div>
      </div>

      <TestReportSummaryCard reportPayload={applicationData.report_payload} fallbackText={interpretation} />

      <ReportSection title="Perfil" eyebrow="Perfil BAI">
        <div className="overflow-x-auto">
          <div className="min-w-[760px]">
            <ProfileScale rawScore={totalScore} tScore={tScore} />
          </div>
        </div>
      </ReportSection>

      <ReportSection title="Tabela de escores" eyebrow="Tabela de Escores BAI">
        <div className="overflow-hidden border-t border-slate-900/80">
            <div className="grid grid-cols-[1.2fr_180px_180px] bg-white px-4 py-2 text-sm font-semibold text-slate-700">
              <div>Escala</div>
              <div className="text-center">Pontuação bruta</div>
              <div className="text-center">Valor da norma</div>
            </div>
            <div className="grid grid-cols-[1.2fr_180px_180px] border-t border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
              <div className="font-medium text-slate-900">{summary.scale || "Escore Total"}</div>
              <div className="bg-[#e9fbfd] text-center font-medium text-slate-900">{summary.raw_score ?? totalScore}</div>
              <div className="bg-[#e9fbfd] text-center font-medium text-slate-900">{summary.norm_value ?? formatNumber(tScore)}</div>
            </div>
            <div className="border-t border-slate-200 bg-[#e9fbfd] px-4 py-2 text-center text-sm font-medium text-slate-800">{summary.description || interpretationLabel}</div>
          </div>
      </ReportSection>

      <ReportSection title="Detalhes da escala" eyebrow="Detalhes da Escala BAI">
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_1fr]">
            <div className="overflow-hidden border border-slate-200">
              {detailTable.map((row: any, index: number) => (
                <div key={row.label} className={`grid grid-cols-[1fr_96px] px-4 py-3 text-sm ${index % 2 === 0 ? "bg-[#eefcfd]" : "bg-white"}`}>
                  <div className="font-medium text-slate-700">{row.label}</div>
                  <div className="text-right font-semibold text-slate-900">{row.value}</div>
                </div>
              ))}
            </div>

            <div className="border border-slate-200 bg-white p-4">
              <NormalCurve tScore={tScore} confidenceInterval={confidenceInterval} />
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-lg font-semibold text-slate-900">{interpretationLabel}</p>
              <p className="mt-2 text-sm leading-relaxed text-slate-700">
                O escore total é o resultado da soma dos escores dos itens individuais, que permite a classificação em níveis de intensidade da ansiedade.
              </p>
            </div>

            <div>
              <h3 className="mb-3 text-base font-semibold text-slate-900">Tabela de classificação</h3>
              <div className="overflow-hidden border border-slate-200">
                <div className="grid grid-cols-[180px_1fr] bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
                  <div>Faixa normativa</div>
                  <div>Interpretação</div>
                </div>
                {classificationTable.map((row: any, index: number) => (
                  <div key={row.classification} className={`grid grid-cols-[180px_1fr] border-t px-4 py-3 text-sm ${index % 2 === 0 ? "bg-[#eefcfd]" : "bg-white"}`}>
                    <div className="font-medium text-slate-900">{row.classification}</div>
                    <div className="text-slate-700">{row.description}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </ReportSection>

      <ReportSection title="Análise dos itens" eyebrow="Análise dos Itens BAI">
        <div className="overflow-hidden border border-slate-200">
            <div className="grid grid-cols-[72px_1fr_240px_72px] bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
              <div>Nr.</div>
              <div>Item (abreviado)</div>
              <div>Resposta</div>
              <div className="text-center">Pontos</div>
            </div>
            <div className="border-t bg-white px-4 py-2 text-sm font-semibold text-slate-900">Escore Total</div>
            <div className="max-h-[520px] overflow-y-auto">
              {itemsTable.map((item: any, index: number) => (
                <div key={item.item} className={`grid grid-cols-[72px_1fr_240px_72px] px-4 py-2 text-sm ${index % 2 === 0 ? "bg-[#eefcfd]" : "bg-white"}`}>
                  <div className="text-slate-700">{item.item}</div>
                  <div className="pr-4 text-slate-700">{item.item_short || item.label}</div>
                  <div className="text-slate-700">{item.response_label_with_code || item.response_label}</div>
                  <div className="text-center font-medium text-slate-900">{item.points}</div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-[1fr_80px] border-t bg-[#eefcfd] px-4 py-2 text-sm">
              <div className="text-right font-medium text-slate-700">Número de respostas faltantes (missing)</div>
              <div className="text-center font-semibold text-slate-900">{computed.missing_count || 0}</div>
            </div>
          </div>
      </ReportSection>

      <ReportSection title="Estatísticas das respostas" eyebrow="Estatísticas das Respostas BAI">
        <div className="space-y-6">
          <div>
            <h3 className="mb-4 text-base font-semibold text-slate-900">Distribuição das respostas</h3>
            <div className="space-y-3">
              {distributionTable.map((row: any) => (
                <div key={row.response_display_code} className="grid grid-cols-[88px_1fr_72px] items-center gap-4">
                  <div className="text-sm font-medium text-slate-700">{row.response_display_code}</div>
                  <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full bg-cyan-200" style={{ width: `${row.percent}%` }} />
                  </div>
                  <div className="text-right text-sm font-semibold text-slate-900">{Math.round(row.percent)} %</div>
                </div>
              ))}
            </div>
          </div>

          {interpretation ? (
            <div className="border border-slate-200 bg-slate-50 p-4 text-sm leading-relaxed text-slate-700 whitespace-pre-line">
              {interpretation}
            </div>
          ) : null}
        </div>
      </ReportSection>
    </div>
  );
}

function BAIResultPageFallback() {
  return <div className="space-y-6" />;
}

export default function BAIResultPage() {
  return (
    <Suspense fallback={<BAIResultPageFallback />}>
      <BAIResultPageContent />
    </Suspense>
  );
}
