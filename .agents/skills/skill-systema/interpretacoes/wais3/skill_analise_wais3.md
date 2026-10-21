# skill_analise_wais3.md

# Skill completa para análise do WAIS-III

## 1. Escopo obrigatório

Esta skill deve ser usada exclusivamente para análise, interpretação e redação clínica dos resultados da **Escala de Inteligência Wechsler para Adultos – Terceira Edição (WAIS-III)**.

Não usar esta skill para WISC-IV, WASI, WAIS-IV ou outros instrumentos. Quando o material de apoio trouxer conteúdos mistos de WISC-IV, WAIS-III e WASI, filtrar apenas os dados, regras, subtestes, índices e procedimentos relacionados ao WAIS-III.

A skill deve orientar a IA a produzir uma análise técnica, auditável, coerente e clinicamente integrada do WAIS-III, sem reproduzir itens protegidos do teste, tabelas normativas integrais ou conteúdos restritos do manual.

## 2. Objetivo da skill

Gerar interpretação clínica do WAIS-III em padrão técnico elevado, considerando:

1. validade da aplicação;
2. idade cronológica e faixa etária do instrumento;
3. pontos brutos;
4. pontos ponderados por subteste;
5. somas de pontos ponderados;
6. quocientes intelectuais;
7. índices fatoriais;
8. percentis;
9. intervalos de confiança;
10. discrepâncias clinicamente relevantes;
11. facilidades e dificuldades relativas;
12. observações comportamentais;
13. integração com anamnese, queixa principal e demais instrumentos do processo avaliativo.

A análise nunca deve se limitar à leitura isolada do QI Total. O resultado deve ser interpretado por níveis: funcionamento global, discrepâncias entre escalas, índices fatoriais, subtestes, padrão intraindividual e implicações funcionais.

## 3. Dados mínimos de entrada

A IA deve solicitar ou receber, preferencialmente em estrutura padronizada, os seguintes campos:

```json
{
  "paciente": {
    "nome": "",
    "idade": "",
    "data_nascimento": "",
    "data_aplicacao": "",
    "escolaridade": "",
    "ocupacao": "",
    "motivo_encaminhamento": ""
  },
  "wais3": {
    "subtestes": {
      "Completar Figuras": {"bruto": null, "ponderado": null},
      "Vocabulário": {"bruto": null, "ponderado": null},
      "Códigos": {"bruto": null, "ponderado": null},
      "Semelhanças": {"bruto": null, "ponderado": null},
      "Cubos": {"bruto": null, "ponderado": null},
      "Aritmética": {"bruto": null, "ponderado": null},
      "Raciocínio Matricial": {"bruto": null, "ponderado": null},
      "Dígitos": {"bruto": null, "ponderado": null},
      "Informação": {"bruto": null, "ponderado": null},
      "Arranjo de Figuras": {"bruto": null, "ponderado": null},
      "Compreensão": {"bruto": null, "ponderado": null},
      "Procurar Símbolos": {"bruto": null, "ponderado": null},
      "Sequência de Números e Letras": {"bruto": null, "ponderado": null},
      "Armar Objetos": {"bruto": null, "ponderado": null}
    },
    "quocientes": {
      "QIV": {"valor": null, "percentil": null, "intervalo_confianca": "", "classificacao": ""},
      "QIE": {"valor": null, "percentil": null, "intervalo_confianca": "", "classificacao": ""},
      "QIT": {"valor": null, "percentil": null, "intervalo_confianca": "", "classificacao": ""}
    },
    "indices": {
      "ICV": {"valor": null, "percentil": null, "intervalo_confianca": "", "classificacao": ""},
      "IOP": {"valor": null, "percentil": null, "intervalo_confianca": "", "classificacao": ""},
      "IMO": {"valor": null, "percentil": null, "intervalo_confianca": "", "classificacao": ""},
      "IVP": {"valor": null, "percentil": null, "intervalo_confianca": "", "classificacao": ""}
    },
    "discrepancias": [],
    "facilidades_dificuldades": [],
    "observacoes_qualitativas": ""
  }
}
```

Se algum dado essencial estiver ausente, a IA deve declarar a limitação e evitar inferências indevidas.

## 4. Validação inicial antes da análise

Antes de interpretar, a IA deve verificar:

