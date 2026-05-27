# skill_wais3_serneuropsi_completa.md

# Skill completa para análise, interpretação e redação clínica do WAIS-III

## 1. Finalidade da skill

Esta skill orienta a IA a corrigir logicamente, analisar e redigir interpretações clínicas do **WAIS-III – Escala Wechsler de Inteligência para Adultos, Terceira Edição**, com base na apostila de apoio fornecida pelo usuário e no padrão técnico de laudos neuropsicológicos.

A skill deve ser utilizada para produzir análises em padrão ouro, com linguagem técnica, integração clínica e cuidado psicométrico. A saída deve ser adequada para uso em laudos neuropsicológicos, relatórios de resultados, sínteses interpretativas e revisão de coerência de resultados do WAIS-III.

## 2. Escopo

Esta skill é exclusiva para o **WAIS-III**.

Não utilizar esta skill para:

- WISC-IV;
- WASI;
- WAIS-IV;
- testes breves de inteligência;
- escalas não Wechsler;
- interpretação diagnóstica isolada sem integração clínica.

Quando houver material misto, considerar apenas conteúdos referentes ao WAIS-III.

## 3. Princípios obrigatórios

A IA deve obedecer aos seguintes princípios:

1. Não reproduzir itens, respostas, tabelas normativas completas ou qualquer material restrito do teste.
2. Não estimar escores normativos sem tabela oficial.
3. Não transformar o WAIS-III em instrumento diagnóstico isolado.
4. Não afirmar deficiência intelectual apenas por QI baixo, sem comportamento adaptativo e análise clínica.
5. Não afirmar altas habilidades apenas por um escore alto isolado.
6. Não interpretar discrepâncias sem verificar valor crítico e frequência/taxa-base.
7. Não interpretar subteste isolado como diagnóstico.
8. Integrar resultados quantitativos e qualitativos.
9. Considerar escolaridade, idade, cultura, linguagem, condições sensoriais, motoras, emocionais e motivacionais.
10. Registrar limitações quando dados essenciais estiverem ausentes.

## 4. Uso restrito e responsabilidade profissional

O WAIS-III é instrumento psicológico de uso restrito. A IA deve atuar como apoio à organização, análise e redação, mas não substitui o julgamento clínico do psicólogo responsável.

Texto obrigatório de cautela quando a skill for usada em relatório:

> Os resultados do WAIS-III devem ser interpretados por profissional habilitado, em conjunto com a entrevista clínica, observação comportamental, histórico de desenvolvimento, escolaridade, contexto sociocultural, condições emocionais e demais instrumentos utilizados na avaliação.

## 5. Dados de entrada esperados

A IA deve receber os dados em uma estrutura semelhante a esta:

```json
{
  "paciente": {
    "nome_completo": "",
    "nome_usado_no_texto": "",
    "idade": "",
    "data_nascimento": "",
    "data_aplicacao": "",
    "escolaridade": "",
    "ocupacao": "",
    "lateralidade": "",
    "motivo_encaminhamento": "",
    "queixas": "",
    "observacoes_clinicas": "",
    "condicoes_interferentes": ""
  },
  "wais3": {
    "versao_manual": "",
    "condicoes_aplicacao": "",
    "ordem_aplicacao_alterada": false,
    "justificativa_alteracao": "",
    "substituicoes": [],
    "subtestes": {
      "Completar Figuras": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Vocabulário": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Códigos": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Semelhanças": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Cubos": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Aritmética": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Raciocínio Matricial": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Dígitos": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Informação": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Arranjo de Figuras": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Compreensão": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Procurar Símbolos": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Sequência de Números e Letras": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""},
      "Armar Objetos": {"bruto": null, "ponderado": null, "classificacao": "", "observacoes": ""}
    },
    "quocientes": {
      "QIV": {"valor": null, "percentil": null, "ic": "", "classificacao": ""},
      "QIE": {"valor": null, "percentil": null, "ic": "", "classificacao": ""},
      "QIT": {"valor": null, "percentil": null, "ic": "", "classificacao": ""}
    },
    "indices": {
      "ICV": {"valor": null, "percentil": null, "ic": "", "classificacao": ""},
      "IOP": {"valor": null, "percentil": null, "ic": "", "classificacao": ""},
      "IMO": {"valor": null, "percentil": null, "ic": "", "classificacao": ""},
      "IVP": {"valor": null, "percentil": null, "ic": "", "classificacao": ""}
    },
    "discrepancias": [
      {
        "comparacao": "",
        "diferenca_observada": null,
        "valor_critico": null,
        "significativa": null,
        "frequencia_acumulada": "",
        "interpretacao": ""
      }
    ],
    "facilidades_dificuldades": [
      {
        "subteste": "",
        "tipo": "facilidade_relativa ou dificuldade_relativa",
        "base": "verbal, execução ou total",
        "diferenca": null,
        "valor_critico": null,
        "frequencia": "",
        "interpretacao": ""
      }
    ]
  }
}
```

Se os campos de valor, percentil, intervalo de confiança ou classificação não forem fornecidos, a IA deve dizer que a interpretação será limitada ao dado disponível.

## 6. Validação inicial

Antes de redigir qualquer análise, a IA deve verificar:

- se o instrumento é WAIS-III;
- se a idade do paciente é compatível com a versão normativa usada;
- se a versão da norma adotada pelo serviço foi informada;
- se há subtestes ausentes;
- se houve substituição de subtestes;
- se a substituição foi tecnicamente justificada;
- se os índices fatoriais foram calculados com os subtestes corretos;
- se Armar Objetos foi usado apenas dentro das regras aplicáveis;
- se o QIT é interpretável ou se há heterogeneidade importante;
- se há fatores que podem comprometer a validade, como fadiga, dor, ansiedade, baixa adesão, alteração visual, alteração motora, baixa escolaridade, barreira linguística, uso de medicação sedativa ou privação de sono.

Modelo de alerta:

> Antes da interpretação clínica, observa-se que [descrever limitação]. Portanto, os resultados devem ser analisados com cautela, priorizando a leitura integrada do perfil cognitivo e evitando conclusões baseadas em pontuações isoladas.

## 7. Estrutura do WAIS-III

O WAIS-III é composto por 14 subtestes, organizados em Escala Verbal, Escala de Execução, quocientes e índices fatoriais.

