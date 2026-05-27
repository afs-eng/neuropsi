"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams, useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, Printer, Edit, LayoutDashboard } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { printCurrentPage } from "@/lib/print";
import { TestReportSummaryCard } from "@/components/tests/TestReportSummaryCard";

const FEMININO = {
  P: [[0,0,5,"MUITO BAIXO"], [1,1,20,"BAIXO"], [2,2,40,"MEDIO"], [3,3,60,"MEDIO"], [4,4,70,"MEDIO"], [5,6,80,"ALTO"], [7,7,90,"ALTO"], [8,14,99,"MUITO ALTO"]],
  E: [[0,5,5,"MUITO BAIXO"], [6,7,10,"BAIXO"], [8,8,20,"BAIXO"], [9,9,40,"MEDIO"], [10,10,50,"MEDIO"], [11,11,70,"MEDIO"], [12,12,90,"ALTO"]],
  N: [[0,2,5,"MUITO BAIXO"], [3,4,10,"BAIXO"], [5,6,20,"BAIXO"], [7,7,30,"MEDIO"], [8,8,40,"MEDIO"], [9,9,50,"MEDIO"], [10,10,60,"MEDIO"], [11,12,70,"MEDIO"], [13,13,80,"ALTO"], [14,15,90,"ALTO"], [16,18,99,"MUITO ALTO"]],
  S: [[0,4,5,"MUITO BAIXO"], [5,5,10,"BAIXO"], [6,7,20,"BAIXO"], [8,8,30,"MEDIO"], [9,9,40,"MEDIO"], [10,10,50,"MEDIO"], [11,12,60,"MEDIO"], [13,13,70,"MEDIO"], [14,14,80,"ALTO"], [15,15,90,"ALTO"], [16,16,99,"MUITO ALTO"]],
};

const MASCULINO = {
  P: [[0,0,5,"MUITO BAIXO"], [1,1,20,"BAIXO"], [2,2,30,"MEDIO"], [3,3,40,"MEDIO"], [4,4,60,"MEDIO"], [5,6,70,"MEDIO"], [7,7,80,"ALTO"], [8,11,90,"ALTO"], [12,14,99,"MUITO ALTO"]],
  E: [[0,4,5,"MUITO BAIXO"], [5,6,10,"BAIXO"], [7,8,20,"BAIXO"], [9,9,30,"MEDIO"], [10,10,50,"MEDIO"], [11,11,70,"MEDIO"], [12,12,90,"ALTO"]],
  N: [[0,2,5,"MUITO BAIXO"], [3,3,10,"BAIXO"], [4,5,20,"BAIXO"], [6,6,30,"MEDIO"], [7,7,40,"MEDIO"], [8,8,50,"MEDIO"], [9,9,60,"MEDIO"], [10,11,70,"MEDIO"], [12,12,80,"ALTO"], [13,16,90,"ALTO"], [17,18,99,"MUITO ALTO"]],
  S: [[0,3,5,"MUITO BAIXO"], [4,5,10,"BAIXO"], [6,6,20,"BAIXO"], [7,8,30,"MEDIO"], [9,9,40,"MEDIO"], [10,11,50,"MEDIO"], [12,12,60,"MEDIO"], [13,13,70,"MEDIO"], [14,14,80,"ALTO"], [15,15,90,"ALTO"], [16,16,99,"MUITO ALTO"]],
};

function classificar(valor: number, tabela: (number | string)[][]) {
  for (const row of tabela) {
    const min = row[0] as number;
    const max = row[1] as number;
    const percentil = row[2] as number;
    const classe = row[3] as string;
    if (min <= valor && valor <= max) {
      return { percentil, classificacao: classe };
    }
  }
  return { percentil: 0, classificacao: "NÃO CLASSIFICADO" };
}

const DEFINICOES = {
  P: "Relaciona-se à rigidez mental e comportamento impulsivo ou transgressor, variando entre busca de sensações e responsabilidade social.",
  E: "Indica tendência à sociabilidade, atividade e espontaneidade ou, em níveis baixos, introversão e preferência por ambientes mais reservados.",
  N: "Refere-se à estabilidade emocional. Altos níveis indicam maior instabilidade afetiva.",
  S: "Indica tendência à desejabilidade social nas respostas, devendo ser interpretada com cautela.",
};

