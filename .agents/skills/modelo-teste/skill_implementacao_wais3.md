# skill_implementacao_wais3.md

# Skill: Implementação do WAIS-III no sistema de avaliação neuropsicológica

## 1. Objetivo da skill

Esta skill orienta a implementação completa, auditável e tecnicamente segura da correção do WAIS-III no sistema. O módulo deve receber os escores brutos dos subtestes, validar idade e dados mínimos, converter os escores brutos em escores ponderados por tabela normativa, calcular somatórios, QIs, índices fatoriais, percentis, intervalos de confiança, análise de discrepâncias, facilidades e dificuldades intraindividuais, além de gerar o payload final para gráficos e interpretação textual.

O sistema não deve “inferir” pontuações normativas. Toda conversão deve vir exclusivamente das tabelas cadastradas no banco ou em arquivos CSV/XLSX validados.

## 2. Escopo do módulo WAIS-III

O WAIS-III deve ser implementado como um módulo independente dentro de `apps/tests/wais3/`, seguindo a arquitetura modular já usada para outros testes.

Estrutura recomendada:

```text
apps/tests/
  registry.py
  norms/
    wais3/
      a1_raw_to_scaled/
      a3_verbal_iq.csv
      a4_performance_iq.csv
      a5_full_scale_iq.csv
      a6_icv.csv
      a7_iop.csv
      a8_imo.csv
      a9_ivp.csv
      a10_prorated_sums.csv
      b1_index_discrepancy_critical_values.csv
      b2_index_discrepancy_base_rates.csv
      b3_subtest_strength_weakness_critical_values.csv
      b6_digit_span_frequency.csv
      b7_digit_span_difference_frequency.csv

  wais3/
    __init__.py
    config.py
    constants.py
    schemas.py
    validators.py
    loaders.py
    norm_utils.py
    calculators.py
    discrepancy.py
    strengths_weaknesses.py
    classifiers.py
    interpreters.py
    serializers.py
```

## 3. Dados de entrada obrigatórios

O `raw_payload` deve conter:

```json
{
  "birth_date": "YYYY-MM-DD",
  "application_date": "YYYY-MM-DD",
  "age_years": 40,
  "age_months": 0,
  "subtests": {
    "vocabulary": {"raw": 24},
    "similarities": {"raw": 18},
    "arithmetic": {"raw": 14},
    "digit_span": {"raw": 15, "forward_span": 6, "backward_span": 4},
    "information": {"raw": 20},
    "comprehension": {"raw": 16},
    "letter_number_sequencing": {"raw": 12},

    "picture_completion": {"raw": 18},
    "digit_symbol_coding": {"raw": 55},
    "block_design": {"raw": 32},
    "matrix_reasoning": {"raw": 19},
    "picture_arrangement": {"raw": 14},
    "symbol_search": {"raw": 28},
    "object_assembly": {"raw": 22}
  },
  "applied_subtests": ["vocabulary", "similarities", "..."],
  "substitutions": [],
  "invalidated_subtests": [],
  "confidence_level": 0.95,
  "significance_level": 0.05
}
```

Regras:
- `birth_date` e `application_date` devem ser obrigatórios.
- A idade deve ser calculada pelo sistema, não digitada manualmente como fonte principal.
- A primeira sessão de aplicação deve ser usada como data-base.
- Não arredondar idade cronológica.
- O WAIS-III é aplicável de 17 a 89 anos, com atenção à exceção do subteste Armar Objetos, limitado até 74 anos.
- O sistema deve bloquear cálculo quando a idade estiver fora da faixa normativa.

## 4. Cálculo da idade cronológica

Implementar função:

```python
def calculate_chronological_age(birth_date, application_date):
    ...
```

Saída esperada:

```json
{
  "years": 40,
  "months": 3,
  "days": 12,
  "norm_age_band": "40-44"
}
```

Regras:
- Calcular anos, meses e dias.
- Não arredondar.
- Usar a faixa etária normativa correspondente às tabelas do WAIS-III.
- A faixa normativa será usada para selecionar a tabela A.1 correta.

## 5. Conversão de escores brutos em escores ponderados

### 5.1 Regra central

Depois de obter os escores brutos de cada subteste, o sistema deve transcrevê-los para o campo `raw_score`, consultar a Tabela A.1 adequada à idade do examinando e localizar o escore ponderado correspondente.

