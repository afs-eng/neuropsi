# SKILL SCARED — PADRÃO OURO

## Documento de Referência para Interpretação Clínica

---

## 1. DESCRIÇÃO DO INSTRUMENTO

### 1.1 Nome e Sigla

**SCARED** — Screen for Child Anxiety Related Emotional Disorders

### 1.2 Finalidade

O SCARED é um instrumento de **rastreio de sintomas ansiosos** em crianças e adolescentes, desenvolvido para identificar manifestações relacionadas a transtornos ansiosos na população infantojuvenil. Não se trata de instrumento diagnóstico isolado, mas sim de ferramenta de triagem que orienta a investigação clínica mais aprofundada.

### 1.3 População-Alvo

Crianças e adolescentes de **6 a 18 anos**, com versões diferenciadas para autorrelato e relato dos pais/cuidadores.

### 1.4 Versões

| Versão | Descrição | Aplicação |
|--------|-----------|-----------|
| **Autorrelato** | Respondido pela própria criança/adolescente | Idade recomendada: 8+ anos (ou conforme capacidade cognitiva) |
| **Pais/Cuidadores** | Respondido por responsável que conhece bem a criança | Para todas as idades |

### 1.5 Quando Aplicar Ambas as Versões

Recomenda-se a aplicação de ambas as versões quando:
- Há necessidade de triangulação de informações
- Existe divergência entre percepção da criança e dos responsáveis
- O quadro clínico requer investigação abrangente
- Há suspeita de sintomas internalizantes que podem não ser observados externamente

---

## 2. ESTRUTURA FATORIAL

### 2.1 Domínios Avaliados

O SCARED avalia **5 domínios específicos** de sintomas ansiosos, além do **escore total**:

| Código do Fator | Nome do Domínio | Itens | Escore Máximo (Pais) |
|-----------------|-----------------|-------|----------------------|
| `panico_sintomas_somaticos` | Pânico / Sintomas Somáticos | 1, 6, 9, 12, 15, 18, 19, 22, 24, 27, 30, 34, 38 | 26 |
| `ansiedade_generalizada` | Ansiedade Generalizada | 5, 7, 14, 21, 23, 28, 33, 35, 37 | 18 |
| `ansiedade_separacao` | Ansiedade de Separação | 4, 8, 13, 16, 20, 25, 29, 31 | 16 |
| `fobia_social` | Fobia Social | 3, 10, 26, 32, 39, 40, 41 | 14 |
| `evitacao_escolar` | Evitação Escolar | 2, 11, 17, 36 | 8 |
| `total` | Escore Total | 1-41 | 82 |

### 2.2 Itens por Domínio

**Pânico / Sintomas Somáticos (13 itens):**
1, 6, 9, 12, 15, 18, 19, 22, 24, 27, 30, 34, 38

**Ansiedade Generalizada (9 itens):**
5, 7, 14, 21, 23, 28, 33, 35, 37

**Ansiedade de Separação (8 itens):**
4, 8, 13, 16, 20, 25, 29, 31

**Fobia Social (7 itens):**
3, 10, 26, 32, 39, 40, 41

**Evitação Escolar (4 itens):**
2, 11, 17, 36

### 2.3 Distribuição de Itens

- **Total de itens:** 41
- **Escore máximo possível:** 82 pontos (cada item pontuado de 0 a 2)
- **Opções de resposta:**
  - 0 = "Nunca ou raramente verdadeiro"
  - 1 = "Algumas vezes verdadeiro"
  - 2 = "Bastante ou frequentemente verdadeiro"

---

## 3. REGRAS DE CÁLCULO E CLASSIFICAÇÃO

### 3.1 Fluxo de Processamento

```
1. raw_payload (respostas brutas)
      ↓
2. compute_scared_scores() → brutos por fator
      ↓
3. classify_scared_scores() → percentis (autorrelato) ou classificação clínica (pais)
      ↓
4. interpret_scared_results() → texto interpretativo
```

### 3.2 Cálculo de Escores Brutos

```python
def compute_scared_scores(raw_payload: dict, patient_age: int | None = None) -> dict:
    responses = raw_payload.get("responses", {})
    form = raw_payload.get("form", "child")
    resp_int = {int(k): int(v) for k, v in responses.items()}

    brutos = {}
    for fator, itens in FATORES.items():
        brutos[fator] = sum(resp_int.get(i, 0) for i in itens)

    brutos["total"] = sum(resp_int.get(i, 0) for i in FATORES_TOTAL)

    return {
        "form": form,
        "brutos": brutos,
        "gender": raw_payload.get("gender", "M"),
        "age": raw_payload.get("age", patient_age),
    }
```

