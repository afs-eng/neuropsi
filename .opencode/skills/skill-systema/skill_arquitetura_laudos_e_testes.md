# Skill: Arquitetura Separada para Sistema de Laudos e Testes Psicológicos/Neuropsicológicos

## Objetivo da Skill

Esta skill orienta a implementação de um sistema neuropsicológico estruturado em dois grandes módulos independentes, porém integrados:

1. **Módulo de Testes**: responsável por cadastro, aplicação, correção, classificação, geração de gráficos e relatório técnico individual de cada instrumento.
2. **Módulo de Laudos**: responsável por montar o laudo completo, integrando anamnese, observação clínica, resultados dos testes, interpretação clínica, hipótese diagnóstica, conclusão geral e sugestões de conduta.

A arquitetura deve permitir que o sistema funcione tanto como uma plataforma de aplicação/correção de testes quanto como um gerador completo de laudos neuropsicológicos.

---

# 1. Princípio Geral da Arquitetura

O sistema deve ser dividido em duas camadas funcionais:

```text
Sistema Neuro
├── Módulo de Testes
│   ├── Aplicação
│   ├── Correção
│   ├── Classificação
│   ├── Gráficos
│   ├── Relatório técnico do teste
│   └── Interpretação do instrumento
│
└── Módulo de Laudos
    ├── Identificação
    ├── Demanda
    ├── Anamnese
    ├── Observação clínica
    ├── Resultados integrados
    ├── Conclusão geral
    ├── Hipótese diagnóstica
    ├── Sugestões de conduta
    └── Exportação DOCX/PDF
```

O módulo de testes deve gerar dados estruturados. O módulo de laudos deve consumir esses dados e transformá-los em narrativa clínica integrada.

---

# 2. Estrutura Recomendada no Backend Django

```text
apps/
├── patients/
│   ├── models.py
│   ├── services.py
│   └── api/
│
├── assessments/
│   ├── models.py
│   ├── services.py
│   └── api/
│
├── tests/
│   ├── registry.py
│   ├── selectors.py
│   ├── models/
│   │   ├── instruments.py
│   │   ├── applications.py
│   │   ├── results.py
│   │   └── templates.py
│   │
│   ├── services/
│   │   ├── application_service.py
│   │   ├── scoring_service.py
│   │   ├── classification_service.py
│   │   ├── interpretation_service.py
│   │   └── chart_service.py
│   │
│   ├── norms/
│   │   ├── bpa2/
│   │   ├── ravlt/
│   │   ├── fdt/
│   │   ├── wasi/
│   │   ├── wisc4/
│   │   ├── wais3/
│   │   ├── srs2/
│   │   ├── scared/
│   │   └── bfp/
│   │
│   ├── bpa2/
│   │   ├── config.py
│   │   ├── schemas.py
│   │   ├── validators.py
│   │   ├── loaders.py
│   │   ├── calculators.py
│   │   ├── classifiers.py
│   │   ├── interpreters.py
│   │   ├── charts.py
│   │   └── constants.py
│   │
│   ├── ravlt/
│   ├── fdt/
│   ├── wasi/
│   ├── wisc4/
│   ├── wais3/
│   ├── srs2/
│   ├── scared/
│   └── bfp/
│
├── reports/
│   ├── models.py
│   ├── builders/
│   │   ├── report_builder.py
│   │   ├── section_builder.py
│   │   ├── conclusion_builder.py
│   │   └── hypothesis_builder.py
│   │
│   ├── sections/
│   │   ├── identification.py
│   │   ├── demand.py
│   │   ├── anamnesis.py
│   │   ├── procedures.py
│   │   ├── clinical_observation.py
│   │   ├── cognitive_results.py
│   │   ├── attention_results.py
│   │   ├── executive_results.py
│   │   ├── memory_results.py
│   │   ├── emotional_results.py
│   │   ├── social_results.py
│   │   ├── conclusion.py
│   │   ├── recommendations.py
│   │   └── references.py
│   │
│   ├── templates/
│   │   ├── child_neuropsychological_report.docx
│   │   ├── adult_neuropsychological_report.docx
│   │   └── psychological_report.docx
│   │
│   ├── export/
│   │   ├── docx_exporter.py
│   │   ├── pdf_exporter.py
│   │   └── chart_embedder.py
│   │
│   └── services.py
```

