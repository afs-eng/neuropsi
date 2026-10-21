# Skill para Elaboração dos Resultados do WAIS-III

## Finalidade

Esta skill orienta a IA do sistema a elaborar os **resultados psicométricos e descritivos do WAIS-III** a partir dos dados já corrigidos, organizando os achados em formato técnico para uso em laudos neuropsicológicos.

Esta skill não substitui o julgamento clínico do profissional. Ela deve apenas:

- organizar os resultados;
- descrever o desempenho por índices, QIs e subtestes;
- identificar facilidades e dificuldades relativas;
- indicar discrepâncias estatisticamente significativas;
- gerar texto técnico compatível com laudo neuropsicológico;
- evitar diagnóstico automático.

A IA deve sempre escrever em linguagem técnica, clara, objetiva e compatível com avaliação neuropsicológica.

## Base utilizada

Esta skill foi elaborada a partir do manual de correção enviado, que mostra o fluxo prático do WAIS-III:

1. Transcrever os escores brutos dos subtestes.
2. Consultar a Tabela A.1 adequada à idade do examinando.
3. Localizar os escores ponderados.
4. Somar os escores ponderados.
5. Não incluir notas entre parênteses nas somas.
6. Calcular médias das escalas verbal, execução e total.
7. Usar as Tabelas A.3 a A.9 para determinar QIs e índices fatoriais.
8. Criar perfil dos escores.
9. Determinar facilidades e dificuldades com base na Tabela B.3.
10. Analisar discrepâncias com as Tabelas B.1 e B.2.
11. Analisar Dígitos Ordem Direta e Ordem Inversa com as Tabelas B.6 e B.7.

## Entrada esperada

A IA deve receber os dados já corrigidos pelo módulo de correção do WAIS-III:

```json
{
  "paciente": {
    "nome": "",
    "idade_anos": null,
    "idade_meses": null,
    "faixa_etaria": ""
  },
  "subtestes": {
    "vocabulario": {"bruto": null, "ponderado": null},
    "semelhancas": {"bruto": null, "ponderado": null},
    "aritmetica": {"bruto": null, "ponderado": null},
    "digitos": {"bruto": null, "ponderado": null},
    "informacao": {"bruto": null, "ponderado": null},
    "compreensao": {"bruto": null, "ponderado": null},
    "sequencia_numeros_letras": {"bruto": null, "ponderado": null},
    "completar_figuras": {"bruto": null, "ponderado": null},
    "codigos": {"bruto": null, "ponderado": null},
    "cubos": {"bruto": null, "ponderado": null},
    "raciocinio_matricial": {"bruto": null, "ponderado": null},
    "arranjo_figuras": {"bruto": null, "ponderado": null},
    "procurar_simbolos": {"bruto": null, "ponderado": null},
    "armar_objetos": {"bruto": null, "ponderado": null}
  },
  "resultados_compostos": {
    "qi_verbal": {
      "soma": null,
      "escore": null,
      "percentil": null,
      "ic_90": null,
      "ic_95": null,
      "classificacao": null
    },
    "qi_execucao": {},
    "qi_total": {},
    "icv": {},
    "iop": {},
    "imo": {},
    "ivp": {}
  },
  "medias": {
    "media_verbal": null,
    "media_execucao": null,
    "media_total": null
  },
  "facilidades_dificuldades": [],
  "discrepancias": [],
  "digitos": {
    "maximo_ordem_direta": null,
    "maximo_ordem_inversa": null,
    "diferenca_direta_inversa": null,
    "frequencia_b6": null,
    "frequencia_b7": null
  }
}
```

## Regras gerais de escrita

A IA deve seguir estas regras:

1. Não apresentar diagnóstico automático com base apenas no WAIS-III.
2. Não afirmar deficiência intelectual, altas habilidades, TDAH, TEA ou qualquer transtorno apenas com base nos índices.
3. Não interpretar um único subteste como evidência diagnóstica isolada.
4. Sempre integrar QI Total, QI Verbal, QI de Execução, índices fatoriais, discrepâncias e subtestes.
5. Quando houver grande discrepância entre índices, sinalizar que o QI Total pode ter menor representatividade clínica.
6. Evitar linguagem alarmista.
7. Usar termos como “sugere”, “indica”, “aponta”, “mostra”, “revela” e “compatível com”.
8. Usar o primeiro nome do paciente, quando fornecido.
9. Evitar tabelas no texto interpretativo, salvo quando o usuário pedir.
10. Utilizar “Em análise clínica” no fechamento interpretativo.
11. Não usar travessões longos.
12. Não usar a expressão “De forma integrada”.
13. Não incluir percentis ou intervalos de confiança em excesso se o texto ficar artificial; priorizar clareza clínica.
14. Preservar a informação estatística essencial quando houver discrepância significativa.

