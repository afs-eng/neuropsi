# Análise de Adequação do Módulo WAIS-III à Skill skill_implementacao_wais3.md

## Contexto
Skill analisada: `.agents/skills/modelo-teste/skill_implementacao_wais3.md`
Módulo avaliado: `apps/tests/wais3/`

---

## 1. Perfil dos Escores (Seção 12 da skill)

### O que a skill exige:
- Payload para gráfico dos escores ponderados (`scaled_profile`) com `label`, `scaled`, `classification`.
- Payload para gráfico dos escores compostos (`composite_profile`) com `label`, `score`, `percentile`.
- Estrutura:
```json
{
  "charts": {
    "scaled_profile": [...],
    "composite_profile": [...]
  }
}
```

### O que o sistema faz hoje:
- Gera `subtestes_ordenados`, mas **não gera** o payload `charts`.
- Os índices estão em `indices`, não em `composite_profile`.
- Não há estrutura pronta para consumo por gráficos.

### Lacuna: ALTA
O payload de perfil gráfico não existe. O frontend/laudo não recebe dados estruturados para renderização de gráficos conforme a skill.

---

## 2. Determinação de Facilidades e Dificuldades (Seção 13 da skill)

### O que a skill exige:

#### 2.1. Média de referência:
- Para cada subteste, calcular diferença entre escore ponderado e média da **escala correspondente**.
- Verbal: diferença = subteste - média da Escala Verbal.
- Execução: diferença = subteste - média da Escala de Execução.
- Todos os subtestes aplicados devem entrar no cálculo da média (principais + suplementares aplicados).

#### 2.2. Payload esperado:
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
    }
  }
}
```

#### 2.3. Tabela B.3:
- Usar para verificar se a diferença é significativa.
- Nível padrão: 0,05 (com opção de 0,15).
- Consultar `base_rate` quando houver significância.
- Regra:
  - diferença positiva significativa = **facilidade**
  - diferença negativa significativa = **dificuldade**

### O que o sistema faz hoje:

#### Problemas encontrados:

1. **Cálculo da média incompleto**: O código atual calcula a média apenas com os 5 subtestes verbais principais e 5 de execução principais. **Não inclui** `compreensao`, `sequencia_numeros_letras` e `procurar_simbolos` quando aplicados. A skill diz "média da Escala Verbal/Execução", que deve incluir todos os subtestes aplicados daquela escala.

2. **Não retorna `base_rate`**: A função `_load_b3` carrega apenas `verbal_n15`, `verbal_n05`, `exec_n15`, `exec_n05`. **Não consulta a Tabela B.3 para obter a base rate** (frequência) da diferença encontrada.

3. **Payload não segue o formato da skill**: O payload atual retorna:
```json
{
  "facilidades_dificuldades": [
    {
      "subteste": "...",
      "escore": ...,
      "media": ...,
      "diferenca": ...,
      "tipo": "facilidade|dificuldade",
      "significancia": "α=0,05"
    }
  ]
}
```
Falta: `reference_mean`, `critical_value`, `is_significant`, `base_rate`.

4. **Não inclui todos os subtestes na análise**: A lista `verbal_subtests` no código não inclui `sequencia_numeros_letras`. A lista `exec_subtests` não inclui `procurar_simbolos` e `armar_objetos`. Ou seja, se esses subtestes forem aplicados, **não serão analisados** para facilidades/dificuldades.

### Lacunas: ALTAS
A análise de facilidades/dificuldades está parcialmente implementada com formato incorreto e subtestes faltando.

---

## 3. Análise de Discrepância entre QIs e Índices Fatoriais (Seção 14 da skill)

### O que a skill exige:

#### 3.1. Fluxo:
```python
def analyze_discrepancy(score_1, score_2, comparison_key, age_band, significance_level):
    difference = score_1 - score_2
    critical_value = lookup_b1(comparison_key, age_band, significance_level)
    is_significant = abs(difference) >= critical_value
    base_rate = lookup_b2(comparison_key, difference) if is_significant else None
    return ...
```

#### 3.2. Payload esperado:
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
      "interpretation": "Não houve discrepância..."
    }
  }
}
```

#### 3.3. Regras:
- Usar Tabela B.1 para valor crítico.
- Usar Tabela B.2 para frequência/base rate **quando houver discrepância significativa**.
- Guardar **sinal positivo/negativo** da diferença (para saber qual ficou superior).
- Gerar **texto interpretativo** automático.

### O que o sistema faz hoje:

#### Problemas encontrados:

1. **Não consulta Tabela B.2**: O código carrega `b1_data` mas **nunca carrega nem usa a Tabela B.2** para obter `base_rate` quando a discrepância é significativa. A skill exige explicitamente: "Usar Tabela B.2 para frequência/base rate quando houver discrepância significativa."

2. **Perde o sinal da diferença**: O código calcula `diff = abs(v1 - v2)`. Ou seja, perde-se completamente a informação de **qual índice ficou superior**. A skill exige: "O sistema deve guardar sinal positivo ou negativo da diferença."

3. **Não gera interpretação textual**: O payload não contém o campo `interpretation` com texto automático. A skill exige: "O texto interpretativo deve dizer qual domínio ficou superior, sem transformar discrepância automaticamente em diagnóstico."

