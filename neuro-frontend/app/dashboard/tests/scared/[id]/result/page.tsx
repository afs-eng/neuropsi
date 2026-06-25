"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { getToken, resolveApiUrl } from "@/lib/api";
import { TestReportSummaryCard } from "@/components/tests/TestReportSummaryCard";
import { TestReportPayload } from "@/lib/test-report";

const FACTOR_NAMES: Record<string, string> = {
  panico_sintomas_somaticos: "Pânico / Sintomas Somáticos",
  ansiedade_generalizada: "Ansiedade Generalizada",
  ansiedade_separacao: "Ansiedade de Separação",
  fobia_social: "Fobia Social",
  evitacao_escolar: "Evitação Escolar",
  total: "Total",
};

const CHILD_ITEMS: Record<number, string> = {
  1: "Quando eu fico com medo, eu tenho dificuldade de respirar.",
  2: "Eu sinto dor de cabeça quando estou na escola.",
  3: "Eu não gosto de estar com pessoas que não conheço bem.",
  4: "Fico com medo quando durmo fora de casa.",
  5: "Eu me preocupo se outras pessoas gosta de mim.",
  6: "Quando eu fico com medo, eu siento como se eu fosse desmaiar.",
  7: "Eu sou nervoso(a).",
  8: "Eu sigo a minha mãe ou o meu pai aonde eles vão.",
  9: "As pessoas me dizem que pareço nervoso(a).",
  10: "Eu fico nervoso(a) com pessoas que eu não conheço bem.",
  11: "Eu tenho dor de barriga na escola.",
  12: "Quando eu fico com medo, eu acho que vou enlouquecer.",
  13: "Eu tenho medo de dormir sozinho(a).",
  14: "Eu me preocupo em ser tão bom quanto as outras crianças.",
  15: "Quando eu fico com medo, tenho a impressão de que as coisas não são reais.",
  16: "Eu tenho pesadelos com coisas ruins acontecendo com os meus pais.",
  17: "Eu fico preocupo quando tenho que ir à escola.",
  18: "Quando eu fico com medo, o meu coração bate rápido.",
  19: "Quando eu fico nervoso(a), eu tremo de medo.",
  20: "Eu tenho pesadelos com alguma coisa ruim acontecendo comigo.",
  21: "Eu fico preocupado(a) se as coisas vão dar certo para mim.",
  22: "Quando eu fico com medo, eu suo muito.",
  23: "Eu sou muito preocupado(a).",
  24: "Eu fico com muito medo sem nenhum motivo.",
  25: "Eu tenho medo de ficar sozinho(a) em casa.",
  26: "Eu tenho dificultades para falar com pessoas que não conheço bem.",
  27: "Quando eu fico com medo, eu me siento sufocado.",
  28: "As pessoas dizem que eu me preocupo demais.",
  29: "Eu não gosto de ficar longe da família.",
  30: "Eu tenho medo de ter ataques de ansiedade (ou ataques de pânico).",
  31: "Eu tenho medo de que alguma coisa ruim aconteça com meus pais.",
  32: "Eu fico com vergonha na frente de pessoas que não conheço bem.",
  33: "Eu me preocupo muito com o que vai acontecer no futuro.",
  34: "Quando eu fico com medo, eu tenho vontade de vomitar.",
  35: "Eu me preocupo muito em fazer as coisas bem feitas.",
  36: "Eu tenho medo de ir à escola.",
  37: "Eu me preocupo com as coisas que já aconteceram.",
  38: "Quando eu fico com medo, eu me siento tonto(a).",
  39: "Fico nervoso(a) quando estou com outras crianças ou adultos e tenho que fazer algo enquanto eles me olham.",
  40: "Eu fico nervoso(a) para ir a festas, bailes ou qualquer lugar onde estejam pessoas que não conheço bem.",
  41: "Eu sou tímido(a).",
};

