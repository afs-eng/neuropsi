# skill_wais3_padrao_ouro_melhoria_relatorio

## Objetivo

Melhorar, auditar e padronizar relatórios técnicos do **WAIS-III – Escala de Inteligência Wechsler para Adultos**, garantindo consistência psicométrica, interpretação clínica precisa, linguagem técnica de padrão ouro e prevenção de erros automáticos em índices, clusters, discrepâncias, GAI e síntese final.

Esta skill deve ser usada sempre que a IA precisar revisar, corrigir, gerar ou aprimorar um relatório WAIS-III no sistema NeuroAvalia.

---

## Escopo da skill

A skill se aplica a relatórios que contenham:

- Dados do avaliado.
- Resultados de QI Verbal, QI de Execução e QI Total.
- Índices fatoriais: ICV, IOP, IMO e IVP.
- Perfil dos subtestes.
- Comparações entre discrepâncias.
- Análise de clusters.
- Comparações clínicas entre clusters.
- GAI, quando calculado.
- Interpretação clínica.
- Síntese interpretativa para laudo.
- Pontos de atenção clínica.

A skill não deve criar diagnóstico isolado com base no WAIS-III. O instrumento deve ser tratado como medida de funcionamento intelectual e perfil cognitivo, exigindo integração com anamnese, observação clínica, histórico funcional, escolaridade, contexto sociocultural e demais instrumentos da avaliação neuropsicológica.

---

## Regras obrigatórias de auditoria antes da interpretação

Antes de escrever qualquer interpretação clínica, a IA deve auditar os dados. Se houver erro numérico, inconsistência psicométrica ou campo incompatível, a IA deve sinalizar o problema e não transformar o dado inconsistente em conclusão clínica.

### 1. Conferência dos índices principais

Validar obrigatoriamente:

- QIV: valor, percentil, intervalo de confiança e classificação.
- QIE: valor, percentil, intervalo de confiança e classificação.
- QIT: valor, percentil, intervalo de confiança e classificação.
- ICV: valor, percentil, intervalo de confiança e classificação.
- IOP: valor, percentil, intervalo de confiança e classificação.
- IMO: valor, percentil, intervalo de confiança e classificação.
- IVP: valor, percentil, intervalo de confiança e classificação.

A IA deve verificar se:

- O ponto composto é compatível com o percentil.
- O ponto composto está dentro do intervalo de confiança informado.
- A classificação corresponde ao valor do ponto composto.
- A soma dos pontos ponderados é coerente com o índice ou quociente apresentado.
- O gráfico representa corretamente os valores da tabela.

Se qualquer item estiver incompatível, usar a marcação:

> **Inconsistência psicométrica identificada:** [descrever o campo]. O dado deve ser revisado antes da interpretação clínica.

---

## Classificação dos pontos compostos

Usar a seguinte classificação, salvo se o manual ou tabela normativa configurada no sistema indicar outra classificação validada:

- **≤ 69:** Extremamente baixo.
- **70–79:** Limítrofe.
- **80–89:** Média inferior.
- **90–109:** Média.
- **110–119:** Média superior.
- **120–129:** Superior.
- **≥ 130:** Muito superior.

Não classificar um ponto composto apenas pelo percentil sem verificar o valor composto.

---

## Regra crítica para clusters

A análise de clusters deve passar por auditoria rígida.

### Campos obrigatórios por cluster

Para cada cluster, verificar:

- Nome do cluster.
- Código.
- Subtestes que compõem o cluster.
- Diferença entre maior e menor subteste.
- Se é interpretável ou não.
- Soma dos pontos ponderados.
- Ponto composto.
- Intervalo de confiança.
- Percentil.
- Classificação.

### Regra de homogeneidade interna

O cluster só deve ser interpretado clinicamente quando a diferença interna entre o maior e o menor subteste for inferior ao critério definido no sistema/manual.

Quando o cluster for marcado como **não interpretável**, a IA deve:

- Não usar o ponto composto como conclusão clínica.
- Não destacar o cluster como força ou fragilidade.
- Retornar a análise aos subtestes individuais.
- Explicar que a heterogeneidade interna impede leitura unitária do agrupamento.