### 3.3 Classificação — Versão Pais/Cuidadores

Para a versão de pais/cuidadores, utiliza-se **pontos de corte fixos** (não percentis):

| Fator | Ponto de Corte (Clínico) | Significado |
|-------|--------------------------|-------------|
| `panico_sintomas_somaticos` | ≥ 7 | Clínico |
| `ansiedade_generalizada` | ≥ 9 | Clínico |
| `ansiedade_separacao` | ≥ 5 | Clínico |
| `fobia_social` | ≥ 8 | Clínico |
| `evitacao_escolar` | ≥ 3 | Clínico |
| `total` | ≥ 25 | Clínico |

**Classificação resultante:** "Clínico" ou "Não clínico"

```python
if form == "parent":
    for fator in FATORES_ANALISE:
        bruto = brutos.get(fator, 0)
        corte = PAIS_CORTES.get(fator, 0)
        classificacao = "Clínico" if bruto >= corte else "Não clínico"
```

### 3.4 Classificação — Versão Autorrelato (Percentis)

Para o autorrelato, utiliza-se **normas por grupo etário e sexo**, calculando-se o **percentil** a partir da distribuição normal:

**Grupos Etários:**
- **Criança:** ≤ 12 anos
- **Adolescente:** > 12 anos

**Parâmetros Normativos:**

| Grupo | Sexo | Fator | Média | Desvio-Padrão |
|-------|------|-------|-------|---------------|
| Criança | Masculino | Total | 22.60 | 10.45 |
| Criança | Masculino | Pânico/Somático | 4.16 | 3.80 |
| Criança | Masculino | Ans. Generalizada | 7.24 | 3.57 |
| Criança | Masculino | Ans. Separação | 4.98 | 2.65 |
| Criança | Masculino | Fobia Social | 4.98 | 2.83 |
| Criança | Masculino | Evitação Escolar | 1.24 | 1.19 |
| Criança | Feminino | Total | 26.55 | 12.21 |
| Criança | Feminino | Pânico/Somático | 5.36 | 4.69 |
| Criança | Feminino | Ans. Generalizada | 8.03 | 3.70 |
| Criança | Feminino | Ans. Separação | 6.03 | 3.22 |
| Criança | Feminino | Fobia Social | 5.74 | 2.92 |
| Criança | Feminino | Evitação Escolar | 1.39 | 1.30 |
| Adolescente | Masculino | Total | 19.73 | 10.41 |
| Adolescente | Masculino | Pânico/Somático | 3.29 | 3.40 |
| Adolescente | Masculino | Ans. Generalizada | 7.51 | 3.73 |
| Adolescente | Masculino | Ans. Separação | 3.55 | 2.36 |
| Adolescente | Masculino | Fobia Social | 4.43 | 2.95 |
| Adolescente | Masculino | Evitação Escolar | 0.94 | 1.14 |
| Adolescente | Feminino | Total | 25.69 | 12.17 |
| Adolescente | Feminino | Pânico/Somático | 5.34 | 4.58 |
| Adolescente | Feminino | Ans. Generalizada | 8.87 | 3.78 |
| Adolescente | Feminino | Ans. Separação | 4.78 | 2.86 |
| Adolescente | Feminino | Fobia Social | 5.46 | 3.20 |
| Adolescente | Feminino | Evitação Escolar | 1.24 | 1.21 |

**Cálculo do Percentil:**

```python
def normal_cdf(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))

# Cálculo do Z-score
z = (bruto - media) / dp
percentil = normal_cdf(z) * 100
```

**Tabela de Classificação por Percentil:**

| Percentil | Classificação | Significado Clínico |
|-----------|----------------|----------------------|
| ≥ 95 | Muito Elevado | Dificuldade clínica elevada |
| ≥ 75 | Elevado | Dificuldade clínica moderada |
| 25-74 | Na Média | Dentro da normalidade |
| 10-24 | Médio Inferior | Dentro da normalidade |
| 5-9 | Baixo | Dentro da normalidade |
| < 5 | Muito Baixo | Dentro da normalidade |