const PARENT_ITEMS: Record<number, string> = {
  1: "Quando meu/minha filho(a) fica com medo, ele/ela tem dificuldades para respirar.",
  2: "Meu/minha filho(a) sente dor de cabeça quando está na escola.",
  3: "Meu/minha filho(a) não gosta de estar com pessoas que não conhece bem.",
  4: "Meu/minha filho(a) fica com medo quando dorme fora de casa.",
  5: "Meu/minha filho(a) se preocupa se as outras pessoas gosta dele/dela.",
  6: "Quando meu/minha filho(a) fica com medo, ele/ela se sente como se fosse desmaiar.",
  7: "Meu/minha filho(a) é nervoso(a).",
  8: "Meu/minha filho(a) me segue aonde quer que eu vá.",
  9: "As pessoas me dizem que meu/minha filho(a) parece nervoso(a).",
  10: "Meu/minha filho(a) fica nervoso(a) com pessoas que ele não conhece bem.",
  11: "Meu/minha filho(a) tem dor de barriga na escola.",
  12: "Quando meu/minha filho(a) fica com medo, ele acha que vai enlouquecer.",
  13: "Meu/minha filho(a) tem medo de dormir sozinho(a).",
  14: "Meu/minha filho(a) se preocupa em ser tão bom quanto as outras crianças.",
  15: "Quando meu/minha filho(a) fica com medo, ele/ela tem a impressão de que as coisas não são reais.",
  16: "Meu/minha filho(a) tem pesadelos com coisas ruins acontecendo com os seus pais.",
  17: "Meu/minha filho(a) fica preocupado quando tem que ir à escola.",
  18: "Quando meu/minha filho(a) fica com medo, o seu coração bate rápido.",
  19: "Quando meu/minha filho(a) fica nervoso, ele treme de medo.",
  20: "Meu/minha filho(a) tem pesadelos com alguma coisa ruim acontecendo com ele.",
  21: "Meu/minha filho(a) fica preocupado se as coisas vai dar certo para ele/ela.",
  22: "Quando meu/minha filho(a) fica com medo, ele sua muito.",
  23: "Meu/minha filho(a) é muito preocupado(a).",
  24: "Meu/minha filho(a) fica com muito medo(a) sem nenhum motivo.",
  25: "Meu/minha filho(a) tem medo de ficar sozinho(a) em casa.",
  26: "Meu/minha filho(a) tem dificuldade para falar com pessoas que não conhece bem.",
  27: "Quando meu/minha filho(a) fica com medo, ele se sente sufocado(a).",
  28: "As pessoas me dizem que meu/minha filho(a) se preocupa demais.",
  29: "Meu/minha filho(a) não gosta de ficar longe de sua família.",
  30: "Meu/minha filho(a) tem medo de ter ataques de ansiedade (ou ataques de pânico).",
  31: "Meu/minha filho(a) tem medo de que alguma coisa ruim possa acontecer comigo ou com o pai / a mãe dele/dela.",
  32: "Meu/minha filho(a) fica com vergonha na frente de pessoas que não conhece bem.",
  33: "Meu/minha filho(a) se preocupo muito com o que vai acontecer no futuro.",
  34: "Quando meu/minha filho(a) fica com medo, ele tem vontade de vomitar.",
  35: "Meu/minha filho(a) se preocupo muito em fazer as coisas bem feitas.",
  36: "Meu/minha filho(a) tem medo de ir à escola.",
  37: "Meu/minha filho(a) se preocupo com as coisas que já aconteceram.",
  38: "Quando meu/minha filho(a) fica com medo, ele se sente tonto(a).",
  39: "Meu/minha filho(a) fica nervoso(a) quando está com outras crianças ou adultos e tem que fazer algo enquanto eles lhe olham.",
  40: "Meu/minha filho(a) fica nervoso(a) quando vai a festas, bailes ou qualquer lugar onde estejam pessoas que ele não conhece bem.",
  41: "Meu/minha filho(a) é tímido(a).",
};