### 7.1 Escala Verbal

Subtestes principais:

- Vocabulário;
- Semelhanças;
- Aritmética;
- Dígitos;
- Informação;
- Compreensão.

Subteste suplementar:

- Sequência de Números e Letras.

### 7.2 Escala de Execução

Subtestes principais:

- Completar Figuras;
- Códigos;
- Cubos;
- Raciocínio Matricial;
- Arranjo de Figuras.

Subteste suplementar:

- Procurar Símbolos.

Subteste opcional:

- Armar Objetos.

### 7.3 Quocientes

- QIV: QI Verbal;
- QIE: QI de Execução;
- QIT: QI Total.

### 7.4 Índices fatoriais

- ICV: Vocabulário, Semelhanças, Informação;
- IMO: Aritmética, Dígitos, Sequência de Números e Letras;
- IOP: Completar Figuras, Cubos, Raciocínio Matricial;
- IVP: Códigos, Procurar Símbolos.

Compreensão, Arranjo de Figuras e Armar Objetos têm valor clínico, mas não compõem os índices fatoriais na estrutura descrita pela apostila.

## 8. Substituições

A IA deve registrar substituições de forma clara.

Regras gerais:

- substituições devem ter justificativa clínica ou técnica;
- não devem ser feitas por conveniência;
- Procurar Símbolos pode substituir Códigos na Escala de Execução, quando tecnicamente justificado;
- Sequência de Números e Letras pode substituir Dígitos na Escala Verbal, quando tecnicamente justificado;
- Armar Objetos pode substituir subteste de execução apenas dentro da faixa normativa aplicável ao manual utilizado;
- não há substituição válida dentro dos índices fatoriais;
- a aplicação de subtestes opcionais pode enriquecer a análise, mas não deve alterar indevidamente os índices.

Texto padrão:

> Houve substituição de [subteste substituído] por [subteste substituto], conforme justificativa técnica: [justificativa]. Essa substituição foi considerada na interpretação do quociente correspondente, mas não deve ser usada para composição dos índices fatoriais quando a regra normativa não permitir.

## 9. Correção e classificação

### 9.1 Ponto composto

Os quocientes e índices fatoriais do WAIS-III usam média 100 e desvio-padrão 15.

Classificação recomendada:

| Ponto composto | Classificação |
|---:|---|
| < 70 | Extremamente baixo |
| 70 a 79 | Limítrofe |
| 80 a 89 | Média inferior |
| 90 a 109 | Média |
| 110 a 119 | Média superior |
| 120 a 129 | Superior |
| ≥ 130 | Muito superior |

### 9.2 Pontos ponderados

Os subtestes usam média 10 e desvio-padrão 3.

Classificação recomendada:

| Ponto ponderado | Classificação |
|---:|---|
| 1 a 2 | Dificuldade grave |
| 3 a 4 | Dificuldade moderada |
| 5 a 7 | Dificuldade leve |
| 8 a 12 | Média |
| 13 a 14 | Média superior |
| 15 a 17 | Superior |
| 18 a 19 | Muito superior |

A IA deve evitar usar automaticamente “déficit” para todo resultado abaixo da média. Preferir:

- desempenho reduzido;
- desempenho abaixo do esperado;
- dificuldade relativa;
- fragilidade no domínio;
- necessidade de interpretação integrada.

## 10. Ordem técnica de interpretação

A IA deve seguir esta hierarquia:

1. Validar aplicação e dados.
2. Interpretar QIT, se representativo.
3. Interpretar QIV e QIE.
4. Verificar discrepância QIV x QIE.
5. Interpretar ICV, IOP, IMO e IVP.
6. Verificar discrepâncias entre índices.
7. Interpretar subtestes por domínio.
8. Levantar facilidades e dificuldades relativas.
9. Integrar observações qualitativas.
10. Integrar com queixa clínica, escolaridade, ocupação e demais testes.
11. Escrever síntese funcional.
12. Formular hipótese diagnóstica apenas quando sustentada por dados integrados.

## 11. Quando o QIT é interpretável

O QIT pode ser descrito como estimativa global quando:

- não há discrepância expressiva entre QIV e QIE;
- os índices fatoriais não apresentam heterogeneidade clinicamente relevante;
- o perfil dos subtestes não revela dispersão acentuada;
- não há interferências relevantes na aplicação;
- o comportamento observado foi compatível com esforço e compreensão da tarefa.

Modelo:

> Os resultados do WAIS-III indicam funcionamento intelectual global situado na faixa [classificação], com QI Total de [valor] ([percentil], intervalo de confiança [IC]). Esse resultado sugere eficiência intelectual global [adequada/elevada/reduzida] para a faixa etária, sendo clinicamente interpretável como estimativa geral do desempenho cognitivo, uma vez que o perfil não apresentou heterogeneidade expressiva entre os principais domínios avaliados.

## 12. Quando o QIT deve ser interpretado com cautela

O QIT deve ser relativizado quando:

- QIV e QIE divergem de forma significativa;
- há grande diferença entre ICV, IOP, IMO e IVP;
- há dispersão acentuada nos subtestes;
- há queda importante em IVP ou IMO em contraste com ICV ou IOP;
- fatores clínicos interferiram na execução;
- há baixa validade ecológica para uso do escore global.

Modelo:

> Embora o QI Total tenha sido de [valor], classificado como [classificação], esse índice deve ser interpretado com cautela, pois o perfil apresentou heterogeneidade entre os domínios avaliados. Nessa condição, a análise dos índices fatoriais e dos subtestes é clinicamente mais informativa do que a leitura isolada do escore global.

## 13. Interpretação do QI Verbal

O QIV reflete habilidades mediadas pela linguagem, raciocínio verbal, conhecimento adquirido, memória auditiva, compreensão verbal e expressão conceitual.

Modelo:

> O QI Verbal situou-se na faixa [classificação], sugerindo [nível] desempenho em tarefas dependentes de linguagem, raciocínio verbal, repertório conceitual e conhecimento previamente adquirido. Esse resultado deve ser analisado considerando escolaridade, contexto sociocultural, desenvolvimento linguístico, audição, atenção auditiva e qualidade da expressão verbal durante a avaliação.

## 14. Interpretação do QI de Execução