1. O instrumento é WAIS-III.
2. O avaliado está na faixa etária do WAIS-III, de 17 a 89 anos. Para o subteste Arranjo de Objetos/Armar Objetos, observar restrições específicas do manual quando aplicáveis.
3. A aplicação seguiu a ordem padronizada.
4. Foram respeitados itens de entrada, sequência inversa, regras de interrupção e limites de tempo.
5. Houve registro adequado de respostas, incluindo inquérito, sem resposta, resposta incompleta, acertos, erros e apontamentos corretos ou incorretos.
6. A conversão de pontos brutos em pontos ponderados foi realizada pelas tabelas oficiais correspondentes à idade.
7. A conversão das somas de pontos ponderados em quocientes/índices foi feita pelas tabelas oficiais.
8. Substituições por subtestes suplementares respeitaram os limites técnicos.
9. O QI Total é interpretável ou há heterogeneidade suficiente para exigir cautela.
10. A interpretação considera dados qualitativos, não apenas números.

## 5. Composição do WAIS-III

### 5.1 Subtestes principais e suplementares

A IA deve reconhecer os 14 subtestes do WAIS-III:

1. Completar Figuras;
2. Vocabulário;
3. Códigos;
4. Semelhanças;
5. Cubos;
6. Aritmética;
7. Raciocínio Matricial;
8. Dígitos;
9. Informação;
10. Arranjo de Figuras;
11. Compreensão;
12. Procurar Símbolos;
13. Sequência de Números e Letras;
14. Armar Objetos.

A IA deve distinguir subtestes usados para os quocientes principais, índices fatoriais e subtestes suplementares, conforme o manual oficial e o protocolo utilizado.

### 5.2 Quocientes principais

A análise deve contemplar:

**QI Verbal (QIV)**  
Representa desempenho em tarefas mediadas pela linguagem, raciocínio verbal, repertório conceitual, memória auditiva imediata, conhecimento adquirido e compreensão social verbal.

**QI de Execução (QIE)**  
Representa desempenho em tarefas visuoespaciais, organização perceptual, raciocínio não verbal, análise de padrões, velocidade grafomotora e solução de problemas com menor mediação verbal.

**QI Total (QIT)**  
Representa estimativa global do funcionamento intelectual, desde que o perfil seja suficientemente homogêneo para permitir interpretação global. Quando houver discrepâncias expressivas entre QIV e QIE ou entre índices fatoriais, o QIT deve ser interpretado com cautela.

### 5.3 Índices fatoriais

A análise deve contemplar:

**Índice de Compreensão Verbal (ICV)**  
Avalia formação de conceitos verbais, raciocínio verbal, conhecimento cristalizado, abstração, vocabulário, acesso lexical e compreensão de informações culturalmente aprendidas.

**Índice de Organização Perceptual (IOP)**  
Avalia raciocínio fluido não verbal, análise visuoespacial, organização perceptiva, percepção de relações entre estímulos, síntese visual e resolução de problemas visuais.

**Índice de Memória Operacional (IMO)**  
Avalia manutenção e manipulação mental de informações, atenção auditiva, controle mental, memória imediata, sequenciamento e resistência à distração.

**Índice de Velocidade de Processamento (IVP)**  
Avalia rapidez de varredura visual, discriminação perceptiva, velocidade grafomotora, atenção visual sustentada, eficiência operacional e execução sob limite de tempo.

## 6. Regras de correção que a IA deve respeitar

### 6.1 Pontos brutos

A IA deve considerar que os pontos brutos são obtidos diretamente no protocolo, conforme os critérios específicos de cada subteste.

Nunca inventar pontos brutos ausentes.

Nunca recalcular pontuação de item sem acesso legítimo ao manual e ao protocolo de resposta.

### 6.2 Conversão em pontos ponderados

A IA deve converter pontos brutos em pontos ponderados apenas quando houver tabela oficial licenciada disponível no sistema.

Sem tabela oficial, a IA deve escrever:

> A conversão dos pontos brutos em pontos ponderados deve ser realizada exclusivamente pelas tabelas normativas oficiais do WAIS-III, considerando a idade cronológica do avaliado. Sem acesso à tabela normativa correspondente, não é adequado estimar ou interpolar escores.

### 6.3 Pontos ponderados

Os pontos ponderados dos subtestes devem ser interpretados em termos normativos e intraindividuais. Não basta dizer se estão altos ou baixos. A IA deve relacionar o subteste ao construto cognitivo correspondente e ao padrão global do avaliado.

### 6.4 Somas de pontos ponderados

A IA deve calcular as somas conforme a estrutura oficial do WAIS-III. Na configuração tradicional:

**QI Verbal**  
Vocabulário + Semelhanças + Aritmética + Dígitos + Informação + Compreensão.

**QI de Execução**  
Completar Figuras + Códigos + Cubos + Raciocínio Matricial + Arranjo de Figuras.

**QI Total**  
Soma dos subtestes principais utilizados para QIV e QIE.

**ICV**  
Vocabulário + Semelhanças + Informação.

**IOP**  
Completar Figuras + Cubos + Raciocínio Matricial.

