"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { api, resolveApiUrl } from "@/lib/api";
import { reportService } from "@/services/reportService";
import { SpecialistPilotPanel } from "@/components/reports/SpecialistPilotPanel";
import { ReportEditorNavigation } from "@/components/reports/ReportEditorNavigation";
import { ReportActionsMenu, ReportStatusBadge, ReportWorkspaceTabs, parseReportWorkspace, type ReportWorkspace } from "@/components/reports/ReportEditorControls";
import { ReportTestDataPanel } from "@/components/reports/ReportTestDataPanel";
import { ArrowLeft, CheckCircle2, Download, FileText, Loader2, RotateCcw, Save, ShieldCheck } from "lucide-react";

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
  if (!value) return "Não informado";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

function getGenerationSource(provider?: string | null, model?: string | null) {
  if (provider === "deterministic" || model === "rules-based") {
    return "Fallback automático";
  }
  if (["openai", "ollama", "anthropic"].includes(String(provider || "").toLowerCase())) {
    return "IA";
  }
  return "Não informado";
}

function getTextStatus(hasManualEdits: boolean, generationSource: string) {
  if (hasManualEdits) return "Editado manualmente";
  if (generationSource === "Fallback automático") {
    return "Igual ao fallback automático";
  }
  if (generationSource === "IA") return "Igual ao texto gerado por IA";
  return "Igual ao texto gerado automaticamente";
}

