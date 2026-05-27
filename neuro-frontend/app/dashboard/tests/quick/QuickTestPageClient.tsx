"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { PageContainer, PageHeader } from "@/components/ui/page";
import { api } from "@/lib/api";
import type { Patient, Evaluation } from "@/types/shared";
import { ArrowLeft, FileText, FlaskConical, Loader2, UserRound } from "lucide-react";

interface Instrument {
  id: number;
  code: string;
  name: string;
  category: string;
  description?: string;
  is_active: boolean;
}

interface QuickPatientForm {
  full_name: string;
  birth_date: string;
  sex: string;
  schooling: string;
  school_name: string;
  grade_year: string;
  mother_name: string;
  father_name: string;
  phone: string;
  email: string;
  city: string;
  state: string;
  notes: string;
  responsible_name: string;
  responsible_phone: string;
}

const INITIAL_FORM: QuickPatientForm = {
  full_name: "",
  birth_date: "",
  sex: "",
  schooling: "",
  school_name: "",
  grade_year: "",
  mother_name: "",
  father_name: "",
  phone: "",
  email: "",
  city: "",
  state: "",
  notes: "",
  responsible_name: "",
  responsible_phone: "",
};

const SCHOOLING_OPTIONS = [
  { value: "preschool", label: "Ensino Pré-escolar" },
  { value: "elementary", label: "Ensino Fundamental" },
  { value: "middle", label: "Ensino Médio" },
  { value: "higher_incomplete", label: "Ensino Superior Incompleto" },
  { value: "higher", label: "Ensino Superior" },
];

function normalizeTestCode(value: string) {
  return String(value || "").trim().toLowerCase().replace(/-/g, "_");
}

