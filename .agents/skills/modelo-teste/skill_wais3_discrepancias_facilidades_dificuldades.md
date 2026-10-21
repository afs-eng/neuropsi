# SKILL_WAIS3_DISCREPANCIAS_FACILIDADES_DIFICULDADES.md

## Objetivo

Implementar, no módulo WAIS-III do sistema, duas análises específicas do protocolo brasileiro atualizado:

1. **Comparações entre discrepâncias**
2. **Determinação das facilidades e dificuldades**

Esta skill parte do pressuposto de que as tabelas normativas já estão cadastradas no sistema. A IA ou o backend **não devem inventar valores críticos, significância estatística ou frequência acumulada**. Esses dados devem ser sempre recuperados pelas tabelas internas do sistema.

---

# 1. Análise: Comparações entre discrepâncias

## 1.1 Finalidade clínica

A análise de discrepâncias verifica se a diferença entre dois QIs, índices fatoriais ou subtestes é estatisticamente significativa e qual é a frequência dessa diferença na amostra de padronização.

Ela deve ser usada para identificar dissociações relevantes entre domínios cognitivos, como:

- desempenho verbal versus desempenho de execução;
- compreensão verbal versus organização perceptual;
- compreensão verbal versus memória operacional;
- organização perceptual versus velocidade de processamento;
- memória operacional versus velocidade de processamento;
- diferenças internas em subtestes específicos.

---

## 1.2 Entradas obrigatórias

O sistema deve receber no `computed_payload`:

```json
{
  "composites": {
    "QIV": {"score": 105},
    "QIE": {"score": 92},
    "QIT": {"score": 99},
    "ICV": {"score": 108},
    "IOP": {"score": 96},
    "IMO": {"score": 87},
    "IVP": {"score": 82}
  },
  "scaled_scores": {
    "DG": 8,
    "SNL": 10,
    "CD": 7,
    "PS": 9
  },
  "process_scores": {
    "digitos_ordem_direta_maior_sequencia": 7,
    "digitos_ordem_inversa_maior_sequencia": 5
  },
  "settings": {
    "base_comparacao": "amostra_geral",
    "nivel_significancia": "0.05"
  }
}
```

---

## 1.3 Pares obrigatórios de discrepância

### Nível composto

```python
COMPOSITE_DISCREPANCY_PAIRS = [
    {
        "key": "QIV_QIE",
        "label": "QI Verbal - QI de Execução",
        "score_1": "QIV",
        "score_2": "QIE",
        "table": "wais3_b1_discrepancias_qi"
    },
    {
        "key": "ICV_IOP",
        "label": "Compreensão Verbal - Organização Perceptual",
        "score_1": "ICV",
        "score_2": "IOP",
        "table": "wais3_b2_discrepancias_indices"
    },
    {
        "key": "ICV_IMO",
        "label": "Compreensão Verbal - Memória Operacional",
        "score_1": "ICV",
        "score_2": "IMO",
        "table": "wais3_b2_discrepancias_indices"
    },
    {
        "key": "IOP_IVP",
        "label": "Organização Perceptual - Velocidade de Processamento",
        "score_1": "IOP",
        "score_2": "IVP",
        "table": "wais3_b2_discrepancias_indices"
    },
    {
        "key": "ICV_IVP",
        "label": "Compreensão Verbal - Velocidade de Processamento",
        "score_1": "ICV",
        "score_2": "IVP",
        "table": "wais3_b2_discrepancias_indices"
    },
    {
        "key": "IOP_IMO",
        "label": "Organização Perceptual - Memória Operacional",
        "score_1": "IOP",
        "score_2": "IMO",
        "table": "wais3_b2_discrepancias_indices"
    },
    {
        "key": "IMO_IVP",
        "label": "Memória Operacional - Velocidade de Processamento",
        "score_1": "IMO",
        "score_2": "IVP",
        "table": "wais3_b2_discrepancias_indices"
    }
]
```

### Nível subteste/processo

