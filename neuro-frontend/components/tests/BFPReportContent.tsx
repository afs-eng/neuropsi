import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import type { TestReportPayload } from "@/lib/test-report";
import { LayoutDashboard } from "lucide-react";

import {
  BFP_FACTOR_GROUPS,
  BFP_FACET_NAMES,
  formatScaleValue,
  getBfpClassificationColor,
} from "@/app/dashboard/tests/bfp/data";

export type ScaleResult = {
  code: string;
  name: string;
  raw_score: number;
  mean: number;
  sd: number;
  z_score: number;
  weighted_score: number;
  percentile: number;
  classification: string;
};

export type BFPApplicationData = {
  id: number;
  evaluation_id?: number;
  patient_name?: string;
  patient_sex?: string | null;
  patient_schooling?: string | null;
  applied_on?: string | null;
  report_payload?: TestReportPayload;
  raw_payload?: {
    sample?: string;
    responses?: Record<string, number>;
  };
  computed_payload?: {
    sample?: string;
    sample_label?: string;
    factors?: Record<string, ScaleResult>;
    facets?: Record<string, ScaleResult>;
  };
  interpretation_text?: string;
};

const SCHOOLING_LABELS: Record<string, string> = {
  preschool: "Ensino pré-escolar",
  elementary: "Ensino fundamental",
  elementary_incomplete: "Ensino fundamental incompleto",
  elementary_complete: "Ensino fundamental completo",
  middle: "Ensino médio",
  middle_incomplete: "Ensino médio incompleto",
  middle_complete: "Ensino médio completo",
  higher_incomplete: "Ensino superior incompleto",
  higher: "Ensino superior",
  higher_complete: "Ensino superior completo",
  postgraduate: "Pós-graduação",
};

function formatSchooling(value?: string | null) {
  if (!value) return "—";
  const normalized = String(value).trim().toLowerCase();
  if (SCHOOLING_LABELS[normalized]) {
    return SCHOOLING_LABELS[normalized];
  }
  return String(value)
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .replace(/(^|\s)\S/g, (char) => char.toUpperCase())
    .trim();
}

function formatSex(value?: string | null) {
  if (value === "M") return "Masculino";
  if (value === "F") return "Feminino";
  return value || "—";
}

function getGroupedRows(factors: Record<string, ScaleResult>, facets: Record<string, ScaleResult>) {
  return BFP_FACTOR_GROUPS.map((factor) => {
    const rows = factor.facets
      .map((code) => {
        const item = facets[code];
        if (!item) return null;
        return {
          code,
          name: item.name || BFP_FACET_NAMES[code as keyof typeof BFP_FACET_NAMES] || code,
          raw_score: item.raw_score,
          percentile: item.percentile,
          classification: item.classification,
        };
      })
      .filter(Boolean) as Array<{
        code: string;
        name: string;
        raw_score: number;
        percentile: number;
        classification: string;
      }>;

    const factorResult = factors[factor.code];

    return {
      code: factor.code,
      rows,
      summaryRow: factorResult
        ? {
          code: factor.code,
          name: factor.name,
          raw_score: factorResult.raw_score,
          percentile: factorResult.percentile,
          classification: factorResult.classification,
        }
        : null,
    };
  }).filter((group) => group.rows.length > 0 || group.summaryRow);
}

const BFP_RADAR_FACETS = [
  { code: "N1", label: "Vulnerabilidade", radarLabel: "Vulnerabilidade" },
  { code: "N2", label: "Instabilidade Emocional", radarLabel: "Instabilidade\nEmocional" },
  { code: "N3", label: "Passividade", radarLabel: "Passividade" },
  { code: "N4", label: "Depressão", radarLabel: "Depressão" },
  { code: "E1", label: "Comunicação", radarLabel: "Comunicação" },
  { code: "E2", label: "Altivez", radarLabel: "Altivez" },
  { code: "E3", label: "Dinamismo", radarLabel: "Dinamismo" },
  { code: "E4", label: "Interações Sociais", radarLabel: "Interações\nSociais" },
  { code: "S1", label: "Amabilidade", radarLabel: "Amabilidade" },
  { code: "S2", label: "Pró-sociabilidade", radarLabel: "Pró-sociabilidade" },
  { code: "S3", label: "Confiança nas Pessoas", radarLabel: "Confiança nas\nPessoas" },
  { code: "R1", label: "Competência", radarLabel: "Competência" },
  { code: "R2", label: "Ponderação", radarLabel: "Ponderação" },
  { code: "R3", label: "Empenho", radarLabel: "Empenho" },
  { code: "A1", label: "Abertura a Ideias", radarLabel: "Abertura a\nIdeias" },
  { code: "A2", label: "Liberalismo", radarLabel: "Liberalismo" },
  { code: "A3", label: "Busca por Novidades", radarLabel: "Busca por\nNovidades" },
] as const;