Modelo de redação:

> O cluster [nome] não deve ser interpretado como medida unitária, pois apresentou heterogeneidade interna entre os subtestes que o compõem. Assim, seu ponto composto deve ser tratado apenas como informação técnica, sem uso como conclusão clínica. A interpretação deve retornar aos subtestes individuais e às observações qualitativas da aplicação.

### Regra de consistência entre ponto composto, percentil e IC

É proibido aceitar combinações incompatíveis. Exemplos de inconsistência:

- Ponto composto muito baixo com percentil médio.
- Ponto composto fora do intervalo de confiança informado.
- Classificação incompatível com o valor composto.
- Diferenças clínicas calculadas a partir de ponto composto claramente errado.

Exemplo de erro crítico:

> Se um cluster aparece com ponto composto **20**, percentil **42**, IC **87–107** e classificação **extremamente baixo**, há inconsistência grave. O percentil e o intervalo de confiança indicam ponto composto próximo da faixa média, não 20. Esse dado deve ser corrigido antes de qualquer comparação clínica.

Quando isso ocorrer, a IA deve escrever:

> O cluster [nome] apresenta incompatibilidade entre ponto composto, percentil, intervalo de confiança e classificação. As comparações clínicas derivadas desse cluster não devem ser interpretadas até que o valor seja recalculado.

---

## Comparações clínicas entre clusters

Antes de interpretar uma comparação clínica entre clusters, validar:

- Se os dois clusters são interpretáveis.
- Se os pontos compostos são consistentes.
- Se a diferença matemática está correta.
- Se o valor crítico foi aplicado corretamente.
- Se a classificação “raro” ou “não raro” corresponde à diferença.
- Se a direção da diferença está correta.

A IA não deve interpretar comparação envolvendo cluster inconsistente ou não interpretável.

Modelo de bloqueio:

> A comparação [cluster A] × [cluster B] não deve ser interpretada, pois pelo menos um dos clusters apresenta inconsistência psicométrica ou não atende aos critérios de interpretabilidade.

---

## Regras para discrepâncias entre índices

As discrepâncias devem ser interpretadas apenas quando:

- A diferença numérica estiver correta.
- A significância estatística estiver indicada corretamente.
- A frequência da diferença na amostra de padronização estiver coerente.
- A direção clínica da diferença estiver corretamente descrita.

### Interpretação das principais discrepâncias

#### QIV > QIE

Usar quando o desempenho verbal for significativamente superior ao desempenho de execução.

Modelo:

> A discrepância favorece o desempenho verbal em relação ao desempenho de execução, indicando maior eficiência em tarefas mediadas pela linguagem, conhecimento adquirido, formação de conceitos e raciocínio verbal, com menor rendimento relativo em demandas visuoespaciais, perceptivas, práticas ou dependentes de organização não verbal.

#### ICV > IOP

Modelo:

> A diferença entre ICV e IOP indica maior eficiência em raciocínio verbal, abstração, vocabulário e conhecimento cristalizado quando comparada às tarefas de organização visuoespacial, análise perceptiva e raciocínio não verbal. Esse padrão sugere assimetria cognitiva relevante e reduz a representatividade de uma leitura global única.

#### ICV > IVP

Modelo:

> O contraste entre ICV e IVP sugere que a capacidade de compreensão verbal e raciocínio conceitual está mais preservada do que a eficiência para executar tarefas simples, rápidas e visualmente mediadas sob pressão temporal. Funcionalmente, esse padrão pode se expressar como boa compreensão de conteúdos verbais complexos, porém com maior lentidão, menor produtividade ou maior custo cognitivo em atividades cronometradas.

#### ICV > IMO

Modelo:

> A discrepância entre ICV e IMO sugere recursos verbais e conceituais mais eficientes do que a capacidade de manter, manipular e atualizar informações em tempo real. Esse padrão pode impactar tarefas que exigem cálculo mental, múltiplas instruções, sequenciamento e controle atencional contínuo.

#### IVP baixo ou relativamente baixo

Modelo:

> O desempenho em Velocidade de Processamento sugere menor eficiência relativa em tarefas que exigem rapidez visuomotora, discriminação visual, atenção sustentada e execução sob limite de tempo. Esse achado deve ser integrado a medidas específicas de atenção, funções executivas, funcionamento emocional e observações comportamentais.

---

## Regras para GAI no WAIS-III

O GAI pode ser apresentado apenas quando calculado por tabela normativa válida.

### Pontos obrigatórios

A IA deve informar:

- Soma ponderada usada.
- Escore composto.
- Percentil.
- Intervalo de confiança.
- Critério de interpretabilidade.
- Se a discrepância entre ICV e IOP permite ou não interpretação clínica.

### Quando o GAI não for interpretável

Se a discrepância entre ICV e IOP atingir ou ultrapassar o critério técnico configurado no sistema, o GAI deve ser descrito como **não interpretável clinicamente**.

Modelo obrigatório:

> Embora o GAI tenha sido calculado por tabela normativa, sua interpretação clínica não é recomendada neste caso, devido à discrepância expressiva entre ICV e IOP. Assim, o índice deve ser apresentado apenas como dado técnico complementar, sem substituir a análise dos índices fatoriais e do padrão intraindividual.

### Proibição

Não usar o GAI como estimativa principal da habilidade intelectual geral quando ele for marcado como não interpretável.

---

## Regra sobre CPI

O relatório WAIS-III não deve apresentar o CPI como índice padrão.

Regra:

> Não gerar, interpretar ou incluir CPI como índice principal do WAIS-III, salvo se houver base normativa explicitamente configurada e justificada pelo sistema. O conjunto padrão do WAIS-III deve priorizar QIV, QIE, QIT, ICV, IOP, IMO, IVP e, quando aplicável, GAI.

---

## Interpretação dos subtestes

A IA deve interpretar subtestes como indicadores complementares, nunca como diagnóstico isolado.

### Subtestes verbais

- **Vocabulário:** repertório lexical, conhecimento cristalizado, expressão verbal, formação conceitual.
- **Semelhanças:** abstração verbal, categorização conceitual, raciocínio conceitual.
- **Informação:** conhecimento factual, memória semântica, repertório de informações gerais.
- **Compreensão:** julgamento social, raciocínio prático verbal, compreensão de normas sociais.
- **Aritmética:** cálculo mental, atenção auditiva, memória operacional, manipulação mental sob demanda.
- **Dígitos:** atenção auditiva, memória imediata, memória operacional e controle mental.
- **Sequência de Números e Letras:** manipulação mental, sequenciamento, memória operacional e flexibilidade atencional.

### Subtestes de execução

- **Completar Figuras:** atenção a detalhes visuais, discriminação perceptiva, análise de estímulos incompletos.
- **Códigos:** velocidade grafomotora, aprendizagem associativa, atenção visual sustentada, execução sob pressão de tempo.
- **Cubos:** organização visuoespacial, análise e síntese visual, construção com modelo.
- **Raciocínio Matricial:** raciocínio fluido não verbal, identificação de padrões e relações visuais.
- **Procurar Símbolos:** busca visual rápida, discriminação visual, velocidade de processamento.
- **Arranjo de Figuras:** sequenciamento lógico, compreensão de situações sociais e organização narrativa visual.
- **Armar Objetos:** integração visuoperceptiva, análise de partes e síntese visual.

### Modelo de redação dos subtestes

> Entre os subtestes com maior rendimento relativo, destacam-se [subtestes], associados a [funções]. Como ponto de menor rendimento relativo, observa-se [subteste], relacionado a [funções]. Esses achados devem ser compreendidos como indicadores do padrão intraindividual, sem conclusão diagnóstica isolada.

---

## Linguagem proibida

Evitar frases genéricas, circulares ou pouco clínicas, como:

- “habilidades relativamente mais eficientes quando comparadas a habilidades relativamente menos eficientes”.
- “desempenho reduzida”.
- “desempenho elevada”.
- “desempenho adequada”.
- “o teste mostra déficit” sem integração clínica.
- “comprova diagnóstico”.
- “fecha diagnóstico”.
- “o paciente é incapaz”.