```python
SUBTEST_DISCREPANCY_PAIRS = [
    {
        "key": "DG_SNL",
        "label": "Dígitos - Sequência de Números e Letras",
        "score_1": "DG",
        "score_2": "SNL",
        "source": "scaled_scores",
        "table": "wais3_b6_discrepancias_subtestes"
    },
    {
        "key": "CD_PS",
        "label": "Código - Procurar Símbolos",
        "score_1": "CD",
        "score_2": "PS",
        "source": "scaled_scores",
        "table": "wais3_b6_discrepancias_subtestes"
    },
    {
        "key": "DIGITOS_DIRETA_INVERSA",
        "label": "Dígitos Ordem Direta - Ordem Inversa",
        "score_1": "digitos_ordem_direta_maior_sequencia",
        "score_2": "digitos_ordem_inversa_maior_sequencia",
        "source": "process_scores",
        "table": "wais3_b7_discrepancias_digitos"
    }
]
```

---

## 1.4 Função de lookup esperada

O sistema já possui as tabelas. Portanto, a skill deve orientar a IA/backend a usar uma função genérica de consulta:

```python
def lookup_wais3_discrepancy(
    table_name: str,
    pair_key: str,
    difference: float,
    base_comparacao: str,
    nivel_significancia: str
) -> dict:
    """
    Deve retornar:
    {
        "valor_critico": int | float,
        "significativa": bool,
        "frequencia_acumulada": str | float | None,
        "nivel_significancia": "0.05" | "0.15",
        "base_comparacao": "amostra_geral" | "nivel_habilidade"
    }
    """
```

A função deve buscar o valor na tabela correta, considerando:

- par comparado;
- diferença absoluta;
- base de comparação;
- nível de significância estatística;
- frequência acumulada correspondente.

---

## 1.5 Cálculo da discrepância

```python
def calculate_discrepancy(score_1: float, score_2: float) -> float:
    return abs(score_1 - score_2)
```

A direção da discrepância deve ser preservada separadamente para interpretação clínica:

```python
def get_discrepancy_direction(label_1: str, score_1: float, label_2: str, score_2: float) -> str:
    if score_1 > score_2:
        return f"{label_1} maior que {label_2}"
    if score_2 > score_1:
        return f"{label_2} maior que {label_1}"
    return "sem diferença entre os escores"
```

---

## 1.6 Implementação da análise de discrepâncias

```python
def compute_wais3_discrepancy_analysis(payload: dict, lookup_func) -> dict:
    composites = payload.get("composites", {})
    scaled_scores = payload.get("scaled_scores", {})
    process_scores = payload.get("process_scores", {})
    settings = payload.get("settings", {})

    base_comparacao = settings.get("base_comparacao", "amostra_geral")
    nivel_significancia = settings.get("nivel_significancia", "0.05")

    results = []

    for pair in COMPOSITE_DISCREPANCY_PAIRS:
        s1 = composites.get(pair["score_1"], {}).get("score")
        s2 = composites.get(pair["score_2"], {}).get("score")

        if s1 is None or s2 is None:
            results.append({
                "key": pair["key"],
                "label": pair["label"],
                "valid": False,
                "reason": "Escore composto ausente"
            })
            continue

        difference = calculate_discrepancy(s1, s2)
        lookup = lookup_func(
            table_name=pair["table"],
            pair_key=pair["key"],
            difference=difference,
            base_comparacao=base_comparacao,
            nivel_significancia=nivel_significancia
        )

        results.append({
            "key": pair["key"],
            "label": pair["label"],
            "valid": True,
            "score_1_label": pair["score_1"],
            "score_1": s1,
            "score_2_label": pair["score_2"],
            "score_2": s2,
            "difference": difference,
            "direction": get_discrepancy_direction(pair["score_1"], s1, pair["score_2"], s2),
            "valor_critico": lookup.get("valor_critico"),
            "significativa": lookup.get("significativa"),
            "frequencia_acumulada": lookup.get("frequencia_acumulada"),
            "nivel_significancia": nivel_significancia,
            "base_comparacao": base_comparacao
        })

    for pair in SUBTEST_DISCREPANCY_PAIRS:
        source = scaled_scores if pair["source"] == "scaled_scores" else process_scores
        s1 = source.get(pair["score_1"])
        s2 = source.get(pair["score_2"])

        if s1 is None or s2 is None:
            results.append({
                "key": pair["key"],
                "label": pair["label"],
                "valid": False,
                "reason": "Escore de subteste/processo ausente"
            })
            continue

        difference = calculate_discrepancy(s1, s2)
        lookup = lookup_func(
            table_name=pair["table"],
            pair_key=pair["key"],
            difference=difference,
            base_comparacao=base_comparacao,
            nivel_significancia=nivel_significancia
        )

        results.append({
            "key": pair["key"],
            "label": pair["label"],
            "valid": True,
            "score_1_label": pair["score_1"],
            "score_1": s1,
            "score_2_label": pair["score_2"],
            "score_2": s2,
            "difference": difference,
            "direction": get_discrepancy_direction(pair["score_1"], s1, pair["score_2"], s2),
            "valor_critico": lookup.get("valor_critico"),
            "significativa": lookup.get("significativa"),
            "frequencia_acumulada": lookup.get("frequencia_acumulada"),
            "nivel_significancia": nivel_significancia,
            "base_comparacao": base_comparacao
        })

    return {
        "analysis": "wais3_discrepancy_analysis",
        "results": results
    }
```