O `computed_payload` deve armazenar:

```json
{
  "subtests": {
    "similarities": {
      "raw": 24,
      "scaled": 13,
      "source_table": "A.1",
      "age_band": "40-44",
      "is_supplemental": false,
      "included_in_composite": true
    }
  }
}
```

### 5.2 Regra de segurança

O sistema nunca deve:
- estimar escore ponderado por interpolação;
- usar tabela de outra faixa etária;
- preencher escore ausente por média;
- incluir subteste suplementar sem regra explícita de substituição;
- incluir notas entre parênteses no somatório dos escores ponderados.

## 6. Subtestes do WAIS-III

### 6.1 Escala Verbal

Subtestes principais:
- Vocabulário
- Semelhanças
- Aritmética
- Dígitos
- Informação

Subtestes verbais suplementares ou adicionais, conforme protocolo:
- Compreensão
- Sequência de Números e Letras

### 6.2 Escala de Execução

Subtestes principais:
- Completar Figuras
- Códigos
- Cubos
- Raciocínio Matricial
- Arranjo de Figuras

Subtestes de execução suplementares ou adicionais, conforme protocolo:
- Procurar Símbolos
- Armar Objetos

## 7. Cálculo dos somatórios principais

Implementar os somatórios a partir dos escores ponderados válidos.

```python
VERBAL_SCALE = [
    "vocabulary",
    "similarities",
    "arithmetic",
    "digit_span",
    "information",
]

PERFORMANCE_SCALE = [
    "picture_completion",
    "digit_symbol_coding",
    "block_design",
    "matrix_reasoning",
    "picture_arrangement",
]

VCI = [
    "vocabulary",
    "similarities",
    "information",
]

POI = [
    "picture_completion",
    "block_design",
    "matrix_reasoning",
]

WMI = [
    "arithmetic",
    "digit_span",
    "letter_number_sequencing",
]

PSI = [
    "digit_symbol_coding",
    "symbol_search",
]
```

Saídas:

```json
{
  "sums": {
    "verbal_scale_sum": 58,
    "performance_scale_sum": 52,
    "full_scale_sum": 110,
    "vci_sum": 36,
    "poi_sum": 33,
    "wmi_sum": 31,
    "psi_sum": 20
  }
}
```

Regras:
- QI Total não é média dos índices fatoriais.
- QI Total deve ser derivado da soma dos escores ponderados dos subtestes principais.
- Não incluir notas entre parênteses.
- Registrar quais subtestes foram incluídos em cada soma.

## 8. Cálculo proporcional pela Tabela A.10

O cálculo proporcional só deve ser usado quando:
- apenas 5 subtestes da Escala Verbal foram aplicados e não há subteste suplementar disponível para substituição;
- apenas 4 subtestes da Escala de Execução foram aplicados e não há subteste suplementar disponível para substituição.

Fluxo:

```python
def calculate_prorated_sum(scale_type, available_scaled_scores):
    raw_sum = sum(available_scaled_scores)
    prorated_sum = lookup_a10(scale_type, number_of_subtests, raw_sum)
    return prorated_sum
```

Payload:

```json
{
  "proration": {
    "used": true,
    "scale": "verbal",
    "available_subtests": 5,
    "raw_sum": 52,
    "prorated_sum": 62,
    "source_table": "A.10",
    "warning": "Resultado proporcional. Interpretar com cautela."
  }
}
```

Regras:
- O sistema deve priorizar substituição válida antes de usar pró-rata.
- O uso de pró-rata deve gerar alerta visível no laudo.
- O sistema deve guardar log da justificativa.
- O sistema não deve usar pró-rata se houver número insuficiente de subtestes.

## 9. Conversão dos somatórios em QIs e índices fatoriais

Após calcular os somatórios, usar as tabelas A.3 a A.9:

```text
A.3 = QI Verbal
A.4 = QI de Execução
A.5 = QI Total
A.6 = Índice de Compreensão Verbal
A.7 = Índice de Organização Perceptual
A.8 = Índice de Memória Operacional
A.9 = Índice de Velocidade de Processamento
```

Cada conversão deve retornar:

```json
{
  "composites": {
    "verbal_iq": {
      "sum": 58,
      "score": 105,
      "percentile": 63,
      "confidence_interval": [99, 111],
      "classification": "Média",
      "source_table": "A.3"
    },
    "performance_iq": {
      "sum": 52,
      "score": 100,
      "percentile": 50,
      "confidence_interval": [94, 106],
      "classification": "Média",
      "source_table": "A.4"
    },
    "full_scale_iq": {
      "sum": 110,
      "score": 103,
      "percentile": 58,
      "confidence_interval": [98, 108],
      "classification": "Média",
      "source_table": "A.5"
    }
  }
}
```

## 10. Classificação dos escores compostos

Usar a classificação padronizada:

```python
def classify_composite(score):
    if score >= 130:
        return "Muito Superior"
    if score >= 120:
        return "Superior"
    if score >= 110:
        return "Média Superior"
    if score >= 90:
        return "Média"
    if score >= 80:
        return "Média Inferior"
    if score >= 70:
        return "Limítrofe"
    return "Deficitário"
```

## 11. Classificação dos escores ponderados

```python
def classify_scaled_score(score):
    if score >= 16:
        return "Muito Superior"
    if score >= 14:
        return "Superior"
    if score >= 12:
        return "Média Superior"
    if score >= 8:
        return "Média"
    if score >= 7:
        return "Média Inferior"
    if score >= 5:
        return "Limítrofe"
    return "Deficitário"
```

## 12. Perfil dos escores

O módulo deve gerar payload para gráfico dos escores ponderados:

```json
{
  "charts": {
    "scaled_profile": [
      {"label": "Vocabulário", "scaled": 13, "classification": "Média Superior"},
      {"label": "Semelhanças", "scaled": 11, "classification": "Média"}
    ],
    "composite_profile": [
      {"label": "QIV", "score": 105, "percentile": 63},
      {"label": "QIE", "score": 100, "percentile": 50},
      {"label": "QIT", "score": 103, "percentile": 58}
    ]
  }
}
```

## 13. Determinação de facilidades e dificuldades

### 13.1 Média de referência

Para cada subteste, calcular a diferença entre o escore ponderado e a média da escala correspondente.

Para subtestes verbais:
```text
diferença = escore ponderado do subteste - média da Escala Verbal
```

Para subtestes de execução:
```text
diferença = escore ponderado do subteste - média da Escala de Execução
```

Payload:

```json
{
  "strengths_weaknesses": {
    "vocabulary": {
      "scaled": 13,
      "reference_mean": 10.4,
      "difference": 2.6,
      "critical_value": 3,
      "is_significant": false,
      "type": null,
      "base_rate": null
    },
    "block_design": {
      "scaled": 15,
      "reference_mean": 10.0,
      "difference": 5.0,
      "critical_value": 3,
      "is_significant": true,
      "type": "facilidade",
      "base_rate": "5%"
    }
  }
}
```

### 13.2 Consulta à Tabela B.3

A Tabela B.3 deve ser usada para verificar se a diferença entre o escore ponderado e a média é significativa. O nível padrão recomendado para o sistema é 0,05, mantendo a opção de 0,15 apenas se o usuário especialista selecionar.

Regra:
- diferença positiva significativa = facilidade;
- diferença negativa significativa = dificuldade;
- diferença absoluta menor que o valor crítico = sem facilidade/dificuldade clinicamente relevante.

## 14. Análise de discrepâncias entre QIs e índices fatoriais

Fluxo:

```python
def analyze_discrepancy(score_1, score_2, comparison_key, age_band, significance_level):
    difference = score_1 - score_2
    critical_value = lookup_b1(comparison_key, age_band, significance_level)
    is_significant = abs(difference) >= critical_value
    base_rate = lookup_b2(comparison_key, difference) if is_significant else None
    return ...
```

Payload:

```json
{
  "discrepancies": {
    "verbal_iq_vs_performance_iq": {
      "score_1": 105,
      "score_2": 100,
      "difference": 5,
      "critical_value": 9,
      "is_significant": false,
      "base_rate": null,
      "interpretation": "Não houve discrepância estatisticamente significativa entre QI Verbal e QI de Execução."
    },
    "vci_vs_poi": {
      "score_1": 112,
      "score_2": 94,
      "difference": 18,
      "critical_value": 12,
      "is_significant": true,
      "base_rate": "10%",
      "interpretation": "Houve discrepância significativa, com melhor desempenho em compreensão verbal."
    }
  }
}
```