---

# 3. Módulo de Testes

## 3.1 Função do módulo de testes

O módulo de testes deve permitir:

- cadastrar instrumentos;
- lançar respostas ou escores brutos;
- aplicar testes digitalmente quando possível;
- corrigir resultados;
- converter escores brutos em escores padronizados;
- gerar percentis, classificações e indicadores clínicos;
- gerar gráficos;
- produzir relatório técnico individual do teste;
- enviar dados estruturados para o módulo de laudos.

---

## 3.2 Modelo de Instrumento

Cada teste deve ser tratado como um módulo independente.

Exemplo:

```text
apps/tests/bpa2/
apps/tests/ravlt/
apps/tests/fdt/
apps/tests/wasi/
apps/tests/wais3/
apps/tests/wisc4/
apps/tests/srs2/
apps/tests/scared/
apps/tests/bfp/
```

Cada módulo deve conter:

```text
config.py          # classe principal do teste
schemas.py         # formato esperado dos dados de entrada
validators.py      # validação dos dados
loaders.py         # carregamento de normas/tabelas
calculators.py     # cálculo dos resultados
classifiers.py     # classificação clínica/normativa
interpreters.py    # texto interpretativo padrão ouro
charts.py          # geração de gráficos
constants.py       # nomes, domínios e configurações fixas
```

---

# 4. Interface Padrão de Todo Teste

Todos os testes devem seguir uma interface comum para que o sistema consiga chamar qualquer instrumento de forma padronizada.

```python
class BaseTestModule:
    code: str
    name: str
    domain: str

    def validate(self, raw_payload: dict) -> None:
        pass

    def calculate(self, raw_payload: dict) -> dict:
        pass

    def classify(self, computed_payload: dict) -> dict:
        pass

    def interpret(self, result_payload: dict, patient_context: dict | None = None) -> str:
        pass

    def generate_chart(self, result_payload: dict) -> str | None:
        pass

    def build_report_payload(self, result_payload: dict) -> dict:
        pass
```

Essa interface garante que BPA-2, RAVLT, FDT, WASI, WAIS-III, WISC-IV, SRS-2, SCARED, BFP e outros instrumentos possam ser processados pelo mesmo serviço central.

---

# 5. Registry dos Testes

Criar um registro global para todos os instrumentos disponíveis.

Arquivo:

```text
apps/tests/registry.py
```

Exemplo:

```python
from apps.tests.bpa2.config import BPA2Module
from apps.tests.ravlt.config import RAVLTModule
from apps.tests.fdt.config import FDTModule
from apps.tests.wasi.config import WASIModule
from apps.tests.wais3.config import WAIS3Module
from apps.tests.wisc4.config import WISC4Module
from apps.tests.srs2.config import SRS2Module
from apps.tests.scared.config import SCAREDModule
from apps.tests.bfp.config import BFPModule

TEST_REGISTRY = {
    "BPA2": BPA2Module(),
    "RAVLT": RAVLTModule(),
    "FDT": FDTModule(),
    "WASI": WASIModule(),
    "WAIS3": WAIS3Module(),
    "WISC4": WISC4Module(),
    "SRS2": SRS2Module(),
    "SCARED": SCAREDModule(),
    "BFP": BFPModule(),
}


def get_test_module(code: str):
    try:
        return TEST_REGISTRY[code]
    except KeyError:
        raise ValueError(f"Instrumento não registrado: {code}")
```

---

# 6. Serviço Central de Correção

Arquivo:

```text
apps/tests/services/scoring_service.py
```

Responsabilidade:

1. receber o código do teste;
2. buscar o módulo no registry;
3. validar dados;
4. calcular;
5. classificar;
6. interpretar;
7. gerar gráfico;
8. devolver payload final estruturado.

Exemplo:

```python
from apps.tests.registry import get_test_module

class ScoringService:
    def score(self, test_code: str, raw_payload: dict, patient_context: dict | None = None) -> dict:
        module = get_test_module(test_code)

        module.validate(raw_payload)
        computed = module.calculate(raw_payload)
        classified = module.classify(computed)
        interpretation = module.interpret(classified, patient_context)
        chart_path = module.generate_chart(classified)
        report_payload = module.build_report_payload(classified)

        return {
            "test_code": test_code,
            "test_name": module.name,
            "domain": module.domain,
            "raw_payload": raw_payload,
            "computed_payload": computed,
            "classified_payload": classified,
            "interpretation": interpretation,
            "chart_path": chart_path,
            "report_payload": report_payload,
        }
```

---

# 7. Payload Padronizado dos Resultados

Cada teste deve retornar dados estruturados no seguinte padrão:

```json
{
  "test_code": "BPA2",
  "test_name": "Bateria Psicológica para Avaliação da Atenção – BPA-2",
  "domain": "Atenção",
  "results": [
    {
      "scale": "Atenção Concentrada",
      "raw_score": 54,
      "percentile": 70,
      "classification": "Média Superior",
      "clinical_indicator": false
    },
    {
      "scale": "Atenção Alternada",
      "raw_score": 23,
      "percentile": 10,
      "classification": "Inferior",
      "clinical_indicator": true
    }
  ],
  "interpretation": "Texto técnico interpretativo do teste.",
  "chart_path": "media/charts/bpa2_123.png",
  "summary_for_report": "Resumo clínico objetivo para o laudo."
}
```

---

# 8. Diferença entre Relatório Técnico do Teste e Laudo Completo

## Relatório técnico do teste

Deve conter apenas:

- nome do teste;
- objetivo do instrumento;
- tabela de resultados;
- gráfico;
- interpretação específica do teste;
- observação de que o resultado não fecha diagnóstico isoladamente.

Exemplo:

```text
A avaliação por meio da BPA-2 evidenciou desempenho variável entre os domínios atencionais, com melhor rendimento em atenção concentrada e maior fragilidade em atenção alternada. Os resultados sugerem vulnerabilidade em tarefas que exigem alternância de foco, flexibilidade atencional e adaptação a mudanças de critério.
```

## Laudo completo

Deve integrar:

- anamnese;
- observação clínica;
- relatório escolar, quando houver;
- resultados de múltiplos testes;
- impacto funcional;
- hipótese diagnóstica;
- conclusão geral;
- encaminhamentos.

Exemplo:

```text
Em análise clínica, os achados atencionais observados na BPA-2, associados às manifestações descritas na anamnese e às observações comportamentais durante a avaliação, indicam prejuízos funcionais em atenção sustentada, alternância atencional e autorregulação executiva, com repercussões no desempenho acadêmico e na organização das atividades diárias.
```

---

# 9. Módulo de Laudos

## 9.1 Função do módulo de laudos

O módulo de laudos deve montar o documento completo, utilizando:

- dados do paciente;
- dados da avaliação;
- anamnese;
- observação clínica;
- resultados dos testes;
- interpretações geradas pelo módulo de testes;
- hipóteses diagnósticas;
- sugestões de conduta;
- referências bibliográficas.

---

## 9.2 Estrutura Interna do Laudo

```text
reports/
├── sections/
│   ├── identification.py
│   ├── demand.py
│   ├── anamnesis.py
│   ├── procedures.py
│   ├── clinical_observation.py
│   ├── intellectual_efficiency.py
│   ├── attention.py
│   ├── executive_functions.py
│   ├── language.py
│   ├── gnosis_praxis.py
│   ├── memory_learning.py
│   ├── emotional_aspects.py
│   ├── social_responsiveness.py
│   ├── personality.py
│   ├── conclusion.py
│   ├── diagnostic_hypothesis.py
│   ├── recommendations.py
│   └── references.py
```

---

# 10. Builder do Laudo

Arquivo:

```text
apps/reports/builders/report_builder.py
```

Exemplo:

```python
class NeuropsychologicalReportBuilder:
    def __init__(self, patient, assessment, test_results):
        self.patient = patient
        self.assessment = assessment
        self.test_results = test_results

    def build(self) -> dict:
        return {
            "identification": self.build_identification(),
            "demand": self.build_demand(),
            "anamnesis": self.build_anamnesis(),
            "procedures": self.build_procedures(),
            "clinical_observation": self.build_clinical_observation(),
            "test_sections": self.build_test_sections(),
            "integrated_analysis": self.build_integrated_analysis(),
            "conclusion": self.build_conclusion(),
            "diagnostic_hypothesis": self.build_diagnostic_hypothesis(),
            "recommendations": self.build_recommendations(),
            "references": self.build_references(),
        }
```

