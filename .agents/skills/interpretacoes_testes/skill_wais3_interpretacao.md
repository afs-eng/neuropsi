# skill_wais3_interpretacao_padrao_ouro.md

## Objetivo da skill

Gerar a interpretação clínica da **Escala Wechsler de Inteligência para Adultos – Terceira Edição (WAIS-III)** no sistema de laudos neuropsicológicos, em padrão técnico, descritivo, auditável e compatível com linguagem profissional.

A skill deve receber os resultados corrigidos do WAIS-III no `computed_payload` e produzir um texto interpretativo integrado, com análise do QIT, QIV, QIE, índices fatoriais e GAI, quando disponível.

## Entrada esperada

A IA deve receber, no mínimo, os seguintes campos:

```json
{
  "paciente_nome": "Nome ou primeiro nome do paciente",
  "teste": "WAIS-III",
  "qiv": {"valor": 91, "classificacao": "Média", "percentil": 27, "intervalo_confianca_95": [86, 97]},
  "qie": {"valor": 77, "classificacao": "Limítrofe", "percentil": 6, "intervalo_confianca_95": [72, 84]},
  "qit": {"valor": 83, "classificacao": "Média Inferior", "percentil": 13, "intervalo_confianca_95": [79, 88]},
  "icv": {"valor": 88, "classificacao": "Média Inferior", "percentil": 21, "intervalo_confianca_95": [83, 94]},
  "iop": {"valor": 87, "classificacao": "Média Inferior", "percentil": 19, "intervalo_confianca_95": [82, 94]},
  "imo": {"valor": 94, "classificacao": "Média", "percentil": 34, "intervalo_confianca_95": [88, 101]},
  "ivp": {"valor": 87, "classificacao": "Média Inferior", "percentil": 19, "intervalo_confianca_95": [80, 96]},
  "gai": {"valor": 85, "classificacao": "Média Inferior", "percentil": 16, "intervalo_confianca_95": [80, 91]}
}
```

Campos opcionais:

```json
{
  "usar_nome_no_texto": false,
  "incluir_percentil": false,
  "incluir_intervalo_confianca": false,
  "nivel_detalhamento": "completo",
  "observacoes_clinicas": "Texto opcional com observações do avaliador"
}
```

## Regras obrigatórias de escrita

1. Escrever em linguagem técnica, clara e descritiva.
2. Não usar tabela na interpretação.
3. Não iniciar parágrafos repetidamente com “No” ou “Na”.
4. Usar preferencialmente construções como “Os resultados obtidos...”, “O Quociente de Inteligência Total...”, “Em contrapartida...”, “Entre os índices fatoriais...”, “O conjunto dos resultados...” e “Em análise clínica...”.
5. Não usar travessão longo.
6. Não usar expressões absolutas como “comprova”, “determina”, “fecha diagnóstico” ou “incapaz”.
7. Evitar linguagem excessivamente patologizante.
8. Descrever o funcionamento cognitivo com base nos resultados, preservando cautela clínica.
9. Quando houver heterogeneidade entre os índices, descrever o perfil como heterogêneo.
10. Quando o QIT estiver abaixo da média, não afirmar deficiência intelectual sem análise adaptativa complementar.
11. Quando o GAI estiver disponível, interpretá-lo como estimativa das habilidades intelectuais gerais menos dependente de memória operacional e velocidade de processamento.
12. O texto deve ser pronto para inserir diretamente no laudo.

## Classificação dos escores compostos

Usar a seguinte classificação para QIs e índices fatoriais da WAIS-III:

```text
≤ 69     = Extremamente Baixo
70–79    = Limítrofe
80–89    = Média Inferior
90–109   = Média
110–119  = Média Superior
120–129  = Superior
≥ 130    = Muito Superior
```

A classificação recebida no `computed_payload` deve ser conferida com essa tabela. Se houver divergência entre valor e classificação, a IA deve priorizar o valor numérico e corrigir a classificação.

## Estrutura obrigatória da interpretação

A interpretação deve seguir esta ordem:

1. Apresentação geral do WAIS-III.
2. Interpretação do QIT.
3. Interpretação do QIV.
4. Interpretação do QIE.
5. Interpretação do ICV.
6. Interpretação do IOP.
7. Interpretação do IMO.
8. Interpretação do IVP.
9. Interpretação do GAI, quando disponível.
10. Síntese clínica integrada do perfil.

## Modelo textual padrão ouro

Usar este modelo como base estrutural. A IA deve substituir valores, classificações e descrições conforme os resultados do paciente.

```text
Os resultados obtidos na Escala Wechsler de Inteligência para Adultos – Terceira Edição (WAIS-III) indicam funcionamento intelectual global situado na faixa [classificação do QIT], com [descrição da homogeneidade ou heterogeneidade] entre os domínios avaliados. O Quociente de Inteligência Total (QIT = [valor]) encontra-se na classificação [classificação], refletindo funcionamento intelectual global [descrição compatível com a classificação], sem que esse achado, isoladamente, seja suficiente para caracterizar diagnóstico clínico específico.

O Quociente de Inteligência Verbal (QIV = [valor]) foi classificado como [classificação], sugerindo [descrição das habilidades verbais compatíveis com o resultado]. Esse índice envolve recursos de compreensão verbal, expressão conceitual, raciocínio mediado pela linguagem, aquisição de conhecimentos e uso funcional de informações verbais.

O Quociente de Inteligência de Execução (QIE = [valor]) situou-se na faixa [classificação], indicando [descrição das habilidades não verbais compatíveis com o resultado]. Esse resultado expressa o funcionamento em tarefas que demandam organização visuoespacial, raciocínio perceptivo, análise de estímulos visuais, solução prática de problemas e eficiência diante de demandas não verbais.

Entre os índices fatoriais, a Compreensão Verbal (ICV = [valor]) apresentou desempenho [classificação], evidenciando [descrição interpretativa]. Esse domínio está associado à formação de conceitos verbais, raciocínio abstrato mediado pela linguagem, compreensão de informações verbais e repertório de conhecimentos adquiridos.

O Índice de Organização Perceptual (IOP = [valor]) também se situou na faixa [classificação], demonstrando [descrição interpretativa]. Esse índice envolve análise, síntese e organização de estímulos visuais, raciocínio não verbal, percepção de relações espaciais e solução de problemas com menor dependência da linguagem.

O Índice de Memória Operacional (IMO = [valor]) foi classificado como [classificação], indicando [descrição interpretativa]. Esse domínio refere-se à capacidade de reter, manipular e reorganizar informações temporárias, especialmente em tarefas auditivo-verbais e de controle mental imediato.

O Índice de Velocidade de Processamento (IVP = [valor]) permaneceu na faixa [classificação], sugerindo [descrição interpretativa]. Esse índice reflete a eficiência em tarefas simples, rápidas e automatizadas, envolvendo rastreamento visual, coordenação visuomotora, precisão gráfica e rapidez na execução.

Quando analisado o Índice de Habilidade Geral (GAI = [valor]), observa-se classificação [classificação], indicando [descrição interpretativa]. O GAI fornece uma estimativa das habilidades intelectuais gerais com menor influência relativa da memória operacional e da velocidade de processamento, sendo útil para compreender os recursos de raciocínio verbal e perceptual de base.

O conjunto dos resultados revela um perfil cognitivo [homogêneo/heterogêneo], com [domínios relativamente mais preservados] e [domínios de maior vulnerabilidade]. Esse padrão sugere [síntese funcional], especialmente em situações que exigem [demandas afetadas], apesar da presença de [recursos preservados].
```

## Modelo refinado com os dados do exemplo

Este é o modelo já preenchido com os dados fornecidos pelo usuário. Deve ser usado como referência de estilo:

```text
Os resultados obtidos na Escala Wechsler de Inteligência para Adultos – Terceira Edição (WAIS-III) indicam funcionamento intelectual global situado na faixa média inferior, com variações discretas entre os domínios avaliados. O Quociente de Inteligência Total (QIT = 83) encontra-se na classificação média inferior, refletindo funcionamento intelectual global abaixo da média esperada para a faixa etária, embora esse achado, isoladamente, não seja suficiente para caracterizar diagnóstico clínico específico.

O Quociente de Inteligência Verbal (QIV = 91) foi classificado na média, sugerindo capacidade verbal funcional, com recursos adequados de compreensão, expressão verbal, aquisição de conhecimentos e raciocínio conceitual em tarefas mediadas pela linguagem. Em contrapartida, o Quociente de Inteligência de Execução (QIE = 77) situou-se na faixa limítrofe, indicando maior vulnerabilidade em tarefas que demandam organização visuoespacial, raciocínio não verbal, rapidez perceptiva, análise de estímulos visuais e eficiência diante de demandas práticas.

Entre os índices fatoriais, a Compreensão Verbal (ICV = 88) apresentou desempenho na média inferior, evidenciando recursos verbais presentes, porém com menor robustez em tarefas de abstração verbal, formação de conceitos e compreensão de conteúdos mediados pela linguagem. O Índice de Organização Perceptual (IOP = 87) também se situou na média inferior, demonstrando desempenho abaixo da média esperada em atividades que envolvem análise, organização e interpretação de estímulos visuais.

O Índice de Memória Operacional (IMO = 94) foi classificado na média, configurando-se como o domínio relativamente mais preservado do perfil cognitivo, indicando capacidade funcional para retenção e manipulação mental de informações temporárias. O Índice de Velocidade de Processamento (IVP = 87) permaneceu na média inferior, sugerindo lentificação relativa em tarefas simples e automatizadas que exigem rapidez, precisão e eficiência visuomotora.

O Índice de Habilidade Geral (GAI = 85) foi classificado na média inferior, reforçando que as habilidades intelectuais de base, especialmente aquelas relacionadas ao raciocínio verbal e perceptual, apresentam funcionamento abaixo da média esperada para a faixa etária. O conjunto dos resultados revela perfil cognitivo global rebaixado e heterogêneo, com melhor desempenho relativo nas tarefas de memória operacional e maior vulnerabilidade nas demandas de execução prática, organização perceptiva e velocidade de processamento. Esse padrão sugere possíveis repercussões em situações que exijam rapidez operacional, integração visuoespacial, solução prática de problemas e adaptação eficiente diante de tarefas novas ou mais complexas, apesar da presença de recursos cognitivos básicos preservados em tarefas de manipulação mental imediata.
```

## Observação técnica importante sobre o exemplo

No exemplo fornecido, o QIE = 77 deve ser classificado como **Limítrofe**, e não como média inferior, conforme a tabela de classificação adotada. Portanto, a IA deve corrigir automaticamente essa inconsistência quando ela aparecer.

Também deve evitar a expressão “faixa limítrofe de adaptação cognitiva” quando o escore estiver na média inferior, pois essa frase pode gerar ambiguidade técnica entre classificação psicométrica e adaptação funcional.

## Regras para descrição da homogeneidade do perfil

A IA deve analisar a distância entre os principais índices:

```text
Diferença máxima entre QIV, QIE, ICV, IOP, IMO e IVP:
0–9 pontos   = perfil relativamente homogêneo
10–14 pontos = variações discretas
15–22 pontos = perfil heterogêneo
≥23 pontos   = perfil acentuadamente heterogêneo
```

Essa regra não substitui análise clínica, mas ajuda a padronizar a redação.

## Banco de frases por classificação

### Muito Superior

```text
desempenho significativamente acima da média esperada, indicando recursos cognitivos amplamente desenvolvidos nesse domínio
```

### Superior

```text
desempenho acima da média esperada, sugerindo recursos cognitivos bem desenvolvidos nesse domínio
```

### Média Superior

```text
desempenho situado acima da média, indicando bom nível de eficiência nesse domínio
```

### Média

```text
desempenho compatível com o esperado para a faixa etária, indicando funcionamento preservado nesse domínio
```

### Média Inferior

```text
desempenho abaixo da média esperada, sugerindo menor eficiência relativa nesse domínio
```

### Limítrofe

```text
desempenho situado em faixa limítrofe, indicando vulnerabilidade importante nesse domínio e maior probabilidade de repercussões funcionais em tarefas de maior exigência
```

### Extremamente Baixo

```text
desempenho significativamente rebaixado, indicando prejuízo importante nesse domínio e necessidade de análise integrada com dados adaptativos, escolares, ocupacionais e clínicos
```