function polarPoint(cx: number, cy: number, radius: number, angle: number) {
  return {
    x: cx + radius * Math.cos(angle),
    y: cy + radius * Math.sin(angle),
  };
}

function polygonPoints(values: number[], cx: number, cy: number, radius: number) {
  return values
    .map((value, index) => {
      const angle = -Math.PI / 2 + (index / values.length) * Math.PI * 2;
      const point = polarPoint(cx, cy, (Math.max(0, Math.min(100, value)) / 100) * radius, angle);
      return `${point.x},${point.y}`;
    })
    .join(" ");
}

function BFPRadarChart({
  facets,
  compact = false,
  bare = false,
  printCompact = false,
  showLegend = true,
}: {
  facets: Record<string, ScaleResult>;
  compact?: boolean;
  bare?: boolean;
  printCompact?: boolean;
  showLegend?: boolean;
}) {
  const width = printCompact ? 680 : compact ? 800 : 900;
  const height = printCompact ? 680 : compact ? 800 : 900;
  const cx = width / 2;
  const cy = height / 2;
  const radius = printCompact ? 215 : compact ? 260 : 280;
  const rings = [20, 40, 60, 80, 100];
  const actualValues = BFP_RADAR_FACETS.map((facet) => Number(facets[facet.code]?.percentile || 0));
  const normValues = BFP_RADAR_FACETS.map(() => 50);

  const chart = (
    <>
      <div className="mt-6 flex justify-center overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className={`h-auto ${printCompact ? "min-w-[560px] max-w-[680px] print:min-w-[560px] print:max-w-[680px]" : compact ? "min-w-[640px] max-w-[800px]" : "min-w-[720px] max-w-[920px]"}`}>
          {rings.map((ring) => (
            <polygon
              key={ring}
              points={polygonPoints(BFP_RADAR_FACETS.map(() => ring), cx, cy, radius)}
              fill="none"
              stroke="#d1d5db"
              strokeWidth="1"
            />
          ))}

          {BFP_RADAR_FACETS.map((facet, index) => {
            const angle = -Math.PI / 2 + (index / BFP_RADAR_FACETS.length) * Math.PI * 2;
            const edge = polarPoint(cx, cy, radius, angle);
            const label = polarPoint(cx, cy, radius + (printCompact ? 38 : compact ? 46 : 54), angle);
            return (
              <g key={facet.code}>
                <line x1={cx} y1={cy} x2={edge.x} y2={edge.y} stroke="#e2e8f0" strokeWidth="1" />
                <text x={label.x} y={label.y} textAnchor="middle" className={`fill-slate-700 font-medium ${printCompact ? "text-[11px]" : compact ? "text-[13px]" : "text-[15px]"}`}>
                  {facet.radarLabel.split("\n").map((line, lineIndex) => (
                    <tspan key={`${facet.code}-${lineIndex}`} x={label.x} dy={lineIndex === 0 ? 0 : printCompact ? 12 : compact ? 14 : 16}>
                      {line}
                    </tspan>
                  ))}
                </text>
              </g>
            );
          })}

          {rings.map((ring) => (
            <text
              key={`label-${ring}`}
              x={cx}
              y={cy - (ring / 100) * radius - 6}
              textAnchor="middle"
              className={`fill-slate-400 ${printCompact ? "text-[10px]" : compact ? "text-[10px]" : "text-[12px]"}`}
            >
              {ring}
            </text>
          ))}

          <polygon points={polygonPoints(normValues, cx, cy, radius)} fill="rgba(59,130,246,0.04)" stroke="#2563eb" strokeWidth="2" />
          <polygon points={polygonPoints(actualValues, cx, cy, radius)} fill="rgba(244,63,94,0.18)" stroke="#e11d48" strokeWidth="3" />

          {actualValues.map((value, index) => {
            const angle = -Math.PI / 2 + (index / actualValues.length) * Math.PI * 2;
            const point = polarPoint(cx, cy, (Math.max(0, Math.min(100, value)) / 100) * radius, angle);
            return <circle key={`point-${BFP_RADAR_FACETS[index].code}`} cx={point.x} cy={point.y} r={compact ? "3.6" : "4.5"} fill="#be123c" stroke="#fff" strokeWidth="1.5" />;
          })}
        </svg>
      </div>

      {showLegend ? (
        <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-sm text-slate-600">
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-8 rounded-full bg-rose-600" />
            Resultado do avaliado
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-8 rounded-full bg-blue-600" />
            Referência normativa (percentil 50)
          </div>
        </div>
      ) : null}
    </>
  );

  if (bare) {
    return chart;
  }

  return (
    <div className="overflow-x-auto rounded-[28px] border border-slate-200 bg-white px-5 py-6 shadow-sm sm:px-8 sm:py-8 report-print-break-avoid">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Perfil Radial</p>
      <h3 className="font-serif text-[2.1rem] font-semibold leading-none tracking-[-0.03em] text-slate-950 sm:text-[3rem]">
        Radar das 17 Facetas do BFP
      </h3>
      <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
        O gráfico radar utiliza obrigatoriamente as 17 facetas do BFP, plotadas em percentis, com comparação direta à linha normativa fixa no percentil 50.
      </p>

      {chart}
    </div>
  );
}

