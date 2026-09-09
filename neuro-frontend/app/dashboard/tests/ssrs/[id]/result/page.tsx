"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Edit3, Printer } from "lucide-react";

import { api } from "@/lib/api";
import { TestReportSummaryCard } from "@/components/tests/TestReportSummaryCard";

const DOMAIN_LABELS: Record<string, string> = {
  social_skills: "Habilidades Sociais",
  behavior_problems: "Problemas de Comportamento",
  academic_competence: "Competência Acadêmica",
};

const DOMAIN_ORDER = ["social_skills", "behavior_problems", "academic_competence"];

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function displayClassification(row: any) {
  const value = String(row?.classification || "").trim();
  if (!value) return "—";
  if (row?.domain === "social_skills") {
    if (value === "Altamente elaborado") return "Repertório altamente elaborado";
    if (value === "Elaborado") return "Repertório elaborado";
    if (value === "Medio inferior") return "Repertório médio inferior";
    if (value === "Baixo") return "Repertório abaixo da média inferior";
  }
  if (row?.domain === "behavior_problems") {
    if (value === "Acima da media superior") return "Repertório acima da média superior";
    if (value === "Medio superior") return "Repertório médio superior";
    if (value === "Mediano") return "Repertório mediano";
    if (value === "Baixo") return "Repertório baixo";
    if (value === "Muito baixo") return "Repertório muito baixo";
  }
  return value;
}

function classificationStyle(row: any) {
  const percentile = Number(row?.percentile || 0);
  if (row?.domain === "behavior_problems") {
    if (percentile >= 66) return "bg-red-50 text-red-700";
    if (percentile <= 25) return "bg-emerald-50 text-emerald-700";
    return "bg-blue-50 text-blue-700";
  }
  if (percentile <= 25) return "bg-red-50 text-red-700";
  if (percentile <= 35) return "bg-amber-50 text-amber-700";
  if (percentile <= 65) return "bg-green-50 text-green-700";
  return "bg-blue-50 text-blue-700";
}

function scaleLabel(row: any) {
  if (row?.scale === "eg") return "Escore Geral (EG)";
  return `Escore em ${String(row?.scale || "").toUpperCase()}`;
}