Regras:
- Usar Tabela B.1 para valor crítico.
- Usar Tabela B.2 para frequência/base rate quando houver discrepância significativa.
- O sistema deve guardar sinal positivo ou negativo da diferença.
- O texto interpretativo deve dizer qual domínio ficou superior, sem transformar discrepância automaticamente em diagnóstico.

## 15. Dígitos: análise complementar

O protocolo deve armazenar:
- escore bruto total em Dígitos;
- maior sequência em Ordem Direta;
- maior sequência em Ordem Inversa.

Payload:

```json
{
  "process_scores": {
    "digit_span": {
      "raw_total": 15,
      "scaled": 10,
      "forward_span": 6,
      "backward_span": 4,
      "b6_frequency_forward": "percentual normativo",
      "b6_frequency_backward": "percentual normativo",
      "b7_difference_frequency": "percentual normativo"
    }
  }
}
```

Regras:
- Usar Tabela B.6 para frequência das sequências mais longas.
- Usar Tabela B.7 para frequência da diferença entre Ordem Direta e Ordem Inversa.
- Interpretar Ordem Direta como amplitude atencional auditiva imediata.
- Interpretar Ordem Inversa como memória operacional e manipulação mental.

## 16. Validações obrigatórias

O módulo deve impedir finalização quando:

```text
- idade fora da faixa WAIS-III;
- data de aplicação anterior à data de nascimento;
- escore bruto ausente em subteste obrigatório sem justificativa;
- tabela normativa não encontrada;
- escore bruto fora do intervalo previsto na tabela;
- tentativa de cálculo de QI Total com composição inválida;
- tentativa de usar Armar Objetos fora da faixa permitida;
- substituição acima do permitido;
- pró-rata sem critério técnico;
- índice fatorial sem todos os subtestes necessários.
```

## 17. Estrutura do computed_payload final

```json
{
  "instrument": "WAIS-III",
  "age": {
    "years": 40,
    "months": 3,
    "days": 12,
    "age_band": "40-44"
  },
  "subtests": {},
  "sums": {},
  "composites": {},
  "strengths_weaknesses": {},
  "discrepancies": {},
  "process_scores": {},
  "charts": {},
  "warnings": [],
  "audit": {
    "norm_tables_used": [],
    "substitutions_used": [],
    "proration_used": false,
    "calculated_at": "ISO-8601"
  }
}
```

## 18. Interpretação textual automatizada

O interpretador deve receber o `computed_payload` e gerar texto técnico com:

1. funcionamento intelectual global;
2. QI Verbal, QI de Execução e QI Total;
3. índices fatoriais: ICV, IOP, IMO e IVP;
4. discrepâncias significativas, quando houver;
5. facilidades e dificuldades intraindividuais;
6. análise dos subtestes rebaixados ou elevados;
7. ressalva técnica quando houver pró-rata, subteste invalidado ou composição incompleta.

Modelo:

```text
A avaliação por meio da Escala Wechsler de Inteligência para Adultos, Terceira Edição, WAIS-III, indicou funcionamento intelectual global situado na faixa [classificação], conforme QI Total = [valor], percentil [percentil]. O perfil apresentou [homogeneidade/heterogeneidade], considerando a comparação entre os índices fatoriais e os subtestes.

O Índice de Compreensão Verbal situou-se na faixa [classificação], indicando [interpretação]. O Índice de Organização Perceptual situou-se na faixa [classificação], sugerindo [interpretação]. O Índice de Memória Operacional apresentou desempenho [classificação], relacionado à sustentação atencional, manipulação mental e controle ativo de informações. O Índice de Velocidade de Processamento apresentou desempenho [classificação], refletindo a eficiência em tarefas de rastreio visual, rapidez grafomotora e processamento de estímulos simples sob limite de tempo.

Em análise clínica, [nome] apresentou [facilidades/dificuldades], sem que esses achados, isoladamente, determinem hipótese diagnóstica. A interpretação deve ser integrada aos demais instrumentos, à anamnese, às observações clínicas e ao funcionamento adaptativo.
```

## 19. Regras para geração de laudo

O texto do WAIS-III no laudo deve conter:

```text
- Nome do instrumento completo.
- Objetivo do teste.
- Tabela com QIs e índices fatoriais.
- Gráfico dos escores compostos, se habilitado.
- Interpretação técnica.
- Ressalvas quando existirem.
```