```python
def percentil_para_classificacao(percentil: float) -> str:
    if percentil >= 95:
        return "Muito Elevado"
    if percentil >= 75:
        return "Elevado"
    if percentil >= 25:
        return "Na Média"
    if percentil >= 10:
        return "Médio Inferior"
    if percentil >= 5:
        return "Baixo"
    return "Muito Baixo"
```

---

## 4. INTERPRETAÇÃO CLÍNICA — PADRÃO OURO

### 4.1 Regras Fundamentais

1. **O SCARED é um instrumento de rastreio**, não diagnóstico. Os resultados indicam presença de sintomas, não confirmam transtorno.
2. **A interpretação deve ser integrada** à anamnese, observação clínica e demais instrumentos.
3. **Nunca diagnosticar com base apenas no SCARED.**
4. **Domínios elevados requerem investigação** mais aprofundada.
5. **Domínios dentro da normalidade não excluem** sintomas que podem não estar sendo captados pelo instrumento.

### 4.2 Regra Crítica de Nomenclatura

No texto final:
- Usar apenas o **primeiro nome** do paciente
- **Não utilizar** o termo "informante"
- Preferir "relato dos pais", "relato dos cuidadores", "percepção materna/paterna" ou "relato familiar"

### 4.3 Classificação Clínica por Versão

**Para Autorrelato:**
- Clínico = percentil ≥ 75 ("Elevado" ou "Muito Elevado")

**Para Pais/Cuidadores:**
- Clínico = escore bruto ≥ ponto de corte

```python
def _is_clinical(row: dict, form_type: str) -> bool:
    classification = (row.get("classificacao") or "").strip().lower()
    if form_type == "parent":
        return classification == "clínico" or classification == "clinico"
    return classification in {"elevado", "muito elevado"}
```

### 4.4 Interpretação por Domínio

#### 4.4.1 Pânico / Sintomas Somáticos

**Quando clínico:**
"O domínio de Pânico/Sintomas Somáticos apresentou classificação clínica, sugerindo presença de manifestações físicas associadas à ansiedade, como desconfortos somáticos recorrentes, sensação de tensão corporal, medo intenso ou sintomas compatíveis com episódios de pânico."

**Quando não clínico:**
"No domínio de Pânico/Sintomas Somáticos, a pontuação situou-se na faixa não clínica, não indicando presença relevante de sintomas físicos associados à ansiedade, crises de pânico ou desconfortos somáticos recorrentes relacionados ao estado emocional."

#### 4.4.2 Ansiedade Generalizada

**Quando clínico:**
"Em Ansiedade Generalizada, observou-se classificação clínica, sugerindo presença de preocupações excessivas, tendência à apreensão constante, dificuldade de relaxamento e antecipação ansiosa diante de diferentes demandas do cotidiano."

**Quando não clínico:**
"Em Ansiedade Generalizada, o resultado foi classificado como não clínico, não indicando preocupações excessivas, estado persistente de apreensão ou antecipação ansiosa significativa diante de múltiplas situações do cotidiano."

#### 4.4.3 Ansiedade de Separação

**Quando clínico:**
"No domínio de Ansiedade de Separação, observou-se classificação clínica, sugerindo presença de insegurança emocional em situações de afastamento das figuras de apego, com possível necessidade aumentada de proximidade, previsibilidade e suporte emocional em contextos de separação. Esse resultado pode estar relacionado a maior desconforto diante de afastamentos, preocupação com a ausência dos cuidadores ou necessidade intensificada de segurança emocional para lidar com situações de autonomia."

**Quando não clínico:**
"No domínio de Ansiedade de Separação, a pontuação foi classificada como não clínica, afastando indicativos de insegurança emocional relevante diante do afastamento das figuras de apego."

#### 4.4.4 Fobia Social

**Quando clínico:**
"Em Fobia Social, observou-se classificação clínica, indicando presença de desconforto relevante em situações de exposição, interação social ou avaliação por outras pessoas, com possível tendência à inibição, evitação ou sofrimento em contextos interpessoais."

**Quando não clínico:**
"Em Fobia Social, o resultado foi classificado como não clínico, afastando indicativos de inibição social importante, medo acentuado de exposição ou desconforto significativo em interações sociais."

#### 4.4.5 Evitação Escolar

