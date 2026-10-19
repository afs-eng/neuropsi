"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { SpecialistProgressPanel } from "./SpecialistProgressPanel";
import { shouldPollSpecialists, startSpecialistPolling, type SpecialistProgressRun } from "./specialistProgress";

type Application = { id: number; instrument_code: string; instrument_name: string; respondent: string; enabled: boolean; supported: boolean };
type Configuration = { configured: boolean; configuration_message: string; model: string; provider: string; can_request: boolean; request_block_reason?: string; report_status?: string; can_review: boolean; applications: Application[] };
type Review = { id: number; decision: string; notes: string; created_at: string };
type Run = SpecialistProgressRun & {
  id: number; application_id: number; instrument_code: string; model: string; provider: string;
  status: string; is_current: boolean; source_sha256: string; output_sha256: string;
  error_code: string; review_is_current: boolean; reviews: Review[];
  usage?: { finish_reason?: string; validation_code?: string; validation_section?: string };
  output: { findings?: { section?: string; statement: string; evidence_ids: string[] }[]; limitations?: string[]; review_questions?: string[] };
  evidence: Record<string, unknown>;
};

const STATUS: Record<string, string> = {
  queued: "Na fila — aguarda worker", running: "Em análise", needs_review: "Aguardando revisão",
  failed: "Falhou — sem repetição automática", stale: "Dados ou versão alterados — rascunho desatualizado",
};

const BPA2_SECTION_TITLES: Record<string, string> = {
  introducao: "Interpretação e Observações Clínicas", ac: "Atenção Concentrada (AC)",
  ad: "Atenção Dividida (AD)", aa: "Atenção Alternada (AA)", ag: "Atenção Geral (AG)",
  analise_clinica: "Análise Clínica",
};

const GENERATION_ERRORS: Record<string, string> = {
  generation_failed: "Falha não classificada. Este registro não contém detalhes suficientes para identificar a causa.",
  output_validation_failed: "A resposta não passou na validação de evidências ou redação.",
  output_schema_invalid: "O modelo não retornou a estrutura JSON exigida após as tentativas permitidas.",
  output_truncated: "A resposta foi interrompida pelo limite de saída; nenhum texto parcial foi aceito.",
  provider_refusal: "O provedor recusou ou filtrou a resposta.",
  provider_timeout: "O modelo não respondeu dentro do tempo permitido.",
  provider_connection: "O worker não conseguiu conectar ao servidor do modelo.",
  provider_rate_limit: "O provedor limitou as requisições.",
  provider_auth: "O provedor recusou a autenticação.",
  provider_error: "O servidor do modelo retornou um erro HTTP.",
  usage_limit_exceeded: "A execução excedeu o limite de requisições ou tokens permitido.",
};

const VALIDATION_ERRORS: Record<string, string> = {
  evidence_not_found: "Foi citada uma evidência inexistente.",
  ungrounded_number: "Um número foi citado sem suporte nas evidências do achado.",
  bpa2_semantics: "A redação confundiu escore/AG ou mencionou outro instrumento.",
  bpa2_missing_evidence: "Faltaram evidências obrigatórias de um componente ou da síntese.",
  bpa2_score_text: "O parágrafo não apresentou corretamente escore em pontos, percentil ou classificação.",
};

export function SpecialistPilotPanel({ reportId }: { reportId: string | number }) {
  return <SpecialistPilotContent key={String(reportId)} reportId={reportId} />;
}