O QIE reflete habilidades não verbais, raciocínio visuoespacial, organização perceptual, análise de padrões, integração visuomotora, velocidade de execução e resolução de problemas visuais.

Modelo:

> O QI de Execução apresentou classificação [classificação], indicando [nível] desempenho em tarefas que exigem raciocínio não verbal, organização visuoespacial, discriminação perceptiva, planejamento visual e execução sob demanda temporal. A interpretação deve considerar velocidade, coordenação motora, acuidade visual, impulsividade, ansiedade de desempenho e estratégias utilizadas durante tarefas visuoconstrutivas.

## 15. Comparação QIV x QIE

### 15.1 Diferença não significativa

> A comparação entre QI Verbal e QI de Execução não evidenciou discrepância clinicamente significativa, sugerindo perfil relativamente equilibrado entre habilidades verbais e não verbais.

### 15.2 QIV superior ao QIE

> A diferença favorece o QI Verbal, indicando melhor rendimento em tarefas mediadas pela linguagem, conhecimento cristalizado e elaboração conceitual, em comparação às tarefas visuoespaciais, perceptivas, grafomotoras ou executadas sob pressão temporal.

### 15.3 QIE superior ao QIV

> A diferença favorece o QI de Execução, sugerindo melhor rendimento em tarefas de raciocínio visual, solução de problemas não verbais e organização perceptual, em comparação às tarefas que exigem verbalização, abstração linguística ou acesso ao conhecimento cristalizado.

## 16. Interpretação dos índices fatoriais

## 16.1 ICV – Índice de Compreensão Verbal

### O que avalia

O ICV reúne habilidades de raciocínio verbal, compreensão, conceituação, inteligência cristalizada, acesso lexical, memória semântica e expressão verbal organizada.

Subtestes:

- Vocabulário;
- Semelhanças;
- Informação.

### Fatores que interferem

- escolaridade;
- acesso cultural;
- hábitos de leitura;
- desenvolvimento da linguagem;
- qualidade da audição;
- atenção auditiva;
- afasia, disartria, apraxia de fala ou alterações linguísticas;
- ansiedade, perfeccionismo ou prolixidade;
- dificuldades executivas na organização da resposta.

### Modelo interpretativo

> O ICV situou-se na faixa [classificação], indicando [nível] desempenho em raciocínio verbal, formação de conceitos, acesso ao repertório lexical e conhecimento cristalizado. Esse resultado sugere que [nome] apresenta [descrição clínica]. A interpretação deve considerar escolaridade, estimulação sociocultural, desenvolvimento linguístico e qualidade da organização verbal observada durante a avaliação.

### Marcadores qualitativos

A IA deve observar:

- respostas concretas;
- respostas abstratas;
- prolixidade;
- perseveração;
- tangencialidade;
- pobreza conceitual;
- dificuldade de evocação;
- melhora com inquérito;
- inconsistência entre subtestes verbais.

### Perfis diferenciais no ICV

- Vocabulário baixo + Semelhanças baixo: fragilidade verbal ampla.
- Vocabulário preservado + Semelhanças baixo: repertório lexical preservado com dificuldade de abstração.
- Informação baixo + Semelhanças preservado: menor exposição cultural com raciocínio verbal preservado.
- Informação alto + Semelhanças baixo: conhecimento factual preservado com fragilidade de síntese conceitual.

## 16.2 IMO – Índice de Memória Operacional

### O que avalia

O IMO mede a capacidade de manter e manipular informações por curto período sob controle atencional. Envolve memória operacional verbal, atenção sustentada, atualização mental, controle executivo, resistência à distração e organização sequencial.

Subtestes:

- Aritmética;
- Dígitos;
- Sequência de Números e Letras.

### Base teórica

A análise deve considerar o modelo funcional da memória operacional:

- alça fonológica;
- executivo central;
- atualização mental;
- manipulação ativa;
- resistência à interferência.

### Modelo interpretativo

> O IMO apresentou classificação [classificação], sugerindo [nível] capacidade de manter, manipular e reorganizar informações auditivas em curto prazo. Esse domínio é sensível à atenção sustentada, controle executivo, memória auditiva, sequenciamento mental e resistência à distração. Quando reduzido, pode se manifestar em dificuldades para seguir instruções, realizar cálculos mentais, manter o fio de tarefas e organizar informações simultâneas.

### Marcadores qualitativos

A IA deve observar:

- perda rápida de sequência;
- intrusões;
- inversões;
- recontagens;
- erros por ansiedade;
- queda com aumento da complexidade;
- diferença entre repetição passiva e manipulação ativa;
- diferença entre Dígitos direto e inverso;
- discrepância entre Dígitos e Sequência de Números e Letras;
- dificuldade em cálculo mental sob tempo.

### Perfis diferenciais no IMO

- Dígitos direto baixo: atenção auditiva básica e armazenamento imediato fragilizados.
- Dígitos inverso baixo com direto preservado: manipulação mental e controle executivo fragilizados.
- Sequência de Números e Letras abaixo de Dígitos: maior dificuldade com atualização, dupla regra e flexibilidade.
- Aritmética baixa com Dígitos preservado: possível fragilidade em raciocínio quantitativo, ansiedade matemática ou escolarização.
- Todos reduzidos: fragilidade ampla de memória operacional e atenção sustentada.

## 16.3 IOP – Índice de Organização Perceptual

### O que avalia

O IOP avalia raciocínio perceptual, organização visuoespacial, inteligência fluida, processamento visual, análise de padrões, síntese visuoconstrutiva e resolução de problemas novos.

Subtestes:

- Completar Figuras;
- Cubos;
- Raciocínio Matricial.

### Base teórica

O IOP deve ser interpretado considerando:

- inteligência fluida;
- processamento visual;
- raciocínio indutivo e dedutivo;
- análise parte-todo;
- rotas visuais dorsal e ventral;
- integração visuomotora;
- planejamento visual.

### Modelo interpretativo

> O IOP situou-se na faixa [classificação], indicando [nível] desempenho em raciocínio visuoespacial, organização perceptual, análise de padrões e resolução de problemas novos com menor dependência da linguagem. Esse índice sugere [descrição clínica], devendo ser analisado em conjunto com acuidade visual, coordenação motora, planejamento, velocidade de execução e estratégias utilizadas diante de tarefas visuais.

