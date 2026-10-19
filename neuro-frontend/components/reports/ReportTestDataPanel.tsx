"use client";

import { WiscChart } from "@/components/charts/WiscChart";

export type ReportTest = {
  applicationKey: string; code: string; name: string; respondent: string; appliedOn: string | null;
  domain: string; summary: string; clinicalInterpretation: string; resultRows: string[];
  structuredResults: Record<string, any>; classifiedPayload: Record<string, any>; computedPayload: Record<string, any>;
  wiscTables: Record<string, any[]>; warnings: string[];
};

const domains: Record<string, string> = {
  funcoes_executivas: "Funções Executivas", linguagem: "Linguagem",
  gnosias_praxias: "Gnosias e Praxias", memoria_aprendizagem: "Memória e Aprendizagem",
};

function numeric(value: unknown) {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const number = Number(value.replace(",", "."));
    return Number.isFinite(number) ? number : null;
  }
  return null;
}

function metricRows(test: ReportTest) {
  const structured = test.structuredResults || {};
  if (Array.isArray(structured.metric_results) && structured.metric_results.length) {
    return structured.metric_results.map((item: any) => ({ label: item.nome || item.codigo || "Métrica", primary: item.valor ?? "-", percentile: item.percentil_num ?? null, classification: item.classificacao || "" }));
  }
  if (Array.isArray(structured.subtestes) && structured.subtestes.length) {
    return structured.subtestes.map((item: any) => ({ label: item.subteste || item.nome || item.codigo || "Subteste", primary: item.total ?? item.escore_padrao ?? item.escore_composto ?? "-", percentile: item.percentil ?? null, classification: item.classificacao || "" }));
  }
  if (Array.isArray(structured.indices) && structured.indices.length) {
    return structured.indices.map((item: any) => ({ label: item.nome || item.indice || "Índice", primary: item.escore_composto ?? "-", percentile: item.percentil ?? null, classification: item.classificacao || "" }));
  }
  if (structured.results && typeof structured.results === "object") {
    return Object.values(structured.results).map((item: any) => ({ label: item.name || "Fator", primary: item.raw_score ?? item.escore_total ?? "-", percentile: item.percentile_text || item.percentil || null, classification: item.classification || item.classificacao || "" }));
  }
  return [];
}

function wiscChartData(test: ReportTest) {
  const payload = test.classifiedPayload || test.structuredResults || test.computedPayload || {};
  const byIndex = Object.fromEntries((Array.isArray(payload.indices) ? payload.indices : []).map((item: any) => [item.indice, item]));
  return [
    { label: "ICV", value: byIndex.icv?.escore_composto }, { label: "IOP", value: byIndex.iop?.escore_composto },
    { label: "IMO", value: byIndex.imt?.escore_composto }, { label: "IVP", value: byIndex.ivp?.escore_composto },
    { label: "QI Total", value: payload.qit_data?.escore_composto }, { label: "GAI", value: payload.gai_data?.escore_composto },
    { label: "CPI", value: payload.cpi_data?.escore_composto },
  ].map((item) => ({ ...item, value: numeric(item.value) })).filter((item) => item.value !== null) as { label: string; value: number }[];
}

const cell = "border-b border-slate-100 px-4 py-3 text-left text-sm text-slate-600";
const heading = "border-b border-slate-200 bg-slate-50 px-4 py-3 text-left text-xs font-medium text-slate-500";

