# skill_wasi_interpretacao.md

## Objetivo
Gerar a interpretação técnica da Escala Wechsler Abreviada de Inteligência – WASI em laudos neuropsicológicos, mantendo padrão ouro, linguagem clínica, coerência diagnóstica e integração com anamnese, funcionalidade adaptativa e demais instrumentos.

A skill deve produzir uma análise descritiva do funcionamento intelectual global, contemplando:

- Quociente de Inteligência Verbal – QIV
- Quociente de Inteligência de Execução – QIE
- Quociente de Inteligência Total – QIT
- discrepância entre domínio verbal e domínio de execução
- impacto funcional provável
- hipótese diagnóstica quando houver indicadores clínicos relevantes

## Estrutura recomendada no sistema

```text
apps/tests/
  wasi/
    __init__.py
    config.py
    schemas.py
    validators.py
    calculators.py
    classifiers.py
    interpreters.py
    constants.py
```

Caso o sistema utilize registro global de instrumentos:

```python
from apps.tests.wasi.config import WASIModule

TEST_REGISTRY = {
    "WASI": WASIModule(),
}
```

## Payload esperado

```json
{
  "instrument": "WASI",
  "patient_name": "Mariana",
  "qiv": 83,
  "qiv_classification": "Média Inferior",
  "qie": 59,
  "qie_classification": "Extremamente Baixa",
  "qit": 68,
  "qit_classification": "Extremamente Baixa",
  "use_first_name_only": true,
  "include_diagnostic_hypothesis": true,
  "adaptive_functioning_data_available": false
}
```

## Classificação dos escores compostos

Utilizar a mesma lógica classificatória dos escores compostos das escalas Wechsler:

```python
WASI_COMPOSITE_CLASSIFICATION = [
    {"min": 130, "max": 999, "label": "Muito Superior"},
    {"min": 120, "max": 129, "label": "Superior"},
    {"min": 110, "max": 119, "label": "Média Superior"},
    {"min": 90,  "max": 109, "label": "Média"},
    {"min": 80,  "max": 89,  "label": "Média Inferior"},
    {"min": 70,  "max": 79,  "label": "Limítrofe"},
    {"min": 0,   "max": 69,  "label": "Extremamente Baixa"},
]
```

## Regras de interpretação clínica

### QIV – Quociente de Inteligência Verbal
Interpretar como indicador de:

- compreensão verbal;
- vocabulário;
- formação de conceitos;
- raciocínio abstrato mediado pela linguagem;
- capacidade de utilizar conhecimento verbal em tarefas estruturadas.

### QIE – Quociente de Inteligência de Execução
Interpretar como indicador de:

- raciocínio não verbal;
- organização perceptual;
- análise visuoespacial;
- identificação de padrões;
- resolução prática de problemas;
- manejo de tarefas novas com menor apoio verbal.

### QIT – Quociente de Inteligência Total
Interpretar como indicador do funcionamento intelectual global, sempre considerando a homogeneidade ou heterogeneidade do perfil.

Quando houver discrepância importante entre QIV e QIE, o QIT deve ser interpretado com cautela, pois pode resumir de forma parcial um perfil cognitivo heterogêneo.

## Regra de discrepância entre QIV e QIE

```python
def classify_qiv_qie_discrepancy(qiv: int, qie: int) -> dict:
    diff = abs(qiv - qie)
    if diff < 10:
        level = "sem discrepância clinicamente relevante"
    elif diff < 15:
        level = "discrepância discreta"
    elif diff < 23:
        level = "discrepância moderada"
    else:
        level = "discrepância acentuada"

    stronger_domain = "verbal" if qiv > qie else "execução" if qie > qiv else "equilibrado"

    return {
        "difference": diff,
        "level": level,
        "stronger_domain": stronger_domain,
    }
```

## Regras para hipótese diagnóstica

A expressão obrigatória é: **“há hipótese diagnóstica de...”**

