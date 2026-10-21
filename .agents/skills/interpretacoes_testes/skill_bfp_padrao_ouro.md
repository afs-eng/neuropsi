# SKILL_BFP_PADRAO_OURO.md

## 1. Objetivo da skill

Implementar no sistema a interpretação do **BFP – Bateria Fatorial de Personalidade**, em padrão técnico, clínico e auditável, para uso em laudos psicológicos e neuropsicológicos.

A skill deve orientar a IA e o backend a:

1. Receber resultados brutos, percentis, escores padronizados e classificações dos fatores e facetas.
2. Validar se os cinco fatores principais estão presentes.
3. Interpretar cada fator de personalidade de forma técnica, descritiva e contextualizada.
4. Interpretar facetas quando disponíveis.
5. Integrar o perfil de personalidade ao funcionamento emocional, comportamental, interpessoal e autorregulatório.
6. Evitar inferências diagnósticas isoladas.
7. Gerar texto compatível com laudo psicológico/neuropsicológico.

---

## 2. Estrutura geral do BFP

O BFP avalia traços de personalidade com base no modelo dos Cinco Grandes Fatores.

Fatores principais:

1. **Neuroticismo**
2. **Extroversão**
3. **Socialização**
4. **Realização**
5. **Abertura à Experiência**

Cada fator deve ser interpretado considerando:

- escore bruto;
- percentil;
- classificação;
- facetas associadas;
- consistência entre fatores;
- dados da anamnese;
- observação clínica;
- demais instrumentos aplicados.

---

## 3. Input esperado

```json
{
  "patient_name": "Paciente",
  "test": "BFP",
  "results": {
    "neuroticismo": {
      "raw": 85,
      "percentile": 90,
      "classification": "Superior",
      "facets": {
        "vulnerabilidade": {"percentile": 88, "classification": "Superior"},
        "instabilidade_emocional": {"percentile": 92, "classification": "Superior"},
        "passividade": {"percentile": 70, "classification": "Média Superior"},
        "depressao": {"percentile": 85, "classification": "Superior"}
      }
    },
    "extroversao": {"percentile": 35, "classification": "Média Inferior"},
    "socializacao": {"percentile": 50, "classification": "Média"},
    "realizacao": {"percentile": 25, "classification": "Média Inferior"},
    "abertura": {"percentile": 60, "classification": "Média"}
  }
}
```

---

## 4. Classificação interpretativa

```python
BFP_CLASSIFICATION_MEANING = {
    "Muito Baixo": "traço muito reduzido em relação à amostra normativa",
    "Baixo": "traço reduzido em relação à amostra normativa",
    "Média Inferior": "tendência discretamente reduzida, ainda próxima da faixa esperada",
    "Média": "funcionamento compatível com a média normativa",
    "Média Superior": "tendência aumentada em relação à média normativa",
    "Superior": "traço elevado em relação à amostra normativa",
    "Muito Superior": "traço muito elevado em relação à amostra normativa"
}
```

A IA deve evitar linguagem determinista. Usar:

- “sugere tendência a...”
- “pode indicar maior propensão a...”
- “esse padrão é compatível com...”
- “deve ser interpretado em conjunto com...”

Evitar:

- “o paciente é...”
- “comprova...”
- “fecha diagnóstico...”
- “determina que...”

---

# 5. Interpretação dos fatores principais

## 5.1 Neuroticismo

### Definição clínica

Avalia instabilidade emocional, reatividade afetiva, vulnerabilidade ao estresse, sensibilidade a críticas, propensão à ansiedade, insegurança, oscilação de humor e vivência subjetiva de sofrimento emocional.

### Neuroticismo elevado

```text
O fator Neuroticismo apresentou classificação [classificação], sugerindo maior tendência à reatividade emocional, sensibilidade ao estresse e vivência mais intensa de afetos negativos. Esse padrão pode se manifestar por preocupações frequentes, insegurança, oscilação emocional e maior dificuldade em lidar com frustrações ou situações de pressão. Em análise clínica, esse resultado deve ser integrado aos dados da anamnese, observação comportamental e demais instrumentos emocionais aplicados.
```

### Neuroticismo médio

```text
O fator Neuroticismo situou-se na faixa média, indicando funcionamento emocional compatível com o esperado para a amostra normativa. Esse resultado sugere equilíbrio relativo na vivência de emoções negativas, sem indicativos psicométricos de reatividade emocional acentuada ou vulnerabilidade emocional clinicamente expressiva nesse fator.
```