**IMO**  
Aritmética + Dígitos + Sequência de Números e Letras.

**IVP**  
Códigos + Procurar Símbolos.

Quando houver substituição ou versão específica do protocolo, a IA deve seguir exatamente a regra do manual/protocolo utilizado e registrar a substituição.

### 6.5 Conversão em QI e índices

A IA deve converter as somas de pontos ponderados em QIV, QIE, QIT, ICV, IOP, IMO e IVP apenas por tabelas oficiais.

A IA deve incluir, quando disponíveis:

1. valor do ponto composto;
2. classificação normativa;
3. percentil;
4. intervalo de confiança;
5. observação interpretativa.

## 7. Classificação normativa

### 7.1 Pontos compostos

Usar a seguinte faixa classificatória, salvo se o manual/protocolo do serviço adotar outra nomenclatura:

| Ponto composto | Classificação |
|---:|---|
| ≥ 130 | Muito Superior |
| 120 a 129 | Superior |
| 110 a 119 | Média Superior |
| 90 a 109 | Média |
| 80 a 89 | Média Inferior |
| 70 a 79 | Limítrofe |
| ≤ 69 | Extremamente Baixo |

### 7.2 Pontos ponderados dos subtestes

Usar a seguinte leitura referencial, salvo regra específica do serviço:

| Ponto ponderado | Classificação interpretativa |
|---:|---|
| 17 a 19 | Muito Superior |
| 15 a 16 | Superior |
| 13 a 14 | Média Superior |
| 8 a 12 | Média |
| 6 a 7 | Média Inferior |
| 4 a 5 | Limítrofe |
| 1 a 3 | Extremamente Baixo |

A IA deve evitar linguagem determinista. Em vez de “déficit”, usar “desempenho abaixo do esperado” quando o resultado isolado não for suficiente para inferir prejuízo clínico.

## 8. Estrutura obrigatória da análise

A análise do WAIS-III deve seguir esta sequência:

1. Introdução técnica do instrumento.
2. Condições de validade e observações clínicas relevantes.
3. Funcionamento intelectual global.
4. Comparação entre QIV, QIE e QIT.
5. Análise dos índices fatoriais.
6. Análise dos subtestes e processos cognitivos.
7. Discrepâncias, facilidades e dificuldades relativas.
8. Integração clínica com queixa, anamnese e demais instrumentos.
9. Síntese interpretativa.
10. Hipótese diagnóstica, quando aplicável, sempre com cautela e sem fechar diagnóstico apenas pelo WAIS-III.

## 9. Introdução técnica padrão

Usar o seguinte modelo, adaptando apenas quando necessário:

> A Escala de Inteligência Wechsler para Adultos – Terceira Edição (WAIS-III) é um instrumento de aplicação individual destinado à avaliação do funcionamento intelectual em adultos, contemplando medidas de desempenho verbal, desempenho de execução, funcionamento intelectual global e índices fatoriais relacionados à compreensão verbal, organização perceptual, memória operacional e velocidade de processamento. Seus resultados permitem examinar não apenas o nível global de eficiência intelectual, mas também o padrão de forças e fragilidades cognitivas do avaliado, devendo ser interpretados em conjunto com os dados clínicos, histórico de desenvolvimento, escolaridade, contexto sociocultural, observações comportamentais e demais instrumentos utilizados no processo avaliativo.

## 10. Análise do funcionamento intelectual global

### 10.1 Quando o QIT é homogêneo e interpretável

Modelo:

> Os resultados obtidos no WAIS-III indicam que [nome] apresentou funcionamento intelectual global situado na faixa [classificação], conforme evidenciado pelo QI Total de [valor] ([percentil], intervalo de confiança [IC]). Esse resultado sugere desempenho global [adequado/reduzido/elevado] para a faixa etária, considerando as demandas cognitivas gerais avaliadas pelo instrumento. A interpretação do QI Total mostra-se clinicamente pertinente, uma vez que não foram observadas discrepâncias expressivas que comprometam sua representatividade como estimativa global do funcionamento intelectual.

### 10.2 Quando o QIT exige cautela

Modelo:

> Embora o QI Total de [valor] situe-se na faixa [classificação], sua interpretação deve ser realizada com cautela, pois o perfil cognitivo apresentou discrepâncias relevantes entre os domínios avaliados. Nesses casos, o QIT pode não representar de maneira suficientemente precisa o funcionamento cognitivo global, sendo clinicamente mais informativa a análise dos índices fatoriais, dos quocientes verbal e de execução e do padrão de desempenho nos subtestes.

## 11. Análise do QI Verbal

A IA deve interpretar o QIV considerando linguagem, raciocínio verbal, conhecimento adquirido, memória verbal imediata e compreensão social verbal.

