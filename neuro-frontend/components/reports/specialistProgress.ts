export type SpecialistProgressRun = {
  id: number;
  application_id: number;
  instrument_code: string;
  status: string;
  is_current: boolean;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  error_code: string;
};

export function isSpecialistPending(run: SpecialistProgressRun) {
  return run.is_current && (run.status === "queued" || run.status === "running");
}

export function shouldPollSpecialists(runs: SpecialistProgressRun[], requestedIds: number[]) {
  return runs.some(isSpecialistPending) || requestedIds.some((id) => !runs.some((run) => run.id === id));
}

export function monitoredSpecialists(runs: SpecialistProgressRun[], requestedIds: number[]) {
  if (requestedIds.length > 0) return runs.filter((run) => requestedIds.includes(run.id));
  const latest = new Map<number, SpecialistProgressRun>();
  for (const run of runs) {
    if (!latest.has(run.application_id) || latest.get(run.application_id)!.id < run.id) {
      latest.set(run.application_id, run);
    }
  }
  return Array.from(latest.values()).sort((a, b) => b.id - a.id);
}

export function elapsedSpecialistSeconds(run: SpecialistProgressRun, now: number) {
  const start = Date.parse(run.status === "queued" ? run.created_at : (run.started_at || run.created_at));
  const end = isSpecialistPending(run) ? now : Date.parse(run.finished_at || "");
  if (!Number.isFinite(start) || !Number.isFinite(end)) return null;
  return Math.max(0, Math.floor((end - start) / 1000));
}

export function formatSpecialistDuration(seconds: number | null) {
  if (seconds === null) return "tempo indisponível";
  const safe = Math.max(0, Math.floor(seconds));
  if (safe < 60) return `${safe}s`;
  const minutes = Math.floor(safe / 60);
  if (minutes < 60) return `${minutes}min ${String(safe % 60).padStart(2, "0")}s`;
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, "0")}min`;
}

type SchedulePoll = (callback: () => Promise<void>, delay: number) => () => void;

export function startSpecialistPolling(refresh: () => Promise<void>, schedule: SchedulePoll, intervalMs = 5000) {
  let stopped = false;
  let cancel = () => {};
  const enqueue = () => {
    cancel = schedule(async () => {
      if (stopped) return;
      try {
        await refresh();
      } catch {
        // A consulta exibe seus próprios erros; uma falha não encerra o acompanhamento.
      } finally {
        if (!stopped) enqueue();
      }
    }, intervalMs);
  };
  enqueue();
  return () => { stopped = true; cancel(); };
}