### Neuroticismo baixo

```text
O fator Neuroticismo apresentou classificação reduzida, sugerindo menor tendência à instabilidade emocional, menor reatividade a situações de estresse e maior estabilidade afetiva. Esse padrão pode estar associado a maior controle emocional e menor propensão a vivenciar emoções negativas de forma intensa, devendo ser interpretado em conjunto com os demais fatores de personalidade e dados clínicos.
```

---

## 5.2 Extroversão

### Definição clínica

Avalia sociabilidade, iniciativa interpessoal, comunicação, assertividade, energia social, busca por estimulação e expressão afetiva positiva.

### Extroversão elevada

```text
O fator Extroversão apresentou classificação [classificação], sugerindo maior tendência à sociabilidade, iniciativa interpessoal, expressividade comunicativa e busca por interação social. Esse perfil pode favorecer facilidade para estabelecer contatos, participar de atividades em grupo e expressar emoções de forma mais aberta.
```

### Extroversão média

```text
O fator Extroversão situou-se na faixa média, indicando repertório social compatível com o esperado para a amostra normativa. Esse resultado sugere equilíbrio entre momentos de interação social e reserva pessoal, sem indicativos de retraimento ou expansividade excessiva nesse fator.
```

### Extroversão baixa

```text
O fator Extroversão apresentou classificação reduzida, sugerindo tendência a menor busca por interação social, maior reserva interpessoal e menor expressividade em contextos sociais. Esse padrão pode estar associado a preferência por atividades mais individualizadas, menor iniciativa social ou postura mais introspectiva, devendo ser interpretado em conjunto com dados de anamnese e observação clínica.
```

---

## 5.3 Socialização

### Definição clínica

Avalia qualidade das relações interpessoais, empatia, confiança, cooperação, altruísmo, cordialidade, respeito a normas sociais e tendência à convivência harmoniosa.

### Socialização elevada

```text
O fator Socialização apresentou classificação [classificação], sugerindo tendência a maior empatia, cooperação, cordialidade e preocupação com o bem-estar de outras pessoas. Esse perfil pode favorecer relações interpessoais mais colaborativas, postura conciliadora e maior sensibilidade às demandas sociais.
```

### Socialização média

```text
O fator Socialização situou-se na faixa média, indicando funcionamento interpessoal compatível com o esperado para a amostra normativa. Esse resultado sugere equilíbrio entre cooperação, assertividade e consideração pelas necessidades de outras pessoas.
```

### Socialização baixa

```text
O fator Socialização apresentou classificação reduzida, sugerindo tendência a menor confiança interpessoal, menor complacência ou maior postura crítica nas relações. Esse padrão pode se associar a dificuldades de cooperação, menor tolerância a frustrações interpessoais ou maior tendência a conflitos, devendo ser analisado com cautela e integrado ao contexto clínico.
```

---

## 5.4 Realização

### Definição clínica

Avalia organização, disciplina, persistência, responsabilidade, planejamento, empenho, cumprimento de metas e autorregulação comportamental.

### Realização elevada

```text
O fator Realização apresentou classificação [classificação], sugerindo maior tendência à organização, responsabilidade, persistência e orientação para metas. Esse perfil pode favorecer planejamento, cumprimento de tarefas, disciplina e maior compromisso com demandas acadêmicas, profissionais ou cotidianas.
```

### Realização média

```text
O fator Realização situou-se na faixa média, indicando recursos de organização, persistência e responsabilidade compatíveis com o esperado para a amostra normativa. Esse padrão sugere funcionamento autorregulatório globalmente adequado nesse fator.
```

### Realização baixa

```text
O fator Realização apresentou classificação reduzida, sugerindo tendência a menor organização, menor persistência diante de tarefas prolongadas e maior dificuldade em manter planejamento ou rotina. Esse padrão pode impactar demandas que exigem disciplina, constância, gerenciamento de tempo e cumprimento de metas, devendo ser integrado aos dados atencionais e executivos da avaliação.
```

---

## 5.5 Abertura à Experiência

### Definição clínica

Avalia curiosidade intelectual, imaginação, flexibilidade cognitiva, criatividade, interesse por novidades, sensibilidade estética e disposição para experiências novas.

### Abertura elevada

```text
O fator Abertura à Experiência apresentou classificação [classificação], sugerindo maior curiosidade intelectual, criatividade, flexibilidade cognitiva e interesse por experiências novas. Esse perfil pode favorecer adaptação a contextos inovadores, pensamento imaginativo e busca por aprendizagem ou exploração de ideias.
```

