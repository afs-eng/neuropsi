"use client";

import { useEffect, useState } from "react";
import {
  elapsedSpecialistSeconds, formatSpecialistDuration, isSpecialistPending,
  monitoredSpecialists, type SpecialistProgressRun,
} from "./specialistProgress";

type Props = {
  runs: SpecialistProgressRun[];
  requestedIds: number[];
  submitting: boolean;
  lastUpdatedAt: number | null;
  refreshError: string;
  errorMessages: Record<string, string>;
};

const LABELS: Record<string, string> = {
  queued: "Na fila — aguardando worker", running: "Gerando e validando",
  needs_review: "Concluído — revisão necessária", failed: "Falhou — execução encerrada",
  stale: "Desatualizado — nova revisão necessária",
};

function openRun(id: number) {
  const element = document.getElementById(`specialist-run-${id}`);
  if (element instanceof HTMLDetailsElement) element.open = true;
}

export function SpecialistProgressPanel({ runs, requestedIds, submitting, lastUpdatedAt, refreshError, errorMessages }: Props) {
  const [now, setNow] = useState(() => Date.now());
  const monitored = monitoredSpecialists(runs, requestedIds);
  const active = monitored.some(isSpecialistPending);
  const missing = requestedIds.filter((id) => !runs.some((run) => run.id === id)).length;
  const ready = monitored.filter((run) => run.status === "needs_review" && run.is_current).length;
  const failed = monitored.filter((run) => run.status === "failed").length;
  const finished = monitored.filter((run) => !isSpecialistPending(run)).length;
  const total = requestedIds.length || monitored.length;

  useEffect(() => {
    if (!active) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [active]);

  if (!submitting && monitored.length === 0 && missing === 0 && !refreshError) return null;

  return (
    <section aria-label="Acompanhamento dos especialistas" className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">{requestedIds.length ? "Acompanhamento da solicitação" : "Últimas execuções por aplicação"}</h3>
        {lastUpdatedAt !== null && <p className="text-xs text-slate-600">Última consulta: <time dateTime={new Date(lastUpdatedAt).toISOString()}>{new Date(lastUpdatedAt).toLocaleTimeString("pt-BR")}</time></p>}
      </div>
      <p role="status" className="mt-2 text-sm text-slate-700">
        {submitting ? "Registrando sua solicitação no sistema…" : `${ready} pronta(s) para revisão · ${failed} falha(s) · ${monitored.filter(isSpecialistPending).length} pendente(s).`}
      </p>
      {(active || missing > 0) && <p className="mt-1 text-xs text-slate-600">Consulta automática a cada 5 segundos enquanto esta aba estiver visível. A barra indica atividade, não percentual nem previsão de término.</p>}
      {refreshError && <p role="alert" className="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-2 text-sm text-amber-900">Não foi possível confirmar o status atual. {refreshError} Os estados abaixo são da última consulta; isso não confirma falha da IA.</p>}
      {submitting && <progress aria-label="Registrando solicitação" className="mt-2 h-2 w-full accent-teal-700" />}
      {missing > 0 && !submitting && <p className="mt-2 text-sm text-amber-900">Aguardando confirmação de {missing} execução(ões) na consulta. O processamento ainda não está confirmado.</p>}
      {total > 1 && <div className="mt-3">
        <p className="text-xs text-slate-600">{finished} de {total} execuções encerradas (inclui falhas e desatualizadas).</p>
        <progress aria-label="Execuções encerradas, incluindo falhas" max={total} value={finished} className="mt-1 h-2 w-full accent-teal-700" />
      </div>}
      <ul className="mt-3 space-y-3">
        {monitored.map((run) => {
          const seconds = elapsedSpecialistSeconds(run, now);
          const pending = isSpecialistPending(run);
          const success = run.status === "needs_review" && run.is_current;
          const tone = run.status === "failed" ? "border-red-200 bg-red-50" : success ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-white";
          return <li key={run.id} className={`rounded-lg border p-3 ${tone}`}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold text-slate-900">{run.instrument_code.toUpperCase()} · aplicação #{run.application_id} · execução #{run.id}</p>
                <p role="status" className="mt-1 text-sm font-medium">{LABELS[run.status] || run.status}</p>
              </div>
              <p aria-live="off" className="text-sm tabular-nums text-slate-700">{run.status === "queued" ? "Espera: " : pending ? "Análise: " : "Duração: "}{formatSpecialistDuration(seconds)}</p>
            </div>
            {pending && <progress aria-label={`${run.instrument_code.toUpperCase()}: ${LABELS[run.status]}`} className="mt-3 h-2 w-full accent-teal-700" />}
            {run.status === "queued" && <p className="mt-2 text-xs text-slate-600">O processamento ainda não começou. O worker local precisa estar ativo na conta correta e conectado ao mesmo banco.</p>}
            {run.status === "queued" && seconds !== null && seconds >= 60 && <p className="mt-2 text-sm text-amber-900">Espera prolongada: confira o worker e o Ollama. Este painel não consegue confirmar se o worker está online.</p>}
            {run.status === "running" && <p className="mt-2 text-xs text-slate-600">O worker iniciou esta execução. A etapa inclui geração e validação; não há percentual nem confirmação contínua de atividade do processo.</p>}
            {run.status === "running" && seconds !== null && seconds >= 300 && <p className="mt-2 text-sm text-amber-900">Execução prolongada. Confira o terminal do worker; o último estado recebido ainda é “Em análise”. Não reenvie repetidamente.</p>}
            {success && <p className="mt-2 text-sm text-emerald-900">Rascunho disponível. Confira o resultado e as evidências antes de aprovar; o laudo não foi alterado.</p>}
            {run.status === "failed" && <p className="mt-2 text-sm text-red-800">{errorMessages[run.error_code] || "A execução terminou com falha."} Código: {run.error_code || "não informado"}. Não haverá repetição automática.</p>}
            {run.status === "stale" && <p className="mt-2 text-sm text-amber-900">Dados ou versão mudaram; esta execução não representa a configuração atual.</p>}
            {!pending && <a href={`#specialist-run-${run.id}`} onClick={() => openRun(run.id)} className="mt-2 inline-block rounded text-sm font-medium text-teal-800 underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4">{success ? "Abrir resultado e evidências" : "Abrir detalhes da execução"}</a>}
          </li>;
        })}
      </ul>
    </section>
  );
}
