"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, ArrowLeft, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

const SOCIAL_ITEMS = [
  [1, "Usa o tempo livre em casa de maneira aceitável."],
  [2, "Em casa, fala em tom de voz apropriado."],
  [3, "Junta-se a grupo de atividade sem ser mandado."],
  [4, "Apresenta-se a novas pessoas sem ser mandado."],
  [5, "Pede informação ou assistência a vendedores nas lojas."],
  [6, "Elogia familiares pelas suas realizações."],
  [7, "Evita situações que possam trazer problemas."],
  [8, "Guarda seus brinquedos ou outras coisas de casa."],
  [9, "Aceita críticas."],
  [10, "Atende ao telefone de forma adequada."],
  [11, "Faz as tarefas domésticas que são estabelecidas como sua obrigação sem precisar ser lembrado."],
  [12, "Tenta fazer as tarefas domésticas antes de pedir sua ajuda."],
  [13, "Controla sua irritação quando discute com os outros."],
  [14, "Inicia uma conversação em vez de ficar esperando que outros o façam."],
  [15, "Finaliza discordância calmamente com você."],
  [16, "Controla a irritação em situações de conflito com você."],
  [17, "Faz elogios para amigos e outras crianças na família."],
  [18, "Completa as tarefas domésticas em um tempo razoável."],
  [19, "Pede permissão para usar coisas de outros da família."],
  [20, "Pede permissão antes de sair de casa."],
  [21, "Usa apropriadamente o tempo enquanto espera sua ajuda para tarefa escolar ou outra tarefa."],
  [22, "Coopera com membros da família sem ser solicitado."],
  [23, "Aceita elogios ou cumprimentos de amigos."],
] as const;

const BEHAVIOR_ITEMS = [
  [24, "Briga com os outros."],
  [25, "Mostra-se triste ou deprimido(a)."],
  [26, "Parece solitário(a)."],
  [27, "Tem baixa autoestima."],
  [28, "Ameaça ou intimida os outros."],
  [29, "Perturba as atividades em andamento."],
  [30, "Demonstra ansiedade quanto a estar com grupos de amigos."],
  [31, "Discute com os outros."],
  [32, "É irrequieto e se mexe excessivamente."],
  [33, "Desobedece regras ou pedidos."],
  [34, "Retruca quando os adultos lhe corrigem."],
  [35, "Age impulsivamente."],
  [36, "Não ouve o que os outros dizem."],
  [37, "Desconcentra-se facilmente."],
  [38, "Tem acessos de birra."],
] as const;

const GENDERS = [
  { value: "F", label: "Feminino" },
  { value: "M", label: "Masculino" },
] as const;

function isAnswered(values: Record<string, string>, item: number) {
  return values[String(item)] !== undefined && values[String(item)] !== "";
}

function ChoiceGroup({ value, onChange, labels }: { value: string; onChange: (value: string) => void; labels: string[] }) {
  function applyChoice(option: number) {
    const nextValue = String(option);
    onChange(value === nextValue ? "" : nextValue);
  }

  return (
    <div className="grid grid-cols-3 gap-1 select-none">
      {[0, 1, 2].map((option) => (
        <button
          key={option}
          type="button"
          title={labels[option]}
          onPointerDown={(event) => {
            event.preventDefault();
            applyChoice(option);
          }}
          onPointerEnter={(event) => {
            if (event.buttons === 1) onChange(String(option));
          }}
          className={`h-10 rounded-lg border text-sm font-black transition ${value === String(option) ? "border-emerald-700 bg-emerald-600 text-white shadow-sm" : "border-slate-200 bg-white text-slate-600 hover:border-emerald-400 hover:bg-emerald-50"}`}
        >
          {option}
        </button>
      ))}
    </div>
  );
}

function SSRSPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const evaluationId = searchParams.get("evaluation_id");
  const applicationId = searchParams.get("application_id");
  const isEditMode = searchParams.get("edit") === "true";

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [patientName, setPatientName] = useState("");
  const [respondentName, setRespondentName] = useState("");
  const [gender, setGender] = useState("F");
  const [frequency, setFrequency] = useState<Record<string, string>>({});
  const [importance, setImportance] = useState<Record<string, string>>({});

  const allItems = useMemo(() => [...SOCIAL_ITEMS, ...BEHAVIOR_ITEMS], []);
  const answeredFrequency = allItems.filter(([item]) => isAnswered(frequency, item)).length;
  const answeredImportance = SOCIAL_ITEMS.filter(([item]) => isAnswered(importance, item)).length;

  useEffect(() => {
    async function loadData() {
      try {
        if (applicationId) {
          const result = await api.get<any>(`/api/tests/applications/${applicationId}`);
          if (result?.patient_name) setPatientName(result.patient_name);
          if (result?.is_validated && !isEditMode) {
            const evalQuery = result.evaluation_id ? `?evaluation_id=${result.evaluation_id}` : "";
            router.replace(`/dashboard/tests/ssrs/${applicationId}/result${evalQuery}`);
            return;
          }
          const raw = result?.raw_payload || {};
          if (raw.gender) setGender(raw.gender);
          if (raw.respondent_name) setRespondentName(raw.respondent_name);
          if (raw.responses) setFrequency(Object.fromEntries(Object.entries(raw.responses).map(([key, value]) => [key, String(value)])));
          if (raw.importance) setImportance(Object.fromEntries(Object.entries(raw.importance).map(([key, value]) => [key, String(value)])));
        }

        if (evaluationId) {
          const evaluation = await api.get<any>(`/api/evaluations/${evaluationId}`);
          if (evaluation?.patient_name) setPatientName(evaluation.patient_name);
          if (evaluation?.patient_sex === "M" || evaluation?.patient_sex === "F") setGender(evaluation.patient_sex);
        }
      } catch (err) {
        console.error("Erro ao carregar SSRS:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [applicationId, evaluationId, isEditMode, router]);

  function setFrequencyValue(item: number, value: string) {
    setFrequency((prev) => ({ ...prev, [String(item)]: value }));
  }

  function setImportanceValue(item: number, value: string) {
    setImportance((prev) => ({ ...prev, [String(item)]: value }));
  }

  function clearForm() {
    if (!confirm("Deseja limpar todas as respostas do SSRS?")) return;
    setFrequency({});
    setImportance({});
    setError("");
  }

  async function handleSave() {
    if (!evaluationId) {
      setError("ID da avaliação não encontrado. Acesse o SSRS a partir de uma avaliação.");
      return;
    }

    const missingFrequency = allItems.map(([item]) => item).filter((item) => !isAnswered(frequency, item));
    const missingImportance = SOCIAL_ITEMS.map(([item]) => item).filter((item) => !isAnswered(importance, item));
    if (missingFrequency.length > 0 || missingImportance.length > 0) {
      const parts = [];
      if (missingFrequency.length) parts.push(`frequência: ${missingFrequency.slice(0, 12).join(", ")}${missingFrequency.length > 12 ? "..." : ""}`);
      if (missingImportance.length) parts.push(`importância: ${missingImportance.slice(0, 12).join(", ")}${missingImportance.length > 12 ? "..." : ""}`);
      setError(`Preencha todos os campos antes de salvar. Pendentes em ${parts.join("; ")}.`);
      return;
    }

    const responsesPayload = Object.fromEntries(allItems.map(([item]) => [String(item), Number(frequency[String(item)])]));
    const importancePayload = Object.fromEntries(SOCIAL_ITEMS.map(([item]) => [String(item), Number(importance[String(item)])]));

    setSaving(true);
    setError("");
    try {
      const result = await api.post<{ application_id: number }>("/api/tests/ssrs/submit", {
        evaluation_id: Number(evaluationId),
        informant: "pais",
        gender,
        respondent_name: respondentName,
        responses: responsesPayload,
        importance: importancePayload,
      });
      router.push(`/dashboard/tests/ssrs/${result.application_id}/result?evaluation_id=${evaluationId}`);
    } catch (err: any) {
      setError(err?.message || "Erro ao salvar SSRS.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="py-16 text-center text-slate-500">Carregando SSRS...</div>;

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-2 sm:px-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()} className="rounded-full border border-slate-200 bg-white shadow-sm">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">SSRS - Pais</h2>
          <p className="text-sm text-slate-500">{patientName ? `Paciente: ${patientName}` : "Correção de Habilidades Sociais e Problemas de Comportamento"}</p>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
          {error}
        </div>
      )}

      <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>Dados da aplicação</CardTitle>
          <CardDescription>Modelo para pais: frequência em todos os 38 itens e importância apenas nos 23 itens de habilidades sociais.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm font-medium text-slate-700">
            Sexo normativo
            <select value={gender} onChange={(event) => setGender(event.target.value)} className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm">
              {GENDERS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
          <label className="space-y-2 text-sm font-medium text-slate-700 md:col-span-2">
            Nome do respondente
            <Input value={respondentName} onChange={(event) => setRespondentName(event.target.value)} placeholder="Opcional" className="h-11 rounded-xl" />
          </label>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>Habilidades Sociais</CardTitle>
          <CardDescription>Frequência: 0 nunca, 1 algumas vezes, 2 muito frequente. Importância: 0 não importante, 1 importante, 2 indispensável.</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-widest text-slate-400">
                <th className="w-[46%] py-3 pr-4 text-left">Item</th>
                <th className="w-[27%] py-3 px-2 text-center">Frequência</th>
                <th className="w-[27%] py-3 pl-2 text-center">Importância</th>
              </tr>
            </thead>
            <tbody>
              {SOCIAL_ITEMS.map(([item, text]) => (
                <tr key={item} className="border-b border-slate-100 align-top">
                  <td className="py-3 pr-4 text-slate-800"><span className="font-black text-slate-950">{item}.</span> {text}</td>
                  <td className="py-2 px-2"><ChoiceGroup value={frequency[String(item)] || ""} onChange={(value) => setFrequencyValue(item, value)} labels={["Nunca", "Algumas vezes", "Muito frequente"]} /></td>
                  <td className="py-2 pl-2"><ChoiceGroup value={importance[String(item)] || ""} onChange={(value) => setImportanceValue(item, value)} labels={["Não importante", "Importante", "Indispensável"]} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Card className="rounded-2xl border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>Problemas de Comportamento</CardTitle>
          <CardDescription>Preencha somente a frequência dos itens 24 a 38.</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-widest text-slate-400">
                <th className="w-[64%] py-3 pr-4 text-left">Item</th>
                <th className="w-[36%] py-3 text-center">Frequência</th>
              </tr>
            </thead>
            <tbody>
              {BEHAVIOR_ITEMS.map(([item, text]) => (
                <tr key={item} className="border-b border-slate-100 align-top">
                  <td className="py-3 pr-4 text-slate-800"><span className="font-black text-slate-950">{item}.</span> {text}</td>
                  <td className="py-2"><ChoiceGroup value={frequency[String(item)] || ""} onChange={(value) => setFrequencyValue(item, value)} labels={["Nunca", "Algumas vezes", "Muito frequente"]} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="sticky bottom-4 z-10 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-xl backdrop-blur">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm font-medium text-slate-600">Frequência: {answeredFrequency}/38 · Importância: {answeredImportance}/23</p>
          <div className="flex gap-3">
            <Button type="button" variant="outline" onClick={clearForm} disabled={saving} className="rounded-xl">Limpar</Button>
            <Button type="button" onClick={handleSave} disabled={saving} className="rounded-xl gap-2">
              <Save className="h-4 w-4" />
              {saving ? "Salvando..." : "Salvar SSRS"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="py-16 text-center text-slate-500">Carregando SSRS...</div>}>
      <SSRSPageContent />
    </Suspense>
  );
}