Modelo:

> O QI Verbal situou-se na faixa [classificação], indicando [preservação/redução/elevação] das habilidades mediadas pela linguagem. Esse resultado sugere que [nome] apresenta [capacidade adequada/dificuldade relativa/desempenho superior] em tarefas que exigem compreensão verbal, formação de conceitos, acesso ao conhecimento previamente adquirido e raciocínio verbal. Deve-se considerar, contudo, a influência da escolaridade, repertório cultural, história ocupacional, qualidade da estimulação linguística e condições emocionais durante a avaliação.

## 12. Análise do QI de Execução

A IA deve interpretar o QIE considerando raciocínio não verbal, organização visuoespacial, análise perceptiva, velocidade e solução de problemas visuais.

Modelo:

> O QI de Execução apresentou classificação [classificação], sugerindo desempenho [adequado/reduzido/elevado] em tarefas que demandam organização visuoespacial, raciocínio não verbal, análise de padrões, integração perceptiva e resolução de problemas com menor dependência de linguagem. Esse resultado deve ser interpretado em conjunto com a velocidade de execução, coordenação visuomotora, tolerância à pressão de tempo, atenção visual e comportamento observado durante tarefas manipulativas ou perceptuais.

## 13. Comparação QIV x QIE

A IA deve verificar se a diferença entre QIV e QIE é significativa segundo os valores críticos oficiais.

### 13.1 Diferença não significativa

> A comparação entre QI Verbal e QI de Execução não indica discrepância clinicamente significativa, sugerindo perfil relativamente equilibrado entre habilidades verbais e não verbais. Dessa forma, a análise global pode considerar uma distribuição mais homogênea do desempenho intelectual.

### 13.2 QIV maior que QIE

> A diferença entre QI Verbal e QI de Execução favorece o desempenho verbal, sugerindo melhor rendimento em tarefas dependentes de raciocínio verbal, conhecimento adquirido e elaboração conceitual quando comparadas às tarefas visuoespaciais, perceptivas ou executadas sob maior demanda visuomotora. Esse padrão pode indicar maior eficiência em contextos mediados pela linguagem e possível dificuldade relativa em tarefas práticas, visuais, rápidas ou perceptualmente organizadas.

### 13.3 QIE maior que QIV

> A diferença entre QI de Execução e QI Verbal favorece o desempenho não verbal, sugerindo melhor rendimento em tarefas de raciocínio visuoespacial, análise de padrões e solução de problemas perceptivos quando comparadas às tarefas de maior exigência verbal. Esse padrão pode indicar maior eficiência em contextos práticos e visuais, com possível dificuldade relativa em tarefas que exigem verbalização, abstração linguística ou acesso formal ao conhecimento adquirido.

## 14. Análise dos índices fatoriais

### 14.1 ICV

> O Índice de Compreensão Verbal situou-se na faixa [classificação], indicando [nível] de eficiência em tarefas de raciocínio verbal, formação de conceitos, vocabulário, abstração e conhecimento cristalizado. Esse resultado sugere que [nome] apresenta [descrição clínica], especialmente em situações que exigem compreensão de informações verbais, elaboração conceitual e expressão verbal organizada.

### 14.2 IOP

> O Índice de Organização Perceptual apresentou classificação [classificação], refletindo [nível] desempenho em tarefas de raciocínio fluido visual, percepção de relações espaciais, análise e síntese de estímulos não verbais. Esse resultado sugere [descrição clínica], devendo ser interpretado em conjunto com a coordenação visuomotora, planejamento visual, velocidade de execução e comportamento frente a tarefas novas.

### 14.3 IMO

> O Índice de Memória Operacional situou-se na faixa [classificação], indicando [nível] capacidade de manter, manipular e reorganizar informações mentalmente por curto período. Esse domínio é sensível a atenção sustentada, controle mental, resistência à distração e eficiência executiva. Desempenhos reduzidos nesse índice podem estar associados a dificuldades em cálculos mentais, acompanhamento de instruções, organização de informações sequenciais e execução de tarefas sob carga cognitiva.

### 14.4 IVP

> O Índice de Velocidade de Processamento apresentou classificação [classificação], sugerindo [nível] eficiência em tarefas que exigem rapidez visuomotora, discriminação visual, atenção sustentada e execução sob limite de tempo. Reduções nesse índice podem refletir lentificação cognitiva, baixa velocidade grafomotora, oscilação atencional, cautela excessiva, ansiedade de desempenho, fadiga ou dificuldade de automatização, devendo ser integradas às observações clínicas.

## 15. Interpretação dos subtestes

A IA deve interpretar os subtestes apenas quando houver ponto ponderado ou classificação.