const PARENT_BADGE_STYLES: Record<string, string> = {
  "Clínico": "bg-red-100 text-red-700 border-red-200",
  "Não clínico": "bg-emerald-100 text-emerald-700 border-emerald-200",
};

const CHILD_BADGE_STYLES: Record<string, string> = {
  "Na Média": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Superior": "bg-amber-100 text-amber-700 border-amber-200",
  "Muito Superior": "bg-red-100 text-red-700 border-red-200",
};

type SCAREDResult = {
  application_id: number;
  evaluation_id: number;
  patient_name: string;
  applied_on: string;
  interpretation: string;
  interpretation_text?: string;
  report_payload?: TestReportPayload;
  raw_payload: any;
  computed_payload: any;
  classified_payload: any;
};

function getFormLabel(formType?: string) {
  return formType === "parent" ? "Pais/Cuidadores" : "Autorrelato";
}

function formatAppliedOn(value: string) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR");
}

function formatNumber(value: unknown) {
  if (value === undefined || value === null || value === "") return "—";
  if (typeof value === "number") {
    return value.toLocaleString("pt-BR", {
      minimumFractionDigits: value % 1 === 0 ? 0 : 2,
      maximumFractionDigits: 2,
    });
  }
  return String(value);
}

function getDisplayClassification(formType: string, classificacao: string) {
  if (formType === "parent") return classificacao;

  const classificationMap: Record<string, string> = {
    "Na Média": "Média",
    Elevado: "Superior",
    "Muito Elevado": "Muito Superior",
  };

  return classificationMap[classificacao] || classificacao;
}

function getClassificationStyle(formType: string, classification: string) {
  const styles = formType === "parent" ? PARENT_BADGE_STYLES : CHILD_BADGE_STYLES;
  return styles[classification] || "bg-slate-100 text-slate-700 border-slate-200";
}