### Marcadores qualitativos

A IA deve observar:

- dificuldade em detalhes visuais;
- erros por pressa;
- falhas de organização parte-todo;
- rotação em Cubos;
- dificuldades de planejamento;
- respostas impulsivas em Raciocínio Matricial;
- inconsistência entre tarefas perceptivas e tarefas construtivas;
- preservação do raciocínio com lentificação;
- possível interferência visual, motora ou executiva.

### Perfis diferenciais no IOP

- Completar Figuras baixo + Cubos/RM preservados: dificuldade de atenção a detalhes, reconhecimento visual ou percepção de elementos essenciais.
- Cubos baixo + RM preservado: possível dificuldade visuoconstrutiva, motora, planejamento ou velocidade, com raciocínio fluido relativamente preservado.
- RM baixo + Cubos preservado: possível fragilidade em inferência abstrata visual, identificação de regras ou flexibilidade cognitiva.
- Todos baixos: fragilidade ampla em processamento visuoespacial e raciocínio perceptual.

## 16.4 IVP – Índice de Velocidade de Processamento

### O que avalia

O IVP mede rapidez e eficiência em tarefas visuais simples sob limite de tempo, envolvendo varredura visual, atenção sustentada, discriminação perceptiva, decisão rápida, coordenação visuomotora e equilíbrio entre velocidade e precisão.

Subtestes:

- Códigos;
- Procurar Símbolos.

### Modelo interpretativo

> O IVP apresentou classificação [classificação], sugerindo [nível] velocidade de processamento visual, atenção sustentada, rapidez perceptiva e eficiência psicomotora sob pressão temporal. Resultados reduzidos podem estar associados a lentificação cognitiva, oscilação atencional, cautela excessiva, ansiedade, perfeccionismo, fadiga, dificuldades motoras finas ou baixa automatização.

### Comparação Códigos x Procurar Símbolos

- Códigos exige maior componente grafomotor e associação número-símbolo.
- Procurar Símbolos exige varredura visual e decisão rápida com menor demanda de desenho.
- Códigos baixo + Procurar Símbolos preservado: suspeitar de componente grafomotor, automatização associativa ou lentificação motora.
- Procurar Símbolos baixo + Códigos preservado: suspeitar de varredura visual, discriminação rápida ou tomada de decisão.
- Ambos baixos: lentificação, baixa eficiência atencional, ansiedade, fadiga ou prejuízo de velocidade de processamento.
- Muitos erros com alta produção: impulsividade e frágil monitoramento.
- Poucos erros com baixa produção: estilo cauteloso, lentidão ou perfeccionismo.

## 17. Interpretação dos subtestes

A IA deve interpretar subtestes somente quando houver ponto ponderado, classificação ou observação qualitativa.

## 17.1 Completar Figuras

### Construtos

- percepção visual;
- atenção a detalhes relevantes;
- reconhecimento de elementos essenciais;
- raciocínio prático visual;
- discriminação de informação relevante;
- velocidade de análise visual.

### Modelo

> Em Completar Figuras, [nome] apresentou desempenho [classificação], sugerindo [nível] capacidade de identificar detalhes visuais relevantes e reconhecer elementos essenciais em estímulos familiares. Desempenhos reduzidos podem refletir desatenção a detalhes, impulsividade, dificuldades perceptivas ou menor eficiência em discriminação visual sob tempo.

## 17.2 Vocabulário

### Construtos

- conhecimento lexical;
- inteligência cristalizada;
- memória semântica;
- expressão verbal;
- formação conceitual;
- qualidade da escolarização;
- repertório cultural.

### Modelo

> Em Vocabulário, o desempenho [classificação] indica [nível] repertório lexical, memória semântica e capacidade de formular definições. Esse subteste é um dos marcadores de inteligência cristalizada e deve ser interpretado considerando escolaridade, estimulação cultural, desenvolvimento linguístico e clareza expressiva.

### Atenção

Não penalizar, na interpretação textual, erros gramaticais ou pronúncia quando o conteúdo conceitual estiver preservado.

## 17.3 Códigos

### Construtos

- velocidade de processamento;
- associação número-símbolo;
- atenção sustentada;
- rastreamento visual;
- coordenação visuomotora;
- aprendizagem incidental;
- componente grafomotor.

### Modelo

> Em Códigos, [nome] apresentou desempenho [classificação], sugerindo [nível] eficiência em velocidade grafomotora, atenção sustentada, associação visual e execução sob limite de tempo. Resultado reduzido pode refletir lentificação psicomotora, dificuldade de automatização, oscilação atencional, ansiedade, baixa precisão motora ou estilo excessivamente cauteloso.

### Observações qualitativas

A IA deve considerar:

- saltos de linha;
- erros não corrigidos;
- autocorreções válidas;
- perda de sequência;
- lentidão com precisão;
- rapidez com muitos erros;
- diferença entre desempenho principal e Códigos-Cópia quando disponível.

## 17.4 Semelhanças

### Construtos

- raciocínio verbal abstrato;
- formação de conceitos;
- categorização;
- generalização;
- flexibilidade cognitiva;
- pensamento categorial.

### Modelo

> Em Semelhanças, [nome] apresentou desempenho [classificação], indicando [nível] capacidade de abstração verbal, categorização e identificação de relações conceituais. Respostas concretas ou baseadas em características superficiais sugerem menor nível de abstração, enquanto respostas conceituais e organizadas indicam melhor raciocínio verbal abstrato.

## 17.5 Cubos

### Construtos

- raciocínio visuoespacial;
- análise parte-todo;
- síntese visuoconstrutiva;
- coordenação visuomotora;
- planejamento;
- velocidade sob pressão temporal.

### Modelo

> Em Cubos, o desempenho [classificação] sugere [nível] organização visuoespacial, planejamento construtivo, análise parte-todo e integração perceptivo-motora. Erros de rotação, lentidão ou dificuldade de reorganização dos cubos devem ser analisados qualitativamente para diferenciar fragilidade visuoespacial, planejamento ineficiente, impulsividade ou lentificação psicomotora.

## 17.6 Aritmética

### Construtos

- cálculo mental;
- atenção sustentada;
- memória operacional;
- raciocínio quantitativo;
- controle sob tempo;
- resistência à distração.

