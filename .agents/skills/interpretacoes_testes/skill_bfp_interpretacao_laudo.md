# Skill: Interpretação do BFP para laudos neuropsicológicos

## Objetivo
Gerar automaticamente a seção interpretativa do BFP – Bateria Fatorial de Personalidade no laudo neuropsicológico, em linguagem técnica, integrada, descritiva e compatível com padrão de auditoria. A interpretação deve transformar os resultados quantitativos em texto clínico funcional, sem reproduzir o manual de forma extensa e sem formular diagnóstico psiquiátrico isolado a partir do teste.

## Entrada esperada
O sistema deve receber um objeto com os dados do paciente e os resultados do BFP.

```json
{
  "paciente": {
    "nome_exibicao": "Anna Luiza",
    "sexo": "Feminino",
    "idade": 19,
    "contexto": "Neuropsicologia"
  },
  "bfp": {
    "tabela_apuracao": "Sexo",
    "resultados": [
      {"codigo": "N1", "nome": "Vulnerabilidade", "escore_bruto": 4.1, "z": 0.8, "percentil": "80", "classificacao": "Alto"},
      {"codigo": "N2", "nome": "Instabilidade", "escore_bruto": 5.3, "z": 2.1, "percentil": "95", "classificacao": "Muito Alto"},
      {"codigo": "N3", "nome": "Passividade", "escore_bruto": 5.0, "z": 1.4, "percentil": "> 90", "classificacao": "Muito Alto"},
      {"codigo": "N4", "nome": "Depressão", "escore_bruto": 2.3, "z": 0.1, "percentil": "> 65", "classificacao": "Médio"},
      {"codigo": "N", "nome": "Neuroticismo", "escore_bruto": 4.2, "z": 1.5, "percentil": "90", "classificacao": "Muito Alto"}
    ]
  }
}
```

## Domínios e facetas obrigatórios
O sistema deve reconhecer os cinco fatores principais e suas facetas:

1. Neuroticismo: Vulnerabilidade, Instabilidade, Passividade/Falta de Energia, Depressão.
2. Extroversão: Nível de Comunicação, Altivez, Dinamismo/Assertividade, Interações Sociais.
3. Socialização: Amabilidade, Pró-sociabilidade, Confiança.
4. Realização: Competência, Ponderação, Empenho.
5. Abertura: Abertura a Ideias, Liberalismo, Busca por Novidades.

## Regra de classificação interpretativa
Usar sempre a classificação original do relatório do BFP. Não recalcular percentis quando o dado já vier pronto.

Mapeamento clínico textual:

- Muito Alto: traço muito acentuado, clinicamente relevante quando associado a prejuízo funcional ou convergência com anamnese.
- Alto: traço elevado, com impacto funcional provável em contextos compatíveis.
- Médio: funcionamento dentro do padrão esperado, com flexibilidade situacional.
- Baixo: baixa expressão do traço, podendo indicar vulnerabilidade ou recurso dependendo do fator.
- Muito Baixo: expressão muito reduzida do traço, devendo ser interpretada conforme o domínio.

## Regra central de segurança clínica
O BFP descreve traços de personalidade. Ele não deve, isoladamente, gerar diagnóstico. O texto pode apontar indicadores, tendências e hipóteses funcionais, mas deve integrar anamnese, observação clínica, demais testes e prejuízo funcional.

Frase obrigatória quando o BFP tiver achados relevantes:

"Em análise clínica, esses resultados devem ser integrados aos dados da anamnese, à observação comportamental e aos demais instrumentos utilizados, uma vez que o BFP descreve tendências de personalidade e não estabelece diagnóstico isolado."

## Estrutura da seção no laudo

### Título
`BFP – BATERIA FATORIAL DE PERSONALIDADE`

### Definição breve
Inserir no início:

"A Bateria Fatorial de Personalidade – BFP é um instrumento psicológico baseado no modelo dos Cinco Grandes Fatores da personalidade, utilizado para avaliar tendências relativamente estáveis do funcionamento emocional, interpessoal, motivacional, comportamental e de abertura à experiência. Seus resultados permitem compreender padrões de autorregulação, sociabilidade, organização, persistência, reatividade emocional e estilo de enfrentamento, devendo ser interpretados em conjunto com a história clínica, observação comportamental e demais achados da avaliação neuropsicológica."