## Descrições por índice

### QIT

Descrever o funcionamento intelectual global. O QIT sintetiza o desempenho geral, mas não deve ser usado isoladamente para diagnóstico.

Frases possíveis:

```text
refletindo funcionamento intelectual global compatível com o esperado para a faixa etária
```

```text
refletindo funcionamento intelectual global abaixo da média esperada para a faixa etária
```

```text
indicando rebaixamento global do funcionamento intelectual, devendo ser interpretado em conjunto com os dados adaptativos, clínicos e funcionais
```

### QIV

Descrever habilidades verbais amplas: compreensão verbal, expressão conceitual, formação de conceitos, raciocínio verbal, aquisição de conhecimentos e uso de informações verbais.

### QIE

Descrever habilidades não verbais e práticas: raciocínio perceptivo, organização visuoespacial, análise visual, solução prática de problemas, eficiência diante de estímulos não verbais e coordenação visuoconstrutiva.

### ICV

Descrever compreensão verbal específica: abstração verbal, conceitos verbais, compreensão de informações verbais, repertório adquirido e julgamento verbal.

### IOP

Descrever organização perceptual: análise de estímulos visuais, organização visuoespacial, raciocínio não verbal, síntese perceptiva e identificação de relações espaciais.

### IMO

Descrever memória operacional: retenção temporária de informações, manipulação mental, atenção auditiva, controle mental imediato, cálculo mental simples e sequenciamento.

### IVP

Descrever velocidade de processamento: rapidez de execução, rastreamento visual, coordenação visuomotora, precisão gráfica, eficiência em tarefas automatizadas e atenção visual sustentada simples.

### GAI

Descrever habilidade geral: raciocínio verbal, raciocínio perceptual, menor influência de memória operacional, menor influência de velocidade de processamento e estimativa das habilidades intelectuais gerais de base.

## Regras para GAI

O GAI só deve ser interpretado quando estiver calculado no `computed_payload`.

Se o GAI não estiver disponível, a IA deve omitir completamente o parágrafo do GAI e não escrever frases como “não foi possível calcular”.

Quando o GAI estiver muito diferente do QIT, a IA deve explicar de forma técnica:

```text
A diferença entre o QIT e o GAI sugere que os componentes de memória operacional e/ou velocidade de processamento influenciaram o desempenho intelectual global, tornando o GAI uma estimativa complementar relevante das habilidades de raciocínio verbal e perceptual.
```

Usar essa frase apenas se houver diferença clinicamente relevante entre QIT e GAI.

Sugestão operacional:

```text
Diferença absoluta entre QIT e GAI ≥ 8 pontos
```

## Regras de consistência psicométrica

Antes de gerar a interpretação, a IA deve verificar:

1. Todos os valores de QI e índices estão entre 40 e 160.
2. As classificações estão coerentes com os valores.
3. QIT, QIV, QIE, ICV, IOP, IMO, IVP e GAI não devem ser confundidos com soma de escores ponderados.
4. Não usar a soma dos escores ponderados no texto interpretativo principal, salvo se o usuário solicitar.
5. Não interpretar valores entre parênteses como escores principais.
6. Não afirmar diagnóstico a partir do WAIS-III isoladamente.
7. Não chamar QIE de “função executiva” de forma isolada. QIE é uma medida ampla de execução/performance, não um índice exclusivo de funções executivas.
8. Não chamar IVP de “atenção” isoladamente. IVP pode ser influenciado por atenção visual, mas mede principalmente velocidade de processamento.
9. Não chamar IMO de “memória de longo prazo”. IMO refere-se à memória operacional.
10. Não usar “déficit” para classificações média inferior sem cautela. Preferir “menor eficiência relativa” ou “vulnerabilidade”.

## Saída esperada

A saída deve ser um texto corrido, sem tabela, pronto para o laudo.

Formato:

```json
{
  "section_key": "wais3_interpretacao",
  "title": "Escala Wechsler de Inteligência para Adultos – Terceira Edição (WAIS-III)",
  "text": "Os resultados obtidos..."
}
```

## Prompt pronto para IA da IDE