function ResultCard({ result }: { result: SCAREDResult }) {
  const raw = result.raw_payload || {};
  const computed = result.computed_payload || {};
  const classified = result.classified_payload || {};
  const rows = classified.analise_geral || [];
  const formType = classified.form_type || computed.form || "child";
  const formLabel = getFormLabel(formType);
  const itemLabels = formType === "parent" ? PARENT_ITEMS : CHILD_ITEMS;
  const responses = raw.responses || {};
  const factorOrder = [
    "panico_sintomas_somaticos",
    "ansiedade_generalizada",
    "ansiedade_separacao",
    "fobia_social",
    "evitacao_escolar",
    "total",
  ];
  const rowByFactor = Object.fromEntries(rows.map((row: any) => [row.fator, row]));
  const responseRows = [];
  for (let i = 0; i < 9; i++) {
    responseRows.push([i + 1, i + 10, i + 19, i + 28, i + 37].filter((item) => item <= 41));
  }
  const interpretationText = result.interpretation || "";
  const interpretationParagraphs = interpretationText
    .split(/\n\s*\n/)
    .map((paragraph: string) => paragraph.trim())
    .filter(Boolean);

  return (
    <div className="rounded-[28px] bg-white/70 p-5 shadow-lg ring-1 ring-black/5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-zinc-900">{formLabel}</h3>
        <span className="text-sm text-zinc-500">Aplicado em {formatAppliedOn(result.applied_on)}</span>
      </div>

      <div className="mb-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {factorOrder.map((factor) => {
          const row = rowByFactor[factor] || {};
          const classification = getDisplayClassification(formType, row.classificacao || "—");
          const percentileValue = formType === "parent" ? row.percentual : row.percentil;
          return (
            <div key={factor} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-sm font-semibold text-slate-900">{FACTOR_NAMES[factor]}</div>
              <div className="mt-3 text-3xl font-bold text-slate-900">{formatNumber(row.escore_bruto)}</div>
              <div className="mt-2 text-sm text-slate-500">
                {formType === "parent"
                  ? `Percentual do fator: ${formatNumber(percentileValue)}`
                  : `Percentil: ${formatNumber(percentileValue)}`}
              </div>
              <div className="mt-3">
                <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium ${getClassificationStyle(formType, classification)}`}>
                  {classification}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="overflow-x-auto mb-6">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dashed border-black/10">
              <th className="pb-3 text-left text-xs font-semibold text-zinc-500 uppercase">Fator</th>
              <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">Pontos Brutos</th>
              <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">
                {formType === "parent" ? "Nota de Corte" : "Média"}
              </th>
              <th className="pb-3 text-center text-xs font-semibold text-zinc-500 uppercase">
                {formType === "parent" ? "Percentual" : "Percentil"}
              </th>
              <th className="pb-3 text-left text-xs font-semibold text-zinc-500 uppercase">Classificação</th>
            </tr>
          </thead>
          <tbody>
            {factorOrder.map((factor) => {
              const row = rowByFactor[factor] || {};
              const classification = getDisplayClassification(formType, row.classificacao || "—");
              return (
                <tr key={factor} className="border-b border-dashed border-black/5">
                  <td className="py-3 text-zinc-900 font-medium">{FACTOR_NAMES[factor]}</td>
                  <td className="py-3 text-center font-medium text-zinc-900">{formatNumber(row.escore_bruto)}</td>
                  <td className="py-3 text-center text-zinc-600">{formatNumber(formType === "parent" ? row.nota_corte : row.media)}</td>
                  <td className="py-3 text-center text-zinc-600">{formatNumber(formType === "parent" ? row.percentual : row.percentil)}</td>
                  <td className="py-3 text-zinc-600">{classification}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="rounded-[20px] bg-white/70 p-4 mb-4">
        <h4 className="mb-3 text-base font-semibold text-zinc-900">Registro de Respostas</h4>
        <div className="border rounded-xl overflow-hidden bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-100">
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
              </tr>
            </thead>
            <tbody>
              {responseRows.map((row, idx) => (
                <tr key={idx} className={`border-t ${idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}>
                  {row.map((itemNumber) => {
                    const value = responses[String(itemNumber)];
                    const style =
                      value === 2 ? "bg-red-100 text-red-800 font-bold" :
                      value === 1 ? "bg-amber-100 text-amber-800 font-bold" :
                      value === 0 ? "bg-slate-200 text-slate-700 font-bold" :
                      "bg-slate-100 text-slate-400";

                    return [
                      <td key={`item-${idx}-${itemNumber}`} className="py-1 px-2 text-center text-slate-700 font-medium">
                        {String(itemNumber).padStart(2, "0")}
                      </td>,
                      <td key={`resp-${idx}-${itemNumber}`} className="py-1 px-2 text-center">
                        <span className={`inline-block w-8 h-6 leading-6 rounded ${style}`}>
                          {value ?? "-"}
                        </span>
                      </td>,
                    ];
                  })}
                  {Array.from({ length: 5 - row.length }).map((_, emptyIdx) => [
                    <td key={`empty-item-${idx}-${emptyIdx}`} className="py-1 px-2" />,
                    <td key={`empty-resp-${idx}-${emptyIdx}`} className="py-1 px-2" />,
                  ])}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
        <p className="text-sm text-amber-800"><strong>Sexo:</strong> {classified.sexo || "Não informado"}</p>
        <p className="text-sm text-amber-800"><strong>Grupo etário:</strong> {classified.grupo_etario || "Não informado"}</p>
        <p className="text-sm text-amber-800"><strong>Síntese:</strong> {classified.sintese || "Sem síntese disponível."}</p>
      </div>

      <div className="space-y-4">
        {interpretationParagraphs.length > 0 ? (
          interpretationParagraphs.map((paragraph: string, index: number) => (
            <div key={index} className="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-sm leading-6 text-zinc-700 shadow-sm whitespace-pre-wrap">
              {paragraph}
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-sm leading-6 text-zinc-700 shadow-sm">
            Sem interpretação disponível.
          </div>
        )}
      </div>
    </div>
  );
}

export default function SCAREDResultPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const [results, setResults] = useState<SCAREDResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [exportingPdf, setExportingPdf] = useState(false);
  const evaluationId = searchParams.get("evaluation_id");

  const handleExportPdf = async () => {
    if (!params.id || exportingPdf) return;
    setExportingPdf(true);
    try {
      const token = getToken() || "";
      const response = await fetch(resolveApiUrl(`/api/tests/applications/${params.id}/export-pdf`), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        cache: "no-store",
      });

      if (!response.ok) {
        let message = `Falha ao gerar PDF (${response.status})`;
        try {
          const payload = await response.json();
          if (payload?.message) message = `${message}: ${payload.message}`;
        } catch {}
        throw new Error(message);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (error: any) {
      console.error(error);
      alert(error?.message || "Não foi possível gerar o PDF do SCARED.");
    } finally {
      setExportingPdf(false);
    }
  };

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const { api } = await import("@/lib/api");
        const scaredResults: SCAREDResult[] = [];
        const seenApplicationIds = new Set<number>();

        const appendResult = (resultData: SCAREDResult | null | undefined) => {
          if (!resultData || seenApplicationIds.has(resultData.application_id)) return;
          seenApplicationIds.add(resultData.application_id);
          scaredResults.push(resultData);
        };

        if (params.id) {
          try {
            const primaryResult = await api.get<SCAREDResult>(`/api/tests/scared/result/${params.id}`);
            appendResult(primaryResult);
          } catch (e) {
            console.error("Erro ao buscar resultado principal:", params.id, e);
          }
        }

        if (evaluationId) {
          try {
            const applications = await api.get<any[]>(`/api/tests/applications?evaluation_id=${evaluationId}&instrument_code=scared`);

            for (const app of applications || []) {
              try {
                const resultData = await api.get<SCAREDResult>(`/api/tests/scared/result/${app.id}`);
                appendResult(resultData);
              } catch (e) {
                console.error("Erro ao buscar resultado:", app.id, e);
              }
            }
          } catch (e) {
            console.error("Erro ao buscar aplicações SCARED da avaliação:", evaluationId, e);
          }
        }

        setResults(scaredResults);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    if (params.id || evaluationId) {
      fetchResults();
    }
  }, [params.id, evaluationId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center">
        <div className="text-zinc-600">Carregando...</div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="min-h-screen bg-slate-300 p-6 md:p-10 flex items-center justify-center">
        <div className="text-zinc-600">Resultado não encontrado</div>
      </div>
    );
  }

  const mainResult = results[0];
  const hasBothForms = results.length > 1;

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
              <h1 className="text-3xl font-medium tracking-tight text-zinc-900">
                SCARED {hasBothForms ? "- Autorrelato + Pais/Cuidadores" : ""}
              </h1>
              <p className="mt-1 text-sm text-zinc-600">
                {mainResult.patient_name} • {results.length === 1 ? getFormLabel(mainResult.classified_payload?.form_type || mainResult.computed_payload?.form) : `${results.length} formulários preenchidos`}
              </p>
            </div>
             <div className="flex gap-3 print:hidden report-print-hide">
               <Link href={`/dashboard/tests/scared/${mainResult.application_id}?evaluation_id=${mainResult.evaluation_id}&edit=true`} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                 Editar
               </Link>
               <button onClick={handleExportPdf} disabled={exportingPdf} className="rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60">
                  {exportingPdf ? "Gerando PDF..." : "Imprimir / PDF"}
                </button>
              <Link href={`/dashboard/evaluations/${mainResult.evaluation_id}?tab=overview`} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">
                Voltar
              </Link>
             </div>
           </div>

          <TestReportSummaryCard reportPayload={mainResult.report_payload} fallbackText={mainResult.interpretation || mainResult.interpretation_text} className="mb-6" />

          {results.map((result, index) => (
            <ResultCard key={result.application_id} result={result} />
          ))}
        </div>
      </div>
    </div>
  );
}