export function ReportTestDataPanel({ tests, selected, onToggle }: { tests: ReportTest[]; selected: string[]; onToggle: (key: string) => void }) {
  const visible = tests.filter((test) => selected.includes(test.applicationKey));
  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6" aria-labelledby="report-test-sources">
        <h2 id="report-test-sources" className="text-base font-semibold text-slate-900">Fontes da avaliação</h2>
        <p className="mt-1 text-sm leading-6 text-slate-500">Consulte os resultados validados usados neste laudo. Selecionar uma aplicação apenas exibe seus dados, sem gerar ou alterar textos.</p>
        {tests.length ? <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {tests.map((test) => <label key={test.applicationKey} className={`flex min-w-0 cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-slate-50 ${selected.includes(test.applicationKey) ? "border-primary/30 bg-primary/5" : "border-slate-200"}`}>
            <input type="checkbox" checked={selected.includes(test.applicationKey)} onChange={() => onToggle(test.applicationKey)} className="mt-0.5 h-4 w-4 shrink-0 accent-teal-700" />
            <span className="min-w-0 break-words"><span className="block text-sm font-medium text-slate-800">{test.name}</span><span className="mt-1 block text-xs leading-5 text-slate-500">Aplicação #{test.applicationKey}{test.respondent ? ` · ${test.respondent}` : ""}</span></span>
          </label>)}
        </div> : <p className="mt-5 rounded-lg bg-slate-50 p-4 text-sm text-slate-500">Nenhuma aplicação validada disponível neste laudo.</p>}
      </section>
      {tests.length > 0 && visible.length === 0 && <p className="py-8 text-center text-sm text-slate-500">Selecione uma aplicação acima para consultar resultados e evidências.</p>}
      {visible.map((test) => {
        const rows = metricRows(test);
        const bpaPayload = test.classifiedPayload || test.structuredResults || test.computedPayload || {};
        const bpaRows = test.code === "bpa2" && Array.isArray(bpaPayload.subtestes) ? bpaPayload.subtestes : [];
        const chart = test.code === "wisc4" ? wiscChartData(test) : [];
        const wiscTables = test.code === "wisc4" && rows.length > 0 && Object.values(test.wiscTables || {}).some((value) => Array.isArray(value) && value.length > 0);
        const date = test.appliedOn ? new Date(test.appliedOn) : null;
        const dateLabel = date && !Number.isNaN(date.getTime()) ? date.toLocaleDateString("pt-BR") : test.appliedOn || "Não informado";
        return <article key={test.applicationKey} className="min-w-0 space-y-5 rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
          <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
            <div className="min-w-0 break-words"><h3 className="font-semibold text-slate-900">{test.name}</h3><p className="mt-1 text-xs text-slate-500">Aplicação #{test.applicationKey}{test.respondent ? ` · Informante: ${test.respondent}` : ""}{test.domain ? ` · ${test.domain}` : ""}</p></div>
            <p className="text-xs text-slate-500">Aplicação: {dateLabel}</p>
          </header>
          {test.summary && <p className="text-sm leading-7 text-slate-700"><span className="font-medium text-slate-900">Resumo: </span>{test.summary}</p>}
          {chart.length > 0 && <div className="overflow-x-auto"><WiscChart data={chart} /></div>}
          {bpaRows.length > 0 && <div role="region" aria-label={`Resultados BPA-2, aplicação ${test.applicationKey}`} tabIndex={0} className="overflow-x-auto rounded-lg border border-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <table className="w-full min-w-[520px] border-collapse"><thead><tr>{["Atenção BPA", "Pontos", "Percentil", "Classificação"].map((label) => <th key={label} scope="col" className={heading}>{label}</th>)}</tr></thead>
              <tbody>{bpaRows.map((item: any, index: number) => <tr key={`${item.codigo}-${index}`}><td className={cell}>{({ ac: "Atenção Concentrada - AC", ad: "Atenção Dividida - AD", aa: "Atenção Alternada - AA", ag: "Atenção Geral - AG" } as Record<string, string>)[String(item.codigo || "").toLowerCase()] || item.subteste || item.codigo || "Subteste"}</td><td className={`${cell} tabular-nums`}>{item.total ?? item.brutos ?? "-"}</td><td className={`${cell} tabular-nums`}>{item.percentil ?? "-"}</td><td className={cell}>{item.classificacao || "-"}</td></tr>)}</tbody>
            </table>
          </div>}
          {test.code !== "bpa2" && rows.length > 0 && (wiscTables ? <div className="space-y-5">
            {Object.entries(domains).map(([key, title]) => {
              const domainRows = test.wiscTables?.[key] || [];
              if (!domainRows.length) return null;
              return <div key={key} role="region" aria-label={title} tabIndex={0} className="overflow-x-auto rounded-lg border border-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
                <table className="w-full min-w-[640px] border-collapse"><caption className="border-b border-slate-200 p-4 text-left text-sm font-semibold text-slate-800">{title}</caption><thead><tr>{["Testes utilizados", "Escore máximo", "Escore médio", "Escore mínimo", "Escore bruto", "Classificação"].map((label) => <th key={label} scope="col" className={heading}>{label}</th>)}</tr></thead>
                  <tbody>{domainRows.map((row: any, index: number) => <tr key={`${row.label}-${index}`}><th scope="row" className={`${cell} font-medium`}>{row.label}</th>{row.note ? <td colSpan={5} className={cell}>{row.note}</td> : <>{[row.maxScore, row.avgScore, row.minScore, row.obtainedScore, row.classification].map((value, i) => <td key={i} className={`${cell} tabular-nums`}>{value}</td>)}</>}</tr>)}</tbody>
                </table>
              </div>;
            })}
          </div> : <div role="region" aria-label={`Indicadores da aplicação ${test.applicationKey}`} tabIndex={0} className="overflow-x-auto rounded-lg border border-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <table className="w-full min-w-[520px] border-collapse"><thead><tr>{["Indicador", "Valor", "Percentil", "Classificação"].map((label) => <th key={label} scope="col" className={heading}>{label}</th>)}</tr></thead>
              <tbody>{rows.map((row: any, index: number) => {
                const percentile = numeric(row.percentile);
                return <tr key={`${row.label}-${index}`}><th scope="row" className={`${cell} font-medium`}>{row.label}</th><td className={`${cell} tabular-nums`}>{String(row.primary ?? "-")}</td><td className={`${cell} tabular-nums`}>{row.percentile ?? "-"}{percentile !== null && <div aria-hidden="true" className="mt-1 h-1 w-20 rounded-full bg-slate-100"><div className="h-1 rounded-full bg-primary/60" style={{ width: `${Math.max(0, Math.min(100, percentile))}%` }} /></div>}</td><td className={cell}>{row.classification || "-"}</td></tr>;
              })}</tbody>
            </table>
          </div>)}
          {test.code !== "bpa2" && !rows.length && test.resultRows.length > 0 && <ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">{test.resultRows.map((row, index) => <li key={index}>{row}</li>)}</ul>}
          {test.clinicalInterpretation && <details className="rounded-lg border border-slate-200 p-4 text-sm"><summary className="cursor-pointer font-medium text-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">{test.code === "bpa2" ? "Interpretação e Observações Clínicas" : "Ver interpretação técnica"}</summary><p className="mt-4 whitespace-pre-wrap break-words leading-7 text-slate-600">{test.clinicalInterpretation}</p></details>}
          {test.warnings.length > 0 && <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"><h4 className="font-medium">Avisos do teste</h4><ul className="mt-2 list-disc space-y-1 pl-5">{test.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></div>}
        </article>;
      })}
    </div>
  );
}