### Quando sugerir hipótese de Deficiência Intelectual
A skill pode sugerir hipótese diagnóstica de Deficiência Intelectual quando:

- QIT estiver na faixa Extremamente Baixa ou Limítrofe com prejuízo funcional importante;
- houver rebaixamento clinicamente significativo em QIV e/ou QIE;
- houver dados de anamnese, observação clínica, desempenho acadêmico ou funcionalidade adaptativa compatíveis.

A hipótese deve sempre ser formulada com cautela:

```text
Há hipótese diagnóstica de Deficiência Intelectual, a ser compreendida de forma integrada aos dados da anamnese, da funcionalidade adaptativa e das demais evidências clínicas.
```

Nunca fechar diagnóstico apenas com o WASI. O texto deve indicar que a interpretação depende da integração com funcionamento adaptativo, história do desenvolvimento, escolaridade, contexto sociocultural e demais instrumentos.

## Modelo fixo de interpretação

```text
A avaliação neuropsicológica de {nome}, por meio da Escala Wechsler Abreviada de Inteligência – WASI, possibilitou a análise do funcionamento intelectual global e de domínios cognitivos centrais, oferecendo indicadores objetivos acerca de seu perfil intelectual.

{nome} obteve Quociente de Inteligência Verbal igual a {qiv}, classificado na faixa {qiv_classification}. {qiv_interpretation}

No Quociente de Inteligência de Execução, {nome} obteve escore {qie}, classificado na faixa {qie_classification}. {qie_interpretation}

O Quociente de Inteligência Total foi {qit}, classificado na faixa {qit_classification}. {qit_interpretation}

Observa-se, portanto, {discrepancy_interpretation}

Em análise clínica, {functional_interpretation} {diagnostic_hypothesis}
```

## Banco de frases para QIV

### Muito Superior ou Superior
```text
Esse resultado indica desempenho verbal acima do esperado, com recursos bem desenvolvidos de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere facilidade para compreender instruções verbais, elaborar respostas conceituais, utilizar conhecimento previamente adquirido e lidar com demandas que exigem organização linguística e abstração verbal.
```

### Média Superior
```text
Esse resultado indica habilidades verbais acima da média esperada, com bons recursos de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere rendimento favorável em tarefas que exigem elaboração verbal, compreensão de conceitos e uso funcional da linguagem em situações estruturadas.
```

### Média
```text
Esse resultado indica funcionamento verbal dentro do esperado, com recursos adequados de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere capacidade funcional para lidar com demandas verbais compatíveis com sua faixa etária e escolaridade.
```

### Média Inferior
```text
Esse resultado indica que suas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem encontram-se abaixo da média esperada, embora ainda preservadas em nível funcional. Tal desempenho sugere que {nome} tende a apresentar melhor rendimento em situações estruturadas, com linguagem clara e apoio contextual, podendo encontrar maior dificuldade diante de demandas verbais mais complexas, abstratas ou que exijam elaboração linguística mais refinada.
```

### Limítrofe
```text
Esse resultado indica fragilidade significativa nas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere maior dificuldade para compreender informações verbais complexas, organizar respostas conceituais, utilizar vocabulário elaborado e lidar com tarefas que demandam abstração linguística.
```

### Extremamente Baixa
```text
Esse resultado indica prejuízo importante nas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem. Tal desempenho sugere dificuldade acentuada para compreender e elaborar informações verbais complexas, organizar conceitos, abstrair significados e responder a demandas que exigem mediação linguística mais elaborada.
```

## Banco de frases para QIE

### Muito Superior ou Superior
```text
Esse resultado evidencia desempenho não verbal acima do esperado, com recursos bem desenvolvidos de raciocínio visuoespacial, organização perceptual, identificação de padrões e resolução prática de problemas. Esse perfil sugere facilidade para lidar com estímulos visuais, compreender relações espaciais e resolver tarefas novas com menor dependência da linguagem.
```