## Estrutura da seção de resultados

A IA deve elaborar a seção do WAIS-III nesta ordem:

```text
1. Introdução do instrumento.
2. Funcionamento intelectual global.
3. Escala Verbal e Escala de Execução.
4. Índices fatoriais.
5. Análise dos subtestes.
6. Facilidades e dificuldades relativas.
7. Discrepâncias significativas.
8. Análise complementar de Dígitos, se houver dados.
9. Síntese interpretativa.
```

## 1. Introdução do instrumento

Modelo base:

```text
A Escala de Inteligência Wechsler para Adultos, Terceira Edição, WAIS-III, foi utilizada com o objetivo de avaliar o funcionamento intelectual global, bem como diferentes domínios cognitivos relacionados à compreensão verbal, organização perceptual, memória operacional e velocidade de processamento. O instrumento permite a análise dos escores compostos, dos índices fatoriais e do desempenho nos subtestes, favorecendo a compreensão do perfil cognitivo do paciente.
```

Modelo mais técnico:

```text
O WAIS-III foi empregado para investigação do funcionamento intelectual e do perfil cognitivo, considerando medidas de desempenho verbal, execução perceptual, raciocínio, atenção, memória operacional e velocidade de processamento. A análise considerou os escores ponderados dos subtestes, os índices fatoriais, os quocientes intelectuais e as discrepâncias estatisticamente relevantes entre os domínios avaliados.
```

## 2. Funcionamento intelectual global

A IA deve interpretar o **QI Total** com cautela.

Campos usados:

```text
qi_total.escore
qi_total.percentil
qi_total.ic_95
qi_total.classificacao
discrepancias entre índices
```

Modelo:

```text
O QI Total foi de [QI_TOTAL], classificado como [CLASSIFICAÇÃO], situando-se no percentil [PERCENTIL]. Esse resultado sugere funcionamento intelectual global [descrição compatível com a classificação], considerando a amostra normativa da faixa etária avaliada. O intervalo de confiança de 95% situa-se entre [IC_95_MIN] e [IC_95_MAX], indicando a faixa provável de variação do desempenho global.
```

Se houver discrepância importante entre índices:

```text
Embora o QI Total tenha sido classificado como [CLASSIFICAÇÃO], sua interpretação deve ser realizada com cautela, uma vez que foram observadas discrepâncias relevantes entre os índices fatoriais. Nesses casos, a análise do perfil cognitivo por domínios tende a oferecer maior precisão clínica do que a leitura isolada do escore global.
```

## Classificação qualitativa dos escores compostos

Usar a seguinte lógica:

```python
def interpretar_classificacao(valor):
    if valor <= 69:
        return "desempenho extremamente baixo, com importante prejuízo em relação ao esperado para a faixa etária"
    if 70 <= valor <= 79:
        return "desempenho limítrofe, indicando funcionamento abaixo do esperado"
    if 80 <= valor <= 89:
        return "desempenho na média inferior, sugerindo fragilidade relativa"
    if 90 <= valor <= 109:
        return "desempenho dentro da média esperada"
    if 110 <= valor <= 119:
        return "desempenho na média superior, indicando recurso cognitivo preservado e acima da média"
    if 120 <= valor <= 129:
        return "desempenho superior, indicando recurso cognitivo expressivo"
    if valor >= 130:
        return "desempenho muito superior, indicando desempenho significativamente elevado"
```

## 3. Escala Verbal e Escala de Execução

### QI Verbal

O QI Verbal deve ser descrito como medida associada a:

```text
conhecimento verbal
formação de conceitos verbais
raciocínio verbal
compreensão de informações socialmente aprendidas
expressão verbal
aprendizagem cristalizada
```

Modelo:

```text
Na Escala Verbal, o paciente obteve QI Verbal de [QIV], classificado como [CLASSIFICAÇÃO], com percentil [PERCENTIL]. Esse resultado indica [interpretação da classificação] em tarefas que envolvem raciocínio verbal, compreensão de conceitos, conhecimento adquirido, abstração verbal e uso da linguagem para resolução de problemas.
```