function toTestPath(code: string) {
  return normalizeTestCode(code).replace(/_/g, "-");
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

interface QuickTestPageClientProps {
  initialTest?: string;
}

export default function QuickTestPageClient({ initialTest = "" }: QuickTestPageClientProps) {
  const router = useRouter();
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [selectedCode, setSelectedCode] = useState("");
  const [form, setForm] = useState<QuickPatientForm>(INITIAL_FORM);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadInstruments() {
      try {
        const data = await api.get<Instrument[]>("/api/tests/instruments");
        const active = data.filter((item) => item.is_active);
        setInstruments(active);

        const requested = normalizeTestCode(initialTest);
        const matched = active.find((item) => normalizeTestCode(item.code) === requested);
        setSelectedCode(matched?.code || active[0]?.code || "");
      } catch (err: any) {
        setError(err?.message || "Nao foi possivel carregar os instrumentos.");
      } finally {
        setLoading(false);
      }
    }

    loadInstruments();
  }, [initialTest]);

  useEffect(() => {
    if (!selectedCode) return;
    const nextTest = toTestPath(selectedCode);
    window.history.replaceState({}, "", `/dashboard/tests/quick?test=${nextTest}`);
  }, [selectedCode]);

  const selectedInstrument = useMemo(
    () => instruments.find((item) => item.code === selectedCode) || null,
    [instruments, selectedCode]
  );

  function updateField<K extends keyof QuickPatientForm>(field: K, value: QuickPatientForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedInstrument) {
      setError("Selecione um teste para continuar.");
      return;
    }

    if (!form.full_name || !form.birth_date || !form.sex || !form.schooling) {
      setError("Preencha nome, data de nascimento, sexo e escolaridade.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const patient = await api.post<Patient>("/api/patients/", {
        full_name: form.full_name,
        birth_date: form.birth_date,
        sex: form.sex,
        schooling: form.schooling,
        school_name: form.school_name || "Nao informado",
        grade_year: form.grade_year || "",
        mother_name: form.mother_name || "",
        father_name: form.father_name || "",
        phone: form.phone || "",
        email: form.email || undefined,
        city: form.city || "",
        state: form.state || "",
        notes: form.notes || "",
        responsible_name: form.responsible_name || "",
        responsible_phone: form.responsible_phone || "",
      });

      const evaluation = await api.post<Evaluation>("/api/evaluations/", {
        patient_id: patient.id,
        title: `Teste rapido - ${selectedInstrument.name}`,
        referral_reason: "Aplicacao avulsa pelo fluxo rapido de testes.",
        evaluation_purpose: `Aplicacao rapida do instrumento ${selectedInstrument.name}.`,
        clinical_hypothesis: "",
        start_date: todayIso(),
        status: "draft",
        priority: "medium",
        general_notes: `Criada automaticamente pelo fluxo rapido para o instrumento ${selectedInstrument.code}.`,
      });

      router.push(`/dashboard/tests/${toTestPath(selectedInstrument.code)}?evaluation_id=${evaluation.id}&quick=1`);
    } catch (err: any) {
      setError(err?.message || "Nao foi possivel iniciar o teste rapido.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Teste Rapido"
        subtitle="Escolha o instrumento, preencha os dados do paciente e abra o formulario do teste sem montar a avaliacao manualmente."
        actions={
          <Link href="/dashboard/tests">
            <Button variant="outline" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Voltar para testes
            </Button>
          </Link>
        }
      />

      {error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      {loading ? (
        <div className="flex h-[420px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
          <aside className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3 rounded-2xl bg-indigo-50 p-4 text-indigo-900">
              <FlaskConical className="h-5 w-5" />
              <div>
                <div className="text-sm font-semibold">Fluxo rapido</div>
                <div className="text-xs text-indigo-700">Cria paciente e avaliacao tecnica em segundo plano.</div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
              <div className="font-semibold text-slate-900">Saida em PDF</div>
              <p className="mt-2">
                Apos concluir o teste, a tela de resultado exibira a analise e o botao <span className="font-semibold">Imprimir / PDF</span> para gerar o documento do instrumento.
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-900">Teste</label>
              <select
                value={selectedCode}
                onChange={(event) => setSelectedCode(event.target.value)}
                className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-700 outline-none focus:border-indigo-400"
              >
                {instruments.map((instrument) => (
                  <option key={instrument.id} value={instrument.code}>
                    {instrument.name}
                  </option>
                ))}
              </select>
            </div>

            {selectedInstrument && (
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">Instrumento selecionado</div>
                <div className="mt-2 text-base font-semibold text-slate-900">{selectedInstrument.name}</div>
                <div className="mt-1 text-sm text-slate-500">{selectedInstrument.description || "Sem descricao tecnica cadastrada."}</div>
              </div>
            )}
          </aside>

          <form onSubmit={handleSubmit} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                <UserRound className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Dados do paciente</h2>
                <p className="text-sm text-slate-500">Esses dados serao usados para criar um cadastro tecnico rapido e abrir o teste escolhido.</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Nome completo</span>
                <input value={form.full_name} onChange={(event) => updateField("full_name", event.target.value)} className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Data de nascimento</span>
                <input type="date" value={form.birth_date} onChange={(event) => updateField("birth_date", event.target.value)} className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Sexo</span>
                <select value={form.sex} onChange={(event) => updateField("sex", event.target.value)} className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400">
                  <option value="">Selecione</option>
                  <option value="F">Feminino</option>
                  <option value="M">Masculino</option>
                  <option value="O">Outro</option>
                </select>
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Escolaridade</span>
                <select value={form.schooling} onChange={(event) => updateField("schooling", event.target.value)} className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400">
                  <option value="">Selecione</option>
                  {SCHOOLING_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Escola / instituicao</span>
                <input value={form.school_name} onChange={(event) => updateField("school_name", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Serie / ano</span>
                <input value={form.grade_year} onChange={(event) => updateField("grade_year", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Nome do responsavel</span>
                <input value={form.responsible_name} onChange={(event) => updateField("responsible_name", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Telefone do responsavel</span>
                <input value={form.responsible_phone} onChange={(event) => updateField("responsible_phone", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Telefone</span>
                <input value={form.phone} onChange={(event) => updateField("phone", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">E-mail</span>
                <input type="email" value={form.email} onChange={(event) => updateField("email", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Cidade</span>
                <input value={form.city} onChange={(event) => updateField("city", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>

              <label className="block text-sm">
                <span className="mb-2 block font-medium text-slate-700">Estado</span>
                <input value={form.state} onChange={(event) => updateField("state", event.target.value)} placeholder="Opcional" className="h-12 w-full rounded-xl border border-slate-200 px-4 outline-none focus:border-indigo-400" />
              </label>
            </div>

            <label className="mt-4 block text-sm">
              <span className="mb-2 block font-medium text-slate-700">Observacoes</span>
              <textarea value={form.notes} onChange={(event) => updateField("notes", event.target.value)} rows={4} className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-indigo-400" />
            </label>

            <div className="mt-6 flex flex-col gap-3 border-t border-slate-100 pt-6 md:flex-row md:items-center md:justify-between">
              <div className="text-sm text-slate-500">
                O sistema vai criar uma avaliacao tecnica rapida e abrir o formulario do instrumento. Ao terminar, use <span className="font-semibold text-slate-700">Imprimir / PDF</span> na tela de resultado.
              </div>
              <Button type="submit" className="gap-2" disabled={submitting || !selectedInstrument}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                Iniciar teste rapido
              </Button>
            </div>
          </form>
        </div>
      )}
    </PageContainer>
  );
}