### 15.1 Completar Figuras

Construtos principais: atenção a detalhes visuais, discriminação perceptiva, memória visual de objetos familiares, organização perceptiva e reconhecimento de elementos essenciais.

Modelo:

> Em Completar Figuras, [nome] apresentou desempenho [classificação], sugerindo [preservação/dificuldade/força] na identificação de detalhes relevantes em estímulos visuais e na discriminação perceptiva de informações incompletas.

### 15.2 Vocabulário

Construtos principais: repertório lexical, conhecimento cristalizado, expressão verbal, formação conceitual e desenvolvimento linguístico.

> Em Vocabulário, o desempenho [classificação] indica [nível] de repertório verbal, acesso lexical e capacidade de definir conceitos. Esse subteste é fortemente influenciado por escolaridade, estimulação sociocultural e experiência linguística.

### 15.3 Códigos

Construtos principais: velocidade grafomotora, aprendizagem associativa, atenção visual, varredura, coordenação visuomotora e execução sob tempo.

> Em Códigos, o resultado [classificação] sugere [nível] de velocidade grafomotora, atenção visual sustentada e eficiência na associação rápida entre símbolos. Baixos resultados podem refletir lentidão motora, oscilação atencional, dificuldade de automatização ou impacto emocional frente à pressão de tempo.

### 15.4 Semelhanças

Construtos principais: abstração verbal, categorização, raciocínio conceitual e pensamento relacional.

> Em Semelhanças, [nome] apresentou desempenho [classificação], indicando [nível] capacidade de abstração verbal, categorização conceitual e identificação de relações entre conceitos.

### 15.5 Cubos

Construtos principais: organização visuoespacial, análise e síntese visual, coordenação visuomotora, planejamento e raciocínio não verbal.

> Em Cubos, o desempenho [classificação] sugere [nível] habilidade de análise visuoespacial, organização perceptiva, planejamento construtivo e integração visuomotora.

### 15.6 Aritmética

Construtos principais: raciocínio quantitativo, memória operacional, atenção auditiva, cálculo mental e controle sob tempo.

> Em Aritmética, o desempenho [classificação] indica [nível] eficiência em cálculo mental, raciocínio quantitativo e manutenção de informações auditivas durante a resolução de problemas. Deve-se considerar influência de escolaridade, ansiedade frente a tarefas numéricas e atenção sustentada.

### 15.7 Raciocínio Matricial

Construtos principais: raciocínio fluido, inferência visual, reconhecimento de padrões, análise lógica não verbal e resolução de problemas novos.

> Em Raciocínio Matricial, [nome] apresentou desempenho [classificação], sugerindo [nível] raciocínio fluido não verbal, identificação de padrões visuais e capacidade de inferência lógica.

### 15.8 Dígitos

Construtos principais: memória auditiva imediata, atenção, sequenciamento, concentração e memória operacional.

> Em Dígitos, o resultado [classificação] indica [nível] capacidade de atenção auditiva, memória imediata e manipulação sequencial de informações. Desempenho reduzido pode estar associado a dificuldades de concentração, controle mental ou resistência à interferência.

### 15.9 Informação

Construtos principais: conhecimento factual, memória semântica, aprendizagem cultural e repertório de informações gerais.

> Em Informação, [nome] apresentou desempenho [classificação], sugerindo [nível] de conhecimento factual e acesso a informações previamente adquiridas. A interpretação deve considerar escolaridade, oportunidades educacionais e contexto sociocultural.

### 15.10 Arranjo de Figuras

Construtos principais: sequenciamento lógico, compreensão de relações sociais, antecipação de consequências, organização temporal e raciocínio prático visual.

> Em Arranjo de Figuras, o desempenho [classificação] sugere [nível] capacidade de organizar sequências visuais com coerência lógica e compreender relações temporais e sociais implícitas.

### 15.11 Compreensão

Construtos principais: julgamento social, compreensão de normas, raciocínio prático verbal, solução de problemas cotidianos e conhecimento social.

> Em Compreensão, [nome] apresentou desempenho [classificação], indicando [nível] capacidade de julgamento social, raciocínio prático verbal e compreensão de normas convencionais. Resultados reduzidos podem refletir dificuldades de abstração social, repertório sociocultural limitado ou rigidez no raciocínio prático.

### 15.12 Procurar Símbolos

Construtos principais: velocidade de processamento visual, discriminação visual, atenção seletiva, varredura visual e eficiência sob tempo.

> Em Procurar Símbolos, o desempenho [classificação] sugere [nível] velocidade de busca visual, discriminação perceptiva e atenção seletiva sob limite temporal.

### 15.13 Sequência de Números e Letras