### QI de Execução

O QI de Execução deve ser descrito como medida associada a:

```text
raciocínio visuoespacial
organização perceptual
análise visual
planejamento não verbal
resolução de problemas visuais
coordenação visuomotora quando aplicável
```

Modelo:

```text
Na Escala de Execução, o paciente apresentou QI de Execução de [QIE], classificado como [CLASSIFICAÇÃO], com percentil [PERCENTIL]. Esse desempenho reflete [interpretação da classificação] em tarefas que demandam organização perceptual, análise visuoespacial, raciocínio não verbal, planejamento visual e resolução de problemas com menor mediação verbal.
```

### Comparação QI Verbal x QI Execução

Se houver discrepância significativa pela Tabela B.1:

```text
A diferença entre QI Verbal e QI de Execução foi de [DIFERENÇA] pontos, atingindo significância estatística no nível de [NÍVEL]. Esse achado indica assimetria relevante entre os recursos verbais e não verbais, devendo ser considerado na interpretação do perfil cognitivo.
```

Se o QI Verbal for maior:

```text
O desempenho verbal mostrou-se superior ao desempenho de execução, sugerindo melhor rendimento em tarefas mediadas por linguagem, conhecimento adquirido e raciocínio verbal.
```

Se o QI de Execução for maior:

```text
O desempenho de execução mostrou-se superior ao verbal, sugerindo melhor rendimento em tarefas visuoespaciais, perceptuais e de resolução de problemas não verbais.
```

Se não houver discrepância:

```text
Não foram observadas discrepâncias estatisticamente significativas entre QI Verbal e QI de Execução, sugerindo maior equilíbrio entre os recursos verbais e não verbais avaliados.
```

## 4. Índices fatoriais

### ICV, Índice de Compreensão Verbal

Domínios associados:

```text
raciocínio verbal
conceituação verbal
conhecimento lexical
abstração verbal
informação adquirida
compreensão social
```

Modelo:

```text
O Índice de Compreensão Verbal foi de [ICV], classificado como [CLASSIFICAÇÃO], com percentil [PERCENTIL]. Esse índice avalia habilidades relacionadas à formação de conceitos verbais, conhecimento lexical, raciocínio verbal, abstração e compreensão de informações adquiridas ao longo da vida.
```

### IOP, Índice de Organização Perceptual

Domínios associados:

```text
raciocínio visuoespacial
análise perceptual
organização visual
solução de problemas não verbais
integração visuoconstrutiva
```

Modelo:

```text
O Índice de Organização Perceptual foi de [IOP], classificado como [CLASSIFICAÇÃO], com percentil [PERCENTIL]. Esse índice reflete habilidades de raciocínio não verbal, análise visuoespacial, organização perceptual e resolução de problemas visuais.
```

### IMO, Índice de Memória Operacional

Domínios associados:

```text
atenção auditiva
memória de trabalho
manipulação mental de informações
controle atencional
sequenciamento
cálculo mental
```

Modelo:

```text
O Índice de Memória Operacional foi de [IMO], classificado como [CLASSIFICAÇÃO], com percentil [PERCENTIL]. Esse resultado indica o desempenho em tarefas que exigem manutenção e manipulação mental de informações, atenção auditiva, concentração, sequenciamento e controle cognitivo ativo.
```

Quando baixo:

```text
Resultados reduzidos nesse índice podem sugerir fragilidade em memória de trabalho, manutenção de informações em curto prazo, atenção auditiva e manipulação mental, especialmente em tarefas que exigem controle simultâneo de múltiplas informações.
```

### IVP, Índice de Velocidade de Processamento

Domínios associados:

```text
rapidez grafomotora
atenção visual
varredura visual
discriminação perceptual
eficiência operacional
ritmo de trabalho
```

Modelo:

```text
O Índice de Velocidade de Processamento foi de [IVP], classificado como [CLASSIFICAÇÃO], com percentil [PERCENTIL]. Esse índice avalia a rapidez e a eficiência com que o paciente processa informações visuais simples, realiza discriminação perceptual, mantém atenção visual e executa respostas grafomotoras sob demanda de tempo.
```

Quando baixo:

```text
Um desempenho reduzido nesse índice pode indicar lentificação no ritmo de execução, menor eficiência grafomotora, dificuldade em varredura visual, oscilação atencional ou redução da velocidade na realização de tarefas estruturadas com limite de tempo.
```