Não usar:
- “o paciente é inteligente”;
- “incapaz”;
- diagnóstico com base exclusiva no WAIS-III;
- explicações deterministas;
- “verifica-se que” no trecho conclusivo.

Preferir:
- “funcionamento intelectual global”;
- “recursos cognitivos”;
- “vulnerabilidade relativa”;
- “facilidade intraindividual”;
- “dificuldade intraindividual”;
- “Em análise clínica”.

## 20. Testes unitários mínimos

Criar testes para:

```text
1. cálculo correto da idade;
2. seleção correta da Tabela A.1 por idade;
3. conversão raw → scaled;
4. soma da Escala Verbal;
5. soma da Escala de Execução;
6. cálculo do QI Total por soma total, não por média;
7. bloqueio de notas entre parênteses;
8. conversão A.3 a A.9;
9. classificação de QIs;
10. classificação de escores ponderados;
11. uso correto da Tabela A.10;
12. bloqueio de pró-rata indevido;
13. análise de discrepância B.1/B.2;
14. análise de facilidade/dificuldade B.3;
15. payload final completo;
16. geração de texto sem diagnóstico automático.
```

## 21. Pseudocódigo do fluxo completo

```python
def score_wais3(raw_payload):
    validated = validate_wais3_payload(raw_payload)

    age = calculate_chronological_age(
        validated.birth_date,
        validated.application_date,
    )

    age_band = resolve_wais3_age_band(age)

    scaled_scores = {}
    for subtest, data in validated.subtests.items():
        scaled_scores[subtest] = lookup_raw_to_scaled(
            table="A.1",
            age_band=age_band,
            subtest=subtest,
            raw_score=data["raw"],
        )

    sums = calculate_wais3_sums(
        scaled_scores=scaled_scores,
        substitutions=validated.substitutions,
        invalidated_subtests=validated.invalidated_subtests,
    )

    if sums.requires_proration:
        sums = apply_a10_proration(sums)

    composites = convert_sums_to_composites(sums)

    strengths_weaknesses = analyze_strengths_weaknesses(
        scaled_scores=scaled_scores,
        verbal_mean=sums.verbal_mean,
        performance_mean=sums.performance_mean,
        significance_level=validated.significance_level,
    )

    discrepancies = analyze_all_discrepancies(
        composites=composites,
        age_band=age_band,
        significance_level=validated.significance_level,
    )

    process_scores = analyze_digit_span_process_scores(
        raw_payload=validated,
        age_band=age_band,
    )

    return build_computed_payload(
        age=age,
        subtests=scaled_scores,
        sums=sums,
        composites=composites,
        strengths_weaknesses=strengths_weaknesses,
        discrepancies=discrepancies,
        process_scores=process_scores,
    )
```

## 22. Princípio de auditoria

Cada valor calculado deve ser rastreável. O sistema deve permitir responder:

```text
- Qual tabela foi usada?
- Qual faixa etária foi usada?
- Qual escore bruto entrou?
- Qual escore ponderado saiu?
- Qual soma gerou o QI?
- Qual tabela converteu a soma?
- Houve substituição?
- Houve pró-rata?
- Qual valor crítico foi usado?
- A discrepância foi estatisticamente significativa?
```

Sem rastreabilidade, o resultado não deve ser aprovado para o laudo final.

## 23. Checklist de aprovação do módulo WAIS-III

```text
[ ] Calcula idade corretamente.
[ ] Seleciona faixa normativa correta.
[ ] Converte todos os escores brutos pela Tabela A.1.
[ ] Calcula somas verbais, execução, total e índices fatoriais.
[ ] Usa A.3 a A.9 para QIs e índices.
[ ] Usa A.10 somente em condição permitida.
[ ] Calcula percentil e intervalo de confiança.
[ ] Classifica todos os compostos.
[ ] Analisa discrepâncias por B.1 e B.2.
[ ] Analisa facilidades/dificuldades por B.3.
[ ] Analisa Dígitos por B.6 e B.7.
[ ] Gera computed_payload completo.
[ ] Gera gráficos a partir de payload, não de texto.
[ ] Gera interpretação técnica sem diagnóstico automático.
[ ] Registra warnings e trilha de auditoria.
```