### Média Superior
```text
Esse resultado evidencia bom desempenho em raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse perfil sugere facilidade relativa em tarefas que envolvem identificação de padrões, organização visual e manejo de problemas novos com apoio perceptual.
```

### Média
```text
Esse resultado indica funcionamento não verbal dentro do esperado, com recursos adequados de raciocínio visuoespacial, organização perceptual, identificação de padrões e resolução prática de problemas. Esse desempenho sugere capacidade funcional para lidar com tarefas visuais e práticas compatíveis com sua faixa etária e escolaridade.
```

### Média Inferior
```text
Esse resultado indica desempenho abaixo da média esperada em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere maior dificuldade em tarefas que demandam interpretação de estímulos visuais, identificação de padrões, organização espacial e manejo de situações novas com menor apoio verbal.
```

### Limítrofe
```text
Esse resultado revela fragilidade significativa em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere dificuldade importante em tarefas que exigem análise visual, percepção de relações espaciais, identificação de padrões e adaptação a problemas novos.
```

### Extremamente Baixa
```text
Esse resultado revela prejuízo importante em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere dificuldade acentuada em tarefas que demandam interpretação e organização de estímulos visuais, percepção de relações espaciais, identificação de padrões e manejo de problemas novos sem apoio direto da linguagem.
```

## Banco de frases para QIT

### Muito Superior ou Superior
```text
O resultado indica funcionamento intelectual global acima do esperado para a população normativa, com recursos cognitivos amplos e bem desenvolvidos. Esse perfil sugere bom potencial para aprendizagem, resolução de problemas, abstração e adaptação cognitiva, respeitando-se as características específicas dos domínios verbal e de execução.
```

### Média Superior
```text
O resultado indica funcionamento intelectual global acima da média esperada, sugerindo bons recursos cognitivos gerais para aprendizagem, compreensão, raciocínio e resolução de problemas, respeitando-se as variações observadas entre os domínios avaliados.
```

### Média
```text
O resultado indica funcionamento intelectual global dentro da faixa esperada para a população normativa, sugerindo recursos cognitivos gerais preservados para aprendizagem, compreensão, raciocínio e resolução de problemas, respeitando-se as variações entre os domínios avaliados.
```

### Média Inferior
```text
O resultado indica funcionamento intelectual global abaixo da média esperada, sugerindo vulnerabilidades cognitivas gerais que podem repercutir em tarefas acadêmicas, adaptativas ou ocupacionais que exijam raciocínio, aprendizagem, organização e resolução de problemas mais complexos.
```

### Limítrofe
```text
O resultado indica funcionamento intelectual global significativamente abaixo da média esperada, sugerindo limitações cognitivas relevantes que podem repercutir em aprendizagem, autonomia, adaptação funcional e resolução de problemas, especialmente em situações com maior complexidade ou menor apoio externo.
```

### Extremamente Baixa
```text
O resultado indica comprometimento significativo do funcionamento intelectual global. Esse desempenho sugere rendimento geral substancialmente inferior ao esperado para a população normativa, com impacto funcional variável conforme o grau de suporte ambiental, as demandas adaptativas e os recursos preservados em cada domínio.
```

## Interpretação da discrepância QIV x QIE

### Sem discrepância clinicamente relevante
```text
um perfil cognitivo relativamente homogêneo entre os domínios verbal e de execução, sem discrepância clinicamente relevante entre as habilidades avaliadas. Esse padrão sugere distribuição mais equilibrada dos recursos cognitivos, ainda que a interpretação deva considerar a classificação obtida em cada índice.
```

### QIV maior que QIE
```text
um perfil cognitivo heterogêneo, com desempenho relativamente mais preservado nas habilidades verbais quando comparado ao desempenho não verbal. A discrepância entre os domínios avaliados sugere que {nome} apresenta melhores recursos em tarefas mediadas pela linguagem do que em atividades que exigem organização perceptual, raciocínio visuoespacial e resolução prática de problemas.
```