function PercentileBars({ title, rows }: { title: string; rows: any[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-slate-900">{title}</h3>
      <div className="space-y-3">
        {rows.map((row) => {
          const percentile = Math.max(0, Math.min(100, Number(row.percentile || 0)));
          return (
            <div key={`${row.domain}-${row.scale}`} className="grid grid-cols-[72px_1fr_42px] items-center gap-3">
              <div className="text-xs font-bold text-slate-600">{row.scale === "eg" ? "EG" : String(row.scale).toUpperCase()}</div>
              <div className="relative h-7 overflow-hidden rounded-lg border border-slate-200 bg-gradient-to-r from-violet-100 via-cyan-200 to-cyan-100">
                <div className="absolute inset-y-0 left-[25%] w-px bg-slate-400/40" />
                <div className="absolute inset-y-0 left-[50%] w-px bg-slate-400/40" />
                <div className="absolute inset-y-0 left-[75%] w-px bg-slate-400/40" />
                <div className="h-full rounded-r-md border border-indigo-500 bg-indigo-300/70" style={{ width: `${percentile}%` }} />
              </div>
              <div className="text-right text-xs font-black text-indigo-700">{formatValue(row.percentile)}</div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 flex justify-between text-[10px] font-medium text-slate-400">
        <span>0</span><span>25</span><span>50</span><span>75</span><span>100</span>
      </div>
    </div>
  );
}

function ResultTable({ title, rows }: { title: string; rows: any[] }) {
  if (!rows.length) return null;
  return (
    <div className="mb-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h3 className="font-semibold text-slate-900">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px]">
          <thead>
            <tr className="bg-slate-50">
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">Escala</th>
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">Fator</th>
              <th className="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-600">Escore</th>
              <th className="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-600">Percentil</th>
              <th className="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-600">Classificação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((row) => (
              <tr key={`${row.domain}-${row.scale}`} className={row.scale === "eg" ? "bg-blue-50/40" : "hover:bg-slate-50"}>
                <td className="px-5 py-3 text-sm font-medium text-slate-900">{scaleLabel(row)}</td>
                <td className="px-5 py-3 text-sm text-slate-700">{formatValue(row.name)}</td>
                <td className="px-5 py-3 text-center text-sm font-bold text-slate-900">{formatValue(row.raw_score)}</td>
                <td className="px-5 py-3 text-center text-sm font-bold text-blue-700">{formatValue(row.percentile)}</td>
                <td className="px-5 py-3 text-center text-sm">
                  <span className={`inline-flex rounded-full px-3 py-1 text-xs font-bold ${classificationStyle(row)}`}>{displayClassification(row)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SSRSResultContent() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const applicationId = params.id as string;
  const evaluationId = searchParams.get("evaluation_id") || "";
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadResult() {
      try {
        const data = await api.get<any>(`/api/tests/applications/${applicationId}`);
        setResult(data);
      } catch (err: any) {
        setError(err?.message || "Erro ao carregar resultado do SSRS.");
      } finally {
        setLoading(false);
      }
    }

    loadResult();
  }, [applicationId]);

  const rows = useMemo(() => result?.classified_payload?.resultados || [], [result]);
  const rowsByDomain = useMemo(() => {
    return Object.fromEntries(DOMAIN_ORDER.map((domain) => [domain, rows.filter((row: any) => row.domain === domain)]));
  }, [rows]);
  const importance = result?.computed_payload?.importance;
  const importanceFactors = importance?.factors ? Object.values(importance.factors) : [];
  const interpretation = String(result?.interpretation_text || "").trim();
  const generalRows = rows.filter((row: any) => row.scale === "eg");

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-300 p-6 text-zinc-600">Carregando resultado do SSRS...</div>;
  }

  if (error || !result) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-300 p-6">
        <div className="w-full max-w-3xl rounded-[32px] bg-white p-8 shadow-xl">
          <button onClick={() => router.push("/dashboard/tests")} className="mb-5 inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700">
            <ArrowLeft className="h-4 w-4" /> Voltar
          </button>
          <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">{error || "Resultado não encontrado."}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-300 p-6 md:p-10 report-print-shell">
      <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7 report-print-card">
        <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6 report-print-content">
          <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between print:hidden report-print-hide">
            <div className="rounded-full border border-black/20 bg-white/70 px-5 py-2 text-lg font-medium tracking-tight text-zinc-800 shadow-sm">NeuroAvalia</div>
            <nav className="flex flex-wrap items-center gap-2 rounded-full bg-white/70 px-3 py-2 text-sm text-zinc-700 shadow-sm">
              <Link href="/dashboard" className="rounded-full px-4 py-2 hover:bg-black/5">Dashboard</Link>
              <Link href="/dashboard/evaluations" className="rounded-full px-4 py-2 hover:bg-black/5">Avaliações</Link>
              <Link href="/dashboard/tests" className="rounded-full px-4 py-2 hover:bg-black/5">Testes</Link>
            </nav>
          </header>

          <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-medium tracking-tight text-zinc-900">SSRS - Resultado</h1>
              <p className="mt-1 text-sm text-zinc-600">{result.patient_name || "Paciente"} • Formulário para Pais</p>
            </div>
            <div className="flex flex-wrap gap-3 print:hidden report-print-hide">
              <Link href={`/dashboard/tests/ssrs?evaluation_id=${evaluationId || result.evaluation_id}&application_id=${applicationId}&edit=true`} className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                <Edit3 className="h-4 w-4" /> Editar
              </Link>
              <button onClick={() => window.print()} className="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-medium text-zinc-700 shadow-sm hover:bg-zinc-50">
                <Printer className="h-4 w-4" /> Imprimir / PDF
              </button>
              <Link href={evaluationId ? `/dashboard/evaluations/${evaluationId}/overview` : "/dashboard/tests"} className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white shadow-lg">Voltar</Link>
            </div>
          </div>

          <TestReportSummaryCard reportPayload={result.report_payload} fallbackText={result.interpretation_text} className="mb-6" />

          <div className="mb-6 grid gap-4 md:grid-cols-3">
            {generalRows.map((row: any) => (
              <div key={row.domain} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="text-xs font-black uppercase tracking-widest text-slate-400">{DOMAIN_LABELS[row.domain] || row.domain_name}</div>
                <div className="mt-3 text-3xl font-black text-slate-950">P{formatValue(row.percentile)}</div>
                <div className="mt-1 text-sm text-slate-600">Escore bruto {formatValue(row.raw_score)}</div>
                <div className={`mt-4 inline-flex rounded-full px-3 py-1 text-xs font-bold ${classificationStyle(row)}`}>{displayClassification(row)}</div>
              </div>
            ))}
          </div>

          {DOMAIN_ORDER.map((domain) => (
            <ResultTable key={domain} title={DOMAIN_LABELS[domain]} rows={rowsByDomain[domain] || []} />
          ))}

          <div className="mb-6 grid gap-6 lg:grid-cols-2">
            {DOMAIN_ORDER.map((domain) => {
              const domainRows = rowsByDomain[domain] || [];
              if (!domainRows.length) return null;
              return <PercentileBars key={domain} title={`Percentil para ${DOMAIN_LABELS[domain]}`} rows={domainRows} />;
            })}
          </div>

          {importance && (
            <div className="mb-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 px-5 py-4">
                <h3 className="font-semibold text-slate-900">Importância - Habilidades Sociais</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[560px]">
                  <thead>
                    <tr className="bg-slate-50">
                      <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">Fator</th>
                      <th className="px-5 py-3 text-center text-xs font-semibold uppercase tracking-wide text-slate-600">Escore de importância</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    <tr className="bg-blue-50/40">
                      <td className="px-5 py-3 text-sm font-bold text-slate-900">Escore Geral (EG)</td>
                      <td className="px-5 py-3 text-center text-sm font-bold text-blue-700">{formatValue(importance.eg)}</td>
                    </tr>
                    {importanceFactors.map((factor: any, index: number) => (
                      <tr key={`${factor.name}-${index}`} className="hover:bg-slate-50">
                        <td className="px-5 py-3 text-sm font-medium text-slate-900">{formatValue(factor.name)}</td>
                        <td className="px-5 py-3 text-center text-sm font-bold text-slate-900">{formatValue(factor.raw_score)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {interpretation && (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="mb-3 font-semibold text-slate-900">Síntese interpretativa</h3>
              <p className="text-sm leading-7 text-slate-700">{interpretation}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-slate-300 p-6 text-zinc-600">Carregando resultado do SSRS...</div>}>
      <SSRSResultContent />
    </Suspense>
  );
}