---

## 1.7 Interpretação textual das discrepâncias

```python
def interpret_wais3_discrepancies(discrepancy_payload: dict) -> str:
    results = discrepancy_payload.get("results", [])
    valid = [item for item in results if item.get("valid")]
    significant = [item for item in valid if item.get("significativa")]

    if not valid:
        return (
            "A análise de discrepâncias da WAIS-III não pôde ser realizada devido à ausência "
            "de escores necessários para comparação."
        )

    if not significant:
        return (
            "A análise das discrepâncias entre os escores da WAIS-III não evidenciou diferenças "
            "estatisticamente significativas entre os pares comparados, sugerindo maior homogeneidade "
            "entre os domínios avaliados."
        )

    sentences = []
    for item in significant:
        sentences.append(
            f"Na comparação {item['label']}, observou-se diferença de {item['difference']} pontos, "
            f"com {item['direction']}. Essa discrepância atingiu o critério de significância estatística "
            f"para o nível {item['nivel_significancia']}, com frequência acumulada de "
            f"{item['frequencia_acumulada']} na amostra de padronização."
        )

    return (
        "A análise das discrepâncias evidenciou diferenças estatisticamente significativas entre "
        "domínios específicos da WAIS-III. "
        + " ".join(sentences)
        + " Esses achados indicam funcionamento cognitivo heterogêneo e devem ser interpretados "
          "em conjunto com os índices fatoriais, subtestes, observações clínicas e demais instrumentos "
          "da avaliação neuropsicológica."
    )
```

---

# 2. Análise: Determinação das facilidades e dificuldades

## 2.1 Finalidade clínica

A análise de facilidades e dificuldades identifica quais subtestes se destacam positiva ou negativamente em relação à média de comparação escolhida.

Ela permite diferenciar:

- facilidades cognitivas relativas;
- dificuldades cognitivas relativas;
- desempenho compatível com a média do próprio perfil;
- assimetria entre habilidades verbais e de execução;
- subtestes que merecem interpretação qualitativa detalhada.

---

## 2.2 Bases de comparação

A Página de Perfil permite duas formas principais:

1. **Diferença da Média Total**
2. **Diferença da Média Verbal e da Média de Execução**

O sistema deve permitir selecionar a base:

```python
STRENGTH_WEAKNESS_BASES = [
    "media_total",
    "media_verbal_execucao"
]
```

---

## 2.3 Subtestes usados na média total

A média total é calculada a partir dos 10 subtestes principais:

```python
TEN_CORE_SUBTESTS = [
    "VC",  # Vocabulário
    "SM",  # Semelhanças
    "AR",  # Aritmética
    "DG",  # Dígitos
    "IN",  # Informação
    "CF",  # Completar Figuras
    "CD",  # Códigos
    "CB",  # Cubos
    "RM",  # Raciocínio Matricial
    "AF"   # Arranjo de Figuras
]
```

---

## 2.4 Subtestes verbais e de execução

```python
VERBAL_CORE_SUBTESTS = ["VC", "SM", "AR", "DG", "IN"]

PERFORMANCE_CORE_SUBTESTS = ["CF", "CD", "CB", "RM", "AF"]
```

---

## 2.5 Ordem dos subtestes na tabela de facilidades/dificuldades

```python
STRENGTH_WEAKNESS_ORDER = [
    "VC",
    "SM",
    "AR",
    "DG",
    "IN",
    "CO",
    "SNL",
    "CF",
    "CD",
    "CB",
    "RM",
    "AF",
    "PS",
    "AO"
]
```

---

## 2.6 Cálculo da média

```python
def calculate_mean_for_keys(scaled_scores: dict, keys: list[str]) -> float:
    values = [scaled_scores[key] for key in keys if scaled_scores.get(key) is not None]

    if not values:
        raise ValueError("Não há escores suficientes para cálculo da média.")

    return sum(values) / len(values)
```

---

## 2.7 Seleção da média de comparação

```python
def get_reference_mean_for_subtest(
    subtest: str,
    scaled_scores: dict,
    base: str
) -> tuple[float, str]:
    if base == "media_total":
        return calculate_mean_for_keys(scaled_scores, TEN_CORE_SUBTESTS), "Média Total"

    if base == "media_verbal_execucao":
        if subtest in VERBAL_CORE_SUBTESTS or subtest in ["CO", "SNL"]:
            return calculate_mean_for_keys(scaled_scores, VERBAL_CORE_SUBTESTS), "Média Verbal"

        if subtest in PERFORMANCE_CORE_SUBTESTS or subtest in ["PS", "AO"]:
            return calculate_mean_for_keys(scaled_scores, PERFORMANCE_CORE_SUBTESTS), "Média de Execução"

    raise ValueError(f"Base de comparação inválida ou subteste não reconhecido: {base} / {subtest}")
```

---

## 2.8 Função de lookup esperada para facilidades/dificuldades

```python
def lookup_wais3_strength_weakness(
    table_name: str,
    subtest: str,
    difference_from_mean: float,
    base_comparacao: str,
    nivel_significancia: str
) -> dict:
    """
    Deve consultar a tabela interna do sistema, equivalente à tabela de
    determinação de facilidades e dificuldades da WAIS-III.

    Deve retornar:
    {
        "valor_critico": int | float,
        "significativa": bool,
        "frequencia_acumulada": str | float | None
    }
    """
```

---

## 2.9 Regra de classificação

```python
def classify_strength_or_weakness(
    difference_from_mean: float,
    valor_critico: float,
    significativa: bool
) -> str:
    if not significativa:
        return "Dentro da média do perfil"

    if difference_from_mean > 0 and abs(difference_from_mean) >= valor_critico:
        return "Facilidade"

    if difference_from_mean < 0 and abs(difference_from_mean) >= valor_critico:
        return "Dificuldade"

    return "Dentro da média do perfil"
```

---

## 2.10 Implementação da análise de facilidades e dificuldades