### Abertura média

```text
O fator Abertura à Experiência situou-se na faixa média, indicando equilíbrio entre interesse por novidades e preferência por situações familiares. Esse resultado sugere flexibilidade compatível com o esperado para a amostra normativa.
```

### Abertura baixa

```text
O fator Abertura à Experiência apresentou classificação reduzida, sugerindo tendência a maior preferência por rotinas conhecidas, menor busca por novidades e postura mais convencional diante de mudanças. Esse padrão pode estar associado a maior necessidade de previsibilidade e menor flexibilidade frente a situações novas, devendo ser interpretado no contexto clínico global.
```

---

# 6. Facetas do BFP

Quando disponíveis, as facetas devem especificar o fator principal, sem repetição excessiva.

## 6.1 Neuroticismo

### Vulnerabilidade

```text
A faceta Vulnerabilidade apresentou classificação [classificação], sugerindo maior sensibilidade diante de situações adversas e possível percepção de menor recurso pessoal para lidar com estressores.
```

### Instabilidade Emocional

```text
A faceta Instabilidade Emocional apresentou classificação [classificação], indicando maior tendência a oscilações afetivas e respostas emocionais intensificadas diante de eventos cotidianos.
```

### Passividade

```text
A faceta Passividade apresentou classificação [classificação], sugerindo tendência a menor iniciativa ou maior dificuldade em agir de forma ativa diante de demandas e situações de pressão.
```

### Depressão

```text
A faceta Depressão apresentou classificação [classificação], sugerindo presença aumentada de indicadores subjetivos de desânimo, pessimismo ou menor vitalidade emocional, devendo ser analisada em conjunto com instrumentos específicos de humor.
```

---

## 6.2 Extroversão

### Comunicação

```text
A faceta Comunicação apresentou classificação [classificação], sugerindo [maior/menor] facilidade para expressão verbal, interação e compartilhamento de ideias em contextos sociais.
```

### Altivez

```text
A faceta Altivez apresentou classificação [classificação], indicando tendência relacionada à autoconfiança, exposição pessoal e percepção de valor próprio nas relações sociais.
```

### Dinamismo

```text
A faceta Dinamismo apresentou classificação [classificação], sugerindo nível [aumentado/reduzido] de energia, iniciativa e ritmo de envolvimento em atividades.
```

### Interações Sociais

```text
A faceta Interações Sociais apresentou classificação [classificação], sugerindo tendência [a maior busca/menor busca] por contato interpessoal e participação em situações sociais.
```

---

## 6.3 Socialização

### Amabilidade

```text
A faceta Amabilidade apresentou classificação [classificação], sugerindo tendência [a maior/menor] cordialidade, acolhimento e disponibilidade nas relações interpessoais.
```

### Pró-sociabilidade

```text
A faceta Pró-sociabilidade apresentou classificação [classificação], indicando tendência [a maior/menor] consideração por regras sociais, cooperação e condutas voltadas à convivência harmoniosa.
```

### Confiança nas Pessoas

```text
A faceta Confiança nas Pessoas apresentou classificação [classificação], sugerindo tendência [a maior/menor] abertura para confiar em outras pessoas e interpretar intenções interpessoais de forma positiva.
```

---

## 6.4 Realização

### Competência

```text
A faceta Competência apresentou classificação [classificação], sugerindo percepção [mais elevada/mais reduzida] de eficácia pessoal, capacidade de realização e segurança para executar tarefas.
```

### Ponderação

```text
A faceta Ponderação apresentou classificação [classificação], indicando tendência [a maior/menor] reflexão antes de agir, planejamento e controle de respostas impulsivas.
```

### Empenho

```text
A faceta Empenho apresentou classificação [classificação], sugerindo tendência [a maior/menor] persistência, dedicação e manutenção de esforço em atividades dirigidas a objetivos.
```

---

## 6.5 Abertura à Experiência

### Abertura a Ideias

```text
A faceta Abertura a Ideias apresentou classificação [classificação], sugerindo tendência [a maior/menor] curiosidade intelectual, interesse por conceitos abstratos e exploração de novas formas de pensamento.
```

### Liberalismo

```text
A faceta Liberalismo apresentou classificação [classificação], indicando tendência [a maior/menor] flexibilidade frente a valores, costumes e perspectivas diferentes das habituais.
```

### Busca por Novidades