**Quando clínico:**
"O domínio de Evitação Escolar apresentou classificação clínica, sugerindo desconforto emocional relevante diante do contexto escolar, com possível tendência à recusa, resistência ou sofrimento associado à frequência e permanência na escola."

**Quando não clínico:**
"O domínio de Evitação Escolar apresentou pontuação não clínica, não sugerindo recusa escolar ou ansiedade relevante associada ao ambiente escolar."

### 4.5 Interpretação do Escore Total

**Quando clínico:**
"Os resultados indicaram presença de sintomas ansiosos em nível global, conforme evidenciado pelo escore total em faixa clínica, sugerindo comprometimento emocional mais abrangente [no autorrelato / segundo o relato dos pais/cuidadores]."

**Quando não clínico:**
"Os resultados indicaram ausência de quadro ansioso global, conforme evidenciado pelo escore total abaixo do ponto de corte ou sem elevação clínica relevante, sugerindo funcionamento emocional geral dentro dos limites esperados [no autorrelato / segundo o relato dos pais/cuidadores]."

### 4.6 Parágrafo de Análise Clínica

**Quando nenhum domínio está elevado:**
"Em análise clínica, o perfil emocional de [nome] não revela indicadores consistentes de quadro ansioso clinicamente significativo, mantendo-se dentro dos limites esperados no conjunto dos domínios investigados."

**Quando apenas um domínio está elevado:**
"Em análise clínica, o perfil emocional de [nome] revela sintomas ansiosos específicos e circunscritos ao domínio de [domínio], sem evidências de comprometimento ansioso amplo nos demais eixos avaliados. Esse padrão sugere manifestação ansiosa mais focal, relacionada a situações específicas do funcionamento emocional."

**Quando múltiplos domínios estão elevados:**
"Em análise clínica, o perfil emocional de [nome] revela sintomatologia ansiosa distribuída em múltiplos domínios, indicando sofrimento emocional mais abrangente e com potencial repercussão sobre o funcionamento adaptativo, relacional e acadêmico."

---

## 5. HIPÓTESE DIAGNÓSTICA

### 5.1 Regra de Aplicação

A expressão **"Há hipótese diagnóstica de..."** deve ser utilizada quando há elevação clínica significativa. A hipótese deve ser **sempre qualificada** pelo domínio predominante.

### 5.2 Modelos de Hipótese

**Múltiplos domínios elevados:**
" Há hipótese diagnóstica de sintomatologia ansiosa clinicamente relevante, com manifestações em múltiplos domínios, devendo o quadro ser interpretado de forma integrada à anamnese, à observação clínica e aos demais instrumentos aplicados."

**Ansiedade de Separação:**
" Há hipótese diagnóstica de sintomatologia ansiosa relacionada à ansiedade de separação, em nível circunscrito, devendo esse achado ser interpretado de forma integrada aos demais dados clínicos e contextuais da avaliação."

**Fobia Social:**
" Há hipótese diagnóstica de sintomatologia ansiosa relacionada à fobia social, devendo esse achado ser interpretado em conjunto com os dados observacionais, escolares e clínicos da avaliação."

**Ansiedade Generalizada:**
" Há hipótese diagnóstica de sintomatologia ansiosa com predomínio de ansiedade generalizada, considerando a presença de preocupações excessivas e apprehension persistente com repercussão funcional."

**Circunscrito (outros):**
" Há hipótese diagnóstica de sintomatologia ansiosa em nível circunscrito, devendo esse achado ser interpretado de forma integrada aos demais dados clínicos e contextuais da avaliação."

### 5.3 Quando NÃO incluir hipótese

Quando nenhum domínio apresentar classificação clínica, **não incluir** hipótese diagnóstica.

---

## 6. INTEGRAÇÃO ENTRE VERSÕES

### 6.1 Quando ambas indicam elevação

"A convergência entre o autorrelato e o relato familiar fortalece a compreensão de que os sintomas ansiosos apresentam consistência clínica e repercussão funcional em diferentes contextos."

### 6.2 Quando apenas o autorrelato indica elevação

"A elevação observada no autorrelato, em contraste com menor percepção familiar, sugere que parte do sofrimento ansioso pode ocorrer de forma internalizada, sem manifestação comportamental evidente ou constante no ambiente familiar."

### 6.3 Quando apenas pais/cuidadores indicam elevação