function SpecialistPilotContent({ reportId }: { reportId: string | number }) {
  const [configuration, setConfiguration] = useState<Configuration | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [requestedIds, setRequestedIds] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<number | null>(null);
  const [refreshError, setRefreshError] = useState("");
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);

  const reload = useCallback(async (silent = false) => {
    const request = ++generation.current;
    controller.current?.abort();
    const abort = new AbortController();
    controller.current = abort;
    const timeout = window.setTimeout(() => abort.abort(), 20000);
    if (!silent) setLoading(true);
    try {
      const [config, results] = await Promise.all([
        api.get<Configuration>(`/api/reports/${reportId}/specialist-status`, { signal: abort.signal }),
        api.get<Run[]>(`/api/reports/${reportId}/specialist-runs`, { signal: abort.signal }),
      ]);
      if (generation.current !== request) return;
      setConfiguration(config);
      setRuns(results);
      setLastUpdatedAt(Date.now());
      setRefreshError("");
      setSelected((current) => current.filter((id) => config.applications.some((app) => app.id === id && app.enabled)));
    } catch (err: unknown) {
      if (generation.current === request) setRefreshError(abort.signal.aborted ? "A consulta demorou demais. Tente atualizar o status." : (err as { message?: string })?.message || "Não foi possível consultar o sistema.");
    } finally {
      window.clearTimeout(timeout);
      if (generation.current === request) setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    void reload();
    return () => { generation.current += 1; controller.current?.abort(); };
  }, [reload]);

  const polling = shouldPollSpecialists(runs, requestedIds);
  useEffect(() => {
    if (!polling) return;
    const refresh = async () => {
      if (document.visibilityState === "visible") await reload(true);
    };
    const stop = startSpecialistPolling(refresh, (callback, delay) => {
      const timer = window.setTimeout(() => void callback(), delay);
      return () => window.clearTimeout(timer);
    });
    const onVisible = () => { void refresh(); };
    document.addEventListener("visibilitychange", onVisible);
    return () => { stop(); document.removeEventListener("visibilitychange", onVisible); };
  }, [polling, reload]);

  async function enqueue() {
    if (busy || !configuration?.can_request || selected.length === 0) return;
    const destination = configuration.provider === "ollama"
      ? "O worker usará o Ollama local configurado. Confira que o modelo é local e que os recursos de nuvem do Ollama estão desativados."
      : "Os dados serão enviados ao provedor externo, que pode cobrar.";
    if (!window.confirm(`Enviar resultados das ${selected.length} aplicações selecionadas ao modelo ${configuration.model}? São dados sensíveis. ${destination} O worker fará até duas requisições por execução. Nenhum texto do laudo será substituído.`)) return;
    setBusy(true);
    setSubmitting(true);
    setError("");
    setNotice("");
    try {
      const result = await api.post<{ run_ids: number[]; skipped: { application_id: number }[] }>(`/api/reports/${reportId}/specialist-runs`, { application_ids: selected });
      setRequestedIds(result.run_ids);
      setNotice(`${result.run_ids.length} execuções solicitadas ou reutilizadas. ${result.skipped.length} aplicações ignoradas. A fila só avança com o worker ligado; falhas não são repetidas automaticamente.`);
      await reload();
    } catch (err: unknown) {
      setError((err as { message?: string })?.message || "Não foi possível solicitar os rascunhos.");
    } finally { setBusy(false); setSubmitting(false); }
  }

  async function review(run: Run, decision: "approved" | "rejected") {
    const text = (notes[run.id] || "").trim();
    if (decision === "rejected" && text.length < 3) {
      setError("Informe um motivo para rejeitar o rascunho.");
      return;
    }
    if (!window.confirm(decision === "approved" ? "Confirmo a revisão dos achados e evidências deste rascunho experimental. Isso não aprova o laudo nem integra o texto automaticamente." : "Registrar a rejeição deste rascunho?")) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api.post(`/api/reports/${reportId}/specialist-runs/${run.id}/reviews`, {
        decision, notes: text, source_sha256: run.source_sha256, output_sha256: run.output_sha256,
      });
      setNotice("Revisão registrada. O texto do laudo não foi alterado.");
      await reload();
    } catch (err: unknown) {
      setError((err as { message?: string })?.message || "Não foi possível registrar a revisão.");
    } finally { setBusy(false); }
  }

  return (
    <section aria-labelledby="specialist-pilot-title" className="mb-6 rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="specialist-pilot-title" className="font-semibold text-slate-900">Especialistas de IA — piloto experimental</h2>
        <Button variant="outline" disabled={loading || busy} onClick={() => void reload()}>{loading ? "Atualizando…" : "Atualizar status"}</Button>
      </div>
      <p className="mt-2 text-sm text-slate-600">O fluxo atual permanece legado. Estes rascunhos não alteram resultados, seções ou DOCX. Cada aplicação/informante é analisado separadamente e exige revisão profissional.</p>
      <p className="mt-2 text-sm text-slate-600">Worker separado: sua atividade não é monitorada neste painel. No piloto local, a fila para quando o computador ou o processo é desligado.</p>
      {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
      {notice && <p role="status" className="mt-3 text-sm text-slate-700">{notice}</p>}
      {configuration && (
        <>
          <p className="mt-3 text-sm font-medium">Provedor: {configuration.provider}. Modelo: {configuration.model || "não selecionado"}. {configuration.configured ? "Configuração disponível; isso não comprova homologação clínica." : configuration.configuration_message}</p>
          {!configuration.can_request && (
            <p id="specialist-request-block" role="status" className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              <strong>Seleção e solicitação bloqueadas: </strong>
              {configuration.request_block_reason || "A API não autorizou a solicitação para este laudo ou perfil. Confira o status do laudo e a permissão da conta responsável."}
              {configuration.report_status && <span className="mt-1 block">Status do laudo: {({ draft: "Rascunho", in_review: "Em revisão", generating: "Em geração", finalized: "Finalizado", sent: "Enviado" } as Record<string, string>)[configuration.report_status] || configuration.report_status}.</span>}
            </p>
          )}
          <fieldset aria-describedby={!configuration.can_request ? "specialist-request-block" : "specialist-selection-help"} disabled={busy || loading || !configuration.can_request} className="mt-4 space-y-2">
            <legend className="mb-2 text-sm font-semibold">Aplicações validadas disponíveis</legend>
            {configuration.applications.length === 0 && <p className="text-sm text-slate-500">Nenhuma aplicação validada nesta avaliação.</p>}
            {configuration.applications.map((app) => (
              <label key={app.id} className={`flex min-h-8 items-start gap-2 text-sm text-slate-700 ${configuration.can_request && app.enabled ? "cursor-pointer" : "cursor-not-allowed"}`}>
                <input type="checkbox" className="mt-0.5 h-4 w-4 shrink-0 accent-teal-700" disabled={!app.enabled} checked={selected.includes(app.id)} onChange={() => setSelected((current) => current.includes(app.id) ? current.filter((id) => id !== app.id) : [...current, app.id])} />
                <span>{app.instrument_name} — aplicação #{app.id}{app.respondent ? ` — informante: ${app.respondent}` : ""}{!app.supported ? " (especialista ainda não implementado)" : !app.enabled ? " (não habilitado neste ambiente)" : ""}</span>
              </label>
            ))}
          </fieldset>
          {configuration.can_request && <p id="specialist-selection-help" role="status" className="mt-2 text-sm text-slate-600">{selected.length === 0 ? "Marque ao menos uma aplicação habilitada para liberar a solicitação." : `${selected.length} aplicação(ões) selecionada(s).`}</p>}
          <Button variant="outline" className="mt-3" disabled={busy || loading || !configuration.can_request || selected.length === 0} onClick={enqueue}>{submitting ? "Registrando solicitação…" : "Solicitar rascunhos selecionados"}</Button>
        </>
      )}
      <SpecialistProgressPanel runs={runs} requestedIds={requestedIds} submitting={submitting} lastUpdatedAt={lastUpdatedAt} refreshError={refreshError} errorMessages={GENERATION_ERRORS} />
      <div className="mt-5 space-y-3">
        {runs.map((run) => (
          <details id={`specialist-run-${run.id}`} key={run.id} className="scroll-mt-6 rounded-xl border border-slate-200 p-3">
            <summary className="cursor-pointer text-sm font-medium">
              {run.instrument_code.toUpperCase()} — aplicação #{run.application_id} — {STATUS[run.status] || run.status}
              {run.review_is_current && run.reviews[0] ? ` · ${run.reviews[0].decision === "approved" ? "Aprovado para o piloto (não integrado)" : "Rejeitado"}` : ""}
            </summary>
            <p className="mt-2 text-xs text-slate-500">Execução #{run.id} · provedor: {run.provider} · modelo: {run.model}</p>
            {run.error_code && <p className="mt-2 text-sm text-red-700">Motivo técnico: {run.error_code}. Solicitar novamente a mesma execução não dispara uma repetição.</p>}
            {GENERATION_ERRORS[run.error_code] && <p className="mt-1 text-sm text-red-700">{GENERATION_ERRORS[run.error_code]}</p>}
             {run.usage?.validation_code && VALIDATION_ERRORS[run.usage.validation_code] && <p className="mt-1 text-sm text-red-700">{VALIDATION_ERRORS[run.usage.validation_code]} Código: {run.usage.validation_code}.</p>}
             {run.instrument_code === "bpa2" && run.usage?.validation_section && BPA2_SECTION_TITLES[run.usage.validation_section] && <p className="mt-1 text-sm text-red-700">Primeira seção com falha de validação: {BPA2_SECTION_TITLES[run.usage.validation_section]}.</p>}
            {!run.is_current && <p className="mt-2 text-sm text-amber-800">Dados ou versão do especialista alterados: solicite um novo rascunho para revisar a configuração atual. O histórico anterior foi preservado.</p>}
            {(run.output.findings || []).map((finding, index) => (
              <div key={index} className="mt-3 text-sm">
                {run.instrument_code === "bpa2" && finding.section && BPA2_SECTION_TITLES[finding.section] && <h3 className="mb-1 font-semibold">{BPA2_SECTION_TITLES[finding.section]}</h3>}
                <p>{finding.statement}</p>
                <details className="mt-1 text-xs text-slate-600">
                  <summary className="cursor-pointer">Consultar evidências citadas</summary>
                  <ul className="mt-1 space-y-1">{finding.evidence_ids.map((id) => <li key={id} className="break-words"><code>{id}</code>: {JSON.stringify(run.evidence[id] ?? null)}</li>)}</ul>
                </details>
              </div>
            ))}
            {(run.output.limitations || []).length > 0 && <div className="mt-3 text-sm"><h3 className="font-medium">Limitações</h3><ul className="list-inside list-disc">{run.output.limitations?.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}
            {(run.output.review_questions || []).length > 0 && <div className="mt-3 text-sm"><h3 className="font-medium">Pontos para revisão</h3><ul className="list-inside list-disc">{run.output.review_questions?.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}
            {configuration?.can_review && run.is_current && run.status === "needs_review" && (
              <div className="mt-4 space-y-2">
                <label htmlFor={`specialist-notes-${run.id}`} className="block text-sm font-medium">Notas de revisão (obrigatórias ao rejeitar)</label>
                <textarea id={`specialist-notes-${run.id}`} maxLength={2000} rows={2} disabled={busy} value={notes[run.id] || ""} onChange={(event) => setNotes((current) => ({ ...current, [run.id]: event.target.value }))} className="w-full rounded-lg border border-slate-300 p-2 text-sm" />
                <div className="flex gap-2"><Button variant="outline" disabled={busy || loading} onClick={() => review(run, "approved")}>Aprovar rascunho</Button><Button variant="outline" disabled={busy || loading} onClick={() => review(run, "rejected")}>Rejeitar</Button></div>
              </div>
            )}
            {run.reviews.length > 0 && <details className="mt-3 text-xs text-slate-600"><summary className="cursor-pointer">Histórico de decisões</summary><ul>{run.reviews.map((item) => <li key={item.id} className="mt-1">{item.decision === "approved" ? "Aprovado para o piloto" : "Rejeitado"} · {new Date(item.created_at).toLocaleString("pt-BR")} · {item.notes || "Sem notas"}</li>)}</ul></details>}
          </details>
        ))}
        {!loading && lastUpdatedAt !== null && runs.length === 0 && <p className="text-sm text-slate-500">Nenhuma execução de especialista solicitada neste laudo.</p>}
      </div>
    </section>
  );
}