4. **Formato do payload incorreto**: O sistema retorna:
```json
{
  "discrepancias": [
    {
      "nivel": "0,05",
      "pares": [
        {
          "par": "...",
          "diferenca": ...,
          "critico": ...,
          "nivel": "0,05"
        }
      ]
    }
  ]
}
```
Isso agrupa por nível de significância, mas a skill espera um dicionário por par de comparação (`verbal_iq_vs_performance_iq`), com `score_1`, `score_2`, `difference` (com sinal), `critical_value`, `is_significant`, `base_rate`, `interpretation`.

### Lacunas: ALTAS
A análise de discrepância está incompleta: falta B.2, sinal da diferença, interpretação textual e formato correto do payload.

---

## 4. Outras Divergências Críticas Identificadas

### 4.1. Classificação de escores ponderados (Seção 11 da skill)
**Skill:**
```python
def classify_scaled_score(score):
    if score >= 16: "Muito Superior"
    if score >= 14: "Superior"
    if score >= 12: "Média Superior"
    if score >= 8:  "Média"
    if score >= 7:  "Média Inferior"
    if score >= 5:  "Limítrofe"
    return "Deficitário"
```

**Código atual (`constants.py`):**
```python
def classify_scaled_score(score):
    if score >= 16: ...
    if score >= 14: ...
    if score >= 12: ...
    if score >= 8:  ...
    if score >= 6:  "Média Inferior"   # <-- ERRO: skill exige >= 7
    if score >= 4:  "Limítrofe"        # <-- ERRO: skill exige >= 5
    return "Extremamente Baixo"         # <-- ERRO: skill exige "Deficitário"
```

**Impacto:** Classificações erradas para escores 5, 6 e 7. Um escore 7 seria "Média" pelo código atual, mas deveria ser "Média Inferior" pela skill.

### 4.2. Classificação de escores compostos em `classifiers.py`
A função `_classify_wechsler` em `classifiers.py` retorna "Extremamente Baixo" para valores <= 69, mas a skill (seção 10) usa "Deficitário". Isso cria inconsistência entre `classify_composite_score` (constants.py) e `_classify_wechsler` (classifiers.py).

### 4.3. Estrutura do computed_payload final (Seção 17 da skill)
A skill define payload com:
```json
{
  "instrument": "WAIS-III",
  "age": { "years": ..., "months": ..., "days": ..., "age_band": "..." },
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

O payload atual tem:
```json
{
  "instrument_code": "wais3",
  "idade": { "anos": ..., "meses": ... },
  "subtestes": {},
  "indices": {},
  "facilidades_dificuldades": [],
  "discrepancias": [],
  "digitos": {},
  ...
}
```

Falta: `sums`, `composites`, `strengths_weaknesses` (formato dicionário), `discrepancies` (formato dicionário), `process_scores`, `charts`, `audit`.

### 4.4. Cálculo proporcional (Proration) - Tabela A.10 (Seção 8 da skill)
**Status: NÃO IMPLEMENTADO.** O sistema não possui nenhuma lógica para cálculo proporcional quando faltam subtestes, embora a skill tenha uma seção completa sobre isso.

### 4.5. Substituição de subtestes (Seções 7 e 8 da skill)
**Status: NÃO IMPLEMENTADO.** O payload aceita `substitutions` mas a lógica de cálculo (`compute_wais3_payload`) ignora esse campo.

### 4.6. Trilha de auditoria (Seção 22 da skill)
**Status: NÃO IMPLEMENTADO.** Não há campo `audit` no payload final.

### 4.7. Dados de entrada obrigatórios (Seção 3 da skill)
A skill exige:
- `birth_date` e `application_date` obrigatórios.
- Idade calculada pelo sistema, não digitada manualmente.

O sistema atual recebe `idade` diretamente no payload de teste, sem validação de datas.

### 4.8. Dígitos - análise complementar (Seção 15 da skill)
O payload esperado pela skill inclui `forward_span`, `backward_span`, `b6_frequency_forward`, `b6_frequency_backward`, `b7_difference_frequency`. O sistema atual calcula escores z mas não retorna os campos com os nomes exatos da skill.

---

## Resumo das Prioridades de Correção

| # | Item | Status | Prioridade |
|---|------|--------|------------|
| 1 | Classificação de escores ponderados (limiares errados) | BUG | **Crítica** |
| 2 | Perfil dos escores (payload charts) | NÃO EXISTE | **Alta** |
| 3 | Facilidades/Dificuldades - subtestes faltando na média | BUG | **Alta** |
| 4 | Facilidades/Dificuldades - não retorna base_rate (B.3) | INCOMPLETO | **Alta** |
| 5 | Discrepância - não consulta B.2 para base_rate | INCOMPLETO | **Alta** |
| 6 | Discrepância - perde sinal da diferença | BUG | **Alta** |
| 7 | Discrepância - não gera interpretação textual | INCOMPLETO | **Alta** |
| 8 | Payload final não segue estrutura da skill (sums, composites, audit) | INCOMPLETO | **Média** |
| 9 | Proration (Tabela A.10) não implementado | NÃO EXISTE | **Média** |
| 10 | Substituição de subtestes não implementada | NÃO EXISTE | **Média** |
| 11 | Trilha de auditoria (audit) não implementada | NÃO EXISTE | **Média** |
| 12 | Dados de entrada (birth_date/application_date) não validados | INCOMPLETO | **Baixa** |

---

## Recomendação
As três áreas solicitadas (Perfil, Facilidades/Dificuldades, Discrepância) possuem lacunas significativas que precisam de correção para alinhamento completo com a skill. Recomendo implementar as correções na ordem de prioridade acima.