Substituir por linguagem técnica:

- “maior eficiência relativa”.
- “menor rendimento relativo”.
- “desempenho reduzido”.
- “desempenho elevado”.
- “desempenho adequado”.
- “sugere”.
- “é compatível com”.
- “deve ser integrado a outros dados clínicos”.

---

## Estrutura recomendada da interpretação clínica

A interpretação clínica deve seguir a ordem abaixo.

### 1. Introdução curta do instrumento

Modelo:

> A Escala de Inteligência Wechsler para Adultos – Terceira Edição (WAIS-III) avalia o funcionamento intelectual em adultos, contemplando medidas de desempenho verbal, desempenho de execução, funcionamento intelectual global e índices fatoriais relacionados à compreensão verbal, organização perceptual, memória operacional e velocidade de processamento. Seus resultados devem ser interpretados em conjunto com entrevista clínica, observação comportamental, escolaridade, histórico funcional, contexto sociocultural e demais instrumentos da avaliação neuropsicológica.

### 2. QI Total e representatividade

Modelo:

> [Nome] apresentou QI Total de [valor], classificado como [classificação], situado no percentil [percentil], com intervalo de confiança de [IC]. Embora esse resultado indique funcionamento intelectual global na faixa [classificação], sua interpretação deve ser realizada com cautela quando houver discrepâncias relevantes entre os domínios avaliados. Nessa condição, a análise dos índices fatoriais e do padrão intraindividual torna-se clinicamente mais informativa do que a leitura isolada do QIT.

### 3. QIV e QIE

Modelo:

> O QI Verbal situou-se na faixa [classificação], sugerindo [interpretação]. O QI de Execução situou-se na faixa [classificação], indicando [interpretação]. A diferença de [diferença] pontos favorece [QIV ou QIE], sugerindo [interpretação funcional].

### 4. Índices fatoriais

Modelo:

> O Índice de Compreensão Verbal apresentou desempenho [classificação], refletindo [funções]. O Índice de Organização Perceptual situou-se na faixa [classificação], sugerindo [funções]. O Índice de Memória Operacional foi classificado como [classificação], indicando [funções]. O Índice de Velocidade de Processamento apresentou classificação [classificação], sugerindo [funções].

### 5. Perfil intraindividual

Modelo:

> Em análise clínica, o maior rendimento ocorreu em [índice], enquanto o menor rendimento foi observado em [índice]. Esse contraste indica [interpretação], devendo ser considerado especialmente em atividades que exigem [demandas funcionais].

### 6. Subtestes

Usar o modelo da seção “Interpretação dos subtestes”.

### 7. Discrepâncias clinicamente relevantes

Interpretar apenas as discrepâncias significativas e clinicamente úteis. Não transformar cada linha da tabela em texto repetitivo.

Modelo:

> As discrepâncias clinicamente mais relevantes ocorreram entre [comparações]. Esses contrastes indicam [interpretação integrada]. Por esse motivo, recomenda-se cautela na interpretação isolada do QIT.

### 8. Clusters

Interpretar somente clusters válidos e consistentes.

Modelo:

> Os clusters clínicos foram considerados indicadores complementares, com interpretação condicionada à homogeneidade interna dos subtestes. Entre os clusters interpretáveis, destacaram-se [clusters]. Clusters com inconsistência interna ou incompatibilidade psicométrica não devem ser utilizados como conclusão clínica.

### 9. GAI

Usar a regra específica do GAI.

### 10. Síntese clínica

Modelo:

> Em análise clínica, [nome] apresentou funcionamento intelectual global na faixa [classificação], com perfil [homogêneo/heterogêneo] entre os domínios avaliados. Os resultados sugerem maior eficiência relativa em [domínio] e menor rendimento relativo em [domínio]. O WAIS-III não deve ser utilizado isoladamente para fechamento de hipótese diagnóstica, devendo seus achados ser integrados à anamnese, observação clínica, funcionamento adaptativo, escolaridade, contexto sociocultural e demais instrumentos da avaliação neuropsicológica.

---

## Critérios de padrão ouro

Um relatório WAIS-III só deve ser considerado padrão ouro quando cumprir todos os critérios abaixo:

- Dados de identificação sem erros.
- Escolaridade escrita corretamente.
- Normativa adequada à idade.
- Índices principais matematicamente consistentes.
- Percentis compatíveis com pontos compostos.
- Intervalos de confiança compatíveis com pontos compostos.
- Classificações corretas.
- Gráficos correspondentes às tabelas.
- Discrepâncias calculadas corretamente.
- Clusters auditados antes da interpretação.
- Comparações clínicas entre clusters consistentes.
- GAI calculado e interpretado apenas quando tecnicamente permitido.
- CPI ausente, salvo justificativa normativa explícita.
- Interpretação sem frases circulares.
- Texto sem erros de concordância.
- Conclusões compatíveis com os dados.
- Ausência de diagnóstico fechado apenas pelo WAIS-III.
- Síntese final integrada e clinicamente útil.

---

## Checklist final obrigatório

Antes de finalizar o relatório, responder internamente:

1. O QIT está coerente com QIV e QIE?
2. Há discrepância que reduz a representatividade do QIT?
3. O maior e o menor índice foram identificados corretamente?
4. A interpretação do ICV está coerente com os subtestes verbais?
5. A interpretação do IOP está coerente com os subtestes de execução?
6. A interpretação do IMO está coerente com os subtestes de memória operacional?
7. A interpretação do IVP está coerente com Códigos e Procurar Símbolos?
8. Os subtestes mais altos e mais baixos foram descritos sem diagnóstico isolado?
9. As discrepâncias significativas foram interpretadas sem repetição excessiva?
10. Os clusters passaram por validação de consistência?
11. Algum cluster apresenta ponto composto incompatível com percentil, IC ou classificação?
12. As comparações clínicas derivam apenas de clusters válidos?
13. O GAI foi calculado com tabela normativa válida?
14. O GAI é interpretável ou apenas dado técnico?
15. O CPI foi removido ou justificado?
16. O texto está sem erros de concordância?
17. A síntese final reflete os resultados principais?
18. O WAIS-III foi descrito como instrumento complementar, e não diagnóstico isolado?

---

## Modelo de síntese interpretativa refinada

> Em análise clínica, [nome] apresentou funcionamento intelectual global na faixa [classificação], com perfil [homogêneo/heterogêneo] entre os domínios avaliados. Observou-se maior eficiência relativa em [domínio de força], associado a [funções cognitivas], e menor rendimento relativo em [domínio de fragilidade], relacionado a [funções cognitivas]. Esse padrão indica que o desempenho global deve ser compreendido a partir das diferenças intraindividuais, especialmente quando houver discrepâncias relevantes entre índices ou quocientes. Os achados do WAIS-III contribuem para caracterizar o perfil intelectual, mas não devem ser utilizados isoladamente para fechamento de hipótese diagnóstica, exigindo integração com anamnese, observação clínica, escolaridade, funcionamento adaptativo, contexto sociocultural e demais instrumentos da avaliação neuropsicológica.

---

## Modelo de alerta para relatório com erro psicométrico

Quando for detectado erro psicométrico relevante:

> O relatório apresenta inconsistência psicométrica que precisa ser corrigida antes da emissão final. O campo [descrever campo] mostra incompatibilidade entre [ponto composto/percentil/IC/classificação]. Como esse dado interfere nas comparações clínicas e na interpretação do perfil, ele não deve ser utilizado como conclusão clínica até que seja recalculado.

---

## Saída esperada da IA

Ao revisar um relatório WAIS-III, a IA deve entregar:

1. Parecer geral.
2. Pontos positivos.
3. Erros críticos.
4. Inconsistências psicométricas.
5. Problemas de texto e formatação.
6. Correções recomendadas.
7. Versão reescrita dos trechos problemáticos.
8. Nota técnica aproximada, se solicitado.
9. Indicação clara se o relatório pode ou não ser considerado padrão ouro.

---

## Regra final

A prioridade máxima é a segurança psicométrica.  
Nunca escrever interpretação clínica sofisticada sobre dado inconsistente.  
Primeiro auditar, depois interpretar.