const CLASSIFICACOES: Record<string, string> = {
  "MUITO BAIXO": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "BAIXO": "bg-blue-50 text-blue-700 border-blue-200",
  "MEDIO": "bg-amber-50 text-amber-700 border-amber-200",
  "ALTO": "bg-orange-50 text-orange-700 border-orange-200",
  "MUITO ALTO": "bg-red-50 text-red-700 border-red-200",
};

function getClassificacaoStyle(classificacao: string) {
  const key = classificacao.toUpperCase();
  return CLASSIFICACOES[key] || "bg-slate-100 text-slate-700 border-slate-200";
}

function parseResponseValue(value: unknown): number | undefined {
  if (value === null || value === undefined || value === "") {
    return undefined;
  }

  const parsed = typeof value === "number" ? value : parseInt(String(value), 10);
  return Number.isNaN(parsed) ? undefined : parsed;
}

function formatAppliedOn(value: unknown): string {
  if (!value) {
    return new Date().toLocaleDateString("pt-BR");
  }

  const date = new Date(String(value));
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString("pt-BR");
}

function EPQJResultPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const params = useParams();
  const [evaluationId, setEvaluationId] = useState(searchParams.get("evaluation_id") || "");
  const [application, setApplication] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const nome = searchParams.get("nome") || "";
  const sexo = application?.computed_payload?.sexo || application?.classified_payload?.sexo || searchParams.get("sexo") || "M";
  const backendResultados = application?.computed_payload?.resultados || application?.classified_payload?.fatores || null;
  const p = backendResultados?.P?.escore ?? parseInt(searchParams.get("p") || "0", 10);
  const e = backendResultados?.E?.escore ?? parseInt(searchParams.get("e") || "0", 10);
  const n = backendResultados?.N?.escore ?? parseInt(searchParams.get("n") || "0", 10);
  const s = backendResultados?.S?.escore ?? parseInt(searchParams.get("s") || "0", 10);

  const respostas: Record<number, number> = {};
  for (let i = 1; i <= 60; i += 1) {
    const rawValue = application?.raw_payload?.[`item_${String(i).padStart(2, "0")}`]
      ?? application?.raw_payload?.[`item_${i}`]
      ?? searchParams.get(`r${i}`);
    const parsedValue = parseResponseValue(rawValue);
    if (parsedValue !== undefined) {
      respostas[i] = parsedValue;
    }
  }

  // Montar array de respostas para display (4 colunas)
  const linhasRespostas = [];
  for (let i = 0; i < 15; i += 1) {
    linhasRespostas.push([i + 1, i + 16, i + 31, i + 46]);
  }

  const normas = sexo === "F" ? FEMININO : MASCULINO;
  const resP = backendResultados?.P || classificar(p, normas.P);
  const resE = backendResultados?.E || classificar(e, normas.E);
  const resN = backendResultados?.N || classificar(n, normas.N);
  const resS = backendResultados?.S || classificar(s, normas.S);

  const RESULTADOS = {
    P: { bruto: p, percentil: resP.percentil, classificacao: resP.classificacao },
    E: { bruto: e, percentil: resE.percentil, classificacao: resE.classificacao },
    N: { bruto: n, percentil: resN.percentil, classificacao: resN.classificacao },
    S: { bruto: s, percentil: resS.percentil, classificacao: resS.classificacao },
  };

  const DADOS_AVALIADO = {
    nome: application?.patient_name || nome,
    dataAplicacao: formatAppliedOn(application?.applied_on),
    sexo: sexo === "F" ? "Feminino" : "Masculino",
    tabelaNormativa: sexo === "F" ? "Feminino" : "Masculino",
  };

  const getBarWidth = (percentil: number) => {
    return `${Math.min(100, Math.max(0, percentil))}%`;
  };

  useEffect(() => {
    async function loadApplicationData() {
      if (!params.id) {
        setLoading(false);
        return;
      }

      try {
        const result = await api.get<any>(`/api/tests/applications/${params.id}`);
        setApplication(result);
        if (result?.evaluation_id) {
          setEvaluationId(String(result.evaluation_id));
        }
      } catch (error) {
        console.error("Erro ao buscar resultado do EPQ-J:", error);
      } finally {
        setLoading(false);
      }
    }

    loadApplicationData();
  }, [params.id]);

  useEffect(() => {
    if (evaluationId) return;

    async function loadApplication() {
      try {
        const result = await api.get<{ evaluation_id?: number }>(`/api/tests/applications/${params.id}`);
        if (result?.evaluation_id) {
          setEvaluationId(String(result.evaluation_id));
        }
      } catch (error) {
        console.error("Erro ao buscar aplicação para montar o retorno:", error);
      }
    }

    if (params.id) {
      loadApplication();
    }
  }, [evaluationId, params.id]);

  const backHref = useMemo(() => {
    return evaluationId ? `/dashboard/evaluations/${evaluationId}?tab=overview` : "/dashboard/evaluations?tab=overview";
  }, [evaluationId]);

  if (loading && !application) {
    return <div className="py-16 text-center text-slate-500">Carregando resultado...</div>;
  }

  return (
    <div className="space-y-6 report-print-shell">
      <div className="flex items-center justify-between print:hidden report-print-hide">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push(backHref)} className="rounded-full">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">EPQ-J - Resultado</h2>
            <p className="text-sm text-slate-500">Questionário de Personalidade para Crianças e Adolescentes</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="rounded-xl gap-2" onClick={() => router.push("/dashboard")}>
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </Button>
          <Button variant="outline" className="rounded-xl gap-2" onClick={() => router.push(`/dashboard/tests/epq-j?application_id=${params.id}&edit=true`)}>
            <Edit className="h-4 w-4" />
            Editar
          </Button>
          <Button variant="outline" className="rounded-xl gap-2" onClick={() => router.push(backHref)}>
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Button>
          <Button variant="outline" className="rounded-xl gap-2" onClick={printCurrentPage}>
            <Printer className="h-4 w-4" />
            Imprimir
          </Button>
          <Button className="rounded-xl gap-2" onClick={printCurrentPage}>
            <Download className="h-4 w-4" />
            Salvar em PDF
          </Button>
        </div>
      </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 space-y-8 report-print-content">
        <TestReportSummaryCard reportPayload={application.report_payload} fallbackText={application.interpretation_text || application.interpretation} className="mb-6" />

        {/* Header */}
        <div className="text-center border-b pb-6">
          <h1 className="text-2xl font-bold text-slate-900">EPQ-J</h1>
          <p className="text-lg text-slate-600">Questionário de Personalidade para Crianças e Adolescentes</p>
          <p className="text-sm text-slate-500 mt-1">Formato Completo</p>
        </div>

        {/* Dados do Avaliado */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">DADOS DO AVALIADO</h2>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b">
                  <td className="py-3 px-4 font-medium text-slate-700 w-1/3">Nome</td>
                  <td className="py-3 px-4 text-slate-900">{DADOS_AVALIADO.nome}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-3 px-4 font-medium text-slate-700">Data da Aplicação</td>
                  <td className="py-3 px-4 text-slate-900">{DADOS_AVALIADO.dataAplicacao}</td>
                </tr>
                <tr className="border-b">
                  <td className="py-3 px-4 font-medium text-slate-700">Sexo</td>
                  <td className="py-3 px-4 text-slate-900">{DADOS_AVALIADO.sexo}</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium text-slate-700">Tabela Normativa</td>
                  <td className="py-3 px-4 text-slate-900">{DADOS_AVALIADO.tabelaNormativa}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Introdução */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">INTRODUÇÃO</h2>
          <div className="text-sm text-slate-600 leading-relaxed space-y-3">
            <p>
              Entre os diferentes testes e demais instrumentos que buscam subsidiar o profissional de psicologia em sua tomada de decisões,
              encontram-se aqueles que avaliam o construto personalidade, abarcando diferentes faixas etárias: adultos, idosos, adolescentes e crianças.
            </p>
            <p>
              A avaliação da personalidade em crianças e adolescentes constitui uma tarefa complexa, pois depende da capacidade de introspecção do respondente.
            </p>
            <p>
              O EPQ-J baseia-se no modelo PEN (Psicoticismo, Extroversão e Neuroticismo), desenvolvido por Hans Eysenck, adaptado para a população brasileira.
            </p>
            <p className="font-medium">
              A interpretação dos resultados deve considerar a integração com outros dados clínicos e instrumentos utilizados no processo avaliativo.
            </p>
          </div>
        </section>

        {/* Definição dos Construtos */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">DEFINIÇÃO DOS CONSTRUTOS</h2>
          <div className="space-y-4">
            <div className="border rounded-xl p-4">
              <h3 className="font-semibold text-slate-900 mb-2">Psicoticismo (P)</h3>
              <p className="text-sm text-slate-600">{DEFINICOES.P}</p>
            </div>
            <div className="border rounded-xl p-4">
              <h3 className="font-semibold text-slate-900 mb-2">Extroversão (E)</h3>
              <p className="text-sm text-slate-600">{DEFINICOES.E}</p>
            </div>
            <div className="border rounded-xl p-4">
              <h3 className="font-semibold text-slate-900 mb-2">Neuroticismo (N)</h3>
              <p className="text-sm text-slate-600">{DEFINICOES.N}</p>
            </div>
            <div className="border rounded-xl p-4">
              <h3 className="font-semibold text-slate-900 mb-2">Sinceridade (S)</h3>
              <p className="text-sm text-slate-600">{DEFINICOES.S}</p>
            </div>
          </div>
        </section>

        {/* Utilização do Relatório */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">UTILIZAÇÃO DO RELATÓRIO</h2>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <p className="text-sm text-amber-800">
              Este documento não constitui um laudo técnico. Representa dados quantitativos e qualitativos que devem ser 
              integrados a outras informações clínicas para uma compreensão adequada do avaliado.
            </p>
          </div>
        </section>

        {/* Identificação do Protocolo */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">IDENTIFICAÇÃO DO PROTOCOLO</h2>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <tbody>
                <tr className="border-b">
                  <td className="py-3 px-4 font-medium text-slate-700 w-1/3">Código do Avaliado</td>
                  <td className="py-3 px-4 text-slate-900">P-1042</td>
                </tr>
                <tr className="border-b">
                  <td className="py-3 px-4 font-medium text-slate-700">Código do Relatório</td>
                  <td className="py-3 px-4 text-slate-900">EPQJ-2026-001</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-medium text-slate-700">Data da Aplicação</td>
                  <td className="py-3 px-4 text-slate-900">{DADOS_AVALIADO.dataAplicacao}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Validade das Respostas */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">VALIDADE DAS RESPOSTAS</h2>
          <h3 className="text-sm font-medium text-slate-700 mb-3">Critérios de Verificação</h3>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50">
                  <th className="py-3 px-4 text-left font-medium text-slate-700">Critério</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Quantidade</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Resultado</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t">
                  <td className="py-3 px-4 text-slate-700">Aquiescência ou Tendência a discordar</td>
                  <td className="py-3 px-4 text-center text-slate-900">2</td>
                  <td className="py-3 px-4 text-center">
                    <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Dentro do esperado</Badge>
                  </td>
                </tr>
                <tr className="border-t">
                  <td className="py-3 px-4 text-slate-700">Escala de Sinceridade</td>
                  <td className="py-3 px-4 text-center text-slate-900">12</td>
                  <td className="py-3 px-4 text-center">
                    <Badge className="bg-amber-50 text-amber-700 border-amber-200">Atenção</Badge>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Resultados */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">RESULTADOS</h2>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50">
                  <th className="py-3 px-4 text-left font-medium text-slate-700">Escala</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Resultado Bruto</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Percentil</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Classificação</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(RESULTADOS).map(([escala, dados], idx) => (
                  <tr key={escala} className={`border-t ${idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}>
                    <td className="py-3 px-4 font-medium text-slate-900">{escala === "P" ? "Psicoticismo (P)" : escala === "E" ? "Extroversão (E)" : escala === "N" ? "Neuroticismo (N)" : "Sinceridade (S)"}</td>
                    <td className="py-3 px-4 text-center text-slate-900">{dados.bruto}</td>
                    <td className="py-3 px-4 text-center text-slate-900">{dados.percentil}</td>
                    <td className="py-3 px-4 text-center">
                      <Badge className={`rounded-full border ${getClassificacaoStyle(dados.classificacao)}`}>
                        {dados.classificacao}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Registro de Respostas */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">REGISTRO DE RESPOSTAS</h2>
          <p className="text-sm text-slate-600 mb-4">Legenda: 1 = Sim | 0 = Não</p>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-100">
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-12">Item</th>
                  <th className="py-2 px-2 text-center font-medium text-slate-700 w-16">Resp.</th>
                </tr>
              </thead>
              <tbody>
                {linhasRespostas.map((linha, idx) => (
                  <tr key={idx} className={`border-t ${idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}>
                    {linha.map((itemNum: number) => (
                      <>
                        <td className="py-1 px-2 text-center text-slate-700 font-medium">{String(itemNum).padStart(2, "0")}</td>
                        <td className="py-1 px-2 text-center">
                          <span className={`inline-block w-8 h-6 leading-6 rounded ${respostas[itemNum] === 1 ? "bg-blue-100 text-blue-800 font-bold" : respostas[itemNum] === 0 ? "bg-slate-200 text-slate-700 font-bold" : "bg-slate-100 text-slate-400"}`}>
                            {respostas[itemNum] !== undefined ? respostas[itemNum] : "-"}
                          </span>
                        </td>
                      </>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Resultado por Fator */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">RESULTADO POR FATOR</h2>
          <div className="border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-100">
                  <th className="py-3 px-4 text-left font-medium text-slate-700">Escala</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Resultado Bruto</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Percentil</th>
                  <th className="py-3 px-4 text-center font-medium text-slate-700">Classificação</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { escala: "P", dados: RESULTADOS.P },
                  { escala: "E", dados: RESULTADOS.E },
                  { escala: "N", dados: RESULTADOS.N },
                  { escala: "S", dados: RESULTADOS.S },
                ].map((item, idx) => (
                  <tr key={item.escala} className={`border-t ${idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}>
                    <td className="py-3 px-4 font-medium text-slate-900">
                      {item.escala === "P" ? "Psicoticismo (P)" : item.escala === "E" ? "Extroversão (E)" : item.escala === "N" ? "Neuroticismo (N)" : "Sinceridade (S)"}
                    </td>
                    <td className="py-3 px-4 text-center text-slate-900">{item.dados.bruto}</td>
                    <td className="py-3 px-4 text-center text-slate-900">{item.dados.percentil}</td>
                    <td className="py-3 px-4 text-center">
                      <Badge className={`rounded-full border ${getClassificacaoStyle(item.dados.classificacao)}`}>
                        {item.dados.classificacao}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Análise Gráfica */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">ANÁLISE GRÁFICA</h2>
          <div className="bg-slate-50 border rounded-xl p-6 font-mono text-sm">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="w-8 font-bold text-slate-700">P</span>
                <div className="flex-1 h-4 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: getBarWidth(RESULTADOS.P.percentil) }} />
                </div>
                <span className="w-12 text-right text-slate-600">{RESULTADOS.P.percentil}%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-8 font-bold text-slate-700">E</span>
                <div className="flex-1 h-4 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: getBarWidth(RESULTADOS.E.percentil) }} />
                </div>
                <span className="w-12 text-right text-slate-600">{RESULTADOS.E.percentil}%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-8 font-bold text-slate-700">N</span>
                <div className="flex-1 h-4 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: getBarWidth(RESULTADOS.N.percentil) }} />
                </div>
                <span className="w-12 text-right text-slate-600">{RESULTADOS.N.percentil}%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-8 font-bold text-slate-700">S</span>
                <div className="flex-1 h-4 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-purple-500 rounded-full" style={{ width: getBarWidth(RESULTADOS.S.percentil) }} />
                </div>
                <span className="w-12 text-right text-slate-600">{RESULTADOS.S.percentil}%</span>
              </div>
            </div>

            {/* Escala visual */}
            <div className="mt-6 pt-4 border-t border-slate-200">
              <div className="flex justify-between text-xs text-slate-500 mb-1">
                <span>0</span>
                <span>25</span>
                <span>50</span>
                <span>75</span>
                <span>100</span>
              </div>
              <div className="h-1 bg-gradient-to-r from-emerald-500 via-amber-500 to-red-500 rounded-full" />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>Muito Baixo</span>
                <span>Baixo</span>
                <span>Médio</span>
                <span>Alto</span>
                <span>Muito Alto</span>
              </div>
            </div>
          </div>
        </section>

        {/* Legenda */}
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">LEGENDA</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-emerald-500" />
              <span className="text-sm text-slate-700">Muito Baixo/Baixo</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-amber-500" />
              <span className="text-sm text-slate-700">Médio</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-orange-500" />
              <span className="text-sm text-slate-700">Alto</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-red-500" />
              <span className="text-sm text-slate-700">Muito Alto</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function EPQJResultPageFallback() {
  return <div className="space-y-6" />;
}

export default function EPQJResultPage() {
  return (
    <Suspense fallback={<EPQJResultPageFallback />}>
      <EPQJResultPageContent />
    </Suspense>
  );
}