```text
Implemente a geração automática da interpretação do WAIS-III no sistema.

Crie ou atualize o módulo `apps/tests/wais3/interpreters.py`.

A função principal deve receber o `computed_payload` do WAIS-III contendo QIV, QIE, QIT, ICV, IOP, IMO, IVP e, quando disponível, GAI. A função deve gerar um texto interpretativo técnico, em português brasileiro, sem tabelas, pronto para inserção no laudo neuropsicológico.

Regras obrigatórias:
1. Usar a classificação dos escores compostos:
   ≤69 Extremamente Baixo;
   70–79 Limítrofe;
   80–89 Média Inferior;
   90–109 Média;
   110–119 Média Superior;
   120–129 Superior;
   ≥130 Muito Superior.
2. Conferir automaticamente se a classificação recebida está coerente com o valor numérico.
3. Corrigir divergências, priorizando o valor numérico.
4. Interpretar QIT, QIV, QIE, ICV, IOP, IMO, IVP e GAI, quando disponível.
5. Omitir o GAI se ele não existir no payload.
6. Não usar tabelas.
7. Não afirmar diagnóstico com base no WAIS-III isoladamente.
8. Não usar valores de soma dos escores ponderados como se fossem QIs.
9. Não interpretar valores entre parênteses.
10. Gerar texto em padrão técnico, objetivo, claro e compatível com laudo neuropsicológico.

A interpretação deve seguir a estrutura:
- apresentação geral do WAIS-III;
- QIT;
- QIV;
- QIE;
- ICV;
- IOP;
- IMO;
- IVP;
- GAI, se disponível;
- síntese clínica integrada.

Use o modelo textual padrão ouro descrito na skill `skill_wais3_interpretacao_padrao_ouro.md`.
```

## Exemplo de função sugerida

```python
def classify_composite_score(value: int) -> str:
    if value <= 69:
        return "Extremamente Baixo"
    if 70 <= value <= 79:
        return "Limítrofe"
    if 80 <= value <= 89:
        return "Média Inferior"
    if 90 <= value <= 109:
        return "Média"
    if 110 <= value <= 119:
        return "Média Superior"
    if 120 <= value <= 129:
        return "Superior"
    return "Muito Superior"
```

```python
def describe_profile_variability(scores: dict[str, int]) -> str:
    valid_scores = [v for v in scores.values() if isinstance(v, int)]
    if not valid_scores:
        return "com variações não especificadas"
    spread = max(valid_scores) - min(valid_scores)

    if spread <= 9:
        return "relativamente homogêneo"
    if spread <= 14:
        return "com variações discretas"
    if spread <= 22:
        return "heterogêneo"
    return "acentuadamente heterogêneo"
```

## Testes unitários obrigatórios

### Teste 1: classificação correta

Entrada:

```json
{
  "qie": {"valor": 77, "classificacao": "Média Inferior"}
}
```

Resultado esperado:

```json
{
  "qie": {"valor": 77, "classificacao_corrigida": "Limítrofe"}
}
```

### Teste 2: omitir GAI ausente

Entrada:

```json
{
  "qit": {"valor": 100},
  "qiv": {"valor": 102},
  "qie": {"valor": 98}
}
```

Resultado esperado:

```text
O texto não deve conter o termo GAI.
```

### Teste 3: não usar soma dos ponderados como QI

Entrada:

```json
{
  "qiv": {"soma_ponderados": 65, "valor": 105}
}
```

Resultado esperado:

```text
O texto deve interpretar QIV = 105, não soma 65.
```

### Teste 4: perfil heterogêneo

Entrada:

```json
{
  "qiv": {"valor": 91},
  "qie": {"valor": 77},
  "icv": {"valor": 88},
  "iop": {"valor": 87},
  "imo": {"valor": 94},
  "ivp": {"valor": 87}
}
```

Diferença máxima: 94 - 77 = 17.

Resultado esperado:

```text
perfil heterogêneo
```

## Resultado final esperado da skill

Com esta skill, o sistema deve ser capaz de transformar automaticamente resultados corrigidos do WAIS-III em uma interpretação clínica clara, técnica, coerente com os dados psicométricos e pronta para compor o laudo neuropsicológico.