### Interpretação por fator
Gerar um parágrafo para cada fator principal. Cada parágrafo deve:

1. Informar a classificação do fator principal.
2. Integrar as facetas mais relevantes.
3. Evitar repetir todos os percentis no corpo do texto, salvo quando necessário.
4. Interpretar o funcionamento clínico e funcional.
5. Usar o primeiro nome ou nome de exibição configurado no laudo.

### Síntese final obrigatória
Finalizar com um parágrafo integrativo iniciado por:

"Em análise clínica, o perfil de personalidade de {nome}..."

## Templates por fator

### Neuroticismo
Se Neuroticismo for Alto ou Muito Alto:

"O fator Neuroticismo apresentou classificação {classificacao}, indicando maior tendência à reatividade emocional, sensibilidade a críticas, insegurança subjetiva e dificuldade de autorregulação diante de situações de tensão. A elevação em {facetas_elevadas} sugere maior vulnerabilidade ao desconforto emocional, oscilação afetiva, baixa tolerância à frustração e possível dificuldade para iniciar ou sustentar ações quando há sobrecarga emocional. Quando a faceta Depressão estiver elevada, acrescentar: Observa-se ainda tendência a interpretações mais negativas sobre si, sobre o futuro e sobre a própria capacidade de enfrentamento."

Se Neuroticismo for Médio:

"O fator Neuroticismo situou-se na classificação média, sugerindo funcionamento emocional global dentro dos limites esperados, com presença de reatividade emocional compatível com as demandas situacionais. As facetas devem ser analisadas individualmente, pois elevações pontuais podem indicar vulnerabilidades específicas mesmo diante de fator global preservado."

Se Neuroticismo for Baixo ou Muito Baixo:

"O fator Neuroticismo apresentou classificação {classificacao}, indicando menor tendência à instabilidade emocional, preocupação excessiva e sofrimento subjetivo recorrente. Esse padrão pode representar recurso de estabilidade emocional, embora escores muito baixos devam ser analisados com cautela quando houver possível minimização de dificuldades ou baixa percepção de sofrimento."

### Extroversão
Se Extroversão for Alto ou Muito Alto:

"O fator Extroversão apresentou classificação {classificacao}, sugerindo maior expressividade social, iniciativa comunicativa, busca por interação e disposição para exposição interpessoal. Elevações em comunicação, dinamismo ou interações sociais indicam tendência a maior envolvimento social e assertividade. Quando Altivez estiver elevada, considerar maior necessidade de reconhecimento, autovalorização e sensibilidade à forma como é percebido pelos demais."

Se Extroversão for Médio:

"O fator Extroversão situou-se na classificação média, indicando repertório social funcional e flexível, com capacidade de comunicação e interação modulada pelas demandas do contexto. Facetas discrepantes devem ser descritas como tendências específicas, sem caracterizar o funcionamento global como deficitário."

Se Extroversão for Baixo ou Muito Baixo:

"O fator Extroversão apresentou classificação {classificacao}, indicando menor expansividade social, menor busca espontânea por interações e tendência a funcionamento mais reservado. Baixos escores em comunicação e interações sociais sugerem possível retraimento, desconforto em situações de exposição e preferência por contextos sociais mais previsíveis ou restritos."

### Socialização
Se Socialização for Alto ou Muito Alto:

"O fator Socialização apresentou classificação {classificacao}, sugerindo tendência a comportamentos cooperativos, empáticos, respeitosos e orientados à manutenção de vínculos interpessoais. Elevações em amabilidade e pró-sociabilidade indicam maior consideração pelas necessidades dos outros e maior adesão a normas sociais."

Se Socialização for Médio:

"O fator Socialização situou-se na classificação média, indicando funcionamento interpessoal global dentro do esperado, com recursos de cooperação, empatia e confiança modulados pelas características do contexto. Facetas baixas devem ser analisadas como vulnerabilidades específicas no modo de estabelecer vínculos ou lidar com regras sociais."

Se Socialização for Baixo ou Muito Baixo:

"O fator Socialização apresentou classificação {classificacao}, sugerindo vulnerabilidades no campo interpessoal, especialmente na confiança, cooperação, adesão a regras sociais ou disponibilidade empática, conforme as facetas reduzidas. Baixa confiança pode indicar postura defensiva e dificuldade para estabelecer intimidade; baixa pró-sociabilidade pode sugerir menor adesão espontânea a normas e maior risco de condutas opositoras; baixa amabilidade pode indicar menor sensibilidade às necessidades emocionais dos outros."

### Realização
Se Realização for Alto ou Muito Alto:

"O fator Realização apresentou classificação {classificacao}, indicando maior orientação para metas, persistência, organização e comprometimento com tarefas. Elevações em competência e empenho sugerem percepção positiva de eficácia pessoal, esforço sustentado e tendência ao planejamento cuidadoso."

Se Realização for Médio:

"O fator Realização situou-se na classificação média, sugerindo funcionamento globalmente adequado em organização, persistência e comprometimento com tarefas. Facetas discrepantes devem ser destacadas, pois podem indicar combinação entre recursos preservados e vulnerabilidades específicas em iniciativa, planejamento ou constância."

Se Realização for Baixo ou Muito Baixo:

"O fator Realização apresentou classificação {classificacao}, indicando fragilidades em organização, persistência, planejamento e manutenção de esforço dirigido a metas. Baixos escores em competência sugerem percepção reduzida de eficácia pessoal e maior tendência à desistência diante de obstáculos; baixa ponderação indica maior risco de decisões pouco planejadas; baixo empenho sugere menor constância e menor cuidado na finalização de tarefas."

### Abertura
Se Abertura for Alto ou Muito Alto:

"O fator Abertura apresentou classificação {classificacao}, indicando maior curiosidade intelectual, flexibilidade cognitiva, interesse por ideias novas e disposição para experiências variadas."

Se Abertura for Médio:

"O fator Abertura situou-se na classificação média, sugerindo flexibilidade compatível com o esperado, com equilíbrio entre manutenção de rotinas e abertura a novas experiências."

Se Abertura for Baixo ou Muito Baixo:

"O fator Abertura apresentou classificação {classificacao}, sugerindo menor busca por novidades, menor flexibilidade diante de mudanças e preferência por rotinas, ideias conhecidas ou ambientes previsíveis. Reduções em abertura a ideias e busca por novidades podem indicar estilo mais concreto, conservador e menos inclinado à exploração de novas possibilidades."

## Regras de discrepância entre facetas
Quando o fator principal estiver médio, mas houver facetas em Alto, Muito Alto, Baixo ou Muito Baixo, o sistema deve gerar frase de discrepância:

"Apesar da classificação global {classificacao_fator}, observam-se variações internas relevantes, com {facetas_altas} em níveis elevados e {facetas_baixas} em níveis reduzidos, indicando perfil heterogêneo dentro do domínio."

## Modelo de saída para Anna Luiza

A Bateria Fatorial de Personalidade – BFP é um instrumento psicológico baseado no modelo dos Cinco Grandes Fatores da personalidade, utilizado para avaliar tendências relativamente estáveis do funcionamento emocional, interpessoal, motivacional, comportamental e de abertura à experiência. Seus resultados permitem compreender padrões de autorregulação, sociabilidade, organização, persistência, reatividade emocional e estilo de enfrentamento, devendo ser interpretados em conjunto com a história clínica, observação comportamental e demais achados da avaliação neuropsicológica.

Os resultados de Anna Luiza indicam Neuroticismo muito alto, com elevação importante em vulnerabilidade, instabilidade emocional e passividade. Esse perfil sugere maior sensibilidade emocional, insegurança subjetiva, oscilação afetiva, baixa tolerância à frustração e tendência a vivenciar desconforto psicológico com maior intensidade. A elevação em passividade também pode indicar dificuldade para iniciar tarefas, sustentar motivação e tomar decisões de forma autônoma quando há sobrecarga emocional ou insegurança. A faceta Depressão permaneceu na faixa média, sugerindo que, embora exista importante reatividade emocional, não se observou elevação proporcional em indicadores de desesperança ou percepção negativa persistente do futuro dentro deste instrumento.

