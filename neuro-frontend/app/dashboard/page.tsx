"use client";

import React from "react";
import Link from "next/link";
import { PageContainer, PageHeader, SectionCard, StatCard } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
import { AuthUser, getStoredUser } from "@/lib/auth-user";
import { compareEvaluationsByDeadline, getEvaluationDeadlineMeta } from "@/lib/evaluation-deadline";
import { 
  Users, 
  ClipboardList, 
  FlaskConical, 
  FileText, 
  Plus, 
  ChevronRight, 
  Stethoscope,
  Sparkles,
  Loader2,
  Inbox,
  Calendar,
  AlertTriangle,
  Siren,
  CheckCircle2,
} from "lucide-react";

interface Evaluation {
  id: number;
  patient_id: number;
  patient_name: string;
  status: string;
  status_display?: string;
  end_date: string | null;
  created_at: string;
}

const QUICK_ACTIONS = [
  { title: "Novo Paciente", icon: Users, href: "/dashboard/patients/new", color: "text-blue-600", bg: "bg-blue-50" },
  { title: "Aplicar Teste", icon: Stethoscope, href: "/dashboard/tests", color: "text-primary", bg: "bg-primary/10" },
  { title: "Gerar Laudo", icon: FileText, href: "/dashboard/reports", color: "text-amber-600", bg: "bg-amber-50" },
  { title: "IA Clínica", icon: Sparkles, href: "/dashboard/ai", color: "text-purple-600", bg: "bg-purple-50" },
];