## 5. Análise dos subtestes

A IA deve descrever os subtestes por domínio, sem transformar cada subteste em diagnóstico.

### Subtestes verbais

#### Vocabulário

Avalia:

```text
conhecimento lexical
expressão verbal
precisão conceitual
aprendizagem cristalizada
```

Modelo:

```text
Em Vocabulário, o desempenho foi classificado como [CLASSIFICAÇÃO_SUBTESTE], indicando [interpretação] quanto à amplitude lexical, expressão verbal e precisão na definição de conceitos.
```

#### Semelhanças

Avalia:

```text
abstração verbal
formação de conceitos
raciocínio categorial
pensamento lógico verbal
```

Modelo:

```text
Em Semelhanças, o desempenho sugere [interpretação], refletindo a capacidade de identificar relações conceituais, estabelecer categorias e realizar abstrações verbais.
```

#### Aritmética

Avalia:

```text
raciocínio quantitativo
atenção auditiva
memória operacional
cálculo mental
resolução de problemas
```

Modelo:

```text
Em Aritmética, o resultado indica [interpretação] em tarefas que exigem raciocínio quantitativo, atenção auditiva, cálculo mental e manipulação de informações em memória operacional.
```

#### Dígitos

Avalia:

```text
atenção auditiva
memória imediata
memória operacional
sequenciamento
controle mental
```

Modelo:

```text
Em Dígitos, o desempenho indica [interpretação] na capacidade de reter, repetir e manipular sequências auditivas, envolvendo atenção imediata e memória operacional.
```

#### Informação

Avalia:

```text
conhecimento geral
aprendizagem escolar e cultural
memória semântica
aquisição de informações
```

Modelo:

```text
Em Informação, o resultado reflete [interpretação] quanto ao repertório de conhecimentos gerais, memória semântica e aquisição de informações culturalmente compartilhadas.
```

#### Compreensão

Avalia:

```text
julgamento social
raciocínio prático verbal
compreensão de normas sociais
resolução de situações cotidianas
```

Modelo:

```text
Em Compreensão, o desempenho indica [interpretação] na capacidade de compreender situações sociais, utilizar julgamento prático e aplicar conhecimentos verbais em contextos cotidianos.
```

#### Sequência de Números e Letras

Avalia:

```text
memória operacional
atenção dividida
sequenciamento mental
manipulação ativa de informações
```

Modelo:

```text
Em Sequência de Números e Letras, o resultado sugere [interpretação] em tarefas de manipulação mental, sequenciamento, atenção dividida e controle executivo sobre informações verbais e numéricas.
```

### Subtestes de execução

#### Completar Figuras

Avalia:

```text
atenção visual
percepção de detalhes
reconhecimento de elementos essenciais
organização perceptual
```

Modelo:

```text
Em Completar Figuras, o desempenho indica [interpretação] na percepção de detalhes visuais, reconhecimento de elementos ausentes e análise perceptual de estímulos familiares.
```

#### Códigos

Avalia:

```text
velocidade de processamento
aprendizagem associativa
atenção visual
coordenação visuomotora
ritmo grafomotor
```

Modelo:

```text
Em Códigos, o resultado reflete [interpretação] na velocidade de processamento, aprendizagem associativa, atenção visual sustentada e execução grafomotora sob limite de tempo.
```

#### Cubos

Avalia:

```text
organização visuoespacial
análise e síntese visual
planejamento perceptual
coordenação visuoconstrutiva
```

Modelo:

```text
Em Cubos, o desempenho sugere [interpretação] na organização visuoespacial, análise e síntese de estímulos visuais, planejamento construtivo e resolução de problemas não verbais.
```

#### Raciocínio Matricial

Avalia:

```text
raciocínio fluido
identificação de padrões
inferência visual
solução de problemas abstratos não verbais
```

Modelo:

```text
Em Raciocínio Matricial, o resultado indica [interpretação] em raciocínio fluido, identificação de padrões, inferência visual e resolução de problemas abstratos com menor demanda verbal.
```

#### Arranjo de Figuras

Avalia:

```text
sequenciamento lógico
compreensão de situações sociais
organização temporal
raciocínio narrativo visual
```

Modelo:

```text
Em Arranjo de Figuras, o desempenho reflete [interpretação] na capacidade de organizar sequências visuais, compreender relações temporais e inferir sentido lógico em situações representadas por imagens.
```

#### Procurar Símbolos

Avalia:

```text
velocidade de processamento
atenção visual
discriminação perceptual
varredura visual
controle de resposta
```

Modelo:

```text
Em Procurar Símbolos, o resultado indica [interpretação] em atenção visual, discriminação perceptual, velocidade de busca e eficiência no processamento de informações visuais simples.
```

#### Armar Objetos

Avalia:

```text
organização perceptual
síntese visual
integração parte-todo
raciocínio visuoconstrutivo
```

Modelo:

```text
Em Armar Objetos, o desempenho sugere [interpretação] na integração de partes em um todo significativo, organização perceptual e síntese visuoconstrutiva.
```

## 6. Facilidades e dificuldades relativas

A IA deve usar a Tabela B.3 para determinar facilidades e dificuldades.

Fluxo:

```text
1. Calcular média dos escores ponderados da escala adequada.
2. Subtrair a média do escore ponderado de cada subteste.
3. Consultar a Tabela B.3 conforme número de subtestes aplicados e escala.
4. Considerar significativo quando a diferença absoluta for igual ou superior ao valor crítico.
5. Se a diferença for positiva, classificar como facilidade.
6. Se a diferença for negativa, classificar como dificuldade.
```

Modelo para facilidade:

```text
Foi observada facilidade relativa em [SUBTESTE], indicando desempenho significativamente acima da média pessoal nesse conjunto de habilidades. Esse achado sugere recurso específico em [DOMÍNIO DO SUBTESTE].
```

Modelo para dificuldade:

```text
Foi observada dificuldade relativa em [SUBTESTE], indicando desempenho significativamente abaixo da média pessoal nesse conjunto de habilidades. Esse achado sugere fragilidade específica em [DOMÍNIO DO SUBTESTE].
```

Modelo quando não há facilidades ou dificuldades significativas:

```text
A análise dos subtestes não evidenciou facilidades ou dificuldades relativas estatisticamente significativas, sugerindo maior homogeneidade interna no conjunto de habilidades avaliadas.
```

## 7. Análise de discrepâncias entre QIs e índices

A IA deve usar a Tabela B.1 e, quando houver significância, consultar a Tabela B.2 para frequência acumulada.

Fluxo:

```text
1. Inserir os valores de QI e índices nas comparações previstas.
2. Calcular Escore 1 menos Escore 2.
3. Preservar o sinal da diferença para interpretação.
4. Usar o valor absoluto para verificar significância estatística.
5. Consultar Tabela B.1 conforme idade e comparação.
6. Se a diferença for significativa, consultar Tabela B.2 para frequência cumulativa.
```

Comparações obrigatórias:

```text
QI Verbal - QI de Execução
Compreensão Verbal - Organização Perceptual
Compreensão Verbal - Memória Operacional
Organização Perceptual - Velocidade de Processamento
Compreensão Verbal - Velocidade de Processamento
Organização Perceptual - Memória Operacional
Memória Operacional - Velocidade de Processamento
```

Modelo com discrepância significativa:

```text
A diferença entre [ÍNDICE_1] e [ÍNDICE_2] foi de [DIFERENÇA] pontos, atingindo significância estatística no nível de [NÍVEL]. A frequência acumulada dessa discrepância na amostra normativa foi de [FREQUÊNCIA]%, indicando que esse padrão é [comum/pouco frequente/raro] entre indivíduos da mesma referência normativa.
```

Modelo sem discrepância significativa:

```text
A diferença entre [ÍNDICE_1] e [ÍNDICE_2] não atingiu significância estatística, sugerindo ausência de discrepância clinicamente relevante entre esses domínios.
```

Regra para frequência:

```python
def interpretar_frequencia(freq):
    if freq <= 5:
        return "raro"
    if freq <= 15:
        return "pouco frequente"
    if freq <= 25:
        return "moderadamente frequente"
    return "comum"
```

## 8. Análise de Dígitos Ordem Direta e Ordem Inversa

Usar as Tabelas B.6 e B.7.

Campos necessários:

```text
maior_sequencia_ordem_direta
maior_sequencia_ordem_inversa
diferenca_direta_menos_inversa
frequencia_ordem_direta
frequencia_ordem_inversa
frequencia_diferenca
```

Modelo:

```text
Na análise complementar do subteste Dígitos, a maior sequência alcançada em Ordem Direta foi de [DIRETA], enquanto em Ordem Inversa foi de [INVERSA]. A diferença entre as duas condições foi de [DIFERENÇA], com frequência acumulada de [FREQUÊNCIA]% na amostra normativa. Esse resultado contribui para a compreensão da relação entre atenção auditiva imediata e manipulação mental ativa de informações.
```

Se ordem inversa muito inferior:

```text
A discrepância entre Ordem Direta e Ordem Inversa sugere maior dificuldade quando a tarefa exige manipulação ativa da informação, controle mental e memória operacional, em comparação à simples repetição imediata de estímulos auditivos.
```

## 9. Perfil dos escores

A IA deve gerar uma síntese do perfil.

Modelo:

```text
O perfil dos escores evidencia [homogeneidade/heterogeneidade] entre os domínios avaliados. Os melhores desempenhos concentraram-se em [DOMÍNIOS], enquanto as maiores fragilidades foram observadas em [DOMÍNIOS]. Esse padrão sugere que o funcionamento cognitivo é caracterizado por [SÍNTESE CLÍNICA].
```

Quando homogêneo:

```text
O perfil mostrou-se relativamente homogêneo, sem discrepâncias expressivas entre os principais domínios avaliados, sugerindo funcionamento cognitivo global mais uniforme.
```

Quando heterogêneo:

```text
O perfil mostrou-se heterogêneo, com diferenças relevantes entre os domínios avaliados. Nesse contexto, a análise dos índices fatoriais e dos subtestes torna-se clinicamente mais informativa do que a interpretação isolada do QI Total.
```

## 10. Síntese interpretativa final

Modelo geral:

```text
Em análise clínica, os resultados do WAIS-III indicam funcionamento intelectual global classificado como [CLASSIFICAÇÃO_QIT], com perfil [homogêneo/heterogêneo] entre os domínios avaliados. Observam-se recursos mais evidentes em [PONTOS FORTES], enquanto as principais fragilidades aparecem em [PONTOS FRACOS]. Esses achados devem ser integrados aos dados da anamnese, observações clínicas, desempenho adaptativo, histórico escolar/profissional e demais instrumentos utilizados no processo avaliativo.
```

Modelo com QI Total pouco representativo:

```text
Em análise clínica, embora o QI Total tenha sido classificado como [CLASSIFICAÇÃO_QIT], a presença de discrepâncias significativas entre os índices sugere que esse escore deve ser interpretado com cautela. O perfil cognitivo mostra maior relevância clínica quando analisado por domínios específicos, especialmente em relação a [DOMÍNIOS PRESERVADOS] e [DOMÍNIOS FRAGILIZADOS].
```

## 11. Saída esperada da IA

A IA deve retornar:

```json
{
  "secao": "Eficiência Intelectual - WAIS-III",
  "texto": "Texto interpretativo completo...",
  "alertas_clinicos": [
    "QI Total deve ser interpretado com cautela devido a discrepâncias significativas.",
    "Não realizar inferência diagnóstica apenas com base no WAIS-III."
  ],
  "dados_utilizados": {
    "qi_total": null,
    "qi_verbal": null,
    "qi_execucao": null,
    "icv": null,
    "iop": null,
    "imo": null,
    "ivp": null
  }
}
```

## 12. Modelo completo de texto para laudo