```text
A faceta Busca por Novidades apresentou classificação [classificação], sugerindo tendência [a maior/menor] interesse por experiências novas, mudanças e situações pouco rotineiras.
```

---

# 7. Integração clínica

A IA deve integrar o BFP com:

- sintomas emocionais;
- queixas de ansiedade ou humor;
- funcionamento atencional;
- funções executivas;
- comportamento adaptativo;
- histórico escolar/profissional;
- dados de entrevista;
- observação clínica.

## Neuroticismo elevado + Realização baixa

```text
A combinação entre elevação em Neuroticismo e redução em Realização pode sugerir maior vulnerabilidade emocional associada a dificuldades de organização, persistência e autorregulação comportamental. Esse padrão pode impactar o manejo de demandas cotidianas, sobretudo em situações que exigem planejamento, tolerância à frustração e manutenção de esforço.
```

## Neuroticismo elevado + Extroversão baixa

```text
A elevação em Neuroticismo associada à redução em Extroversão pode indicar maior tendência à vivência interna de sofrimento emocional, com menor busca espontânea por apoio social ou maior reserva interpessoal. Esse padrão pode contribuir para retraimento, ruminação ou dificuldade de expressão emocional.
```

## Socialização baixa + Neuroticismo elevado

```text
A combinação entre menor Socialização e maior Neuroticismo pode sugerir maior vulnerabilidade a conflitos interpessoais, sensibilidade a críticas e dificuldade de regulação emocional em contextos relacionais.
```

## Realização baixa + desempenho atencional/executivo rebaixado

```text
A redução em Realização, quando associada a prejuízos atencionais ou executivos em instrumentos cognitivos, pode reforçar a hipótese de dificuldades funcionais em planejamento, organização, persistência e gerenciamento de tarefas.
```

## Abertura baixa + rigidez comportamental

```text
A redução em Abertura à Experiência, quando compatível com dados clínicos de rigidez ou baixa flexibilidade, pode sugerir maior preferência por previsibilidade, rotinas conhecidas e menor tolerância a mudanças.
```

---

# 8. Estrutura do texto final

O texto final deve seguir esta ordem:

1. Apresentação do instrumento.
2. Síntese dos fatores principais.
3. Interpretação dos fatores clinicamente relevantes.
4. Interpretação das facetas alteradas.
5. Integração entre fatores.
6. Fechamento clínico cauteloso.

Modelo:

```text
A Bateria Fatorial de Personalidade (BFP) foi utilizada para investigar traços de personalidade com base no modelo dos Cinco Grandes Fatores, permitindo compreender tendências emocionais, interpessoais, motivacionais e comportamentais.

[Nome] apresentou elevação em [fator], sugerindo [interpretação]. Também se observou [resultado em outro fator], indicando [interpretação].

Nas facetas, destacaram-se [facetas relevantes], o que sugere [interpretação integrada].

Em análise clínica, o perfil de personalidade indica [síntese]. Esses achados devem ser compreendidos como tendências de funcionamento psicológico, não constituindo, isoladamente, diagnóstico psicopatológico.
```

---

# 9. Regras de segurança interpretativa

A IA nunca deve:

1. Fechar diagnóstico com base apenas no BFP.
2. Usar linguagem moralizante.
3. Transformar traços em rótulos fixos.
4. Ignorar contexto sociocultural.
5. Ignorar idade, escolaridade e condições clínicas.
6. Interpretar percentil isoladamente sem classificação.
7. Criar facetas inexistentes.
8. Dizer que o teste “prova” determinada condição.
9. Usar o BFP como diagnóstico de transtorno de personalidade sem integração clínica ampla.

---

# 10. Funções sugeridas para implementação

## 10.1 Classificação geral

```python
def classify_bfp_domain(classification: str) -> str:
    high = ["Média Superior", "Superior", "Muito Superior"]
    low = ["Média Inferior", "Baixo", "Muito Baixo"]

    if classification in high:
        return "elevado"

    if classification in low:
        return "reduzido"

    return "médio"
```

## 10.2 Identificação de fatores clinicamente relevantes

```python
def get_relevant_bfp_factors(results: dict) -> dict:
    relevant = {}

    for factor, data in results.items():
        classification = data.get("classification")
        level = classify_bfp_domain(classification)

        if level != "médio":
            relevant[factor] = {
                "classification": classification,
                "level": level,
                "percentile": data.get("percentile")
            }

    return relevant
```

## 10.3 Interpretação automática do fator