"A elevação observada no relato familiar, em contraste com menor autopercepção dos sintomas, pode indicar baixa consciência emocional, minimização subjetiva das dificuldades ou maior expressão dos sintomas ansiosos em contextos observados pelos responsáveis."

### 6.4 Quando nenhuma indica elevação

"A ausência de elevações clínicas no autorrelato e no relato familiar sugere que, no momento da avaliação, não há indicadores consistentes de quadro ansioso global pelo instrumento aplicado."

---

## 7. INTEGRAÇÃO COM OUTROS INSTRUMENTOS

### 7.1 SCARED + EBADEP-IJ (Depressão)

**Quando houver sintomas ansiosos e depressivos:**
"Os achados sugerem sofrimento internalizante, com associação entre sintomas ansiosos e humor rebaixado."

### 7.2 SCARED + EPQ-J (Personalidade - Neuroticismo)

**Quando houver neuroticismo elevado:**
"O perfil de maior sensibilidade emocional pode intensificar a vivência subjetiva de preocupação, insegurança e tensão emocional."

### 7.3 SCARED + SRS-2 (Autismo)

**Quando houver TEA ou traços autísticos:**
"Parte das manifestações ansiosas pode estar associada à sobrecarga social, rigidez cognitiva, sensibilidade sensorial e dificuldades de previsibilidade ambiental."

### 7.4 SCARED + TDAH

**Quando houver TDAH:**
"As manifestações ansiosas podem ser intensificadas por dificuldades de autorregulação, falhas de organização, experiências de frustração e maior exposição a cobranças acadêmicas ou comportamentais."

---

## 8. TEMPLATES DE INTERPRETAÇÃO

### 8.1 Template 1 — Sem Elevação Clínica Significativa

A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar.

Os resultados obtidos não indicaram elevação clínica significativa na pontuação total nem nos domínios específicos avaliados. Esse padrão sugere ausência de indicadores consistentes de sofrimento ansioso global no momento da avaliação, considerando os parâmetros do instrumento. Ainda assim, a interpretação deve ser compreendida em conjunto com a anamnese, a observação clínica e os demais instrumentos aplicados, uma vez que manifestações emocionais podem variar conforme o contexto, o vínculo, a demanda ambiental e o momento do desenvolvimento.

Em análise clínica, o perfil emocional de [nome] não revela indicadores consistentes de quadro ansioso clinicamente significativo, mantendo-se dentro dos limites esperados no conjunto dos domínios investigados.

### 8.2 Template 2 — Elevação Específica em Ansiedade de Separação

A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar.

O perfil obtido não indica quadro ansioso global, porém evidencia elevação específica em ansiedade de separação. Esse achado sugere vulnerabilidade emocional em situações de afastamento das figuras de apego, podendo envolver insegurança, necessidade aumentada de proximidade, preocupação com separações e maior desconforto em contextos que exigem autonomia emocional.

Em análise clínica, o perfil emocional de [nome] revela sintomas ansiosos específicos e circunscritos ao domínio de Ansiedade de Separação, sem evidências de comprometimento ansioso amplo nos demais eixos avaliados. Há hipótese diagnóstica de sintomatologia ansiosa relacionada à ansiedade de separação, em nível circunscrito, devendo esse achado ser interpretado de forma integrada aos demais dados clínicos e contextuais da avaliação.

### 8.3 Template 3 — Ansiedade Generalizada Predominante

A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar.

Os resultados indicaram elevação clínica em sintomas compatíveis com ansiedade generalizada, sugerindo padrão de preocupação excessiva, antecipação negativa, tensão subjetiva e dificuldade de relaxamento diante de demandas cotidianas. Esse perfil pode repercutir na autoconfiança, na tolerância a erros, na tomada de decisão e na capacidade de lidar com incertezas.

Em análise clínica, o perfil emocional de [nome] revela sintomatologia ansiosa com predomínio de ansiedade generalizada. Há hipótese diagnóstica de sintomatologia ansiosa com predomínio de ansiedade generalizada, considerando a presença de preocupações excessivas e apreensão persistente com repercussão funcional, devendo tal hipótese ser confirmada pela integração entre os dados da escala, anamnese, observação clínica e prejuízo funcional.

### 8.4 Template 4 — Ansiedade Social / Fobia Social

A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar.