---

# 11. Integração entre Testes e Laudos

O módulo de testes deve enviar para o laudo três tipos de informação:

## 11.1 Resultado técnico

Usado para tabelas e gráficos.

```json
{
  "scale": "Atenção Concentrada",
  "raw_score": 54,
  "percentile": 70,
  "classification": "Média Superior"
}
```

## 11.2 Interpretação do teste

Usada na seção específica do teste.

```text
A avaliação da atenção por meio da BPA-2 indicou desempenho heterogêneo, com melhor rendimento em atenção concentrada e maior fragilidade em atenção alternada.
```

## 11.3 Síntese clínica para conclusão

Usada na conclusão geral.

```text
Os achados indicam vulnerabilidade em alternância atencional e autorregulação executiva, com possível impacto funcional em demandas escolares prolongadas.
```

---

# 12. Regras de Integração Clínica

O sistema deve respeitar as seguintes regras:

1. Nenhum teste deve fechar diagnóstico isoladamente.
2. O laudo deve integrar resultados dos testes, anamnese, observação clínica e funcionalidade.
3. A conclusão deve utilizar linguagem técnica, clara e defensável.
4. A expressão “hipótese diagnóstica” deve ser utilizada quando houver sustentação clínica.
5. O sistema deve diferenciar desempenho em ambiente estruturado de impacto ecológico na vida diária.
6. Resultados classificados como média, média inferior ou inferior em escalas sintomáticas só devem ser interpretados como prejuízo quando o manual do teste ou a regra clínica do instrumento indicar essa leitura.
7. Em E-TDAH-PAIS, E-TDAH-AD e SCARED, classificações inferior, média inferior e média não devem ser tratadas automaticamente como déficit clínico.
8. Em instrumentos cognitivos, classificações inferiores podem indicar fragilidade de desempenho, desde que contextualizadas.
9. O texto final deve evitar repetição excessiva, redundância e conclusões absolutas.
10. O laudo deve terminar nas referências bibliográficas, sem tabelas brutas após essa seção.

---

# 13. Organização dos Testes por Domínio no Laudo

Os resultados devem ser agrupados por domínio clínico, não apenas por ordem de aplicação.

```text
Eficiência Intelectual
├── WASI
├── WISC-IV
└── WAIS-III

Atenção
├── BPA-2
├── FDT
└── E-TDAH

Funções Executivas
├── FDT
├── Subtestes Wechsler
└── Escalas comportamentais

Memória e Aprendizagem
├── RAVLT
├── Dígitos
├── Sequência de Números e Letras
└── Figuras Complexas de Rey

Aspectos Emocionais
├── BAI
├── BDI
├── EBADEP
├── SCARED
└── HTP como dado qualitativo complementar

Responsividade Social / TEA
├── SRS-2
├── Observação clínica
└── Anamnese

Personalidade
├── BFP
├── EPQ-J
└── IPHEXA
```

---

# 14. Modelos de Status dos Testes

Cada aplicação de teste deve ter status próprio.

```text
DRAFT          # rascunho
IN_PROGRESS    # aplicação iniciada
COMPLETED      # aplicação finalizada
SCORED         # corrigido
INTERPRETED    # interpretação gerada
REVIEWED       # revisado pelo profissional
LOCKED         # travado para edição
```

---

# 15. Modelos de Status do Laudo

```text
DRAFT          # rascunho
IN_REVIEW      # em revisão
APPROVED       # aprovado
EXPORTED       # exportado
LOCKED         # travado
```

---

# 16. Modelos Django Recomendados

## Instrument

```python
class Instrument(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=100)
    version = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
```

## TestApplication