Construtos principais: memória operacional, manipulação mental, sequenciamento, atenção auditiva e controle executivo.

> Em Sequência de Números e Letras, [nome] apresentou desempenho [classificação], indicando [nível] capacidade de reorganizar mentalmente informações auditivas, manter instruções e manipular estímulos em sequência.

### 15.14 Armar Objetos

Construtos principais: organização visuoespacial, síntese perceptiva, percepção de partes e todo, planejamento construtivo e coordenação visuomotora.

> Em Armar Objetos, o desempenho [classificação] sugere [nível] habilidade de integrar partes em um todo coerente, com participação de planejamento visuoconstrutivo e análise perceptiva.

## 16. Facilidades e dificuldades relativas

A IA deve calcular facilidades e dificuldades relativas quando houver dados suficientes.

Procedimento:

1. Calcular a média dos pontos ponderados da Escala Verbal.
2. Calcular a média dos pontos ponderados da Escala de Execução.
3. Calcular a média dos pontos ponderados do conjunto total de subtestes principais.
4. Comparar cada subteste com a média correspondente.
5. Verificar se a diferença excede o valor crítico oficial.
6. Verificar frequência acumulada ou taxa-base, quando disponível.
7. Classificar como facilidade relativa ou dificuldade relativa apenas quando houver suporte estatístico e coerência clínica.

Texto para facilidade relativa:

> O desempenho em [subteste] configurou facilidade relativa no perfil de [nome], indicando rendimento superior ao seu próprio padrão médio em tarefas que exigem [construtos]. Esse achado sugere uma área de maior eficiência intraindividual, especialmente quando comparada aos demais domínios avaliados.

Texto para dificuldade relativa:

> O desempenho em [subteste] configurou dificuldade relativa no perfil de [nome], indicando rendimento inferior ao seu próprio padrão médio em tarefas que exigem [construtos]. Esse achado não deve ser interpretado de forma isolada como déficit, mas como fragilidade relativa dentro do perfil cognitivo observado.

## 17. Comparação entre discrepâncias

A IA deve realizar comparação entre discrepâncias apenas quando houver valores oficiais de diferença, valor crítico e taxa-base.

Procedimento:

1. Transferir os valores dos pontos compostos ou pontos ponderados para a tabela de comparação.
2. Subtrair o segundo valor do primeiro.
3. Manter o sinal da diferença, positivo ou negativo.
4. Consultar o valor crítico oficial.
5. Comparar diferença observada com valor crítico.
6. Registrar se a diferença é estatisticamente significativa.
7. Consultar a frequência acumulada/taxa-base.
8. Interpretar apenas diferenças raras ou clinicamente relevantes com maior peso.

Modelo:

> A discrepância entre [índice 1] e [índice 2] foi de [diferença] pontos. Considerando o valor crítico de [valor], essa diferença [atinge/não atinge] significância estatística. Quando considerada a frequência acumulada de [taxa-base], observa-se que esse padrão é [comum/incomum] na amostra normativa, devendo ser interpretado [com cautela/como achado clinicamente relevante] no contexto do funcionamento global de [nome].

## 18. Critérios de cautela interpretativa

A IA deve usar linguagem de cautela quando houver:

1. discrepância expressiva entre QIV e QIE;
2. discrepância expressiva entre índices fatoriais;
3. grande variação entre subtestes;
4. baixo engajamento;
5. ansiedade, fadiga, dor, privação de sono ou uso de medicação com potencial impacto cognitivo;
6. alterações sensoriais ou motoras;
7. baixa escolaridade ou escolaridade irregular;
8. diferenças culturais ou linguísticas;
9. aplicação em múltiplas sessões com intervalo prolongado;
10. subtestes não aplicados;
11. substituições acima do permitido;
12. dados normativos incompletos.

Modelo:

> A interpretação dos resultados deve ser realizada com cautela, uma vez que [descrever fator]. Esse aspecto pode ter influenciado o desempenho em tarefas que exigem [domínios], especialmente nos subtestes [subtestes]. Dessa forma, recomenda-se priorizar a análise integrada do perfil, em vez de conclusões baseadas apenas em pontuações isoladas.

## 19. Integração clínica

A IA deve sempre integrar o WAIS-III com:

1. motivo do encaminhamento;
2. histórico escolar e ocupacional;
3. queixas cognitivas;
4. observação clínica durante a aplicação;
5. resultados de atenção, memória, funções executivas e escalas emocionais, quando disponíveis;
6. sintomas de ansiedade, depressão, TDAH, TEA, envelhecimento, declínio cognitivo ou outras hipóteses clínicas;
7. funcionalidade cotidiana.

Nunca escrever:

> “O WAIS-III confirma diagnóstico de...”