O perfil obtido evidenciou elevação em ansiedade social, sugerindo desconforto significativo em situações de exposição interpessoal, avaliação social, interação com pares ou participação em atividades coletivas. Esse padrão pode estar associado a retraimento, evitação de interações, medo de julgamento e maior inibição em contextos sociais ou escolares.

Em análise clínica, o perfil emocional de [nome] revela sintomatologia ansiosa com predomínio de ansiedade social. Há hipótese diagnóstica de sintomatologia ansiosa relacionada à fobia social, devendo esse achado ser interpretado em conjunto com os dados observacionais, escolares e clínicos da avaliação.

### 8.5 Template 5 — Evitação Escolar

A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar.

Os resultados indicaram elevação em evitação escolar, sugerindo sofrimento emocional associado ao contexto acadêmico. Esse achado pode refletir ansiedade diante de exigências escolares, dificuldades de adaptação, medo de desempenho, desconforto social ou sobrecarga emocional relacionada ao ambiente educacional. A interpretação deve considerar se a evitação está associada a dificuldades de aprendizagem, experiências sociais negativas, bullying, rigidez comportamental, sobrecarga sensorial ou sintomas ansiosos mais amplos.

Em análise clínica, o perfil emocional de [nome] revela sintomatologia ansiosa com repercussão no contexto escolar. Há hipótese diagnóstica de sintomatologia ansiosa com repercussão escolar, exigindo investigação complementar das condições ambientais, acadêmicas e socioemocionais envolvidas.

### 8.6 Template 6 — Múltiplas Elevações Clínicas

A Escala SCARED foi aplicada com o objetivo de rastrear sintomas ansiosos em crianças e adolescentes, investigando manifestações relacionadas à ansiedade generalizada, ansiedade de separação, ansiedade social, sintomas de pânico/somatização e evitação escolar.

Os resultados evidenciaram elevações clinicamente relevantes em múltiplos domínios, indicando sofrimento ansioso significativo e multifatorial. Observam-se indicadores associados a preocupação excessiva, insegurança emocional, desconforto social, manifestações somáticas de ansiedade e possível evitação de contextos escolares. Esse conjunto sugere que os sintomas ansiosos não se restringem a uma situação específica, apresentando maior amplitude e potencial impacto sobre o funcionamento emocional, social e acadêmico.

Em análise clínica, o perfil emocional de [nome] revela sintomatologia ansiosa distribuída em múltiplos domínios, indicando sofrimento emocional mais abrangente e com potencial repercussão sobre o funcionamento adaptativo, relacional e acadêmico. Há hipótese diagnóstica de transtorno ansioso, devendo ser especificado o padrão predominante conforme a integração dos resultados, da anamnese, da observação clínica e do prejuízo funcional identificado.

---

## 9. CÓDIGO DE INTERPRETAÇÃO (ALGORITMO BASE)

O seguinte código Python constitui o algoritmo de interpretação implementado no sistema:

```python
def interpret_scared_results(merged_data: dict, patient_name: str = "") -> str:
    rows = {row.get("fator"): row for row in merged_data.get("analise_geral", [])}
    if not rows:
        return "Sem resultados para interpretação."

    form_type = merged_data.get("form_type") or "child"
    source_phrase = _source_phrase(form_type)
    name = _first_name(patient_name)

    total_row = rows.get("total", {})
    total_clinical = _is_clinical(total_row, form_type)

    paragraphs = [_opening_paragraph(form_type)]

    if total_clinical:
        paragraphs.append(
            f"Os resultados indicaram presença de sintomas ansiosos em nível global, "
            f"conforme evidenciado pelo escore total em faixa clínica, sugerindo "
            f"comprometimento emocional mais abrangente {source_phrase}."
        )
    else:
        paragraphs.append(
            f"Os resultados indicaram ausência de quadro ansioso global, conforme "
            f"evidenciado pelo escore total abaixo do ponto de corte ou sem elevação "
            f"clínica relevante, sugerindo funcionamento emocional geral dentro dos "
            f"limites esperados {source_phrase}."
        )

    # Domínios individuais...
    # [Código completo em interpreters.py]

    # Identificação de domínios alterados
    altered_domains = [
        FATORES_DISPLAY_NAMES.get(key, key)
        for key, row in rows.items()
        if key != "total" and _is_clinical(row, form_type)
    ]

    # Parágrafo final
    if not altered_domains:
        final_paragraph = (
            f"Em análise clínica, o perfil emocional de {name} não revela indicadores "
            f"consistentes de quadro ansioso clinicamente significativo, mantendo-se "
            f"dentro dos limites esperados no conjunto dos domínios investigados."
        )
    elif len(altered_domains) == 1:
        domain_name = altered_domains[0]
        final_paragraph = (
            f"Em análise clínica, o perfil emocional de {name} revela sintomas ansiosos "
            f"específicos e circunscritos ao domínio de {domain_name}, sem evidências "
            f"de comprometimento ansioso amplo nos demais eixos avaliados. Esse padrão "
            f"sugere manifestação ansiosa mais focal, relacionada a situações específicas "
            f"do funcionamento emocional."
        )
    else:
        final_paragraph = (
            f"Em análise clínica, o perfil emocional de {name} revela sintomatologia "
            f"ansiosa distribuída em múltiplos domínios, indicando sofrimento emocional "
            f"mais abrangente e com potencial repercussão sobre o funcionamento adaptativo, "
            f"relacional e acadêmico."
        )

    # Hipótese diagnóstica
    hypothesis = ""
    if len(altered_domains) > 1 or total_clinical:
        hypothesis = (
            " Há hipótese diagnóstica de sintomatologia ansiosa clinicamente relevante, "
            "com manifestações em múltiplos domínios, devendo o quadro ser interpretado "
            "de forma integrada à anamnese, à observação clínica e aos demais instrumentos "
            "aplicados."
        )
    elif altered_domains:
        # [Lógica específica por domínio]

    paragraphs.append(final_paragraph + hypothesis)
    return "\n\n".join(paragraphs)
```

---

## 10. FORMATO DE SAÍDA

### 10.1 Características do Texto Final

- **Texto corrido** (não tabelas, não tópicos)
- **Sem excesso de pontuações numéricas** no corpo interpretativo
- **Linguagem clínica adequada** para laudo neuropsicológico
- **Pronto para inserção direta** no laudo

### 10.2 Estrutura Obrigatória

1. **Abertura:** Descrição do instrumento e propósito
2. **Resultados:** Domínios com e sem alteração (sem excesso de números)
3. **Integração:** Análise funcional dos achados
4. **Fechamento:** Hipótese diagnóstica (quando aplicável)

### 10.3 O que EVITAR

- "O SCARED diagnosticou..."
- "A criança tem ansiedade" sem integração clínica
- "Resultado normal" de forma simplista
- Usar o termo "informante"
- Excesso de dados numéricos no texto interpretativo

### 10.4 O que PREFERIR

- "Os achados sugerem..."
- "O perfil indica..."
- "Há indicadores compatíveis com..."
- "Em análise clínica..."
- "A hipótese deve ser compreendida de forma integrada..."

---

## 11. RESUMO OPERACIONAL

| Passo | Ação | Ferramenta |
|-------|------|------------|
| 1 | Receber raw_payload (responses, form, age, gender) | calculators.py |
| 2 | Calcular escores brutos por fator | calculators.py |
| 3 | Classificar (percentis para autorrelato, cortes para pais) | classifiers.py |
| 4 | Gerar texto interpretativo | interpreters.py |
| 5 | Inserir hipóteses diagnósticas conforme domínios elevados | interpreters.py |
| 6 | Se aplicável, integrar com outras versões e instrumentos | Skill completa |

---

## 12. REFERÊNCIAS

- Birmaher, B., et al. (1997). Psychometric properties of the Screen for Child Anxiety Related Emotional Disorders (SCARED): A replication study. *Journal of the American Academy of Child & Adolescent Psychiatry*, 36(5), 645-652.
- Birmaher, B., et al. (1999). The Screen for Child Anxiety Related Emotional Disorders (SCARED): Scale construction and psychometric characteristics. *Journal of the American Academy of Child & Adolescent Psychiatry*, 38(10), 1230-1236.
- Asbahr, F. R., et al. (2005). Brazilian Portuguese version of the Screen for Child Anxiety Related Emotional Disorders (SCARED). *Journal of Anxiety Disorders*, 19(2), 175-187.

---

*Documento de referência para interpretação clínica do SCARED — Versão 1.0*
*Este documento deve ser utilizado em conjunto com o código Python em apps/tests/scared/interpreters.py*