```python
class TestApplication(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    assessment = models.ForeignKey("assessments.Assessment", on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.PROTECT)
    raw_payload = models.JSONField(default=dict)
    computed_payload = models.JSONField(default=dict)
    classified_payload = models.JSONField(default=dict)
    interpretation = models.TextField(blank=True)
    chart_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=50, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Report

```python
class Report(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    assessment = models.ForeignKey("assessments.Assessment", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content_payload = models.JSONField(default=dict)
    status = models.CharField(max_length=50, default="DRAFT")
    docx_file = models.FileField(upload_to="reports/docx/", blank=True, null=True)
    pdf_file = models.FileField(upload_to="reports/pdf/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

# 17. Fluxo Completo do Sistema

```text
1. Cadastrar paciente
2. Criar avaliação
3. Selecionar instrumentos
4. Aplicar teste ou lançar resultados brutos
5. Corrigir teste
6. Gerar classificação
7. Gerar gráfico
8. Gerar relatório técnico do teste
9. Revisar resultado do teste
10. Enviar resultados para o laudo
11. Montar laudo completo
12. Integrar achados clínicos
13. Gerar conclusão geral
14. Gerar hipótese diagnóstica
15. Gerar sugestões de conduta
16. Exportar DOCX/PDF
```

---

# 18. Regra de Ouro da Separação

O módulo de testes não deve escrever o laudo completo.

O módulo de testes deve produzir:

```text
resultado + classificação + gráfico + interpretação específica + síntese clínica
```

O módulo de laudos deve produzir:

```text
narrativa integrada + conclusão geral + hipótese diagnóstica + recomendações
```

---

# 19. Exemplo Prático: BPA-2

## Entrada

```json
{
  "norm_method": "age",
  "age": 9,
  "ac_raw": 54,
  "ad_raw": 35,
  "aa_raw": 23,
  "ag_raw": 112
}
```

## Saída do módulo de testes

```json
{
  "test_code": "BPA2",
  "domain": "Atenção",
  "results": [
    {
      "scale": "Atenção Concentrada",
      "raw_score": 54,
      "percentile": 70,
      "classification": "Média Superior"
    },
    {
      "scale": "Atenção Alternada",
      "raw_score": 23,
      "percentile": 10,
      "classification": "Inferior"
    }
  ],
  "interpretation": "Texto interpretativo do BPA-2.",
  "summary_for_report": "Indica melhor desempenho em atenção concentrada e fragilidade em alternância atencional."
}
```

## Uso no laudo

```text
Em análise clínica, os resultados obtidos na BPA-2 indicam perfil atencional heterogêneo, com melhor rendimento em atenção concentrada e maior fragilidade em atenção alternada. Esse padrão sugere dificuldade em tarefas que exigem mudança de foco, flexibilidade atencional e adaptação a novos critérios, podendo repercutir em atividades escolares que demandam alternância entre instruções, organização sequencial e monitoramento contínuo.
```

---

# 20. Exemplo Prático: WASI

## Entrada

```json
{
  "vocabulary_score": 42,
  "similarities_score": 38,
  "block_design_score": 35,
  "matrix_reasoning_score": 44,
  "verbal_iq": 103,
  "performance_iq": 82,
  "full_scale_iq": 93
}
```

## Saída do módulo de testes

```json
{
  "test_code": "WASI",
  "domain": "Eficiência Intelectual",
  "results": {
    "qiv": {
      "score": 103,
      "classification": "Média"
    },
    "qie": {
      "score": 82,
      "classification": "Média Inferior"
    },
    "qit": {
      "score": 93,
      "classification": "Média"
    }
  },
  "interpretation": "Texto interpretativo da WASI.",
  "summary_for_report": "Funcionamento intelectual global médio, com melhor desempenho verbal em relação ao não verbal."
}
```

## Uso no laudo

```text
Em análise clínica, o perfil intelectual evidencia funcionamento cognitivo global dentro da média, com predominância das habilidades verbais em relação às habilidades de execução. Esse padrão sugere maior eficiência em tarefas mediadas pela linguagem, compreensão conceitual e raciocínio verbal, em contraste com desempenho relativamente inferior em atividades que exigem organização visuoespacial, raciocínio perceptual e resolução prática de problemas.
```

---

# 21. Interface Recomendada no Frontend

## Menu principal

```text
Dashboard
Pacientes
Avaliações
Testes
Laudos
Modelos
Configurações
```

## Dentro de uma avaliação

```text
Avaliação de João
├── Dados clínicos
├── Anamnese
├── Observações
├── Testes aplicados
│   ├── BPA-2
│   ├── WASI
│   ├── RAVLT
│   └── SRS-2
├── Relatórios dos testes
└── Laudo final
```

## Tela de Teste

```text
BPA-2
├── Dados de entrada
├── Correção
├── Resultado
├── Gráfico
├── Interpretação
└── Enviar para laudo
```

## Tela de Laudo

```text
Laudo Neuropsicológico
├── Identificação
├── Demanda
├── Anamnese
├── Procedimentos
├── Análise por domínios
├── Conclusão geral
├── Hipótese diagnóstica
├── Sugestões de conduta
├── Referências
└── Exportar
```

---

# 22. Regras de Formatação dos Laudos

1. Fonte principal: Times New Roman, tamanho 12.
2. Texto justificado.
3. Títulos em negrito.
4. Tabelas com fonte Times New Roman, tamanho 10 ou 11.
5. Legendas abaixo de tabelas e gráficos, fonte tamanho 8, itálico.
6. Não utilizar divisores com linhas longas.
7. Não deixar conteúdo bruto após as referências.
8. A seção de referências deve ser a última do documento.
9. Gráficos devem ser exportados em alta resolução.
10. A conclusão geral deve iniciar diretamente com o nome do paciente sempre que essa regra estiver ativa no modelo.

---

# 23. Regras de Texto Clínico

1. Usar “Em análise clínica” para fechamento interpretativo.
2. Evitar iniciar parágrafos repetidamente com “No” ou “Na”.
3. Evitar “verifica-se” em conclusões integradas.
4. Preferir “conclui-se que” em trechos conclusivos.
5. Utilizar “hipótese diagnóstica” quando houver sustentação clínica.
6. Evitar linguagem categórica quando os dados não forem suficientes.
7. Não afirmar diagnóstico apenas com base em escala de rastreio.
8. Integrar impacto funcional sempre que possível.
9. Diferenciar resultado psicométrico de manifestação ecológica.
10. Manter coerência entre resultados, conclusão e encaminhamentos.

---

# 24. Ordem de Implementação Recomendada

## Fase 1: Núcleo dos testes

1. Criar app `tests`.
2. Criar models `Instrument` e `TestApplication`.
3. Criar `BaseTestModule`.
4. Criar `registry.py`.
5. Implementar primeiro teste piloto: BPA-2.
6. Criar `ScoringService`.
7. Salvar `raw_payload`, `computed_payload`, `classified_payload` e `interpretation`.

## Fase 2: Relatórios técnicos dos testes

1. Criar geração de tabela.
2. Criar geração de gráfico.
3. Criar exportação individual do teste.
4. Criar botão “Enviar para laudo”.

## Fase 3: Núcleo dos laudos

1. Criar app `reports`.
2. Criar `ReportBuilder`.
3. Criar seções fixas.
4. Importar resultados dos testes.
5. Gerar laudo em payload estruturado.

## Fase 4: Exportação

1. Gerar DOCX.
2. Gerar PDF.
3. Embutir tabelas e gráficos.
4. Aplicar formatação padrão.

## Fase 5: IA integrada

1. IA para interpretação de teste.
2. IA para integração clínica.
3. IA para conclusão geral.
4. IA para hipótese diagnóstica.
5. IA para revisão de coerência.

---

# 25. Resultado Esperado

Ao final da implementação, o sistema deve permitir dois usos independentes:

## Uso 1: Sistema de testes

```text
Aplicar BPA-2 → corrigir → gerar gráfico → gerar relatório técnico
```

## Uso 2: Sistema de laudos

```text
Selecionar paciente → importar testes → integrar dados → gerar laudo completo
```

## Uso 3: Sistema combinado

```text
Aplicar todos os testes → corrigir automaticamente → gerar interpretações → montar laudo completo → exportar DOCX/PDF
```

---

# 26. Diretriz Final

A implementação deve tratar testes e laudos como módulos separados.

O teste produz evidência psicométrica.

O laudo produz interpretação clínica integrada.

Essa separação torna o sistema mais profissional, escalável, auditável e semelhante a plataformas especializadas de avaliação psicológica, mantendo a flexibilidade necessária para gerar laudos neuropsicológicos completos com padrão técnico elevado.