Na Extroversão, Anna Luiza apresentou classificação muito baixa, com redução expressiva em comunicação e interações sociais, além de dinamismo baixo. Esse padrão sugere funcionamento mais reservado, menor busca espontânea por contatos sociais, possível desconforto em situações de exposição interpessoal e preferência por ambientes mais previsíveis ou com menor demanda social. A Altivez em faixa média indica percepção de valor pessoal sem elevação marcante de necessidade de reconhecimento ou destaque social.

O fator Socialização foi classificado como muito baixo, com destaque para confiança muito baixa e pró-sociabilidade baixa, embora a amabilidade tenha permanecido na faixa média. Esse perfil sugere postura interpessoal mais defensiva, dificuldade para confiar plenamente nos outros e possível cautela no estabelecimento de vínculos. A manutenção da amabilidade em nível médio indica que tais dificuldades não significam ausência de cordialidade ou consideração interpessoal, mas maior seletividade, desconfiança e reserva nas relações.

Em Realização, o desempenho global situou-se na faixa média, porém com perfil interno heterogêneo. A competência muito baixa sugere percepção reduzida de eficácia pessoal, maior insegurança diante de tarefas desafiadoras e tendência a duvidar da própria capacidade de realização. Em contrapartida, o empenho muito alto indica elevado esforço, dedicação e exigência pessoal na execução de tarefas. Essa combinação pode refletir um padrão de alta cobrança interna associado a baixa autoconfiança, no qual a paciente tende a esforçar-se intensamente, mas com percepção subjetiva de insuficiência ou medo de não corresponder às demandas.

O fator Abertura apresentou classificação muito baixa, com reduções em abertura a ideias e busca por novidades, enquanto liberalismo permaneceu em faixa média. Esse padrão sugere preferência por rotinas, menor busca espontânea por experiências novas e possível desconforto diante de mudanças, especialmente quando exigem flexibilidade cognitiva, exploração de alternativas ou adaptação a contextos pouco previsíveis.

Em análise clínica, o perfil de personalidade de Anna Luiza é marcado por elevada reatividade emocional, retraimento social, baixa confiança interpessoal, menor abertura a mudanças e um padrão de realização caracterizado por contraste entre baixa percepção de competência e elevado empenho. Esse conjunto sugere tendência a funcionamento emocionalmente sensível, autocobrança elevada, insegurança diante de demandas e preferência por contextos previsíveis, com possíveis impactos sobre autonomia, relações sociais, tomada de decisão e enfrentamento de situações novas. Esses resultados devem ser integrados aos dados da anamnese, à observação comportamental e aos demais instrumentos utilizados, uma vez que o BFP descreve tendências de personalidade e não estabelece diagnóstico isolado.

## Função Python sugerida para o sistema

```python
def gerar_interpretacao_bfp(nome: str, resultados: dict) -> str:
    """
    Gera interpretação descritiva do BFP para laudo neuropsicológico.
    resultados deve conter fatores e facetas com classificações originais.
    """
    fatores = ["Neuroticismo", "Extroversão", "Socialização", "Realização", "Abertura"]
    # 1. Validar se todos os fatores existem.
    # 2. Agrupar facetas por fator.
    # 3. Identificar facetas elevadas: Alto/Muito Alto.
    # 4. Identificar facetas reduzidas: Baixo/Muito Baixo.
    # 5. Aplicar templates por fator.
    # 6. Gerar síntese final integrativa.
    # 7. Nunca gerar diagnóstico isolado.
    raise NotImplementedError
```

## Critérios de qualidade obrigatórios

- Não usar travessões longos.
- Não iniciar todos os parágrafos com “No” ou “Na”.
- Usar linguagem técnica, clara e integrada.
- Não copiar o texto extenso do manual.
- Não repetir percentis de todas as facetas no texto, exceto quando o laudo exigir tabela.
- Não transformar traço de personalidade em diagnóstico.
- Sempre terminar com síntese funcional iniciada por “Em análise clínica”.
- Em laudos, usar apenas o primeiro nome ou nome de exibição, salvo na identificação e conclusão geral quando o sistema exigir nome completo.