### QIE maior que QIV
```text
um perfil cognitivo heterogêneo, com desempenho relativamente mais preservado nas habilidades de execução quando comparado ao desempenho verbal. A discrepância entre os domínios avaliados sugere que {nome} apresenta melhores recursos em tarefas visuais, perceptuais e práticas do que em atividades que exigem compreensão verbal, elaboração linguística e raciocínio abstrato mediado pela linguagem.
```

## Interpretação funcional final

### Quando QIT é média ou superior
```text
esse padrão sugere recursos intelectuais globais preservados, com possíveis facilidades ou vulnerabilidades específicas conforme a distribuição entre os domínios verbal e de execução. A interpretação deve considerar a compatibilidade entre os resultados objetivos, as observações clínicas e o funcionamento adaptativo cotidiano.
```

### Quando QIT é média inferior ou limítrofe
```text
esse padrão pode repercutir no cotidiano em situações que envolvam aprendizagem, organização, autonomia, compreensão de demandas complexas e resolução de problemas novos. A magnitude do impacto funcional deve ser compreendida de forma integrada aos dados da anamnese, observação clínica, escolaridade, contexto sociocultural e demais instrumentos aplicados.
```

### Quando QIT é extremamente baixa
```text
esse padrão pode repercutir de forma significativa no cotidiano, especialmente em situações que envolvam autonomia para resolver problemas novos, lidar com informações complexas, organizar-se diante de demandas práticas e adaptar-se a tarefas com menor mediação externa. O rebaixamento global do desempenho intelectual indica limitações cognitivas relevantes, que devem ser compreendidas em conjunto com a funcionalidade adaptativa, a história do desenvolvimento, os dados escolares ou ocupacionais e as demais evidências clínicas.
```

## Função principal de interpretação

```python
def interpret_wasi(payload: dict) -> str:
    nome = payload.get("patient_name", "O paciente")
    qiv = payload["qiv"]
    qie = payload["qie"]
    qit = payload["qit"]

    qiv_classification = payload.get("qiv_classification") or classify_composite(qiv)
    qie_classification = payload.get("qie_classification") or classify_composite(qie)
    qit_classification = payload.get("qit_classification") or classify_composite(qit)

    discrepancy = classify_qiv_qie_discrepancy(qiv, qie)

    qiv_text = get_qiv_phrase(qiv_classification, nome)
    qie_text = get_qie_phrase(qie_classification, nome)
    qit_text = get_qit_phrase(qit_classification, nome)
    discrepancy_text = get_discrepancy_phrase(discrepancy, nome)
    functional_text = get_functional_phrase(qit_classification)

    diagnostic_hypothesis = ""
    if payload.get("include_diagnostic_hypothesis", True):
        if qit <= 69:
            diagnostic_hypothesis = (
                "Há hipótese diagnóstica de Deficiência Intelectual, "
                "a ser compreendida de forma integrada aos dados da anamnese, "
                "da funcionalidade adaptativa e das demais evidências clínicas."
            )
        elif 70 <= qit <= 79:
            diagnostic_hypothesis = (
                "Há hipótese diagnóstica de funcionamento intelectual limítrofe, "
                "a ser compreendida de forma integrada aos dados da anamnese, "
                "da funcionalidade adaptativa e das demais evidências clínicas."
            )

    return f"""
A avaliação neuropsicológica de {nome}, por meio da Escala Wechsler Abreviada de Inteligência – WASI, possibilitou a análise do funcionamento intelectual global e de domínios cognitivos centrais, oferecendo indicadores objetivos acerca de seu perfil intelectual.

{nome} obteve Quociente de Inteligência Verbal igual a {qiv}, classificado na faixa {qiv_classification}. {qiv_text}

No Quociente de Inteligência de Execução, {nome} obteve escore {qie}, classificado na faixa {qie_classification}. {qie_text}

O Quociente de Inteligência Total foi {qit}, classificado na faixa {qit_classification}. {qit_text}

Observa-se, portanto, {discrepancy_text}

Em análise clínica, {functional_text} {diagnostic_hypothesis}
""".strip()
```

