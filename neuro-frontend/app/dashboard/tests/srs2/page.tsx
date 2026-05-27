"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, ArrowLeft, Save, User } from "lucide-react";
import { api } from "@/lib/api";

type ItemData = {
  item: number;
  fator: string;
  pergunta: string;
};

type FormOption = {
  value: string;
  label: string;
};

function SRS2PageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [allItems, setAllItems] = useState<Record<string, ItemData[]>>({});
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [form, setForm] = useState<string>("idade_escolar");
  const items: ItemData[] = allItems[form] || [];
  const [gender, setGender] = useState<string>("M");
  const [age, setAge] = useState<number>(10);
  const [respondentName, setRespondentName] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showValidationErrors, setShowValidationErrors] = useState(false);
  const [patientName, setPatientName] = useState<string>("");

  const evaluationId = searchParams.get("evaluation_id");
  const applicationId = searchParams.get("application_id");
  const isEditMode = searchParams.get("edit") === "true";

  useEffect(() => {
    async function loadData() {
      if (!evaluationId && applicationId) {
        try {
          const result = await api.get<any>(`/api/tests/applications/${applicationId}`);
          if (result && result.evaluation_id) {
            const newEvalId = result.evaluation_id.toString();
            router.replace(`/dashboard/tests/srs2?application_id=${applicationId}&evaluation_id=${newEvalId}&edit=true`);
            return;
          }
        } catch (err) {
          console.error("Error loading:", err);
        }
      }

      try {
        if (applicationId && !isEditMode) {
          const result = await api.get<any>(`/api/tests/applications/${applicationId}`);
          if (result && result.is_validated) {
            const resultEvaluationId = result.evaluation_id ? `?evaluation_id=${result.evaluation_id}` : "";
            router.push(`/dashboard/tests/srs2/${applicationId}/result${resultEvaluationId}`);
            return;
          }
          if (result && result.raw_payload) {
            const raw = result.raw_payload;
            if (raw.form) setForm(raw.form);
            if (raw.gender) setGender(raw.gender);
            if (raw.age) setAge(raw.age);
            if (raw.respondent_name) setRespondentName(raw.respondent_name);
            const existingScores: Record<string, string> = {};
            for (let i = 1; i <= 65; i++) {
              const key = String(i);
              if (raw.responses && raw.responses[key] !== undefined) {
                existingScores[key] = String(raw.responses[key]);
              }
            }
            setResponses(existingScores);
          }
        }

        const itemsData = await api.get<any>("/api/tests/srs2/items");
        if (itemsData) setAllItems(itemsData);
      } catch (err) {
        console.error("Error loading:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [applicationId, isEditMode, router, evaluationId]);

  useEffect(() => {
    if (!loading && evaluationId) {
      (async () => {
        try {
          const evalData = await api.get<any>(`/api/evaluations/${evaluationId}`);
          if (evalData?.patient_birth_date) {
            const birthDate = new Date(evalData.patient_birth_date);
            const today = new Date();
            let patientAge = today.getFullYear() - birthDate.getFullYear();
            const monthDiff = today.getMonth() - birthDate.getMonth();
            if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
              patientAge--;
            }
            setAge(patientAge);

            if (patientAge <= 5) {
              setForm("pre_escola");
            } else if (patientAge <= 18) {
              setForm("idade_escolar");
            } else {
              setForm("adulto_autorrelato");
            }
          }
          if (evalData?.patient_sex) {
            setGender(evalData.patient_sex);
          }
          if (evalData?.patient_name) {
            setPatientName(evalData.patient_name);
          }
        } catch (err) {
          console.error("Error getting patient age:", err);
        }
      })();
    }
  }, [loading, evaluationId]);

  const clearForm = () => {
    if (!confirm("Deseja realmente limpar todos os campos do formulário?")) {
      return;
    }

    setResponses({});
    setRespondentName("");
    setError(null);
    setShowValidationErrors(false);
  };

  const missingItems: number[] = [];
  for (let i = 1; i <= 65; i++) {
    const val = parseInt(responses[String(i)]);
    if (!(val >= 1 && val <= 4)) {
      missingItems.push(i);
    }
  }
  const answeredCount = 65 - missingItems.length;
  const hasValidationErrors = showValidationErrors && missingItems.length > 0;

  const handleSave = async () => {
    if (!evaluationId) {
      setError("ID da avaliação não encontrado. Acesse este teste a partir de uma avaliação.");
      return;
    }
    setError(null);
    
    const responsesPayload: Record<string, number> = {};
    for (let i = 1; i <= 65; i++) {
      const val = parseInt(responses[String(i)]);
      if (val >= 1 && val <= 4) {
        responsesPayload[String(i)] = val;
      }
    }

    if (missingItems.length > 0) {
      setShowValidationErrors(true);
      requestAnimationFrame(() => {
        const firstMissingInput = document.querySelector(`input[name="item_${missingItems[0] - 1}"]`) as HTMLInputElement | null;
        firstMissingInput?.focus();
        firstMissingInput?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      return;
    }
    setShowValidationErrors(false);
    setSaving(true);
    
    try {
      const result = await api.post<{ application_id: number }>("/api/tests/srs2/submit", {
        evaluation_id: parseInt(evaluationId),
        form,
        gender,
        age,
        respondent_name: respondentName,
        responses: responsesPayload,
      });
      router.push(`/dashboard/tests/srs2/${result.application_id}/result?evaluation_id=${evaluationId}`);
    } catch (err: any) {
      console.error("Erro ao salvar:", err);
      setError("Erro ao salvar: " + (err?.message || "Tente novamente"));
    } finally {
      setSaving(false);
    }
  };

  const formOptions: FormOption[] = [
    { value: "pre_escola", label: "Pré-Escola (4-5 anos)" },
    { value: "idade_escolar", label: "Idade Escolar (6-18 anos)" },
    { value: "adulto_autorrelato", label: "Adulto Autorrelato (>18 anos)" },
    { value: "adulto_heterorrelato", label: "Adulto Heterorrelato (>18 anos)" },
  ];

  const filteredFormOptions = formOptions.filter((opt) => {
    if (age <= 5) return opt.value === "pre_escola";
    if (age <= 18) return opt.value === "idade_escolar";
    return opt.value.startsWith("adulto");
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()} className="rounded-full">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">SRS-2</h2>
          {patientName && <p className="text-sm text-slate-500">Paciente: {patientName}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2 rounded-2xl border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>Itens do instrumento</CardTitle>
            <CardDescription>Marque a frequência para cada item.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(hasValidationErrors || error) && (
              <div
                role="alert"
                className={`rounded-2xl border p-4 shadow-sm ${
                  hasValidationErrors
                    ? "border-rose-200 bg-rose-50 text-rose-900"
                    : "border-amber-200 bg-amber-50 text-amber-900"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 rounded-full p-2 ${hasValidationErrors ? "bg-rose-100" : "bg-amber-100"}`}>
                    <AlertCircle className="h-5 w-5" />
                  </div>
                  <div className="space-y-1">
                    <p className="font-semibold">
                      {hasValidationErrors ? `Faltam ${missingItems.length} item(ns) para concluir o SRS-2` : "Não foi possível salvar"}
                    </p>
                    <p className="text-sm">
                      {hasValidationErrors
                        ? `Respondidos: ${answeredCount}/65. Os campos pendentes foram destacados em vermelho para facilitar a revisão.`
                        : error}
                    </p>
                    {hasValidationErrors && (
                      <p className="text-sm font-medium">
                        Itens pendentes: {missingItems.slice(0, 12).join(", ")}{missingItems.length > 12 ? "..." : ""}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-600">
              <p className="font-medium mb-2">Escala de frequência:</p>
              <div className="grid grid-cols-4 gap-2">
                <span>1 = Nenhuma</span>
                <span>2 = Um pouco</span>
                <span>3 = Muito</span>
                <span>4 = Quase sempre</span>
              </div>
            </div>

            <div className="border rounded-xl overflow-hidden">
              <div className="grid grid-cols-[60px_1fr_80px] bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700">
                <div>Item</div>
                <div>Descrição</div>
                <div className="text-center">Resp.</div>
              </div>
              <div className="max-h-[500px] overflow-y-auto">
                {items.map((item, idx) => {
                  const isMissing = hasValidationErrors && missingItems.includes(item.item);

                  return (
                    <div
                      key={idx}
                      className={`grid grid-cols-[60px_1fr_80px] items-center px-4 py-3 border-t transition-colors ${
                        isMissing
                          ? "border-l-4 border-l-rose-500 border-t-rose-100 bg-rose-50"
                          : idx % 2 === 0
                            ? "bg-white"
                            : "bg-slate-50/50"
                      }`}
                    >
                      <div className={`text-sm font-medium ${isMissing ? "text-rose-900" : "text-slate-900"}`}>
                        {String(item.item).padStart(2, "0")}
                      </div>
                      <div className={`text-sm pr-4 ${isMissing ? "text-rose-950" : "text-slate-700"}`}>
                        {item.pergunta}
                        {isMissing && <span className="ml-2 text-xs font-semibold text-rose-700">Não respondido</span>}
                      </div>
                      <div className="flex justify-center">
                        <Input
                          type="text"
                          inputMode="numeric"
                          maxLength={1}
                          aria-invalid={isMissing}
                          aria-label={`Resposta do item ${item.item}`}
                          className={`h-8 w-12 rounded-lg text-center ${
                            isMissing
                              ? "border-rose-500 bg-white text-rose-950 shadow-sm ring-2 ring-rose-100 placeholder:text-rose-300 focus-visible:ring-rose-500"
                              : ""
                          }`}
                          value={responses[String(item.item)] || ""}
                          onChange={(e) => {
                            const val = e.target.value;
                            if (val === "" || ["1", "2", "3", "4"].includes(val)) {
                              setResponses({ ...responses, [String(item.item)]: val });
                            }
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && idx < items.length - 1) {
                              const nextInput = document.querySelector(`input[name="item_${idx + 1}"]`) as HTMLInputElement;
                              if (nextInput) nextInput.focus();
                            }
                          }}
                          placeholder="1-4"
                          name={`item_${idx}`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex gap-2">
              <Button className="rounded-xl gap-2" onClick={handleSave} disabled={saving}>
                <Save className="h-4 w-4" />
                Salvar aplicação
              </Button>
              <Button
                variant="outline"
                className="rounded-xl text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                onClick={clearForm}
                disabled={saving}
              >
                Limpar Campos
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>Informações do teste</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-slate-600">
            <div>
              <label className="font-medium text-slate-900">Formulário</label>
              <select 
                value={form} 
                onChange={(e) => setForm(e.target.value)} 
                disabled={filteredFormOptions.length === 1}
                className={`w-full mt-1 p-2 border rounded-lg ${filteredFormOptions.length === 1 ? "bg-slate-100 cursor-not-allowed text-slate-500" : ""}`}
              >
                {filteredFormOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-medium text-slate-900">Sexo</label>
              <select 
                value={gender} 
                disabled
                className="w-full mt-1 p-2 border rounded-lg bg-slate-100 cursor-not-allowed text-slate-500"
              >
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
              </select>
            </div>
            <div>
              <label className="font-medium text-slate-900">Idade</label>
              <Input 
                type="number" 
                value={age} 
                readOnly
                className="mt-1 bg-slate-100 text-slate-500 cursor-not-allowed" 
              />
            </div>
            {(form === "adulto_autorrelato" || form === "adulto_heterorrelato") && (
              <div>
                <label className="font-medium text-slate-900 flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Respondedor
                </label>
                <Input 
                  value={respondentName} 
                  onChange={(e) => setRespondentName(e.target.value)} 
                  className="mt-1" 
                  placeholder="Nome do respondedor"
                />
              </div>
            )}
            <div className="pt-4 border-t">
              <p className="font-medium text-slate-900">SRS-2</p>
              <p>Social Responsiveness Scale - 2ª Edição</p>
              <p className="text-xs text-slate-500 mt-1">65 itens com escala Likert de 4 pontos</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SRS2PageFallback() {
  return <div className="min-h-screen w-full bg-slate-300 p-6 md:p-10" />;
}

export default function SRS2Page() {
  return (
    <Suspense fallback={<SRS2PageFallback />}>
      <SRS2PageContent />
    </Suspense>
  );
}