```python
def compute_wais3_strengths_weaknesses(payload: dict, lookup_func) -> dict:
    scaled_scores = payload.get("scaled_scores", {})
    settings = payload.get("settings", {})

    base = settings.get("strength_weakness_base", "media_total")
    nivel_significancia = settings.get("nivel_significancia", "0.05")

    results = []

    for subtest in STRENGTH_WEAKNESS_ORDER:
        score = scaled_scores.get(subtest)

        if score is None:
            results.append({
                "subtest": subtest,
                "valid": False,
                "reason": "Escore ponderado ausente"
            })
            continue

        reference_mean, reference_label = get_reference_mean_for_subtest(
            subtest=subtest,
            scaled_scores=scaled_scores,
            base=base
        )

        difference_from_mean = score - reference_mean

        lookup = lookup_func(
            table_name="wais3_b3_facilidades_dificuldades",
            subtest=subtest,
            difference_from_mean=abs(difference_from_mean),
            base_comparacao=base,
            nivel_significancia=nivel_significancia
        )

        classification = classify_strength_or_weakness(
            difference_from_mean=difference_from_mean,
            valor_critico=lookup.get("valor_critico"),
            significativa=lookup.get("significativa")
        )

        results.append({
            "subtest": subtest,
            "valid": True,
            "score": score,
            "reference_mean": round(reference_mean, 2),
            "reference_label": reference_label,
            "difference_from_mean": round(difference_from_mean, 2),
            "valor_critico": lookup.get("valor_critico"),
            "significativa": lookup.get("significativa"),
            "classification": classification,
            "frequencia_acumulada": lookup.get("frequencia_acumulada"),
            "nivel_significancia": nivel_significancia,
            "base_comparacao": base
        })

    return {
        "analysis": "wais3_strengths_weaknesses",
        "base": base,
        "nivel_significancia": nivel_significancia,
        "results": results
    }
```

---

## 2.11 Interpretação textual das facilidades e dificuldades

```python
SUBTEST_FULL_NAMES = {
    "VC": "Vocabulário",
    "SM": "Semelhanças",
    "AR": "Aritmética",
    "DG": "Dígitos",
    "IN": "Informação",
    "CO": "Compreensão",
    "SNL": "Sequência de Números e Letras",
    "CF": "Completar Figuras",
    "CD": "Códigos",
    "CB": "Cubos",
    "RM": "Raciocínio Matricial",
    "AF": "Arranjo de Figuras",
    "PS": "Procurar Símbolos",
    "AO": "Armar Objetos"
}


def interpret_wais3_strengths_weaknesses(strength_payload: dict) -> str:
    results = strength_payload.get("results", [])

    valid = [item for item in results if item.get("valid")]
    strengths = [item for item in valid if item.get("classification") == "Facilidade"]
    weaknesses = [item for item in valid if item.get("classification") == "Dificuldade"]

    if not valid:
        return (
            "A determinação de facilidades e dificuldades não pôde ser realizada devido "
            "à ausência de escores ponderados suficientes."
        )

    if not strengths and not weaknesses:
        return (
            "A análise de facilidades e dificuldades não indicou subtestes com diferenças "
            "estatisticamente significativas em relação à média de comparação selecionada, "
            "sugerindo ausência de pontos fortes ou fragilidades relativas relevantes dentro "
            "do próprio perfil da WAIS-III."
        )

    parts = []

    if strengths:
        strength_names = [
            f"{SUBTEST_FULL_NAMES.get(item['subtest'], item['subtest'])} "
            f"(diferença de {item['difference_from_mean']} pontos)"
            for item in strengths
        ]
        parts.append(
            "Foram identificadas facilidades relativas nos seguintes subtestes: "
            + "; ".join(strength_names)
            + "."
        )

    if weaknesses:
        weakness_names = [
            f"{SUBTEST_FULL_NAMES.get(item['subtest'], item['subtest'])} "
            f"(diferença de {item['difference_from_mean']} pontos)"
            for item in weaknesses
        ]
        parts.append(
            "Foram identificadas dificuldades relativas nos seguintes subtestes: "
            + "; ".join(weakness_names)
            + "."
        )

    return (
        "A determinação de facilidades e dificuldades foi realizada a partir da comparação "
        "dos escores ponderados com a média de referência selecionada. "
        + " ".join(parts)
        + " Esses achados representam forças e fragilidades relativas dentro do próprio perfil "
          "do examinando, não devendo ser interpretados isoladamente como déficits ou habilidades "
          "absolutas sem integração com os índices fatoriais, observações clínicas e demais instrumentos."
    )
```

---

# 3. Integração no `calculate_wais3`

Adicionar ao cálculo principal:

```python
def calculate_wais3(payload: dict) -> dict:
    # cálculo já existente:
    result = {
        "test": "WAIS-III",
        # composites, sums, gai, clusters etc.
    }

    result["discrepancy_analysis"] = compute_wais3_discrepancy_analysis(
        payload=result,
        lookup_func=lookup_wais3_discrepancy
    )

    result["strengths_weaknesses"] = compute_wais3_strengths_weaknesses(
        payload=result,
        lookup_func=lookup_wais3_strength_weakness
    )

    return result
```

Atenção: se o `payload` original contiver `settings`, `scaled_scores` e `process_scores`, esses campos devem ser preservados no `result` antes de chamar as análises.

---

# 4. Integração no `interpreters.py`

```python
def generate_wais3_advanced_interpretation(patient_name: str, result: dict) -> str:
    base_text = generate_wais3_interpretation(patient_name, result)

    discrepancy_text = interpret_wais3_discrepancies(
        result.get("discrepancy_analysis", {})
    )

    strengths_text = interpret_wais3_strengths_weaknesses(
        result.get("strengths_weaknesses", {})
    )

    return "\n\n".join([
        base_text,
        discrepancy_text,
        strengths_text
    ])
```

---

# 5. Regras obrigatórias para a IA

1. Não calcular valor crítico por regra fixa.
2. Não inferir frequência acumulada.
3. Sempre consultar as tabelas internas do sistema.
4. Sempre preservar a direção da diferença.
5. Sempre diferenciar:
   - diferença estatisticamente significativa;
   - diferença clinicamente relevante;
   - diferença apenas numérica.
6. Não interpretar facilidade relativa como habilidade superior absoluta.
7. Não interpretar dificuldade relativa como déficit absoluto.
8. Integrar os achados com QI, índices, subtestes, observação clínica e demais testes.
9. Não fechar hipótese diagnóstica com base apenas nessas duas análises.

---

# 6. Saída esperada no `computed_payload`

```json
{
  "discrepancy_analysis": {
    "analysis": "wais3_discrepancy_analysis",
    "results": [
      {
        "key": "ICV_IOP",
        "label": "Compreensão Verbal - Organização Perceptual",
        "valid": true,
        "score_1": 108,
        "score_2": 96,
        "difference": 12,
        "direction": "ICV maior que IOP",
        "valor_critico": 10,
        "significativa": true,
        "frequencia_acumulada": "15%",
        "nivel_significancia": "0.05",
        "base_comparacao": "amostra_geral"
      }
    ]
  },
  "strengths_weaknesses": {
    "analysis": "wais3_strengths_weaknesses",
    "base": "media_total",
    "results": [
      {
        "subtest": "VC",
        "score": 13,
        "reference_mean": 10.2,
        "difference_from_mean": 2.8,
        "valor_critico": 3,
        "significativa": false,
        "classification": "Dentro da média do perfil",
        "frequencia_acumulada": "25%"
      }
    ]
  }
}
```

---

# 7. Texto final esperado no laudo

A IA deve gerar texto técnico, sem tabela obrigatória, por exemplo:

```text
A análise das discrepâncias entre os escores da WAIS-III evidenciou diferença estatisticamente significativa entre Compreensão Verbal e Organização Perceptual, com maior desempenho em Compreensão Verbal. Esse achado sugere desempenho relativamente mais eficiente em tarefas mediadas por linguagem, repertório conceitual e raciocínio verbal quando comparado às tarefas de organização perceptual e raciocínio visuoespacial.

Na determinação das facilidades e dificuldades, foram observadas facilidades relativas em Vocabulário e Semelhanças, indicando maior eficiência em repertório lexical, memória semântica e abstração verbal. Foram identificadas dificuldades relativas em Códigos e Procurar Símbolos, sugerindo menor eficiência em velocidade de processamento, rastreio visual e execução grafomotora sob limite de tempo.

Em análise clínica, essas diferenças representam variações internas do perfil cognitivo e devem ser interpretadas em conjunto com os demais resultados da avaliação neuropsicológica.
```