### Modelo

> Em Aritmética, [nome] apresentou desempenho [classificação], indicando [nível] eficiência em cálculo mental, raciocínio quantitativo e manutenção de informações sob pressão temporal. Baixos resultados podem refletir dificuldades em memória operacional, ansiedade diante de números, escolarização, flutuação atencional ou fragilidade em estratégias de cálculo.

## 17.7 Raciocínio Matricial

### Construtos

- inteligência fluida;
- raciocínio indutivo;
- identificação de padrões;
- relações abstratas visuais;
- análise visual sem dependência de linguagem;
- flexibilidade cognitiva.

### Modelo

> Em Raciocínio Matricial, [nome] apresentou desempenho [classificação], sugerindo [nível] raciocínio fluido não verbal, identificação de padrões e inferência lógica visual. Desempenhos reduzidos podem indicar dificuldade em abstração visual, reconhecimento de regras implícitas, flexibilidade cognitiva ou análise de relações entre estímulos.

### Padrões qualitativos

Considerar dificuldades com:

- complementação;
- classificação;
- analogia;
- sequência serial;
- pressa;
- ruminação;
- autocorreções;
- verbalização de estratégia;
- erros por atenção versus erros por raciocínio.

## 17.8 Dígitos

### Construtos

- atenção auditiva;
- memória de curto prazo;
- concentração;
- sequenciamento;
- memória operacional na ordem inversa;
- controle inibitório.

### Modelo

> Em Dígitos, o desempenho [classificação] indica [nível] atenção auditiva, memória imediata e manipulação sequencial. Diferenças entre repetição direta e inversa ajudam a distinguir armazenamento simples de informação e manipulação mental ativa.

## 17.9 Informação

### Construtos

- conhecimento factual;
- inteligência cristalizada;
- memória semântica;
- aprendizagem cultural;
- acesso a informações previamente adquiridas.

### Modelo

> Em Informação, [nome] apresentou desempenho [classificação], sugerindo [nível] conhecimento factual, memória semântica e recuperação de informações aprendidas ao longo da vida. A interpretação deve considerar escolaridade, exposição cultural, oportunidades de aprendizagem e hábitos de leitura.

## 17.10 Arranjo de Figuras

### Construtos

- organização sequencial;
- percepção de causalidade;
- julgamento social visual;
- planejamento;
- narrativa lógica;
- antecipação de consequências;
- rapidez visuoperceptiva.

### Modelo

> Em Arranjo de Figuras, [nome] apresentou desempenho [classificação], sugerindo [nível] capacidade de organizar eventos em sequência lógica, compreender relações de causa e consequência e integrar pistas sociais visuais. Dificuldades podem refletir impulsividade, desatenção, prejuízo de planejamento, leitura social limitada ou pensamento desorganizado.

## 17.11 Compreensão

### Construtos

- julgamento prático;
- raciocínio verbal aplicado;
- conhecimento de normas sociais;
- tomada de decisão;
- adaptação cotidiana;
- pragmática social.

### Modelo

> Em Compreensão, [nome] apresentou desempenho [classificação], indicando [nível] julgamento prático, compreensão de normas sociais e raciocínio verbal aplicado a situações cotidianas. Respostas concretas, vagas ou culturalmente inadequadas podem sugerir dificuldade de abstração social, raciocínio prático ou organização verbal.

## 17.12 Procurar Símbolos

### Construtos

- velocidade de processamento;
- atenção concentrada;
- discriminação visual rápida;
- varredura visual;
- tomada de decisão;
- controle de impulsos.

### Modelo

> Em Procurar Símbolos, [nome] apresentou desempenho [classificação], sugerindo [nível] velocidade de varredura visual, discriminação perceptiva e atenção seletiva sob tempo. Baixa produção com poucos erros sugere lentidão ou cautela; alta produção com muitos erros pode indicar impulsividade ou monitoramento reduzido.

## 17.13 Sequência de Números e Letras

### Construtos

- memória operacional verbal;
- atenção sustentada;
- flexibilidade mental;
- alternância entre regras;
- organização sequencial;
- resistência à interferência.

### Modelo

> Em Sequência de Números e Letras, [nome] apresentou desempenho [classificação], indicando [nível] capacidade de manter e reorganizar mentalmente informações auditivas segundo regras simultâneas. Resultados reduzidos podem indicar dificuldade de manipulação ativa, flexibilidade cognitiva, atenção sustentada ou estratégias internas de organização.

## 17.14 Armar Objetos

### Construtos

- organização visuoespacial;
- relação parte-todo;
- planejamento visoconstrutivo;
- coordenação motora fina;
- velocidade visuomotora;
- integração perceptual.

### Modelo

> Em Armar Objetos, [nome] apresentou desempenho [classificação], sugerindo [nível] habilidade de integrar partes em um todo visualmente significativo. A análise deve diferenciar dificuldade em reconhecer o objeto, dificuldade em montar as partes e lentificação na execução. Por ser subteste opcional, seu valor é principalmente qualitativo e complementar.

## 18. Facilidades e dificuldades relativas

A IA deve identificar facilidades e dificuldades relativas quando houver dados suficientes.

### Procedimento

1. Calcular média dos pontos ponderados da escala ou conjunto comparado.
2. Comparar cada subteste com a média correspondente.
3. Verificar se a diferença atinge valor crítico oficial.
4. Consultar frequência acumulada/taxa-base quando disponível.
5. Só então classificar como facilidade ou dificuldade relativa.
6. Integrar com observação clínica.

### Modelo de facilidade relativa

> O subteste [subteste] configurou facilidade relativa no perfil de [nome], indicando desempenho acima de seu próprio padrão médio em tarefas que envolvem [construtos]. Esse achado sugere uma área de maior eficiência intraindividual, especialmente em comparação aos demais domínios avaliados.

### Modelo de dificuldade relativa

> O subteste [subteste] configurou dificuldade relativa no perfil de [nome], indicando desempenho abaixo de seu próprio padrão médio em tarefas que envolvem [construtos]. Esse achado não deve ser interpretado isoladamente como déficit, mas como fragilidade relativa dentro do perfil cognitivo observado.

## 19. Discrepâncias

A IA deve interpretar discrepâncias em três níveis:

1. entre QIV e QIE;
2. entre índices fatoriais;
3. entre subtestes.

### Regras

- considerar diferença observada;
- comparar com valor crítico;
- verificar frequência/taxa-base;
- interpretar apenas se houver significância e relevância clínica;
- considerar sinais positivo/negativo quando a tabela assim exigir;
- não chamar discrepância de déficit sem análise funcional.

### Modelo

> A diferença entre [domínio 1] e [domínio 2] foi de [valor] pontos. Considerando o valor crítico de [valor crítico], essa discrepância [atinge/não atinge] significância estatística. A frequência acumulada de [frequência] indica que esse padrão é [comum/incomum] na amostra normativa. Clinicamente, esse achado sugere [interpretação], desde que integrado ao histórico e às observações comportamentais.

## 20. Integração por perfis cognitivos

## 20.1 Perfil verbal forte e execução baixa

Interpretação provável:

- melhor raciocínio mediado pela linguagem;
- bom acesso a conceitos;
- fragilidade visuoespacial, grafomotora, perceptual ou de velocidade;
- possível interferência motora, visual, ansiedade ou lentificação.

Texto:

> O perfil sugere maior eficiência em tarefas mediadas pela linguagem, com desempenho relativamente inferior em tarefas visuoespaciais ou executivas. Esse padrão pode se expressar funcionalmente como melhor rendimento em explicações verbais e menor eficiência em atividades que exigem rapidez, organização visual ou execução prática.

## 20.2 Perfil execução forte e verbal baixo

Interpretação provável:

- melhor raciocínio visual;
- maior facilidade com problemas não verbais;
- fragilidade em linguagem, repertório cultural, escolaridade, abstração verbal ou memória semântica.

Texto:

> O perfil indica maior eficiência em raciocínio não verbal e organização perceptual, com fragilidade relativa em tarefas que exigem linguagem, conceituação verbal e conhecimento cristalizado. Esse padrão deve ser interpretado considerando escolaridade, história linguística e contexto sociocultural.

## 20.3 ICV alto e IMO baixo

Interpretação provável:

- bom repertório verbal;
- dificuldade em manipular informações ativamente;
- queixas de esquecimento operacional, perda do fio, dificuldade com instruções longas.

Texto:

> A discrepância entre ICV e IMO sugere que [nome] possui recursos verbais e conceituais mais preservados do que sua eficiência para manter e manipular informações em tempo real. Funcionalmente, isso pode gerar desempenho satisfatório em tarefas de compreensão verbal estruturada, mas dificuldade em atividades que exigem atualização mental, cálculo, múltiplas instruções ou controle atencional contínuo.

## 20.4 ICV alto e IVP baixo

Interpretação provável:

- raciocínio verbal preservado;
- lentificação operacional;
- produção lenta;
- ansiedade/perfeccionismo/fadiga;
- possível diferença entre capacidade conceitual e rendimento sob tempo.

Texto:

> O contraste entre ICV e IVP indica que a capacidade de raciocínio verbal pode estar mais preservada do que a eficiência para executar tarefas simples sob pressão temporal. Em contexto funcional, [nome] pode compreender bem informações complexas, mas apresentar lentidão, menor produtividade ou maior custo cognitivo em atividades cronometradas.

## 20.5 IOP alto e IVP baixo

Interpretação provável:

- raciocínio visual preservado;
- lentificação ou dificuldade de execução;
- impacto grafomotor ou atencional.

Texto:

> O desempenho relativamente superior em organização perceptual, associado a velocidade de processamento inferior, sugere que [nome] pode resolver problemas visuais quando dispõe de tempo suficiente, mas apresenta menor eficiência em tarefas rápidas, repetitivas ou dependentes de automatização visuomotora.

## 20.6 IMO e IVP baixos

Interpretação provável:

- fragilidade atencional/executiva;
- lentificação cognitiva;
- sobrecarga mental;
- possível associação com TDAH, ansiedade, depressão, privação de sono, fadiga ou condição neurológica.

Texto:

> A associação entre desempenho reduzido em memória operacional e velocidade de processamento sugere fragilidade em eficiência cognitiva online, especialmente em tarefas que exigem manter informações ativas, responder rapidamente e monitorar a própria execução. Esse padrão pode contribuir para queixas de lentidão, distração, perda do fio da tarefa e baixa produtividade, devendo ser integrado aos demais instrumentos de atenção e funções executivas.

## 21. Integração com hipóteses clínicas

A IA deve usar o WAIS-III como parte da formulação clínica, não como prova isolada.

### 21.1 Deficiência intelectual

Não concluir apenas por QIT < 70.

Exigir:

- funcionamento intelectual significativamente abaixo da média;
- prejuízo adaptativo;
- início no período do desenvolvimento;
- análise de fatores interferentes;
- integração com escalas adaptativas e dados clínicos.

Modelo:

> Os resultados intelectuais situam-se em faixa compatível com funcionamento significativamente rebaixado. Entretanto, a hipótese diagnóstica de deficiência intelectual exige integração com avaliação do comportamento adaptativo, história do desenvolvimento, escolaridade, funcionalidade cotidiana e exclusão de fatores que possam ter reduzido artificialmente o desempenho.

### 21.2 Altas habilidades/superdotação

Não concluir apenas por um subteste alto.

Considerar:

- QI ou índices significativamente elevados;
- consistência do perfil;
- desempenho funcional/acadêmico;
- criatividade, motivação, produção e contexto;
- avaliação complementar.

Modelo:

> Os resultados indicam desempenho intelectual superior em [domínios], podendo contribuir para investigação de altas habilidades/superdotação. Contudo, essa hipótese requer análise multidimensional, incluindo histórico de desempenho, criatividade, engajamento, produção e dados contextuais.

### 21.3 TDAH

Possíveis achados:

- IMO reduzido;
- IVP reduzido;
- erros por impulsividade;
- inconsistência;
- queda em Dígitos, Sequência de Números e Letras, Códigos e Procurar Símbolos;
- discrepância entre raciocínio e eficiência operacional.

Modelo:

> O padrão de desempenho sugere fragilidades em memória operacional, atenção sustentada e/ou velocidade de processamento, achados que podem ser compatíveis com dificuldades atencionais. Entretanto, a hipótese diagnóstica de TDAH deve ser sustentada por entrevista clínica, escalas comportamentais, histórico de sintomas em múltiplos contextos e demais medidas neuropsicológicas.

### 21.4 TEA

Possíveis achados:

- discrepâncias entre raciocínio visual e compreensão social;
- respostas concretas em Semelhanças ou Compreensão;
- dificuldades em julgamento social;
- rigidez nas estratégias;
- maior eficiência em padrões visuais em alguns casos.

Modelo:

> Alguns achados qualitativos, como respostas concretas, rigidez conceitual ou dificuldades em julgamento social, podem contribuir para a compreensão do funcionamento sociocognitivo. Ainda assim, o WAIS-III não é instrumento diagnóstico para TEA e deve ser integrado a escalas específicas, anamnese e observação clínica.

### 21.5 Ansiedade, depressão e fadiga

Possíveis achados:

- lentificação;
- cautela excessiva;
- queda em tarefas cronometradas;
- oscilação de atenção;
- desempenho melhor quando sem pressão temporal;
- autocorreções frequentes.

Modelo:

> O desempenho em tarefas sob tempo pode ter sido influenciado por ansiedade, fadiga, baixa energia ou estilo excessivamente cauteloso. Esse fator deve ser considerado antes de atribuir o resultado exclusivamente a déficit cognitivo.

### 21.6 Quadros neurológicos

Possíveis achados:

- queda em IOP;
- alterações visuoespaciais;
- lentificação em IVP;
- dificuldade grafomotora;
- falhas de reconhecimento visual;
- discrepância entre conhecimento cristalizado e desempenho fluido.

Modelo:

> O padrão observado pode sugerir impacto em processos visuoespaciais, velocidade de processamento ou organização executiva. Em contexto neurológico, recomenda-se integrar esses achados a exame clínico, histórico médico, neuroimagem quando disponível e instrumentos específicos de memória, linguagem, atenção e funções executivas.

## 22. Estrutura de saída no laudo

Usar a seguinte estrutura:

```markdown
### WAIS-III – Escala Wechsler de Inteligência para Adultos

[Introdução técnica]

[Validade/observações de aplicação, se necessário]

[Funcionamento intelectual global]

[QI Verbal e QI de Execução]

[Índices fatoriais: ICV, IOP, IMO, IVP]

[Subtestes clinicamente relevantes]

[Discrepâncias, facilidades e dificuldades relativas]

[Integração clínica]

[Hipótese Diagnóstica, se aplicável]
```

## 23. Introdução técnica padrão

> A Escala Wechsler de Inteligência para Adultos – Terceira Edição (WAIS-III) é um instrumento de aplicação individual destinado à avaliação do funcionamento intelectual em adultos, contemplando medidas de desempenho verbal, desempenho de execução, funcionamento intelectual global e índices fatoriais relacionados à compreensão verbal, organização perceptual, memória operacional e velocidade de processamento. Seus resultados permitem examinar tanto o nível global de eficiência intelectual quanto o padrão de forças e fragilidades cognitivas, devendo ser interpretados em conjunto com dados clínicos, histórico escolar e ocupacional, contexto sociocultural, observações comportamentais e demais instrumentos utilizados na avaliação.

## 24. Modelo completo de análise interpretativa

> Os resultados obtidos no WAIS-III indicam que [nome] apresentou funcionamento intelectual global situado na faixa [classificação], com QI Total de [valor] ([percentil], intervalo de confiança [IC]). Esse resultado sugere [interpretação do funcionamento global]. A interpretação do QIT [é clinicamente representativa/deve ser realizada com cautela], considerando [homogeneidade ou heterogeneidade do perfil].
>
> O QI Verbal situou-se na faixa [classificação], indicando [interpretação verbal]. O QI de Execução apresentou classificação [classificação], sugerindo [interpretação execução]. A comparação entre esses quocientes [não revelou/revelou] discrepância clinicamente relevante, o que sugere [síntese].
>
> Entre os índices fatoriais, o ICV apresentou desempenho [classificação], refletindo [raciocínio verbal, conhecimento cristalizado, abstração]. O IOP situou-se na faixa [classificação], indicando [organização perceptual, raciocínio fluido, processamento visual]. O IMO apresentou classificação [classificação], sugerindo [memória operacional, atenção auditiva, manipulação mental]. O IVP situou-se na faixa [classificação], refletindo [velocidade de processamento, varredura visual, atenção sustentada e eficiência psicomotora].
>
> A análise dos subtestes evidenciou [facilidades] e [fragilidades], especialmente em [domínios]. Qualitativamente, observou-se [observações clínicas]. Em análise clínica, o perfil sugere [síntese funcional], com possíveis repercussões em [atividades acadêmicas/profissionais/cotidianas], sobretudo quando há demanda de [atenção, velocidade, memória operacional, linguagem, raciocínio visual].
>
> Os achados devem ser integrados aos demais instrumentos e à anamnese para formulação diagnóstica. O WAIS-III contribui para a caracterização do perfil intelectual, mas não deve ser utilizado isoladamente para fechamento diagnóstico.

## 25. Modelo para perfil homogêneo

> [nome] apresentou perfil intelectual relativamente homogêneo, com resultados distribuídos de maneira consistente entre os domínios verbal, visuoespacial, memória operacional e velocidade de processamento. Nessa configuração, o QI Total pode ser considerado uma estimativa representativa do funcionamento intelectual global. Em análise clínica, os achados sugerem [descrição funcional], sem discrepâncias expressivas que indiquem fragilidade específica relevante no perfil avaliado.

## 26. Modelo para perfil heterogêneo

> [nome] apresentou perfil cognitivo heterogêneo, com discrepâncias relevantes entre [domínios]. Embora o QI Total esteja classificado como [classificação], sua interpretação deve ser cautelosa, pois a média global pode mascarar áreas de maior eficiência e fragilidades específicas. Em análise clínica, mostra-se mais adequado enfatizar a leitura dos índices fatoriais e dos subtestes, especialmente [domínios fortes] e [domínios frágeis].

## 27. Modelo para análise breve