```text
A Escala de Inteligência Wechsler para Adultos, Terceira Edição, WAIS-III, foi utilizada com o objetivo de avaliar o funcionamento intelectual global e o perfil cognitivo do paciente, considerando habilidades verbais, perceptuais, atencionais, mnemônicas e de velocidade de processamento.

O QI Total foi de [QIT], classificado como [CLASSIFICAÇÃO_QIT], situando-se no percentil [PERCENTIL_QIT]. Esse resultado sugere [INTERPRETAÇÃO_QIT] em relação à amostra normativa da faixa etária avaliada. O intervalo de confiança de 95% situa-se entre [IC95_QIT], indicando a faixa provável de variação do desempenho global.

Na Escala Verbal, o paciente obteve QI Verbal de [QIV], classificado como [CLASSIFICAÇÃO_QIV], com percentil [PERCENTIL_QIV]. Esse resultado indica [INTERPRETAÇÃO_QIV] em tarefas que envolvem raciocínio verbal, compreensão conceitual, conhecimento adquirido e uso da linguagem para resolução de problemas. Na Escala de Execução, apresentou QI de Execução de [QIE], classificado como [CLASSIFICAÇÃO_QIE], com percentil [PERCENTIL_QIE], sugerindo [INTERPRETAÇÃO_QIE] em tarefas de organização perceptual, raciocínio visuoespacial e resolução de problemas não verbais.

Quanto aos índices fatoriais, o Índice de Compreensão Verbal foi de [ICV], classificado como [CLASSIFICAÇÃO_ICV], indicando [INTERPRETAÇÃO_ICV]. O Índice de Organização Perceptual foi de [IOP], classificado como [CLASSIFICAÇÃO_IOP], refletindo [INTERPRETAÇÃO_IOP]. O Índice de Memória Operacional foi de [IMO], classificado como [CLASSIFICAÇÃO_IMO], sugerindo [INTERPRETAÇÃO_IMO]. O Índice de Velocidade de Processamento foi de [IVP], classificado como [CLASSIFICAÇÃO_IVP], indicando [INTERPRETAÇÃO_IVP].

Na análise dos subtestes, os melhores desempenhos foram observados em [SUBTESTES_PONTOS_FORTES], sugerindo recursos em [DOMÍNIOS_FORTES]. As maiores fragilidades foram verificadas em [SUBTESTES_FRAGILIDADES], indicando possíveis dificuldades em [DOMÍNIOS_FRÁGEIS]. A análise de facilidades e dificuldades relativas demonstrou [RESULTADO_B3].

Na análise de discrepâncias, [RESULTADO_DISCREPANCIAS]. Esses achados indicam [INTERPRETAÇÃO_DAS_DISCREPANCIAS].

Em análise clínica, os resultados do WAIS-III indicam funcionamento intelectual global [CLASSIFICAÇÃO_QIT], com perfil [HOMOGÊNEO/HETEROGÊNEO] entre os domínios avaliados. Os achados devem ser integrados aos dados da anamnese, observações clínicas, desempenho funcional, histórico escolar/profissional e demais instrumentos utilizados no processo avaliativo.
```

## 13. Prompt pronto para IA da IDE

```text
Você é uma IA responsável por gerar a seção de resultados interpretativos do WAIS-III no sistema neuropsicológico.

Receba como entrada os resultados já corrigidos do WAIS-III: escores brutos, escores ponderados, QI Verbal, QI de Execução, QI Total, ICV, IOP, IMO, IVP, percentis, intervalos de confiança, classificações, análise de facilidades/dificuldades pela Tabela B.3, discrepâncias pela Tabela B.1/B.2 e análise complementar de Dígitos pelas Tabelas B.6/B.7.

Gere um texto técnico para laudo neuropsicológico com a seguinte estrutura:
1. Apresentação do instrumento.
2. Funcionamento intelectual global.
3. QI Verbal e QI de Execução.
4. Índices fatoriais.
5. Desempenho por subtestes.
6. Facilidades e dificuldades relativas.
7. Discrepâncias estatisticamente significativas.
8. Síntese clínica final iniciada por “Em análise clínica”.

Regras:
- Não gerar diagnóstico automático.
- Não afirmar transtorno apenas com base no WAIS-III.
- Não interpretar subteste isolado como diagnóstico.
- Se houver discrepâncias significativas entre índices, escrever que o QI Total deve ser interpretado com cautela.
- Preservar linguagem técnica e objetiva.
- Usar o primeiro nome do paciente quando fornecido.
- Não usar travessões longos.
- Não usar tabelas, salvo se solicitado.
- Não usar a expressão “De forma integrada”.
- Preferir “Em análise clínica”.
- O diagnóstico deve permanecer como hipótese clínica do profissional.

Retorne:
{
  "secao": "Eficiência Intelectual - WAIS-III",
  "texto": "...",
  "alertas_clinicos": [],
  "dados_utilizados": {}
}
```

## 14. Observação final

Esta skill deve ser usada depois da skill de correção normativa. A primeira skill calcula os resultados. Esta skill elabora a apresentação clínica e textual dos resultados para o laudo.

Fluxo final recomendado:

```text
Resultados brutos
→ Correção normativa WAIS-III
→ Cálculo de QIs, índices e discrepâncias
→ Skill de elaboração dos resultados
→ Texto técnico para laudo
→ Revisão clínica do profissional
```