function BFPFactorRadarChart({ factors }: { factors: Record<string, ScaleResult> }) {
  const factorAxis = BFP_FACTOR_GROUPS.map((factor) => ({
    code: factor.code,
    label: factor.name,
    percentile: Number(factors[factor.code]?.percentile || 0),
  }));
  const width = 360;
  const height = 300;
  const cx = width / 2;
  const cy = 150;
  const radius = 120;
  const rings = [20, 40, 60, 80, 100];
  const actualValues = factorAxis.map((item) => item.percentile);
  const normValues = factorAxis.map(() => 50);

  return (
    <div className="flex justify-center overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto min-w-[320px] max-w-[360px]">
        {rings.map((ring) => (
          <polygon key={ring} points={polygonPoints(factorAxis.map(() => ring), cx, cy, radius)} fill="none" stroke="#d1d5db" strokeWidth="1" />
        ))}

        {factorAxis.map((factor, index) => {
          const angle = -Math.PI / 2 + (index / factorAxis.length) * Math.PI * 2;
          const edge = polarPoint(cx, cy, radius, angle);
          const label = polarPoint(cx, cy, radius + 42, angle);
          return (
            <g key={factor.code}>
              <line x1={cx} y1={cy} x2={edge.x} y2={edge.y} stroke="#e2e8f0" strokeWidth="1" />
              <text x={label.x} y={label.y} textAnchor="middle" className="fill-slate-700 text-[10px] font-medium">
                {factor.label}
              </text>
            </g>
          );
        })}

        <polygon points={polygonPoints(normValues, cx, cy, radius)} fill="rgba(245,158,11,0.05)" stroke="#f59e0b" strokeWidth="2.4" />
        <polygon points={polygonPoints(actualValues, cx, cy, radius)} fill="rgba(14,116,144,0.28)" stroke="#0f766e" strokeWidth="3" />

        {actualValues.map((value, index) => {
          const angle = -Math.PI / 2 + (index / actualValues.length) * Math.PI * 2;
          const point = polarPoint(cx, cy, (Math.max(0, Math.min(100, value)) / 100) * radius, angle);
          return <circle key={`factor-point-${factorAxis[index].code}`} cx={point.x} cy={point.y} r="4.5" fill="#0f766e" stroke="#fff" strokeWidth="1.5" />;
        })}
      </svg>
    </div>
  );
}