## Modelo final com os dados fornecidos

```text
A avaliação neuropsicológica de Mariana, por meio da Escala Wechsler Abreviada de Inteligência – WASI, possibilitou a análise do funcionamento intelectual global e de domínios cognitivos centrais, oferecendo indicadores objetivos acerca de seu perfil intelectual.

Mariana obteve Quociente de Inteligência Verbal igual a 83, classificado na faixa Média Inferior. Esse resultado indica que suas habilidades de compreensão verbal, vocabulário, formação de conceitos e raciocínio abstrato mediado pela linguagem encontram-se abaixo da média esperada, embora ainda preservadas em nível funcional. Tal desempenho sugere que Mariana tende a apresentar melhor rendimento em situações estruturadas, com linguagem clara e apoio contextual, podendo encontrar maior dificuldade diante de demandas verbais mais complexas, abstratas ou que exijam elaboração linguística mais refinada.

No Quociente de Inteligência de Execução, Mariana obteve escore 59, classificado na faixa Extremamente Baixa. Esse resultado revela prejuízo importante em habilidades de raciocínio não verbal, organização perceptual, análise visuoespacial e resolução prática de problemas. Esse achado sugere dificuldade acentuada em tarefas que demandam interpretação e organização de estímulos visuais, percepção de relações espaciais, identificação de padrões e manejo de problemas novos sem apoio direto da linguagem.

O Quociente de Inteligência Total foi 68, classificado na faixa Extremamente Baixa, indicando comprometimento significativo do funcionamento intelectual global. Esse resultado sugere desempenho geral substancialmente inferior ao esperado para a população normativa, com impacto mais expressivo decorrente do rebaixamento nas habilidades de execução, embora também haja fragilidades no domínio verbal.

Observa-se, portanto, um perfil cognitivo heterogêneo, com desempenho relativamente menos comprometido nas habilidades verbais quando comparado ao desempenho não verbal. A discrepância entre os domínios avaliados sugere que Mariana apresenta melhores recursos em tarefas mediadas pela linguagem do que em atividades que exigem organização perceptual, raciocínio visuoespacial e resolução prática de problemas.

Em análise clínica, esse padrão pode repercutir de forma significativa no cotidiano, especialmente em situações que envolvam autonomia para resolver problemas novos, lidar com informações visuais complexas, organizar-se diante de demandas práticas e adaptar-se a tarefas com menor mediação verbal. Embora o domínio verbal se mostre relativamente mais preservado, o rebaixamento global do desempenho intelectual e, sobretudo, o prejuízo importante no raciocínio de execução indicam limitações cognitivas relevantes, compatíveis com funcionamento intelectual significativamente abaixo do esperado. Há hipótese diagnóstica de Deficiência Intelectual, a ser compreendida de forma integrada aos dados da anamnese, da funcionalidade adaptativa e das demais evidências clínicas.
```

## Regras de estilo obrigatórias

- Usar apenas o primeiro nome do paciente nas seções interpretativas.
- Manter linguagem técnica, descritiva e integrada.
- Não iniciar a conclusão com “Diante da análise integrada”.
- Evitar travessões longos.
- Usar “Em análise clínica” no fechamento interpretativo.
- Quando houver hipótese clínica, usar obrigatoriamente “há hipótese diagnóstica de...”.
- Nunca fechar Deficiência Intelectual apenas pelo WASI; sempre integrar funcionalidade adaptativa e dados clínicos.
- Evitar tabelas na interpretação, salvo se o usuário solicitar expressamente.
- Não utilizar o termo “informante”.
- Não usar nomes completos no corpo da análise, apenas na identificação e conclusão geral quando solicitado.
```