function StatusBadge({ children }: { children: string }) {
  const map: Record<string, string> = {
    "init": "text-amber-600 bg-amber-50 border-amber-100",
    "in_progress": "text-primary bg-primary/10 border-primary/20",
    "completed": "text-emerald-600 bg-emerald-50 border-emerald-100",
    "report": "text-indigo-600 bg-indigo-50 border-indigo-100",
  };
  
  const labels: Record<string, string> = {
    "init": "Triagem",
    "in_progress": "Avaliação",
    "completed": "Finalizado",
    "report": "Laudo",
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${map[children] || "bg-slate-50 text-slate-500 border-slate-100"}`}>
      {labels[children] || children}
    </span>
  );
}

export default function DashboardPage() {
  const [user, setUser] = React.useState<AuthUser | null>(null);
  const [evaluations, setEvaluations] = React.useState<Evaluation[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const initDashboard = async () => {
      setUser(getStoredUser());

      try {
        const { api } = await import("@/lib/api");
        // Busca estatisticas e avaliações recentes em paralelo
        const [evalsRes] = await Promise.all([
          api.get<Evaluation[]>("/api/evaluations/"),
          // api.get("/api/dashboard/stats") // Exemplo de endpoint futuro
        ]);

        setEvaluations(Array.isArray(evalsRes) ? evalsRes : []);
      } catch (e) {
        console.error("Erro ao carregar dashboard:", e);
      } finally {
        setLoading(false);
      }
    };

    initDashboard();
  }, []);

  const getGreeting = () => {
    if (!user) return "Bem-vindo(a) de volta.";
    const rawName = user.full_name || user.username || "Profissional";
    const cleanName = rawName.replace(/^(Dr\.|Dra\.|Dr|Dra)\s+/i, "").trim();
    const firstName = cleanName.split(/\s+/)[0];
    const isFemale = user.sex === "F" || (firstName.toLowerCase().endsWith("a") && !["luca", "joshua"].includes(firstName.toLowerCase()));
    return `Bem-vindo(a) de volta, ${isFemale ? "Dra. " : "Dr. "}${firstName}.`;
  };

  const dashboardStats = [
    { title: "Total de Pacientes", value: evaluations.length.toString(), trend: { value: 0, label: "total" }, icon: Users },
    { title: "Avaliações Ativas", value: evaluations.filter(e => e.status !== 'completed').length.toString(), trend: { value: 0, label: "em curso" }, icon: ClipboardList },
    { title: "Laudos Pendentes", value: evaluations.filter(e => e.status === 'report').length.toString(), trend: { value: 0, label: "p/ fazer" }, icon: FileText },
    { title: "Testes Aplicados", value: "...", trend: { value: 0, label: "total" }, icon: FlaskConical },
  ];

  const activeEvaluations = evaluations.filter((evaluation) => !["approved", "archived", "completed"].includes(evaluation.status));
  const scheduledEvaluations = [...activeEvaluations].sort(compareEvaluationsByDeadline);
  const urgentAgenda = scheduledEvaluations.slice(0, 5);

  const deadlineSummary = activeEvaluations.reduce(
    (acc, evaluation) => {
      const meta = getEvaluationDeadlineMeta(evaluation.end_date, evaluation.status);

      if (meta.isOverdue) {
        acc.overdue += 1;
      } else if (meta.label === "Vence hoje") {
        acc.today += 1;
      } else if (meta.label.startsWith("Vence em ")) {
        acc.week += 1;
      } else if (meta.label === "Sem prazo") {
        acc.missing += 1;
      }

      return acc;
    },
    { overdue: 0, today: 0, week: 0, missing: 0 },
  );

  const deadlineStats = [
    {
      title: "Atrasadas",
      value: deadlineSummary.overdue,
      description: "Exigem contato e replanejamento imediato.",
      icon: AlertTriangle,
      className: deadlineSummary.overdue > 0 ? "border-rose-200 bg-rose-50/60" : undefined,
    },
    {
      title: "Vencem Hoje",
      value: deadlineSummary.today,
      description: "Prioridade da agenda clínica de hoje.",
      icon: Siren,
      className: deadlineSummary.today > 0 ? "border-amber-200 bg-amber-50/60" : undefined,
    },
    {
      title: "Próx. 7 Dias",
      value: deadlineSummary.week,
      description: "Casos que já pedem janela de execução.",
      icon: Calendar,
    },
    {
      title: "Sem Prazo",
      value: deadlineSummary.missing,
      description: "Cadastros sem meta de entrega definida.",
      icon: CheckCircle2,
      className: deadlineSummary.missing > 0 ? "border-slate-200 bg-slate-50/80" : undefined,
    },
  ];

  return (
    <PageContainer>
      <PageHeader
        title="Dashboard"
        subtitle={`${getGreeting()} Aqui está o resumo da sua clínica hoje.`}
        actions={
          <div className="flex items-center gap-3">
            <Link href="/dashboard/evaluations/new">
              <Button className="gap-2 shadow-spike font-bold">
                <Plus className="h-4 w-4" />
                Nova Avaliação
              </Button>
            </Link>
          </div>
        }
      />

      {/* Stats Grid */}
      <div className="mb-10 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {dashboardStats.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </div>

      <div className="mb-10 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {deadlineStats.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-8">
          <SectionCard title="Agenda de Prazos" description="Casos mais sensíveis para atrasos e organização da semana.">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                <Loader2 className="h-8 w-8 animate-spin mb-4" />
                <p className="text-sm font-medium">Carregando seus dados clínicos...</p>
              </div>
            ) : urgentAgenda.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-100">
                      <th className="pb-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">CÓDIGO</th>
                      <th className="pb-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">PACIENTE</th>
                      <th className="pb-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">STATUS</th>
                      <th className="pb-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">PRAZO</th>
                      <th className="pb-4"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {urgentAgenda.map((evaluation) => {
                      const deadlineMeta = getEvaluationDeadlineMeta(evaluation.end_date, evaluation.status);

                      return (
                        <tr key={evaluation.id} className="group transition-colors hover:bg-slate-50/50">
                          <td className="py-4 text-sm font-bold text-slate-900">#{evaluation.id.toString().padStart(4, "0")}</td>
                          <td className="py-4">
                            <div className="flex items-center gap-3">
                              <Link
                                href={`/dashboard/patients/${evaluation.patient_id}`}
                                className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/5 text-[10px] font-black text-primary transition-colors hover:bg-primary/10"
                              >
                                {evaluation.patient_name?.charAt(0) || "P"}
                              </Link>
                              <Link
                                href={`/dashboard/patients/${evaluation.patient_id}`}
                                className="text-sm font-bold text-slate-700 transition-colors hover:text-primary"
                              >
                                {evaluation.patient_name}
                              </Link>
                            </div>
                          </td>
                          <td className="py-4">
                            <StatusBadge>{evaluation.status_display || evaluation.status}</StatusBadge>
                          </td>
                          <td className="py-4">
                            <div className="flex flex-col gap-1">
                              <span className={`inline-flex w-fit items-center rounded-full border px-2.5 py-1 text-[10px] font-black uppercase tracking-widest ${deadlineMeta.badgeClassName}`}>
                                {deadlineMeta.label}
                              </span>
                              <span className="text-xs font-medium text-slate-400">{deadlineMeta.helperText}</span>
                            </div>
                          </td>
                          <td className="py-4 text-right">
                            <Link href={`/dashboard/evaluations/${evaluation.id}`}>
                              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 opacity-0 transition-opacity group-hover:opacity-100">
                                <ChevronRight className="h-4 w-4 text-primary" />
                              </Button>
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                <div className="h-16 w-16 rounded-full bg-slate-50 flex items-center justify-center mb-4">
                   <Inbox className="h-8 w-8 text-slate-200" />
                </div>
                <p className="text-sm font-bold text-slate-900 mb-1">Nenhum prazo ativo encontrado</p>
                <p className="text-xs font-medium text-slate-500 mb-6">Defina metas de entrega para organizar a agenda clínica aqui.</p>
                <Link href="/dashboard/evaluations/new">
                   <Button variant="outline" size="sm" className="font-bold gap-2">
                      <Plus className="h-4 w-4" />
                      Criar Avaliação
                    </Button>
                 </Link>
               </div>
             )}
           </SectionCard>
        </div>

        <div className="space-y-8">
          <SectionCard title="Ações Rápidas">
            <div className="grid grid-cols-2 gap-4">
              {QUICK_ACTIONS.map((action) => (
                <Link key={action.title} href={action.href}>
                  <button className="flex h-24 w-full flex-col items-center justify-center gap-2 rounded-xl border border-slate-100 bg-white shadow-sm transition-all hover:border-primary/20 hover:shadow-spike group">
                    <div className={`p-2 rounded-lg ${action.bg} ${action.color} group-hover:scale-110 transition-transform`}>
                      <action.icon className="h-5 w-5" />
                    </div>
                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">{action.title}</span>
                  </button>
                </Link>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    </PageContainer>
  );
}