```python
def interpret_bfp_factor(factor: str, classification: str, patient_name: str) -> str:
    level = classify_bfp_domain(classification)

    templates = {
        "neuroticismo": {
            "elevado": f"O fator Neuroticismo apresentou classificação {classification}, sugerindo maior tendência à reatividade emocional, sensibilidade ao estresse e vivência mais intensa de afetos negativos.",
            "médio": f"O fator Neuroticismo situou-se na faixa média, indicando funcionamento emocional compatível com o esperado para a amostra normativa.",
            "reduzido": f"O fator Neuroticismo apresentou classificação {classification}, sugerindo menor tendência à instabilidade emocional e maior estabilidade afetiva."
        },
        "extroversao": {
            "elevado": f"O fator Extroversão apresentou classificação {classification}, sugerindo maior sociabilidade, expressividade comunicativa e busca por interação social.",
            "médio": f"O fator Extroversão situou-se na faixa média, indicando equilíbrio entre interação social e reserva pessoal.",
            "reduzido": f"O fator Extroversão apresentou classificação {classification}, sugerindo maior reserva interpessoal, menor busca por interação social e postura mais introspectiva."
        },
        "socializacao": {
            "elevado": f"O fator Socialização apresentou classificação {classification}, sugerindo maior empatia, cooperação e cordialidade nas relações interpessoais.",
            "médio": f"O fator Socialização situou-se na faixa média, indicando funcionamento interpessoal compatível com o esperado.",
            "reduzido": f"O fator Socialização apresentou classificação {classification}, sugerindo menor confiança interpessoal, maior postura crítica ou menor tendência à cooperação."
        },
        "realizacao": {
            "elevado": f"O fator Realização apresentou classificação {classification}, sugerindo maior organização, responsabilidade, persistência e orientação para metas.",
            "médio": f"O fator Realização situou-se na faixa média, indicando recursos de organização e persistência compatíveis com o esperado.",
            "reduzido": f"O fator Realização apresentou classificação {classification}, sugerindo menor organização, menor persistência e maior dificuldade em manter planejamento ou rotina."
        },
        "abertura": {
            "elevado": f"O fator Abertura à Experiência apresentou classificação {classification}, sugerindo maior curiosidade intelectual, criatividade e flexibilidade cognitiva.",
            "médio": f"O fator Abertura à Experiência situou-se na faixa média, indicando equilíbrio entre interesse por novidades e preferência por situações familiares.",
            "reduzido": f"O fator Abertura à Experiência apresentou classificação {classification}, sugerindo maior preferência por rotinas conhecidas, menor busca por novidades e postura mais convencional."
        }
    }

    return templates[factor][level]
```

---

# 11. Output esperado

```json
{
  "test": "BFP",
  "interpretation": {
    "summary": "Perfil de personalidade com elevação em Neuroticismo e redução em Realização.",
    "factors": {
      "neuroticismo": "texto interpretativo",
      "extroversao": "texto interpretativo",
      "socializacao": "texto interpretativo",
      "realizacao": "texto interpretativo",
      "abertura": "texto interpretativo"
    },
    "clinical_integration": "texto integrado final"
  }
}
```

---

# 12. Fechamento padrão

Sempre finalizar com:

```text
Em análise clínica, os resultados do BFP devem ser compreendidos como indicadores de tendências de personalidade, e não como determinantes absolutos do comportamento. A interpretação deve ser integrada à anamnese, observação clínica, histórico de funcionamento e demais instrumentos utilizados na avaliação.

---

# 13. ANÁLISE AUTOMATIZADA PARA LAUDO (SUGESTÃO)

Adicionar ao backend uma função de resumo automátizado para gerar um parágrafo sintético e itens de destaque que possam ser revisados e inseridos no laudo pelo avaliador. Isso padroniza saídas e aumenta auditabilidade.

Regras resumidas:

- Destacar fatores com percentil >= 85 ou < 15.
- Marcar como "extremo" percentis >= 97.5 ou < 2.5.
- Priorizar linguagem condicional ("sugere", "pode indicar").

Exemplo de implementação (pseudocódigo Python):

```python
def summarize_bfp_for_report(results: dict) -> dict:
    # Mesma função ilustrativa disponível em skill_bfp_grafico_tabela.md
    # Retorna: {'summary': str, 'relevant': list, 'combinations': list, 'recommendations': list}
    ...
```

Observação: adaptar nomes de chaves (neuroticismo/extroversao/...) conforme o payload real do sistema.
```