function BFPFacetsLegend() {
  const factorColors: Record<string, string> = {
    NN: "text-orange-600",
    EE: "text-blue-500",
    SS: "text-teal-600",
    RR: "text-amber-600",
    AA: "text-violet-500",
  };

  return (
    <div className="grid gap-4 text-sm leading-6 text-slate-700 md:grid-cols-2 xl:grid-cols-3 print:gap-2.5 print:grid-cols-3 print:text-[11px] print:leading-5">
      {BFP_FACTOR_GROUPS.map((factor) => (
        <div key={factor.code} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 print:rounded-xl print:px-2.5 print:py-2 report-print-break-avoid">
          <div className={`text-xl font-semibold print:text-base ${factorColors[factor.code] || "text-sky-700"}`}>{factor.name}</div>
          <ul className="mt-2 space-y-1 text-[1rem] text-slate-700 print:mt-1 print:space-y-0 print:text-[0.82rem] print:leading-5">
            {factor.facets.map((facetCode) => (
              <li key={facetCode}>· {BFP_FACET_NAMES[facetCode] || facetCode}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function ReportPage({ pageNumber, children, compact = false }: { pageNumber: string; children: ReactNode; compact?: boolean }) {
  return (
    <section className={`relative mx-auto min-h-[297mm] w-full max-w-[210mm] overflow-hidden bg-white px-[16mm] shadow-[0_8px_28px_rgba(0,0,0,0.12)] print:shadow-none a4-print-page ${compact ? "pt-[14mm] pb-[11mm]" : "pt-[18mm] pb-[15mm]"}`}>
      <div className={`absolute left-[16mm] h-px w-[calc(100%-32mm)] bg-slate-400 ${compact ? "top-[8mm]" : "top-[10mm]"}`} />
      <div className={`a4-print-page-body ${compact ? "min-h-[calc(297mm-27mm)] pb-[18mm]" : "min-h-[calc(297mm-33mm)] pb-[24mm]"}`}>
        {children}
      </div>
      <div className={`absolute left-[16mm] h-px w-[calc(100%-32mm)] bg-slate-400 ${compact ? "bottom-[18mm]" : "bottom-[22mm]"}`} />
      <footer className={`absolute left-[16mm] right-[16mm] grid grid-cols-[135px_1fr_105px] items-center gap-4 text-slate-400 ${compact ? "bottom-[5mm] text-[6px]" : "bottom-[7mm] text-[7px]"}`}>
        <div className="text-sm font-black tracking-[0.12em] text-lime-700">SISTEMA</div>
        <div>Relatório gerado automaticamente. Os resultados devem ser integrados ao contexto clínico e avaliativo.</div>
        <div className="text-right text-[8px]">{pageNumber}</div>
      </footer>
    </section>
  );
}

function ReportHeader({ applicationCode, evaluationCode, appliedOn, compact = false }: { applicationCode: string; evaluationCode: string; appliedOn: string; compact?: boolean }) {
  return (
    <header className={`grid grid-cols-[1fr_250px] items-start border-b border-slate-400 ${compact ? "mb-[12px] min-h-[62px] gap-[14px] pb-3" : "mb-[18px] min-h-[78px] gap-[18px] pb-4"}`}>
      <div className={`grid items-start ${compact ? "grid-cols-[40px_1fr] gap-2.5 pt-[2px]" : "grid-cols-[48px_1fr] gap-3 pt-[4px]"}`}>
        <div className={`grid place-items-center rounded-[14px] bg-gradient-to-br from-[#123a78] to-[#4d86c6] font-extrabold tracking-[-0.08em] text-white ${compact ? "h-10 w-10 text-[16px]" : "h-12 w-12 text-[19px]"}`}>BFP</div>
        <div className="self-center">
          <div className={`font-black leading-none tracking-[-0.06em] text-[#202a44] ${compact ? "text-[24px]" : "text-[28px]"}`}>BFP</div>
          <div className={`font-extrabold uppercase leading-[1.15] tracking-[0.05em] text-[#202a44] ${compact ? "mt-1 text-[8px]" : "mt-[3px] text-[9px]"}`}>Bateria Fatorial de Personalidade</div>
        </div>
      </div>
      <div className={`uppercase text-slate-600 ${compact ? "space-y-[5px] pt-[1px] text-[7.8px]" : "space-y-[7px] pt-[2px] text-[8.5px]"}`}>
        <div className={`grid grid-cols-[1fr_92px] items-center gap-3 ${compact ? "min-h-[12px]" : "min-h-[15px]"}`}><span>Código da aplicação</span><strong className={`text-right text-slate-900 ${compact ? "text-[8px]" : "text-[9px]"}`}>{applicationCode}</strong></div>
        <div className={`grid grid-cols-[1fr_92px] items-center gap-3 ${compact ? "min-h-[12px]" : "min-h-[15px]"}`}><span>Código da avaliação</span><strong className={`text-right text-slate-900 ${compact ? "text-[8px]" : "text-[9px]"}`}>{evaluationCode}</strong></div>
        <div className={`grid grid-cols-[1fr_92px] items-center gap-3 ${compact ? "min-h-[12px]" : "min-h-[15px]"}`}><span>Data da aplicação</span><strong className={`text-right text-slate-900 ${compact ? "text-[8px]" : "text-[9px]"}`}>{appliedOn}</strong></div>
      </div>
    </header>
  );
}

function DataField({ label, value }: { label: string; value: string }) {
  const isNameField = label === "Nome";

  return (
    <div className={`grid min-h-[30px] items-center bg-[#e8f5fb] px-[10px] text-[9.3px] ${isNameField ? "grid-cols-[72px_1fr] gap-0" : "grid-cols-[82px_1fr] gap-2"}`}>
      <div className="py-2 uppercase text-slate-600">{label}</div>
      <div className="py-2 font-bold text-slate-600">{value}</div>
    </div>
  );
}

interface BFPReportContentProps {
  application: BFPApplicationData;
  applicationId: string;
  evaluationId?: string;
  onPrint?: () => void;
  onEdit?: () => void;
  onBack?: () => void;
  hideActions?: boolean;
  printVariant?: "full" | "summary";
}

export function BFPReportContent({
  application,
  applicationId,
  evaluationId,
  onPrint,
  onEdit,
  onBack,
  hideActions = false,
  printVariant = "full",
}: BFPReportContentProps) {
  const computed = application.computed_payload || {};
  const factors = computed.factors || {};
  const facets = computed.facets || {};
  const interpretation = application.interpretation_text || "";
  const responseValues = Object.values(application.raw_payload?.responses || {});
  const sampleLabel = computed.sample_label || application.raw_payload?.sample || "Geral";
  const appliedOn = application.applied_on ? new Date(application.applied_on).toLocaleDateString("pt-BR") : "—";
  const answeredCount = responseValues.filter((value) => value >= 1 && value <= 7).length;
  const isSummaryPrint = printVariant === "summary";
  const interpretationParagraphs = interpretation
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
  const introInterpretation = interpretationParagraphs[0] || "";
  const factorInterpretations = BFP_FACTOR_GROUPS.map((factor, index) => ({
    title: factor.name,
    text: interpretationParagraphs[index + 1] || "",
  })).filter((item) => item.text);
  const finalInterpretation = interpretationParagraphs[BFP_FACTOR_GROUPS.length + 1] || "";
  const groupedRows = getGroupedRows(factors, facets);
  const applicationCode = String(application.id || applicationId || "—");
  const evaluationCode = evaluationId || String(application.evaluation_id || "—");

  const pageOneSection = (
    <ReportPage pageNumber="1 / 4">
      <ReportHeader applicationCode={applicationCode} evaluationCode={evaluationCode} appliedOn={appliedOn} />

      <h1 className="mb-3 text-[22px] font-bold text-[#123a78]">Dados do avaliado</h1>
      <div className="mb-[18px] grid grid-cols-2 gap-x-[18px] gap-y-[12px]">
        <DataField label="Nome" value={application.patient_name || "—"} />
        <DataField label="Tabela normativa" value={`Percentil - ${sampleLabel}`} />
        <DataField label="Aplicação" value={appliedOn} />
        <DataField label="Sexo" value={formatSex(application.patient_sex)} />
        <DataField label="Escolaridade" value={formatSchooling(application.patient_schooling)} />
        <DataField label="Itens válidos" value={`${answeredCount} / 126`} />
      </div>

      <div className="my-4 grid grid-cols-[170px_1fr] gap-4 border-y border-slate-400 py-3">
        <h2 className="text-[18px] font-bold text-[#123a78]">Personalidade</h2>
        <div className="space-y-1.5 text-[12px] text-slate-600">
          <p className="m-0 text-justify">A Bateria Fatorial de Personalidade investiga traços de personalidade com base no modelo dos Cinco Grandes Fatores, permitindo análise ampla do funcionamento emocional, interpessoal, motivacional e comportamental.</p>
          <p className="m-0 text-justify">O resultado deve ser interpretado por profissional habilitado e integrado à entrevista, observação clínica e demais dados disponíveis no processo avaliativo.</p>
        </div>
      </div>

      <div className="grid grid-cols-[1.1fr_0.9fr] gap-7">
        <div>
          <div className="mb-[14px] text-center text-[15px] font-black uppercase text-[#123a78]">Radar de avaliação dos fatores</div>
          <div className="mb-2 flex items-center justify-center gap-4 text-[9px] text-slate-600">
            <span className="inline-flex items-center gap-1.5"><span className="h-[10px] w-9 border-2 border-[#0d2858] bg-[rgba(18,58,120,.35)]"></span>Resultado do avaliado</span>
            <span className="inline-flex items-center gap-1.5"><span className="h-[10px] w-9 border-2 border-[#f28f22] bg-white"></span>Amostra normativa</span>
          </div>
          <div className="grid min-h-[330px] place-items-center">
            <BFPFactorRadarChart factors={factors} />
          </div>
        </div>
        <div>
          <div className="mb-[14px] text-center text-[15px] font-black uppercase text-[#123a78]">Fatores avaliados</div>
          <div className="grid gap-3 text-[10px] text-slate-600">
            {BFP_FACTOR_GROUPS.map((factor) => (
              <p key={factor.code} className="m-0 text-left"><strong className="text-[#123a78]">{factor.name}:</strong> {factor.summary}</p>
            ))}
          </div>
        </div>
      </div>
    </ReportPage>
  );

  const pageTwoSection = (
    <ReportPage pageNumber="2 / 4">
      <ReportHeader applicationCode={applicationCode} evaluationCode={evaluationCode} appliedOn={appliedOn} />

      <div className="mt-[22px] grid grid-cols-[1.28fr_0.72fr] gap-6">
        <div>
          <div className="mb-[14px] text-center text-[15px] font-black uppercase text-[#123a78]">Radar de avaliação das facetas</div>
          <div className="mb-2 flex items-center justify-center gap-4 text-[9px] text-slate-600">
            <span className="inline-flex items-center gap-1.5"><span className="h-[10px] w-9 border-2 border-[#0d2858] bg-[rgba(18,58,120,.35)]"></span>Resultado do avaliado</span>
            <span className="inline-flex items-center gap-1.5"><span className="h-[10px] w-9 border-2 border-[#f28f22] bg-white"></span>Amostra normativa</span>
          </div>
          <div className="grid min-h-[410px] place-items-center">
            <BFPRadarChart facets={facets} compact bare printCompact showLegend={false} />
          </div>
        </div>
        <div>
          <div className="mb-[14px] text-center text-[15px] font-black uppercase text-[#123a78]">Facetas avaliadas</div>
          <div className="ml-8 mt-10 max-w-[210px] justify-self-end text-[12px] leading-[1.35] text-slate-600">
            {BFP_FACTOR_GROUPS.map((factor) => (
              <div key={factor.code} className="mb-6">
                <strong className="text-[#123a78]">{factor.name}:</strong>
                <ul className="mt-1 ml-[18px] list-disc p-0">
                  {factor.facets.map((facetCode) => (
                    <li key={facetCode}>{BFP_FACET_NAMES[facetCode] || facetCode}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    </ReportPage>
  );

  return (
    <div className="report-print-shell mx-auto max-w-6xl space-y-8 bg-slate-100 px-0 py-6 print:bg-white print:py-0">
      {!hideActions && (
        <div className="mx-auto flex max-w-[210mm] items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm print:hidden report-print-hide">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">BFP - Resultado</h2>
            <p className="text-sm text-slate-500">Bateria Fatorial de Personalidade</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {onPrint ? <Button variant="outline" className="gap-2 rounded-xl" onClick={onPrint}>Imprimir / PDF</Button> : null}
            {onEdit ? <Button variant="outline" className="gap-2 rounded-xl" onClick={onEdit}>Editar aplicação</Button> : null}
            {onBack ? <Button variant="outline" className="gap-2 rounded-xl" onClick={onBack}><LayoutDashboard className="h-4 w-4" />{evaluationId ? "Voltar à Avaliação" : "Voltar"}</Button> : null}
          </div>
        </div>
      )}

      {pageOneSection}

      {pageTwoSection}

      <ReportPage pageNumber="3 / 4" compact>
        <ReportHeader applicationCode={applicationCode} evaluationCode={evaluationCode} appliedOn={appliedOn} compact />
        <div className="mb-3 rounded-[18px] border border-[#d7dfea] bg-gradient-to-b from-[#fcfdff] to-white px-[18px] pt-4 pb-[16px]">
          <div className="mb-1 text-[7px] font-extrabold uppercase tracking-[0.22em] text-[#557099]">Resultados normativos</div>
          <h2 className="mb-2 font-serif text-[28px] font-bold leading-none text-[#071a45]">Tabela de resultados</h2>
          <table className="w-full border-collapse text-[12px] leading-[1.15] text-[#12233f]">
            <thead>
              <tr>
                <th className="border-y border-[#90a3c4] px-2 py-[4px] text-center font-extrabold text-[#102e68]">Faceta/Dimensãoas</th>
                <th className="border-y border-[#90a3c4] px-2 py-[4px] text-center font-extrabold text-[#102e68]">Escore Bruto</th>
                <th className="border-y border-[#90a3c4] px-2 py-[4px] text-center font-extrabold text-[#102e68]">Percentil</th>
                <th className="border-y border-[#90a3c4] px-2 py-[4px] text-center font-extrabold text-[#102e68]">Classificação</th>
              </tr>
            </thead>
            <tbody>
              {groupedRows.map((group) => (
                <>
                  {group.summaryRow ? (
                    <tr key={`${group.code}-factor`} className="bg-[#fbfcff] font-extrabold text-[#071a45]">
                      <td className="border-b border-t border-[#90a3c4] px-2 py-[4px] uppercase">{group.summaryRow.name}</td>
                      <td className="border-b border-t border-[#90a3c4] px-2 py-[4px] text-center whitespace-nowrap">{formatScaleValue(group.summaryRow.raw_score, 2)}</td>
                      <td className="border-b border-t border-[#90a3c4] px-2 py-[4px] text-center whitespace-nowrap">{formatScaleValue(group.summaryRow.percentile, 1)}</td>
                      <td className="border-b border-t border-[#90a3c4] px-2 py-[4px] text-center whitespace-nowrap">{group.summaryRow.classification || "-"}</td>
                    </tr>
                  ) : null}
                  {group.rows.map((row) => (
                    <tr key={row.code}>
                      <td className="border-b border-[#dbe3ef] px-2 py-[10px]">{row.name}</td>
                      <td className="border-b border-[#dbe3ef] px-2 py-[10px] text-center whitespace-nowrap">{formatScaleValue(row.raw_score, 2)}</td>
                      <td className="border-b border-[#dbe3ef] px-2 py-[10px] text-center whitespace-nowrap">{formatScaleValue(row.percentile, 1)}</td>
                      <td className="border-b border-[#dbe3ef] px-2 py-[10px] text-center whitespace-nowrap">{row.classification || "-"}</td>
                    </tr>
                  ))}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </ReportPage>

      <ReportPage pageNumber="4 / 4">
        <ReportHeader applicationCode={applicationCode} evaluationCode={evaluationCode} appliedOn={appliedOn} />
        <div className="mb-[18px] rounded-[18px] border border-[#d7dfea] bg-gradient-to-b from-[#fcfdff] to-white px-[22px] pt-5 pb-[22px]">
          <div className="mb-1 text-[8px] font-extrabold uppercase tracking-[0.24em] text-[#557099]">Interpretação clínica</div>
          <h2 className="mb-3 font-serif text-[32px] font-bold leading-[1.05] text-[#071a45]">Síntese dos resultados</h2>
          {interpretation ? (
            <div className="space-y-3 text-[10.2px] leading-[1.58] text-[#24324a]">
              {introInterpretation ? <p className="m-0 text-justify">{introInterpretation}</p> : null}
              {factorInterpretations.map((item) => (
                <div key={item.title} className="mb-[11px]">
                  <h4 className="mb-[3px] text-[12.5px] font-extrabold text-[#123a78]">{item.title}</h4>
                  <p className="m-0 text-justify">{item.text}</p>
                </div>
              ))}
              <hr className="my-3 border-0 border-t border-[#cfd8e6]" />
              {finalInterpretation ? <p className="m-0 text-justify">{finalInterpretation}</p> : null}
            </div>
          ) : (
            <div className="text-[10.2px] text-[#24324a]">Interpretação ainda não disponível para esta aplicação.</div>
          )}
        </div>
      </ReportPage>
    </div>
  );
}