Preferir:

> “Os achados do WAIS-III são compatíveis com...”
> “O perfil observado pode contribuir para a hipótese diagnóstica de...”
> “Os resultados devem ser integrados aos demais dados clínicos antes de qualquer conclusão diagnóstica.”

## 20. Modelo completo de análise textual

### 20.1 Modelo quando perfil é globalmente preservado

> Os resultados obtidos na Escala de Inteligência Wechsler para Adultos – Terceira Edição (WAIS-III) indicam que [nome] apresentou funcionamento intelectual global situado na faixa [classificação], com QI Total de [valor] ([percentil], intervalo de confiança [IC]). Esse desempenho sugere eficiência intelectual global [adequada/elevada] para sua faixa etária, com recursos cognitivos compatíveis com as demandas gerais de raciocínio, compreensão, resolução de problemas e aprendizagem avaliadas pelo instrumento.
>
> O QI Verbal situou-se na faixa [classificação], indicando [descrição]. O QI de Execução apresentou classificação [classificação], sugerindo [descrição]. A comparação entre esses quocientes [indica/não indica] discrepância clinicamente significativa, o que [permite interpretação global mais homogênea/exige análise cautelosa do QI Total].
>
> Entre os índices fatoriais, o ICV apresentou desempenho [classificação], refletindo [descrição]. O IOP situou-se em [classificação], sugerindo [descrição]. O IMO foi classificado como [classificação], indicando [descrição]. O IVP apresentou desempenho [classificação], sugerindo [descrição].
>
> A análise dos subtestes evidencia [facilidades] e [dificuldades], apontando para um perfil caracterizado por [síntese]. Em análise clínica, os achados do WAIS-III sugerem [síntese funcional], devendo ser integrados aos demais dados da avaliação para compreensão diagnóstica e planejamento de conduta.

### 20.2 Modelo quando há rebaixamento global

> Os resultados obtidos no WAIS-III indicam funcionamento intelectual global situado na faixa [classificação], com QI Total de [valor] ([percentil], intervalo de confiança [IC]). Esse achado sugere desempenho global abaixo do esperado para a faixa etária, com impacto potencial em tarefas que exigem raciocínio, aprendizagem, resolução de problemas, organização mental e adaptação a demandas cognitivas complexas.
>
> O perfil deve ser interpretado considerando a distribuição dos resultados entre os domínios verbal, visuoespacial, memória operacional e velocidade de processamento. O QI Verbal apresentou classificação [classificação], enquanto o QI de Execução situou-se na faixa [classificação]. Essa configuração sugere [descrever se há equilíbrio ou discrepância].
>
> Em análise clínica, o padrão observado pode estar associado a [hipóteses funcionais], especialmente quando integrado às queixas de [queixas] e aos dados de [outros instrumentos]. O WAIS-III, isoladamente, não permite fechamento diagnóstico, mas contribui para caracterizar o funcionamento intelectual e orientar a hipótese diagnóstica de [hipótese], quando sustentada pelos demais achados clínicos.

### 20.3 Modelo quando há heterogeneidade importante

> O desempenho de [nome] no WAIS-III revelou perfil cognitivo heterogêneo, com variações relevantes entre os domínios avaliados. Embora o QI Total tenha sido de [valor], classificado como [classificação], esse índice deve ser interpretado com cautela, pois discrepâncias entre [domínios] reduzem sua representatividade como estimativa única do funcionamento intelectual.
>
> Nessa configuração, a análise dos índices fatoriais mostra-se clinicamente mais informativa. O desempenho em [índice mais alto] sugere [força], enquanto o desempenho em [índice mais baixo] indica [fragilidade]. Esse contraste pode se manifestar funcionalmente como [implicações], especialmente em contextos que exigem [demandas].
>
> Em análise clínica, os resultados indicam que [nome] apresenta recursos preservados em [áreas] e fragilidades relativas em [áreas]. Esse padrão deve ser integrado às observações comportamentais e aos demais instrumentos para formulação da hipótese diagnóstica e definição de encaminhamentos.

## 21. Hipótese diagnóstica

A seção de hipótese diagnóstica deve aparecer apenas quando solicitada ou quando a análise estiver sendo integrada ao laudo completo.

A IA deve escrever:

> Hipótese Diagnóstica: Os resultados do WAIS-III, integrados aos dados de anamnese, observação clínica e demais instrumentos aplicados, contribuem para a hipótese diagnóstica de [condição], considerando [justificativa técnica]. Ressalta-se que o WAIS-III não deve ser utilizado isoladamente para fechamento diagnóstico.

Quando o WAIS-III não sustenta hipótese específica:

> Hipótese Diagnóstica: Os achados do WAIS-III, isoladamente, não sustentam hipótese diagnóstica específica. O instrumento contribui para a caracterização do perfil intelectual e deve ser integrado aos demais dados clínicos para conclusão diagnóstica.

## 22. Regras de redação para o padrão do laudo

A IA deve seguir estas regras:

1. Usar linguagem técnica, clara e objetiva.
2. Evitar repetição excessiva de início de frases com “No” ou “Na”.
3. Usar “Em análise clínica” para iniciar sínteses integrativas.
4. Não usar travessões longos.
5. Não usar o termo “informante”.
6. Não inserir tabelas nas interpretações, salvo solicitação expressa.
7. Usar apenas o primeiro nome do paciente nas seções analíticas, salvo orientação contrária.
8. Usar nome completo apenas na identificação e na conclusão geral, quando necessário.
9. Não iniciar conclusão geral com “Diante da análise integrada”.
10. Quando usar “Diante da integração...”, escrever “conclui-se que”, nunca “verifica-se que”.
11. Não escrever diagnóstico fechado com base apenas no WAIS-III.
12. Não mencionar itens específicos do teste.
13. Não expor conteúdo protegido do manual.
14. Não incluir dados brutos desnecessários no corpo interpretativo.
15. Não manter textos residuais após referências bibliográficas.

## 23. Procedimentos no laudo

Quando o usuário solicitar a seção “Procedimentos”, usar:

> Escala de Inteligência Wechsler para Adultos – Terceira Edição (WAIS-III), aplicada com o objetivo de avaliar o funcionamento intelectual global, o desempenho verbal, o desempenho de execução e os índices fatoriais de compreensão verbal, organização perceptual, memória operacional e velocidade de processamento.

## 24. Referência bibliográfica

Usar, quando o WAIS-III tiver sido aplicado:

> WECHSLER, D. WAIS-III: Escala de Inteligência Wechsler para Adultos: Manual. São Paulo: Pearson Clinical Brasil, 2004.

Se o serviço utilizar edição, adaptação ou manual específico diferente, substituir pela referência correta do material utilizado.

## 25. Checklist de auditoria antes de entregar a análise

Antes de finalizar, a IA deve verificar:

1. O texto menciona apenas WAIS-III, sem WISC-IV ou WASI.
2. O nome do paciente está correto.
3. Não há nome de outro paciente.
4. Todos os valores descritos correspondem aos dados fornecidos.
5. O QIT não foi supervalorizado quando há heterogeneidade importante.
6. Percentis e intervalos de confiança não foram inventados.
7. Classificações normativas estão coerentes com os pontos compostos.
8. Pontos ponderados foram interpretados de forma coerente com os subtestes.
9. Discrepâncias só foram interpretadas quando avaliadas por valor crítico.
10. Facilidades e dificuldades só foram descritas quando calculadas por comparação intraindividual.
11. O texto integra aspectos funcionais e clínicos.
12. O WAIS-III não foi usado isoladamente para diagnóstico.
13. Não há tabelas se o usuário pediu apenas texto.
14. Não há linguagem determinista, exagerada ou contraditória.
15. A análise termina com síntese clínica clara.

## 26. Saída esperada da IA

A IA deve entregar a análise no seguinte formato:

```markdown
### WAIS-III – Escala de Inteligência Wechsler para Adultos

[Introdução técnica breve]

[Análise do funcionamento intelectual global]

[Análise do QI Verbal e QI de Execução]

[Análise dos índices fatoriais]

[Análise dos subtestes relevantes]

[Discrepâncias, facilidades e dificuldades relativas]

[Integração clínica]

[Hipótese Diagnóstica, se aplicável]
```

## 27. Exemplo de prompt interno para a IA

> Analise os resultados do WAIS-III abaixo em padrão ouro internacional. Use apenas o primeiro nome do paciente no corpo do texto. Não use tabelas. Não interprete WISC-IV ou WASI. Faça análise do QIT, QIV, QIE, ICV, IOP, IMO e IVP. Verifique discrepâncias, facilidades e dificuldades relativas quando os dados permitirem. Integre os achados com a queixa clínica e finalize com uma síntese em “Em análise clínica”. Não feche diagnóstico apenas pelo WAIS-III.

## 28. Critério final de qualidade

A análise será considerada adequada quando responder a quatro perguntas:

1. Qual é o nível global de funcionamento intelectual?
2. O QIT representa bem o perfil ou deve ser interpretado com cautela?
3. Quais domínios cognitivos estão preservados, elevados ou fragilizados?
4. Qual é a implicação clínica e funcional desses achados dentro da avaliação neuropsicológica?

Se uma dessas perguntas não estiver respondida, a análise deve ser revisada.