> O desempenho de [nome] no WAIS-III indica funcionamento intelectual global na faixa [classificação]. O perfil mostra [homogeneidade/heterogeneidade], com melhor desempenho em [áreas] e fragilidades relativas em [áreas]. Os resultados sugerem [síntese funcional]. Em análise clínica, esses achados devem ser integrados às queixas de [queixa] e aos demais instrumentos aplicados, não sendo suficientes, isoladamente, para definição diagnóstica.

## 28. Hipótese Diagnóstica

A seção de hipótese diagnóstica deve ser usada quando solicitada pelo usuário ou quando o texto for parte da conclusão do laudo.

Modelo quando houver suporte integrado:

> Hipótese Diagnóstica: Os resultados do WAIS-III, integrados aos dados da anamnese, observação clínica e demais instrumentos aplicados, contribuem para a hipótese diagnóstica de [condição], considerando [justificativa]. Ressalta-se que o WAIS-III não estabelece diagnóstico de forma isolada, sendo sua contribuição voltada à caracterização do perfil intelectual e dos domínios cognitivos associados.

Modelo quando não houver suporte suficiente:

> Hipótese Diagnóstica: Os achados do WAIS-III, isoladamente, não sustentam hipótese diagnóstica específica. O instrumento contribui para a caracterização do funcionamento intelectual, devendo ser integrado aos demais dados clínicos para conclusão diagnóstica.

## 29. Regras de redação conforme preferência do usuário

A IA deve seguir estas preferências nos laudos:

1. Usar linguagem técnica, precisa e de padrão ouro.
2. Evitar repetições desnecessárias.
3. Evitar iniciar frases repetidamente com “No” ou “Na”.
4. Usar “Em análise clínica” nas sínteses integrativas.
5. Não usar travessões longos.
6. Não usar o termo “informante”.
7. Não inserir tabelas nas interpretações, salvo solicitação expressa.
8. Usar apenas o primeiro nome do paciente no corpo analítico, salvo orientação diferente.
9. Não iniciar conclusão geral com “Diante da análise integrada”.
10. Quando usar “Diante da integração...”, escrever “conclui-se que”, nunca “verifica-se que”.
11. Sempre que houver hipótese diagnóstica, usar a expressão “hipótese diagnóstica”.
12. Não usar “leve/moderado/severo” para TEA conforme nomenclatura antiga; usar nível de suporte quando aplicável ao DSM-5-TR™.
13. Não usar linhas divisórias no corpo do laudo.
14. Não expor dados brutos desnecessários no texto final.
15. Não deixar conteúdo após referências bibliográficas.

## 30. Procedimentos

Quando o usuário pedir a seção “Procedimentos”, usar:

> Escala Wechsler de Inteligência para Adultos – Terceira Edição (WAIS-III), aplicada com o objetivo de avaliar o funcionamento intelectual global, o desempenho verbal, o desempenho de execução e os índices fatoriais de compreensão verbal, organização perceptual, memória operacional e velocidade de processamento.

## 31. Referência bibliográfica

Usar a referência compatível com o material utilizado pelo serviço. Sugestões:

> WECHSLER, D.; NASCIMENTO, E. WAIS-III: Escala de Inteligência Wechsler para Adultos: Manual. São Paulo: Pearson Clinical Brasil/Casa do Psicólogo, 2004.

Ou, quando a versão de administração e aplicação adotada for a da apostila:

> WECHSLER, D.; NASCIMENTO, E. Escala Wechsler de Inteligência para Adultos (WAIS-III) – Terceira Edição: Administração e Aplicação. São Paulo: Hogrefe, 2023.

A referência final deve sempre corresponder ao manual efetivamente utilizado no serviço.

## 32. Checklist de qualidade

Antes de entregar a análise, a IA deve confirmar:

- o texto fala apenas do WAIS-III;
- a idade e versão normativa foram consideradas;
- subtestes, quocientes e índices estão coerentes;
- não há nome de outro paciente;
- não há valores inventados;
- percentis e intervalos de confiança só aparecem se fornecidos;
- classificações batem com os valores;
- QIT não foi superinterpretado quando o perfil é heterogêneo;
- discrepâncias foram interpretadas com valor crítico;
- facilidades e dificuldades relativas foram baseadas em comparação intraindividual;
- subtestes foram interpretados por construto;
- observações qualitativas foram integradas;
- fatores interferentes foram considerados;
- hipótese diagnóstica não foi fechada apenas pelo WAIS-III;
- o texto está técnico, claro, sem contradições e sem excesso de repetição.

## 33. Prompt de uso interno

Use este prompt quando for acionar a skill:

> Analise os resultados do WAIS-III em padrão ouro internacional, usando apenas dados fornecidos. Não interprete WISC-IV, WASI ou outros testes. Verifique validade da aplicação, QIT, QIV, QIE, ICV, IOP, IMO e IVP. Analise discrepâncias, facilidades e dificuldades relativas quando os dados permitirem. Interprete subtestes por construto, integrando aspectos quantitativos e qualitativos. Use linguagem técnica, sem tabelas, sem expor itens protegidos e sem fechar diagnóstico apenas pelo WAIS-III. Finalize com síntese iniciada por “Em análise clínica” e inclua “Hipótese Diagnóstica” apenas quando houver dados integrados suficientes.

## 34. Saída esperada

A resposta final deve ser um texto fluido, técnico e clinicamente integrado, com esta forma:

```markdown
### WAIS-III – Escala Wechsler de Inteligência para Adultos

[Introdução técnica]

[Funcionamento intelectual global]

[QIV, QIE e comparação]

[ICV, IOP, IMO e IVP]

[Subtestes relevantes]

[Discrepâncias e facilidades/dificuldades relativas]

[Integração clínica]

[Hipótese Diagnóstica, se aplicável]
```

## 35. Critério final de excelência

A análise só estará em padrão ouro quando responder claramente:

1. Qual é o nível global de funcionamento intelectual?
2. O QIT é representativo ou deve ser interpretado com cautela?
3. Quais domínios estão mais preservados?
4. Quais domínios estão fragilizados?
5. Quais achados são estatisticamente relevantes?
6. Quais achados são clinicamente relevantes?
7. Como o perfil explica as queixas do paciente?
8. Quais limitações devem ser consideradas?
9. O texto evita diagnóstico isolado pelo WAIS-III?
10. A síntese final orienta a formulação clínica e os encaminhamentos?
