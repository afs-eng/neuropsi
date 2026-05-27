"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { WiscChart } from "@/components/charts/WiscChart";
import { resolveApiUrl } from "@/lib/api";
import { reportService } from "@/services/reportService";
import { ArrowLeft, Calendar, CheckCircle2, Download, FileText, Loader2, RotateCcw, Save, User } from "lucide-react";

const WISC_SUBSCALE_KEYS = new Set([
  "funcoes_executivas",
  "linguagem",
  "gnosias_praxias",
  "memoria_aprendizagem",
]);

const WISC_SUBSCALE_ORDER = [
  "funcoes_executivas",
  "linguagem",
  "gnosias_praxias",
  "memoria_aprendizagem",
];

const WISC_DOMAIN_LABELS: Record<string, string> = {
  funcoes_executivas: "Funções Executivas",
  linguagem: "Linguagem",
  gnosias_praxias: "Gnosias e Praxias",
  memoria_aprendizagem: "Memória e Aprendizagem",
};

const TEST_SECTION_MAP: Record<string, string> = {
  wisc4: "capacidade_cognitiva_global",
  wasi: "capacidade_cognitiva_global",
  wais3: "capacidade_cognitiva_global",
  bpa2: "atencao",
  fdt: "funcoes_executivas",
  ravlt: "memoria_aprendizagem",
  epq_j: "epq_j",
  scared: "scared",
  srs2: "srs2",
  ebadep_a: "aspectos_emocionais_comportamentais",
  ebadep_ij: "aspectos_emocionais_comportamentais",
  ebaped_ij: "aspectos_emocionais_comportamentais",
  etdah_ad: "etdah_ad",
  etdah_pais: "etdah_pais",
};

function formatTimestamp(value?: string | null) {
  if (!value) return "Nao informado";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

function formatShortDate(value?: string | null) {
  if (!value) return "Nao informado";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR");
}

function normalizeNumber(value: unknown) {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const normalized = Number(value.replace(",", "."));
    return Number.isFinite(normalized) ? normalized : null;
  }
  return null;
}

function getPercentileWidth(value: unknown) {
  const number = normalizeNumber(value);
  if (number === null) return null;
  return Math.max(0, Math.min(100, number));
}

function getGenerationSource(provider?: string | null, model?: string | null) {
  if (provider === "deterministic" || model === "rules-based") {
    return "Fallback automatico";
  }
  if (["openai", "ollama", "anthropic"].includes(String(provider || "").toLowerCase())) {
    return "IA";
  }
  return "Nao informado";
}

function getTextStatus(hasManualEdits: boolean, generationSource: string) {
  if (hasManualEdits) return "Editado manualmente";
  if (generationSource === "Fallback automatico") {
    return "Igual ao fallback automatico";
  }
  if (generationSource === "IA") return "Igual ao texto gerado por IA";
  return "Igual ao texto gerado automaticamente";
}

function getGenerationDetails(metadata: Record<string, any>) {
  const requestedModel = metadata.requested_model || metadata.model || "Nao informado";
  const effectiveModel = metadata.model || "Nao informado";
  const usedModelFallback = Boolean(metadata.used_model_fallback);
  const promptName = metadata.prompt_name || "Nao informado";
  const generationPath = metadata.generation_path || "Nao informado";

  return {
    requestedModel,
    effectiveModel,
    usedModelFallback,
    promptName,
    generationPath,
  };
}