function getGenerationDetails(metadata: Record<string, any>) {
  const requestedModel = metadata.requested_model || metadata.model || "Não informado";
  const effectiveModel = metadata.model || "Não informado";
  const usedModelFallback = Boolean(metadata.used_model_fallback);
  const promptName = metadata.prompt_name || "Não informado";
  const generationPath = metadata.generation_path || "Não informado";

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
    .map((item: any, index: number) => ({
      applicationId: item.application_id ?? item.id ?? null,
      applicationKey: String(item.application_id ?? item.id ?? `legacy-${index}`),
      respondent: String(item.respondent_name || item.respondent || item.informant || ""),
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
      const key = item.applicationKey;
      if (!item.code && !item.name) return false;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
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
  const router = useRouter();
  const workspace = parseReportWorkspace(searchParams.get("view"));
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

  function selectWorkspace(value: ReportWorkspace) {
    const query = new URLSearchParams(searchParams.toString());
    query.set("view", value);
    const hash = value === "specialists" ? window.location.hash : "";
    router.replace(`/dashboard/reports/${reportId}?${query.toString()}${hash}`, { scroll: false });
  }

  useEffect(() => {
    const revealSpecialist = () => {
      if (!window.location.hash.startsWith("#specialist-run-")) return;
      const url = new URL(window.location.href);
      url.searchParams.set("view", "specialists");
      router.replace(`${url.pathname}${url.search}${url.hash}`, { scroll: false });
    };
    revealSpecialist();
    window.addEventListener("hashchange", revealSpecialist);
    return () => window.removeEventListener("hashchange", revealSpecialist);
  }, [router]);

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

  async function handleAudit() {
    if (!report) return;
    if (activeSection && editedText !== String(activeSection.edited_text || activeSection.generated_text || "")) {
      setError("Salve as alterações antes de executar a auditoria.");
      return;
    }
    if (!window.confirm("Auditar os textos salvos com o provedor de IA configurado? Essa operação pode gerar cobrança.")) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const result = await api.post<{ status: string; alerts: { issue: string }[] }>(`/api/reports/${report.id}/audit`, {});
      setNotice(result.status === "ok" ? "Auditoria concluída sem alertas. Revise o laudo antes de aprovar." : `Pendências da auditoria: ${(result.alerts || []).map((alert) => alert.issue).join("; ")}`);
      await loadReport();
    } catch (err: any) {
      setError(err?.message || "Não foi possível auditar o laudo.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateRevision() {
    if (!report || !window.confirm("Criar uma nova revisão, preservando o laudo aprovado original?")) return;
    setSaving(true);
    setError("");
    try {
      const revision = await api.post<{ id: number }>(`/api/reports/${report.id}/revisions`, {});
      router.push(`/dashboard/reports/${revision.id}`);
    } catch (err: any) {
      setError(err?.message || "Não foi possível criar uma nova revisão.");
    } finally {
      setSaving(false);
    }
  }

  async function handleFinalize() {
    if (!report) return;
    if (activeSection && editedText !== String(activeSection.edited_text || activeSection.generated_text || "")) {
      setError("Salve e audite as alterações antes de aprovar o laudo.");
      return;
    }
    if (!window.confirm("Confirmo a revisão clínica e aprovo os textos salvos sob minha responsabilidade profissional.")) return;
    setSaving(true);
    setError("");
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
      window.setTimeout(() => {
        link.remove();
        window.URL.revokeObjectURL(url);
      }, 1000);
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

  const isFinalized = report.status === "finalized" || report.status === "sent";
  const isTestsOnlyReport = report.ai_metadata?.generation_scope === "tests_only";
  const generationMetadata = activeSection?.generation_metadata || {};
  const warnings = activeSection?.warnings_payload || [];
  const generatedText = activeSection?.generated_text || "";
  const hasManualEdits = Boolean(activeSection && (activeSection.edited_text || "") !== generatedText);
  const generationTimestamp = generationMetadata.generated_at || activeSection?.updated_at;
  const generationSource = getGenerationSource(generationMetadata.provider, generationMetadata.model);
  const textStatus = getTextStatus(hasManualEdits, generationSource);
  const generationDetails = getGenerationDetails(generationMetadata);
  const hasUnsavedChanges = Boolean(activeSection && editedText !== String(activeSection.edited_text || activeSection.generated_text || ""));

  return (
    <PageContainer className="!p-4 sm:!p-6 lg:!p-8">
      <header className="mb-6 space-y-5">
        <Link href="/dashboard/reports" className="inline-flex items-center gap-2 rounded text-sm text-slate-500 hover:text-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />Todos os laudos
        </Link>
        <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between">
          <div className="min-w-0 flex-1 space-y-2">
            <div className="flex flex-wrap items-center gap-2.5"><span className="text-xs font-medium text-slate-500">LAUDO #{report.id}</span><ReportStatusBadge status={report.status} /></div>
            <h1 className="break-words text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">{report.patient_name || report.title}</h1>
            <p className="break-words text-sm text-slate-500">{report.title} <span aria-hidden="true">·</span> {report.evaluation_title || "Avaliação neuropsicológica"}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button type="button" variant="outline" className="gap-2 bg-white" onClick={handleExportDocx} disabled={isTestsOnlyReport}>
              <Download aria-hidden="true" className="h-4 w-4" />Exportar DOCX
            </Button>
            <ReportActionsMenu disabled={saving} actions={[
              { label: "Visualizar HTML", onSelect: handleExportHtml, disabled: isTestsOnlyReport, icon: <FileText aria-hidden="true" className="h-4 w-4" /> },
              ...(isFinalized ? [{ label: "Criar nova revisão", onSelect: handleCreateRevision }] : [
                { label: "Regenerar testes", onSelect: handleRegenerateTests, disabled: completedTests.length === 0, icon: <RotateCcw aria-hidden="true" className="h-4 w-4" /> },
              ]),
            ]} />
          </div>
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-2 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
          <span>Responsável: <span className="font-medium text-slate-700">{report.author_name || "Não informado"}</span></span>
          <span>Atualizado em {formatTimestamp(report.updated_at)}</span>
          <span>{report.sections?.length || 0} capítulos · {completedTests.length} aplicações validadas</span>
        </div>
      </header>

      {error && <div role="alert" className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      {notice && <div role="status" className="mb-4 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">{notice}</div>}
      {isTestsOnlyReport && (
        <div className="mb-4 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
              Somente testes
            </span>
            <span>
              Este laudo contém apenas seções de testes validados. Aprovação e exportação ficam disponíveis após gerar o laudo completo.
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
                As fontes foram atualizadas, mas ainda faltam seções no texto atual. Reconstrua o laudo para incluir: {missingSections.join(", ")}.
              </div>
            </div>
            <Button variant="outline" className="border-amber-300 bg-white text-amber-900 hover:bg-amber-100" disabled={saving} onClick={handleRebuildReport}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Reconstruir laudo
            </Button>
          </div>
        </div>
      )}

      <ReportWorkspaceTabs value={workspace} onChange={selectWorkspace} />

      <section id="report-panel-editor" role="tabpanel" aria-labelledby="report-tab-editor" hidden={workspace !== "editor"} tabIndex={0} className="rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
      <div className="grid min-w-0 grid-cols-1 items-start gap-5 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[240px_minmax(0,1fr)]">
        <ReportEditorNavigation sections={report.sections || []} activeSectionId={activeSectionId} onSelect={setActiveSectionId} />

        <div className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-5 py-4 sm:px-6">
            <div>
              <h2 className="text-base font-semibold text-slate-900">{activeSection?.title || "Selecione um capítulo"}</h2>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                {isTestsOnlyReport
                  ? "Rascunho de testes · gere o laudo completo antes de concluir."
                  : isFinalized ? "Versão aprovada · conteúdo disponível para consulta." : "Revise o conteúdo antes de salvar este capítulo."}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {isFinalized && (
                <Button type="button" variant="outline" disabled={saving} onClick={handleCreateRevision}>
                  Nova revisão
                </Button>
              )}
              {!isFinalized && (
                <>
                  <ReportActionsMenu label="Opções" disabled={saving || !activeSection} actions={[
                    { label: isWiscSubscaleActive ? "Regenerar domínios WISC" : "Regenerar seção", onSelect: isWiscSubscaleActive ? handleRegenerateWiscSubscales : handleRegenerate, icon: <RotateCcw aria-hidden="true" className="h-4 w-4" /> },
                  ]} />
                  <Button type="button" className="gap-2" disabled={saving || !activeSection} onClick={handleSave}>
                    {saving ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin motion-reduce:animate-none" /> : <Save aria-hidden="true" className="h-4 w-4" />}
                    {saving ? "Processando…" : "Salvar seção"}
                  </Button>
                </>
              )}
            </div>
          </div>

          {activeSection && warnings.length > 0 && (
            <div className="mx-5 mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 sm:mx-6">
              <h3 className="font-medium">Atenção antes de concluir este capítulo</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5">{warnings.map((warning: string, index: number) => <li key={index}>{warning}</li>)}</ul>
            </div>
          )}
          <div className="px-5 py-5 sm:px-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
              <label htmlFor="report-section-content" className="font-medium text-slate-600">Conteúdo do capítulo</label>
              <span role="status">{!activeSection ? "Nenhum capítulo selecionado" : isFinalized ? "Somente leitura" : hasUnsavedChanges ? "Alterações não salvas" : "Texto salvo"}</span>
            </div>
            <textarea
              id="report-section-content" name="section_content" lang="pt-BR" spellCheck
              value={editedText}
              onChange={(event) => setEditedText(event.target.value)}
              disabled={isFinalized || !activeSection}
              className="min-h-[480px] w-full resize-y rounded-lg border border-slate-100 bg-white p-4 text-[15px] leading-8 text-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary disabled:bg-slate-50/50 disabled:text-slate-600 sm:p-5 lg:min-h-[580px]"
              placeholder="Selecione um capítulo para revisar o conteúdo…"
            />
            <p className="mt-3 text-xs leading-5 text-slate-500">{isFinalized ? "Para alterar este conteúdo, crie uma nova revisão. O original aprovado será preservado." : "Salvar uma seção não aprova o laudo. A revisão e a aprovação final são etapas separadas."}</p>
          </div>
          {activeSection && <div className="divide-y divide-slate-100 border-t border-slate-100">
            <details className="px-5 py-4 sm:px-6">
              <summary className="cursor-pointer text-sm font-medium text-slate-600 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">Origem e detalhes da geração</summary>
              <dl className="mt-5 grid gap-x-6 gap-y-4 text-sm sm:grid-cols-2 [&_dt]:text-xs [&_dt]:text-slate-500 [&_dd]:mt-1 [&_dd]:break-words [&_dd]:text-slate-800">
                <div><dt>Origem</dt><dd>{generationSource}</dd></div>
                <div><dt>Status do texto salvo</dt><dd>{textStatus}</dd></div>
                <div><dt>Provedor</dt><dd>{generationMetadata.provider || "Não informado"}</dd></div>
                <div><dt>Modelo</dt><dd>{generationDetails.effectiveModel}</dd></div>
                <div><dt>Última geração</dt><dd>{formatTimestamp(generationTimestamp)}</dd></div>
                <div><dt>Execução</dt><dd>{generationDetails.usedModelFallback ? "IA com fallback de modelo" : generationDetails.generationPath === "ai" ? "IA direta" : generationDetails.generationPath === "deterministic_fallback" ? "Fallback da seção" : "Fluxo padrão"}</dd></div>
                {generationSource === "IA" && <><div><dt>Modelo solicitado</dt><dd>{generationDetails.requestedModel}</dd></div><div><dt>Prompt</dt><dd>{generationDetails.promptName}</dd></div></>}
              </dl>
            </details>
            {hasManualEdits && generatedText && <details className="px-5 py-4 sm:px-6">
              <summary className="cursor-pointer text-sm font-medium text-slate-600 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">Comparar com o texto gerado</summary>
              <p className="mt-4 text-xs leading-5 text-slate-500">Versão gerada antes da edição manual. O conteúdo atual permanece no editor acima.</p>
              <pre className="mt-3 max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-4 font-sans text-sm leading-7 text-slate-600">{generatedText}</pre>
            </details>}
          </div>}
        </div>

        <div className="min-w-0 space-y-5 lg:col-start-2">
          <section aria-labelledby="report-final-review" className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="flex items-start gap-3"><ShieldCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-primary" /><div><h2 id="report-final-review" className="text-sm font-semibold text-slate-900">Revisão e conclusão do laudo</h2><p className="mt-1 text-sm leading-6 text-slate-500">{isFinalized ? "Esta versão foi aprovada. Alterações exigem uma nova revisão, sem modificar o original." : "Após conferir todos os capítulos, audite os textos salvos e registre a aprovação profissional. A auditoria não substitui a revisão clínica."}</p></div></div>
            {!isFinalized && <div className="mt-5 flex flex-wrap gap-2">
              <Button type="button" variant="outline" disabled={saving || isFinalized || isTestsOnlyReport} onClick={handleAudit}>Auditar textos salvos</Button>
              <Button type="button" variant="outline" className="gap-2" disabled={saving || isFinalized || isTestsOnlyReport} onClick={handleFinalize}><CheckCircle2 aria-hidden="true" className="h-4 w-4" />Aprovar laudo</Button>
            </div>}
          </section>
          <details className="rounded-xl border border-slate-200 bg-white px-5 py-4 sm:px-6">
            <summary className="cursor-pointer text-sm font-medium text-slate-600 hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">Informações do laudo e histórico</summary>
            <dl className="mt-5 space-y-3 text-sm text-slate-600"><div><dt className="text-xs text-slate-500">Interessado</dt><dd className="mt-1">{report.interested_party || report.patient_name}</dd></div><div><dt className="text-xs text-slate-500">Finalidade</dt><dd className="mt-1 break-words">{report.purpose || "Não informada"}</dd></div></dl>
            <h3 className="mt-5 text-xs font-medium text-slate-500">Últimas versões</h3>
            {(report.versions || []).length ? <ul className="mt-2 divide-y divide-slate-100">{(report.versions || []).slice(0, 5).map((version: any) => <li key={version.id} className="flex flex-wrap justify-between gap-2 py-2 text-sm text-slate-600"><span>Versão {version.version_number}</span><span>{version.created_by}</span></li>)}</ul> : <p className="mt-2 text-sm text-slate-500">Nenhuma versão anterior registrada.</p>}
          </details>
        </div>
      </div>
      </section>

      <section id="report-panel-tests" role="tabpanel" aria-labelledby="report-tab-tests" hidden={workspace !== "tests"} tabIndex={0} className="min-w-0 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
        <ReportTestDataPanel tests={completedTests} selected={selectedTests} onToggle={(key) => setSelectedTests((previous) => previous.includes(key) ? previous.filter((value) => value !== key) : [...previous, key])} />
      </section>

      <section id="report-panel-specialists" role="tabpanel" aria-labelledby="report-tab-specialists" hidden={workspace !== "specialists"} tabIndex={0} className="min-w-0 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
        <SpecialistPilotPanel key={String(report.id)} reportId={report.id} />
      </section>
    </PageContainer>
  );
}
