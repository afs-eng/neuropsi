"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type Blocker = { code: string; message: string; application_id: number | null };
type Application = {
  application_id: number; instrument_code: string; instrument_name: string;
  validated: boolean; supported: boolean; enabled: boolean; issues: string[];
};
type Preparation = {
  id: number; report_id: number; status: string; stored_status: string;
  is_current: boolean; created_at: string; source_sha256: string;
  steps: { key: string; title: string; status: string }[];
};
export type PreparationStatus = {
  enabled: boolean; can_prepare?: boolean; ready_for_execution?: boolean;
  blockers?: Blocker[]; applications?: Application[]; limitations?: string[];
  targets?: { id: number; title: string; status: string }[];
  target_report_id?: number | null; latest?: Preparation | null;
};

const preparationLabels: Record<string, string> = {
  prepared: "Fontes registradas", blocked: "Pendências identificadas", stale: "Fontes alteradas — registre uma nova preparação",
};
const reportLabels: Record<string, string> = {
  draft: "Rascunho", in_review: "Em revisão", generating: "Em geração", finalized: "Finalizado", sent: "Enviado",
};

export function ReportPreparationView({ data, loading, submitting, error, notice, selectedReport, onSelect, onRefresh, onPrepare }: {
  data: PreparationStatus | null; loading: boolean; submitting: boolean; error: string; notice: string;
  selectedReport: string; onSelect: (value: string) => void; onRefresh: () => void; onPrepare: () => void;
}) {
  if (data && !data.enabled) return null;
  const busy = loading || submitting;
  const latest = data?.latest;
  return (
    <section aria-label="Preparação automatizada do laudo" aria-busy={busy} className="mb-6 min-w-0 break-words rounded-xl border border-slate-200 bg-white p-6 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold text-slate-900">Preparação do laudo com IA</h2>
          <p className="text-sm text-slate-600">Primeira etapa: conferir fontes e registrar pendências. Ainda não gera interpretações ou altera o laudo.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" disabled={busy} onClick={onRefresh}>Atualizar fontes</Button>
          <Button type="button" disabled={busy || !data?.can_prepare || !!error} onClick={onPrepare}>
            {submitting ? "Registrando fontes…" : "Preparar laudo com IA"}
          </Button>
        </div>
      </div>
      {loading && <p role="status" className="text-sm text-slate-600">Conferindo fontes…</p>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {notice && <p role="status" className="text-sm text-slate-700">{notice}</p>}
      {!!data?.targets?.length && (
        <div className="space-y-1">
          <label htmlFor="preparation-target-report" className="block text-sm font-medium text-slate-800">Laudo alvo</label>
          <select id="preparation-target-report" name="report_id" autoComplete="off" value={selectedReport} disabled={busy} onChange={(event) => onSelect(event.target.value)} className="w-full max-w-lg rounded-md border border-slate-300 bg-white p-2 text-sm text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <option value="">Selecionar automaticamente, se houver um único laudo editável</option>
            {data.targets.map((target) => <option key={target.id} value={target.id}>#{target.id} — {target.title} ({reportLabels[target.status] || target.status})</option>)}
          </select>
        </div>
      )}
      {!loading && data?.enabled && (
        <>
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-slate-900">Cobertura da avaliação</h3>
            {!data.applications?.length ? <p className="text-sm text-slate-600">Nenhuma aplicação registrada.</p> : (
              <ul className="divide-y divide-slate-100">
                {data.applications.map((app) => (
                  <li key={app.application_id} className="flex flex-wrap justify-between gap-2 py-2 text-sm">
                    <span className="font-medium text-slate-800">{app.instrument_name} — aplicação #{app.application_id}</span>
                    <span className="text-slate-600">
                      {app.validated ? "Validada" : "Não validada"} · {!app.supported ? "Sem especialista" : !app.enabled ? "Especialista desabilitado" : "Perfil executável; homologação não verificada"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {!!data.blockers?.length && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
              <h3 className="text-sm font-semibold text-amber-900">Pendências atuais ({data.blockers.length})</h3>
              <ul className="mt-2 list-disc pl-5 text-sm text-amber-950 space-y-1">
                {data.blockers.map((blocker, index) => <li key={`${blocker.code}-${blocker.application_id}-${index}`}>
                  {blocker.application_id ? `Aplicação #${blocker.application_id}: ` : ""}{blocker.message}
                </li>)}
              </ul>
              <p className="mt-2 text-sm text-amber-950">Com um laudo editável selecionado, é possível registrar pendências sem iniciar processamento.</p>
            </div>
          )}
          {latest && (
            <div className="space-y-2 border-t border-slate-100 pt-4">
              <h3 className="text-sm font-semibold text-slate-900">Preparação #{latest.id} — {preparationLabels[latest.status] || latest.status}</h3>
              <p className="text-sm text-slate-600">Registro em <time dateTime={latest.created_at}>{new Date(latest.created_at).toLocaleString("pt-BR")}</time>. Nenhuma IA agendada.</p>
              <ol className="list-decimal pl-5 text-sm text-slate-700 space-y-1">
                {latest.steps.map((step) => <li key={step.key}>{step.title}: {step.status === "completed" ? "fontes registradas (não é aprovação clínica)" : "não disponível nesta entrega"}</li>)}
              </ol>
              <Link href={`/dashboard/reports/${latest.report_id}`} className="inline-block text-sm font-medium text-primary underline hover:text-primary/80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">Abrir laudo alvo #{latest.report_id}</Link>
            </div>
          )}
          <details className="text-sm text-slate-600">
            <summary className="cursor-pointer font-medium hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">Limites desta etapa</summary>
            <ul className="mt-2 list-disc pl-5 space-y-1">{data.limitations?.map((limit) => <li key={limit}>{limit}</li>)}</ul>
          </details>
        </>
      )}
    </section>
  );
}

export function ReportPreparationPanel({ evaluationId }: { evaluationId: number }) {
  const [data, setData] = useState<PreparationStatus | null>(null);
  const [selectedReport, setSelectedReport] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const submittingRef = useRef(false);
  const mounted = useRef(false);
  const endpoint = `/api/report-preparations/evaluations/${evaluationId}`;

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError("");
    api.get<PreparationStatus>(`${endpoint}${selectedReport ? `?report_id=${selectedReport}` : ""}`, { signal: controller.signal })
      .then((result) => { if (active) setData(result); })
      .catch((reason: { message?: string }) => { if (active) setError(reason.message || "Não foi possível consultar a preparação."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; controller.abort(); };
  }, [endpoint, selectedReport, refresh]);

  async function prepare() {
    if (submittingRef.current || loading || !data?.can_prepare) return;
    submittingRef.current = true;
    setSubmitting(true);
    setError("");
    setNotice("");
    try {
      const result = await api.post<{ message: string }>(endpoint, { report_id: selectedReport ? Number(selectedReport) : data.target_report_id });
      if (mounted.current) {
        setNotice(result.message);
        setLoading(true);
        setRefresh((value) => value + 1);
      }
    } catch (reason) {
      if (mounted.current) setError((reason as { message?: string }).message || "Não foi possível registrar as fontes. Atualize antes de tentar novamente.");
    } finally {
      submittingRef.current = false;
      if (mounted.current) setSubmitting(false);
    }
  }

  return <ReportPreparationView data={data} loading={loading} submitting={submitting} error={error} notice={notice}
    selectedReport={selectedReport} onSelect={(value) => { setLoading(true); setSelectedReport(value); setNotice(""); }}
    onRefresh={() => { setLoading(true); setNotice(""); setRefresh((value) => value + 1); }} onPrepare={prepare} />;
}