function getCompletedTests(report: any) {
  const tests = report?.context_payload?.validated_tests || report?.snapshot_payload?.validated_tests || [];
  const seen = new Set<string>();

  return tests
    .map((item: any) => ({
      code: item.instrument_code || "",
      name: item.instrument_name || item.instrument || item.instrument_code || "Teste",
      appliedOn: item.applied_on || null,
      domain: item.domain || "",
      summary: item.summary || "",
      clinicalInterpretation: item.clinical_interpretation || item.interpretation_text || "",
      resultRows: item.result_rows || [],
      structuredResults: item.structured_results || {},
      classifiedPayload: item.classified_payload || {},
      computedPayload: item.computed_payload || {},
      wiscTables: item.wisc_tables || {},
      warnings: item.warnings || [],
    }))
    .filter((item: any) => {
      const key = `${item.code}:${item.name}`;
      if (!item.code && !item.name) return false;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function buildMetricRows(test: any) {
  const structured = test.structuredResults || {};

  if (Array.isArray(structured.metric_results) && structured.metric_results.length > 0) {
    return structured.metric_results.map((item: any) => ({
      label: item.nome || item.codigo || "Metrica",
      primary: item.valor ?? "-",
      percentile: item.percentil_num ?? null,
      classification: item.classificacao || "",
    }));
  }

  if (Array.isArray(structured.subtestes) && structured.subtestes.length > 0) {
    return structured.subtestes.map((item: any) => ({
      label: item.subteste || item.nome || item.codigo || "Subteste",
      primary: item.total ?? item.escore_padrao ?? item.escore_composto ?? "-",
      percentile: item.percentil ?? null,
      classification: item.classificacao || "",
    }));
  }

  if (Array.isArray(structured.indices) && structured.indices.length > 0) {
    return structured.indices.map((item: any) => ({
      label: item.nome || item.indice || "Indice",
      primary: item.escore_composto ?? "-",
      percentile: item.percentil ?? null,
      classification: item.classificacao || "",
    }));
  }

  if (structured.results && typeof structured.results === "object") {
    return Object.values(structured.results).map((item: any) => ({
      label: item.name || "Fator",
      primary: item.raw_score ?? item.escore_total ?? "-",
      percentile: item.percentile_text || item.percentil || null,
      classification: item.classification || item.classificacao || "",
    }));
  }

  return [];
}

function getBpa2Subtests(test: any) {
  const payload = test.classifiedPayload || test.structuredResults || test.computedPayload || {};
  return Array.isArray(payload.subtestes) ? payload.subtestes : [];
}

function getBpa2Label(code: string, fallback?: string) {
  const labels: Record<string, string> = {
    ac: "Atenção Concentrada - AC",
    ad: "Atenção Dividida - AD",
    aa: "Atenção Alternada - AA",
    ag: "Atenção Geral - AG",
  };

  return labels[String(code || "").toLowerCase()] || fallback || code || "Subteste";
}

function getWiscChartData(test: any) {
  const payload = test.classifiedPayload || test.structuredResults || test.computedPayload || {};
  const indices = Array.isArray(payload.indices) ? payload.indices : [];
  const byIndex = Object.fromEntries(indices.map((item: any) => [item.indice, item]));
  const rows = [
    { label: "ICV", value: byIndex.icv?.escore_composto },
    { label: "IOP", value: byIndex.iop?.escore_composto },
    { label: "IMO", value: byIndex.imt?.escore_composto },
    { label: "IVP", value: byIndex.ivp?.escore_composto },
    { label: "QI Total", value: payload.qit_data?.escore_composto },
    { label: "GAI", value: payload.gai_data?.escore_composto },
    { label: "CPI", value: payload.cpi_data?.escore_composto },
  ];

  return rows
    .map((item) => ({ ...item, value: normalizeNumber(item.value) }))
    .filter((item) => item.value !== null) as Array<{ label: string; value: number }>;
}

function getMissingSectionsFromTests(report: any, completedTests: any[]) {
  if (report?.ai_metadata?.generation_scope === "tests_only") {
    return [];
  }

  const currentSectionKeys = new Set((report?.sections || []).map((section: any) => section.key));
  const missing = new Set<string>();

  for (const test of completedTests) {
    const mappedSection = TEST_SECTION_MAP[test.code];
    if (mappedSection && !currentSectionKeys.has(mappedSection)) {
      missing.add(mappedSection);
    }
  }

  return Array.from(missing);
}

export default function ReportDetailPage() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const reportId = params.id;
  const autobuildTriggeredRef = useRef(false);
  const [report, setReport] = useState<any>(null);
  const [activeSectionId, setActiveSectionId] = useState<number | null>(null);
  const [editedText, setEditedText] = useState("");
  const [selectedTests, setSelectedTests] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const activeSection = useMemo(
    () => report?.sections?.find((section: any) => section.id === activeSectionId) || null,
    [activeSectionId, report]
  );
  const wiscSubscaleSections = useMemo(
    () => (report?.sections || []).filter((section: any) => WISC_SUBSCALE_KEYS.has(section.key)),
    [report]
  );
  const isWiscSubscaleActive = Boolean(activeSection && WISC_SUBSCALE_KEYS.has(activeSection.key));
  const completedTests = useMemo(() => getCompletedTests(report), [report]);
  const missingSections = useMemo(
    () => getMissingSectionsFromTests(report, completedTests),
    [report, completedTests]
  );
  const sidebarSections = useMemo(
    () => report?.sections?.filter((section: any) => !WISC_SUBSCALE_KEYS.has(section.key)) || [],
    [report]
  );

  const loadReport = useCallback(async () => {
    try {
      setError("");
      const data = await reportService.get(reportId);
      setReport(data);
      if (data.sections?.length) {
        const firstSection = data.sections[0];
        setActiveSectionId((current) => current ?? firstSection.id);
        if (!activeSectionId) {
          setEditedText(firstSection.edited_text || firstSection.generated_text || "");
        }
      }
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel carregar o laudo.");
    } finally {
      setLoading(false);
    }
  }, [activeSectionId, reportId]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  useEffect(() => {
    if (searchParams.get("autobuild") === "1") {
      setNotice("Geracao do laudo iniciada. A pagina sera atualizada automaticamente quando as secoes ficarem prontas.");
    }
  }, [searchParams]);

  const handleRebuildReport = useCallback(async () => {
    if (!report) return;
    setSaving(true);
    setNotice("");
    try {
      const updated = await reportService.build(report.id);
      setReport(updated);
      if ((updated as any)?.sections?.length) {
        const firstSection = (updated as any).sections[0];
        setActiveSectionId(firstSection.id);
        setEditedText(firstSection.edited_text || firstSection.generated_text || "");
      }
      setNotice("Laudo reconstruido com os testes validados mais recentes.");
      await loadReport();
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel reconstruir o laudo.");
    } finally {
      setSaving(false);
    }
  }, [loadReport, report]);

  useEffect(() => {
    if (searchParams.get("autobuild") !== "1") return;
    if (!report || report.status === "generating") return;
    if (missingSections.length === 0) return;
    if (autobuildTriggeredRef.current) return;

    autobuildTriggeredRef.current = true;
    setNotice("Novos testes validados foram encontrados. Reconstruindo o laudo automaticamente para incluir as secoes faltantes.");
    handleRebuildReport().catch(() => {
      autobuildTriggeredRef.current = false;
    });
  }, [handleRebuildReport, missingSections, report, searchParams]);

  useEffect(() => {
    if (!report || report.status !== "generating") return;

    const intervalId = window.setInterval(() => {
      loadReport().catch(() => undefined);
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [loadReport, report]);

  useEffect(() => {
    if (activeSection) {
      setEditedText(activeSection.edited_text || activeSection.generated_text || "");
    }
  }, [activeSectionId, activeSection]);

  async function handleSave() {
    if (!activeSection) return;
    setSaving(true);
    setNotice("");
    try {
      const updated = await reportService.saveSection(activeSection.id, editedText);
      setReport((current: any) => ({
        ...current,
        sections: current.sections.map((section: any) =>
          section.id === activeSection.id ? { ...section, ...updated } : section
        ),
      }));
      setNotice("Secao salva com sucesso.");
      await loadReport();
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel salvar a secao.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRegenerate() {
    if (!activeSection || !report) return;
    setSaving(true);
    setNotice("");
    try {
      const updated = await reportService.regenerateSection(report.id, activeSection.key) as Record<string, string | undefined>;
      setReport((current: any) => ({
        ...current,
        sections: current.sections.map((section: any) =>
          section.id === activeSection.id ? { ...section, ...updated } : section
        ),
      }));
      setEditedText(String(updated.edited_text || updated.generated_text || ""));
      setNotice("Secao regenerada com sucesso.");
      await loadReport();
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel regenerar a secao.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRegenerateWiscSubscales() {
    if (!report || wiscSubscaleSections.length === 0) return;
    setSaving(true);
    setNotice("");
    try {
      const updatedSections: Record<string, any> = {};
      for (const key of WISC_SUBSCALE_ORDER) {
        const section = wiscSubscaleSections.find((item: any) => item.key === key);
        if (!section) continue;
        updatedSections[key] = await reportService.regenerateSection(report.id, key);
      }

      setReport((current: any) => ({
        ...current,
        sections: current.sections.map((section: any) =>
          updatedSections[section.key] ? { ...section, ...updatedSections[section.key] } : section
        ),
      }));

      const preferredSection = wiscSubscaleSections.find((section: any) => section.id === activeSectionId)
        || wiscSubscaleSections[0];
      if (preferredSection && updatedSections[preferredSection.key]) {
        const updated = updatedSections[preferredSection.key] as Record<string, string | undefined>;
        setActiveSectionId(updated.id ?? preferredSection.id);
        setEditedText(String(updated.edited_text || updated.generated_text || ""));
      }

      setNotice("Subscalas-Wisc regeneradas com sucesso.");
      await loadReport();
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel regenerar as Subscalas-Wisc.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRegenerateTests() {
    if (!report) return;
    const currentSectionKey = activeSection?.key;
    setSaving(true);
    setNotice("");
    try {
      const updated = await reportService.regenerateTests(report.id) as any;
      setReport(updated);

      if (updated?.status === "generating") {
        setNotice("Regeneracao dos testes iniciada. A pagina sera atualizada automaticamente quando as secoes ficarem prontas.");
        return;
      }

      const nextActiveSection = (updated.sections || []).find((section: any) => section.key === currentSectionKey)
        || (updated.sections || []).find((section: any) => section.id === activeSectionId)
        || null;

      if (nextActiveSection) {
        setActiveSectionId(nextActiveSection.id);
        setEditedText(String(nextActiveSection.edited_text || nextActiveSection.generated_text || ""));
      }

      setNotice("Secoes de testes regeneradas com sucesso.");
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel regenerar as secoes de testes.");
    } finally {
      setSaving(false);
    }
  }

  async function handleFinalize() {
    if (!report) return;
    setSaving(true);
    setNotice("");
    try {
      const updated = await reportService.finalize(report.id);
      setReport(updated);
      setNotice("Laudo finalizado com sucesso.");
      await loadReport();
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel finalizar o laudo.");
    } finally {
      setSaving(false);
    }
  }

  async function handleExportHtml() {
    if (!report) return;
    try {
      const data = await reportService.exportHtml(report.id);
      const popup = window.open("", "_blank");
      if (popup) {
        popup.document.open();
        popup.document.write(data.html);
        popup.document.close();
      }
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel exportar o laudo.");
    }
  }

  async function handleExportDocx() {
    if (!report) return;
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(resolveApiUrl(`/api/reports/${report.id}/export-docx`), {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        let message = "Nao foi possivel exportar o laudo em DOCX.";
        try {
          const payload = await response.json();
          message = payload?.message || message;
        } catch {
          try {
            const text = await response.text();
            if (text) message = text;
          } catch {}
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const patientName = (report.patient_name || "paciente")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-zA-Z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      link.download = `Laudo-${patientName || report.id}.docx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel exportar o laudo em DOCX.");
    }
  }

  if (loading) {
    return (
      <div className="flex h-[420px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!report) {
    return (
      <PageContainer>
        <PageHeader title="Laudo" subtitle={error || "Laudo nao encontrado."} />
      </PageContainer>
    );
  }

  const isFinalized = report.status === "finalized";
  const isTestsOnlyReport = report.ai_metadata?.generation_scope === "tests_only";
  const generationMetadata = activeSection?.generation_metadata || {};
  const warnings = activeSection?.warnings_payload || [];
  const generatedText = activeSection?.generated_text || "";
  const hasManualEdits = Boolean(activeSection && (activeSection.edited_text || "") !== generatedText);
  const generationTimestamp = generationMetadata.generated_at || activeSection?.updated_at;
  const generationSource = getGenerationSource(generationMetadata.provider, generationMetadata.model);
  const textStatus = getTextStatus(hasManualEdits, generationSource);
  const generationDetails = getGenerationDetails(generationMetadata);
  const visibleSelectedTests = completedTests.filter((test: any) => selectedTests.includes(`${test.code}:${test.name}`));

  return (
    <PageContainer>
      <PageHeader
        title={report.title}
        subtitle={`${report.patient_name || "Paciente"} · ${report.evaluation_title || "Avaliacao"}${report.purpose ? ` · ${report.purpose}` : ""}`}
        actions={
          <div className="flex gap-2">
            <Link href="/dashboard/reports">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Voltar
              </Button>
            </Link>
            <Button variant="outline" className="gap-2" onClick={handleExportHtml} disabled={isTestsOnlyReport}>
              <Download className="h-4 w-4" />
              Exportar HTML
            </Button>
            <Button variant="outline" className="gap-2" onClick={handleExportDocx} disabled={isTestsOnlyReport}>
              <FileText className="h-4 w-4" />
              Exportar DOCX
            </Button>
          </div>
        }
      />

      {error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      {notice && <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</div>}
      {isTestsOnlyReport && (
        <div className="mb-4 rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-indigo-600 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-white">
              Somente testes
            </span>
            <span>
              Este laudo foi gerado apenas com as secoes de testes validados. Finalizacao e exportacao ficam disponiveis apos gerar o laudo completo.
            </span>
          </div>
        </div>
      )}
      {missingSections.length > 0 && (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="font-medium">Novos testes validados foram encontrados</div>
              <div className="mt-1">
                O snapshot do laudo ja foi atualizado, mas ainda faltam secoes correspondentes no texto atual. Reconstrua o laudo para incluir: {missingSections.join(", ")}.
              </div>
            </div>
            <Button variant="outline" className="border-amber-300 bg-white text-amber-900 hover:bg-amber-100" disabled={saving} onClick={handleRebuildReport}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Reconstruir laudo
            </Button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="space-y-2">
            {wiscSubscaleSections.length > 0 && (
              <button
                type="button"
                onClick={handleRegenerateWiscSubscales}
                disabled={saving}
                className={`w-full rounded-xl border px-4 py-3 text-left text-sm transition ${
                  isWiscSubscaleActive
                    ? "border-indigo-600 bg-indigo-600 text-white"
                    : "border-slate-200 bg-slate-50 text-slate-700 hover:bg-white"
                }`}
              >
                <div className="font-medium">Subscalas-Wisc</div>
                <div className={`mt-1 text-xs ${isWiscSubscaleActive ? "text-indigo-100" : "text-slate-400"}`}>
                  Regenera Funções Executivas, Linguagem, Gnosias e Praxias, Memória e Aprendizagem
                </div>
              </button>
            )}

            {sidebarSections.map((section: any) => (
              <button
                key={section.id}
                type="button"
                onClick={() => setActiveSectionId(section.id)}
                className={`w-full rounded-xl border px-4 py-3 text-left text-sm transition ${
                  activeSectionId === section.id
                    ? "border-indigo-600 bg-indigo-600 text-white"
                    : "border-slate-200 bg-slate-50 text-slate-700 hover:bg-white"
                }`}
              >
                <div className="font-medium">{section.title}</div>
                <div className={`mt-1 text-xs ${activeSectionId === section.id ? "text-indigo-100" : "text-slate-400"}`}>
                  {section.key}
                </div>
              </button>
            ))}
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-600">
            <div className="flex items-center gap-2"><User className="h-4 w-4 text-slate-400" />{report.author_name}</div>
            <div className="mt-2 flex items-center gap-2"><Calendar className="h-4 w-4 text-slate-400" />{report.updated_at ? new Date(report.updated_at).toLocaleString("pt-BR") : "Sem atualizacao"}</div>
            <div className="mt-2 flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-slate-400" />Status: {report.status}</div>
            <div className="mt-2 text-xs text-slate-500">Interessado: {report.interested_party || report.patient_name}</div>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">Testes concluidos</h3>
            <div className="space-y-2">
              {completedTests.length > 0 ? completedTests.map((test: any) => {
                const key = `${test.code}:${test.name}`;
                const isSelected = selectedTests.includes(key);

                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setSelectedTests((prev) => prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key])}
                    className={`w-full rounded-xl border px-3 py-2 text-xs transition text-left ${isSelected ? "border-indigo-600 bg-indigo-600 text-white" : "border-slate-100 bg-slate-50 text-slate-600 hover:bg-white"}`}
                  >
                    <div className="font-medium text-slate-800">{test.name}</div>
                    <div className="mt-1 uppercase tracking-wide text-slate-400">{test.code || "sem-codigo"}</div>
                  </button>
                );
              }) : (
                <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs text-slate-500">
                  Nenhum teste concluido disponivel neste laudo.
                </div>
              )}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">Historico</h3>
            <div className="space-y-2">
              {(report.versions || []).slice(0, 5).map((version: any) => (
                <div key={version.id} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs text-slate-600">
                  <div className="font-medium text-slate-800">Versao {version.version_number}</div>
                  <div>{version.created_by}</div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <main className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">{isWiscSubscaleActive ? "Subscalas-Wisc" : activeSection?.title || "Selecione uma secao"}</h2>
              <p className="text-sm text-slate-500">
                {isTestsOnlyReport
                  ? "Edite e regenere as secoes de testes. Gere o laudo completo quando quiser concluir e exportar o documento final."
                  : "Edite o rascunho gerado e regenere a secao quando necessario."}
              </p>
            </div>
            <div className="flex gap-2">
              {!isFinalized && (
                <>
                  <Button variant="outline" className="gap-2" disabled={saving || completedTests.length === 0} onClick={handleRegenerateTests}>
                    <RotateCcw className="h-4 w-4" />
                    Regenerar testes
                  </Button>
                  <Button variant="outline" className="gap-2" disabled={saving || !activeSection} onClick={isWiscSubscaleActive ? handleRegenerateWiscSubscales : handleRegenerate}>
                    <RotateCcw className="h-4 w-4" />
                    {isWiscSubscaleActive ? "Regenerar Subscalas-Wisc" : "Regenerar secao"}
                  </Button>
                  <Button className="gap-2" disabled={saving || !activeSection} onClick={handleSave}>
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    Salvar
                  </Button>
                </>
              )}
              <Button variant="outline" disabled={saving || isFinalized || isTestsOnlyReport} onClick={handleFinalize}>
                Finalizar
              </Button>
            </div>
          </div>

          {activeSection && (
            <div className="border-b border-slate-200 bg-slate-50/70 px-6 py-4">
              {isWiscSubscaleActive && wiscSubscaleSections.length > 0 && (
                <div className="mb-4 flex flex-wrap gap-2">
                  {wiscSubscaleSections.map((section: any) => (
                    <button
                      key={section.id}
                      type="button"
                      onClick={() => setActiveSectionId(section.id)}
                      className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                        activeSectionId === section.id
                          ? "border-indigo-600 bg-indigo-600 text-white"
                          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                      }`}
                    >
                      {section.title}
                    </button>
                  ))}
                </div>
              )}

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Origem</div>
                  <div className="mt-1 font-medium text-slate-800">{generationSource}</div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Provider</div>
                  <div className="mt-1 font-medium text-slate-800">{generationMetadata.provider || "Nao informado"}</div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Modelo</div>
                  <div className="mt-1 font-medium text-slate-800">{generationDetails.effectiveModel}</div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Ultima geracao</div>
                  <div className="mt-1 font-medium text-slate-800">{formatTimestamp(generationTimestamp)}</div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Status do texto</div>
                  <div className="mt-1 font-medium text-slate-800">{textStatus}</div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                  <div className="text-xs uppercase tracking-wide text-slate-400">Execucao</div>
                  <div className="mt-1 font-medium text-slate-800">{generationDetails.usedModelFallback ? "IA com fallback de modelo" : generationDetails.generationPath === "ai" ? "IA direta" : generationDetails.generationPath === "deterministic_fallback" ? "Fallback da secao" : "Fluxo padrao"}</div>
                </div>
              </div>

              {generationSource === "IA" && (
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-wide text-slate-400">Modelo solicitado</div>
                    <div className="mt-1 font-medium text-slate-800">{generationDetails.requestedModel}</div>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm">
                    <div className="text-xs uppercase tracking-wide text-slate-400">Prompt</div>
                    <div className="mt-1 font-medium break-all text-slate-800">{generationDetails.promptName}</div>
                  </div>
                </div>
              )}

              {selectedTests.length > 0 && (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-slate-900">Dados dos testes concluidos</h3>
                      <p className="mt-1 text-xs text-slate-500">Resumo estrutural usado na construcao do laudo. Mostra apenas testes validados.</p>
                    </div>
                    <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                      {visibleSelectedTests.length} teste{visibleSelectedTests.length > 1 ? "s" : ""}
                    </div>
                  </div>

                  <div className="mt-4 space-y-4">
                    {visibleSelectedTests.map((test: any) => {
                      const metricRows = buildMetricRows(test);
                      const bpa2Subtests = test.code === "bpa2" ? getBpa2Subtests(test) : [];
                      const wiscChartData = test.code === "wisc4" ? getWiscChartData(test) : [];

                      return (
                        <div key={`${test.code}-${test.name}`} className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
                          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                            <div>
                              <div className="text-sm font-semibold text-slate-900">{test.name}</div>
                              <div className="mt-1 text-xs uppercase tracking-wide text-slate-400">{test.code || "sem-codigo"}{test.domain ? ` · ${test.domain}` : ""}</div>
                            </div>
                            <div className="text-xs text-slate-500">Aplicado em {formatShortDate(test.appliedOn)}</div>
                          </div>

                          {test.summary && (
                            <div className="mt-3 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                              <span className="font-medium text-slate-900">Resumo:</span> {test.summary}
                            </div>
                          )}

                          {test.code === "wisc4" && wiscChartData.length > 0 && (
                            <div className="mt-3">
                              <WiscChart data={wiscChartData} />
                            </div>
                          )}

                          {test.code === "bpa2" && bpa2Subtests.length > 0 && (
                            <div className="mt-3 space-y-3">
                              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                                <div className="grid grid-cols-[minmax(0,2fr)_120px_120px_minmax(0,1fr)] gap-3 border-b border-slate-100 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                                  <div>Atencao BPA</div>
                                  <div>Pontos</div>
                                  <div>Percentil</div>
                                  <div>Classificacao</div>
                                </div>
                                <div>
                                  {bpa2Subtests.map((item: any, index: number) => (
                                    <div key={`${item.codigo}-${index}`} className="grid grid-cols-[minmax(0,2fr)_120px_120px_minmax(0,1fr)] gap-3 border-b border-slate-100 px-3 py-2 text-sm last:border-b-0">
                                      <div className="font-medium text-slate-800">{getBpa2Label(item.codigo, item.subteste)}</div>
                                      <div className="text-slate-600">{item.total ?? item.brutos ?? "-"}</div>
                                      <div className="text-slate-600">{item.percentil ?? "-"}</div>
                                      <div className="text-slate-600">{item.classificacao || "-"}</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {test.code !== "bpa2" && metricRows.length > 0 && (
                            test.code === "wisc4" && Object.values(test.wiscTables || {}).some((rows: any) => Array.isArray(rows) && rows.length > 0) ? (
                              <div className="mt-3 space-y-4">
                                {WISC_SUBSCALE_ORDER.map((domainKey) => {
                                  const rows = test.wiscTables?.[domainKey] || [];
                                  if (!rows.length) return null;

                                  return (
                                    <div key={domainKey} className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                                      <div className="border-b border-slate-100 px-3 py-2 text-sm font-semibold text-slate-800">
                                        {WISC_DOMAIN_LABELS[domainKey] || domainKey}
                                      </div>
                                      <div className="overflow-x-auto">
                                        <table className="w-full border-collapse table-fixed text-[9px] leading-[1.4]">
                                          <colgroup>
                                            <col className="w-[27%]" />
                                            <col className="w-[14%]" />
                                            <col className="w-[14%]" />
                                            <col className="w-[14%]" />
                                            <col className="w-[14%]" />
                                            <col className="w-[17%]" />
                                          </colgroup>
                                          <thead>
                                            <tr>
                                              <th className="border border-white bg-[#A8D08D] px-3 py-2 text-left font-semibold uppercase tracking-wide text-slate-900">Testes Utilizados</th>
                                              <th className="border border-white bg-[#A8D08D] px-2 py-2 text-center font-semibold uppercase tracking-wide text-slate-900">Escore Máximo</th>
                                              <th className="border border-white bg-[#A8D08D] px-2 py-2 text-center font-semibold uppercase tracking-wide text-slate-900">Escore Médio</th>
                                              <th className="border border-white bg-[#A8D08D] px-2 py-2 text-center font-semibold uppercase tracking-wide text-slate-900">Escore Mínimo</th>
                                              <th className="border border-white bg-[#A8D08D] px-2 py-2 text-center font-semibold uppercase tracking-wide text-slate-900">Escore Bruto</th>
                                              <th className="border border-white bg-[#A8D08D] px-2 py-2 text-center font-semibold uppercase tracking-wide text-slate-900">Classificação</th>
                                            </tr>
                                          </thead>
                                          <tbody>
                                            {rows.map((row: any, index: number) => (
                                              row.note ? (
                                                <tr key={`${domainKey}-${row.label}-${index}`}>
                                                  <td className="border border-white bg-[#538135] px-3 py-1.5 font-medium text-white">{row.label}</td>
                                                  <td colSpan={5} className="border border-white bg-[#E2EFD9] px-3 py-1.5 text-left text-slate-700">{row.note}</td>
                                                </tr>
                                              ) : (
                                                <tr key={`${domainKey}-${row.label}-${index}`}>
                                                  <td className="border border-white bg-[#538135] px-3 py-1.5 text-left font-medium text-white">{row.label}</td>
                                                  <td className="border border-white bg-[#E2EFD9] px-2 py-1.5 text-center text-slate-700">{row.maxScore}</td>
                                                  <td className="border border-white bg-[#E2EFD9] px-2 py-1.5 text-center text-slate-700">{row.avgScore}</td>
                                                  <td className="border border-white bg-[#E2EFD9] px-2 py-1.5 text-center text-slate-700">{row.minScore}</td>
                                                  <td className="border border-white bg-[#E2EFD9] px-2 py-1.5 text-center text-slate-700">{row.obtainedScore}</td>
                                                  <td className="border border-white bg-[#E2EFD9] px-2 py-1.5 text-center text-slate-700">{row.classification}</td>
                                                </tr>
                                              )
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            ) : (
                            <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white">
                              <div className="grid grid-cols-[minmax(0,2fr)_120px_120px_minmax(0,1fr)] gap-3 border-b border-slate-100 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                                <div>Indicador</div>
                                <div>Valor</div>
                                <div>Percentil</div>
                                <div>Classificacao</div>
                              </div>
                              <div>
                                {metricRows.map((row: any, index: number) => {
                                  const percentileWidth = getPercentileWidth(row.percentile);

                                  return (
                                    <div key={`${row.label}-${index}`} className="grid grid-cols-[minmax(0,2fr)_120px_120px_minmax(0,1fr)] gap-3 border-b border-slate-100 px-3 py-2 text-sm last:border-b-0">
                                      <div className="font-medium text-slate-800">{row.label}</div>
                                      <div className="text-slate-600">{String(row.primary ?? "-")}</div>
                                      <div>
                                        <div className="text-slate-600">{row.percentile ?? "-"}</div>
                                        {percentileWidth !== null && (
                                          <div className="mt-1 h-1.5 rounded-full bg-slate-100">
                                            <div className="h-1.5 rounded-full bg-indigo-500" style={{ width: `${percentileWidth}%` }} />
                                          </div>
                                        )}
                                      </div>
                                      <div className="text-slate-600">{row.classification || "-"}</div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                            )
                          )}

                          {(test.code !== "bpa2" && !metricRows.length && test.resultRows.length > 0) && (
                            <div className="mt-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
                              <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">Linhas de resultado</div>
                              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                                {test.resultRows.map((row: string, index: number) => (
                                  <li key={`${index}-${row}`}>{row}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {test.clinicalInterpretation && (
                            <details className="mt-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                              <summary className="cursor-pointer font-medium text-slate-900">{test.code === "bpa2" ? "Interpretação e Observações Clínicas" : "Ver interpretacao tecnica"}</summary>
                              <pre className="mt-3 whitespace-pre-wrap hide-scrollbar text-sm leading-6 text-slate-600">{test.clinicalInterpretation}</pre>
                            </details>
                          )}

                          {test.warnings.length > 0 && (
                            <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                              <div className="font-medium">Avisos do teste</div>
                              <ul className="mt-2 list-disc pl-5">
                                {test.warnings.map((warning: string, index: number) => (
                                  <li key={`${index}-${warning}`}>{warning}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {warnings.length > 0 && (
                <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  <div className="font-medium">Avisos da geracao</div>
                  <ul className="mt-2 list-disc pl-5">
                    {warnings.map((warning: string, index: number) => (
                      <li key={`${index}-${warning}`}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {hasManualEdits && generatedText && (
                <div className="mt-3 grid gap-3 xl:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 bg-white">
                    <div className="border-b border-slate-100 px-4 py-3 text-sm font-medium text-slate-800">
                      {generationSource === "Fallback automatico" ? "Texto gerado pelo fallback automatico" : generationSource === "IA" ? "Texto gerado por IA" : "Texto gerado automaticamente"}
                    </div>
                    <pre className="max-h-72 overflow-auto hide-scrollbar whitespace-pre-wrap px-4 py-3 text-sm leading-7 text-slate-600">{generatedText}</pre>
                  </div>
                  <div className="rounded-xl border border-indigo-200 bg-indigo-50/60 px-4 py-3 text-sm text-indigo-900">
                    <div className="font-medium">Texto atual em edicao</div>
                    <p className="mt-2 leading-6">O editor abaixo mostra o texto editado por voce. O painel ao lado preserva a ultima versao gerada pela IA para comparacao.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          <textarea
            value={editedText}
            onChange={(event) => setEditedText(event.target.value)}
            disabled={isFinalized || !activeSection}
            className="min-h-[620px] w-full resize-none border-0 p-6 text-sm leading-7 text-slate-700 focus:ring-0 hide-scrollbar overflow-auto"
            placeholder="Selecione uma secao para revisar o conteudo..."
          />
        </main>
      </div>
    </PageContainer>
  );
}
