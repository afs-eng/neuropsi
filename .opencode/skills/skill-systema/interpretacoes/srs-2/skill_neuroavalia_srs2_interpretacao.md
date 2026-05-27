# Skill NeuroAvalia – SRS-2: Correção, Validação e Interpretação Clínica para Todos os Perfis de Resultado

## 1. Finalidade da skill

Esta skill orienta a IA do NeuroAvalia a gerar, revisar e corrigir interpretações clínicas do **SRS-2 – Escala de Responsividade Social, Segunda Edição**, garantindo coerência entre:

- pontuação bruta;
- Escore T;
- classificação clínica;
- gráficos;
- tabelas;
- análise por domínio;
- síntese clínica;
- hipótese diagnóstica;
- regra de segurança quanto ao uso do instrumento.

A skill deve ser usada sempre que o sistema gerar relatório do SRS-2, independentemente do perfil de resultado: normal, leve, moderado, severo, homogêneo, heterogêneo, com elevação isolada ou com elevação combinada entre comunicação social e padrões restritos/repetitivos.

## 2. Regra central obrigatória

A IA nunca deve interpretar como déficit um domínio classificado como **dentro dos limites normais**.

Exemplo proibido:

> O domínio de Percepção Social apresentou elevação em nível dentro dos limites normais, indicando dificuldades em perceber pistas interpessoais.

Correção obrigatória:

> O domínio de Percepção Social situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à percepção de pistas sociais básicas e captação de elementos relevantes do contexto interpessoal.

## 3. Critério classificatório obrigatório

A IA deve classificar todos os domínios exclusivamente pelo Escore T.

| Escore T | Classificação | Regra interpretativa |
|---:|---|---|
| T ≤ 59 | Dentro dos limites normais | Não interpretar como prejuízo clínico |
| 60 ≤ T ≤ 65 | Nível leve | Interpretar como elevação leve ou dificuldade discreta |
| 66 ≤ T ≤ 75 | Nível moderado | Interpretar como prejuízo clinicamente relevante |
| T ≥ 76 | Nível severo | Interpretar como prejuízo expressivo |

## 4. Termos permitidos por classificação

### 4.1 Dentro dos limites normais

Usar:

- situou-se dentro dos limites normativos;
- permaneceu dentro da faixa esperada;
- não apresentou elevação clinicamente significativa;
- não indicou prejuízo clínico neste instrumento;
- sugere preservação relativa do domínio avaliado.

Não usar:

- apresentou elevação;
- apresentou déficit;
- indicou dificuldade;
- evidenciou prejuízo;
- sugeriu comprometimento.

### 4.2 Nível leve

Usar:

- apresentou elevação em nível leve;
- sugere dificuldades discretas;
- indica traços ou sinais leves;
- aponta para dificuldades sutis, porém clinicamente relevantes;
- deve ser interpretado em conjunto com dados clínicos.

Não usar:

- comprometimento grave;
- prejuízo severo;
- déficit intenso;
- diagnóstico confirmado.

### 4.3 Nível moderado

Usar:

- apresentou elevação em nível moderado;
- indica prejuízo clinicamente relevante;
- sugere impacto funcional potencial;
- aponta para dificuldades consistentes no domínio avaliado.

Não usar:

- leve;
- discreto apenas;
- sem prejuízo;
- dentro da normalidade.

### 4.4 Nível severo

Usar:

- apresentou elevação em nível severo;
- indica prejuízo expressivo;
- sugere impacto funcional importante;
- requer investigação clínica aprofundada;
- demanda integração cuidadosa com anamnese, observação clínica e demais instrumentos.

Não usar:

- comprova TEA;
- confirma diagnóstico;
- diagnóstico fechado pelo SRS-2.

## 5. Funções lógicas obrigatórias

### 5.1 Função de classificação

```python
def classificar_srs2(escore_t: int) -> str:
    if escore_t <= 59:
        return "Dentro dos limites normais"
    if 60 <= escore_t <= 65:
        return "Nível leve"
    if 66 <= escore_t <= 75:
        return "Nível moderado"
    return "Nível severo"
```

### 5.2 Função de status clínico

```python
def tem_elevacao_clinica(escore_t: int) -> bool:
    return escore_t >= 60
```

### 5.3 Função para identificar domínio mais elevado

```python
def dominio_mais_elevado(escalas: list[dict]) -> dict:
    dominios = [e for e in escalas if e["nome"] != "Escore Total"]
    return max(dominios, key=lambda e: e["escore_t"])
```

### 5.4 Função para identificar domínios elevados

```python
def dominios_elevados(escalas: list[dict]) -> list[dict]:
    return [
        e for e in escalas
        if e["nome"] != "Escore Total" and e["escore_t"] >= 60
    ]
```

### 5.5 Função para identificar domínios normais

```python
def dominios_normais(escalas: list[dict]) -> list[dict]:
    return [
        e for e in escalas
        if e["nome"] != "Escore Total" and e["escore_t"] <= 59
    ]
```

## 6. Regra de ouro para análise por domínio

A IA deve gerar uma frase diferente para cada domínio conforme a classificação. Nenhuma frase pode contradizer o Escore T.

## 7. Modelos por domínio e classificação

### 7.1 Percepção Social

**Dentro dos limites normais**

> O domínio de Percepção Social situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à percepção de pistas sociais básicas, expressões faciais, gestos, tom de voz e captação de elementos relevantes do contexto interpessoal.

**Nível leve**

> O domínio de Percepção Social apresentou elevação em nível leve, sugerindo dificuldades discretas na identificação de pistas sociais básicas, como expressões faciais, gestos, tom de voz e sinais contextuais relevantes para a interação interpessoal.

**Nível moderado**

> O domínio de Percepção Social apresentou elevação em nível moderado, indicando dificuldade clinicamente relevante para perceber pistas sociais básicas e captar elementos importantes do contexto interpessoal, o que pode comprometer a adequação das respostas sociais em situações cotidianas.

**Nível severo**

> O domínio de Percepção Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na identificação de pistas sociais básicas e na captação de sinais interpessoais relevantes, com potencial impacto importante na adaptação social.

### 7.2 Cognição Social

**Dentro dos limites normais**

> O domínio de Cognição Social permaneceu dentro dos limites normativos, sugerindo ausência de elevação clinicamente significativa, neste instrumento, quanto à interpretação de pistas sociais, compreensão de intenções e inferência de estados emocionais ou mentais de outras pessoas.

**Nível leve**

> O domínio de Cognição Social apresentou elevação em nível leve, sugerindo dificuldades discretas na compreensão de situações sociais, interpretação de intenções e inferência de estados mentais de outras pessoas.

**Nível moderado**

> O domínio de Cognição Social apresentou elevação em nível moderado, indicando dificuldade clinicamente relevante para interpretar situações sociais, compreender intenções, reconhecer perspectivas e manejar regras sociais implícitas.

**Nível severo**

> O domínio de Cognição Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na interpretação de informações sociais, na compreensão de intenções e na atribuição de significado às interações interpessoais.

### 7.3 Comunicação Social

**Dentro dos limites normais**

> O domínio de Comunicação Social situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à comunicação social expressiva, reciprocidade comunicativa e adequação da comunicação ao contexto.

**Nível leve**

> O domínio de Comunicação Social apresentou elevação em nível leve, sugerindo dificuldades discretas em sustentar trocas comunicativas recíprocas, ajustar a comunicação ao contexto e integrar recursos verbais e não verbais durante a interação social.

**Nível moderado**

> O domínio de Comunicação Social apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes na comunicação social recíproca, incluindo sustentação de trocas comunicativas, adequação da linguagem ao contexto e uso integrado de recursos expressivos verbais e não verbais.

**Nível severo**

> O domínio de Comunicação Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na comunicação social recíproca, com impacto importante na capacidade de iniciar, manter e adaptar trocas comunicativas em contextos interpessoais.

### 7.4 Motivação Social

**Dentro dos limites normais**

> O domínio de Motivação Social permaneceu dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto ao interesse espontâneo, iniciativa e engajamento em interações sociais.

**Nível leve**

> O domínio de Motivação Social apresentou elevação em nível leve, sugerindo dificuldades discretas no interesse espontâneo por interações sociais, na iniciativa interpessoal ou no engajamento social.

**Nível moderado**

> O domínio de Motivação Social apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes no interesse espontâneo, na iniciativa social e no engajamento interpessoal, podendo refletir menor busca ativa por interação social.

**Nível severo**

> O domínio de Motivação Social apresentou elevação em nível severo, sugerindo prejuízo expressivo na iniciativa social, no interesse espontâneo por interações e no engajamento interpessoal.

### 7.5 Padrões Restritos e Repetitivos

**Dentro dos limites normais**

> O domínio de Padrões Restritos e Repetitivos situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à presença de rigidez comportamental, repetitividade, interesses restritos ou resistência a mudanças.

**Nível leve**

> O domínio de Padrões Restritos e Repetitivos apresentou elevação em nível leve, sugerindo sinais discretos de rigidez comportamental, repetitividade, interesses restritos ou menor flexibilidade diante de mudanças.

**Nível moderado**

> O domínio de Padrões Restritos e Repetitivos apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes relacionadas à rigidez comportamental, repetitividade, interesses restritos ou menor flexibilidade diante de mudanças.

**Nível severo**

> O domínio de Padrões Restritos e Repetitivos apresentou elevação em nível severo, sugerindo prejuízo expressivo associado à rigidez comportamental, comportamentos repetitivos, interesses restritos e resistência significativa a mudanças.

### 7.6 Comunicação e Interação Social

**Dentro dos limites normais**

> A escala de Comunicação e Interação Social situou-se dentro dos limites normativos, sugerindo ausência de elevação clinicamente significativa, neste instrumento, no conjunto de habilidades relacionadas à reciprocidade socioemocional, comunicação social e manutenção de interações interpessoais.

**Nível leve**

> A escala de Comunicação e Interação Social apresentou elevação em nível leve, sugerindo dificuldades discretas no conjunto de habilidades relacionadas à reciprocidade socioemocional, comunicação social e manutenção de interações interpessoais.

**Nível moderado**

> A escala de Comunicação e Interação Social apresentou elevação em nível moderado, indicando dificuldades clinicamente relevantes nos componentes centrais de reciprocidade social, comunicação interpessoal e manutenção de relações sociais.

**Nível severo**

> A escala de Comunicação e Interação Social apresentou elevação em nível severo, sugerindo prejuízo expressivo nas habilidades de reciprocidade socioemocional, comunicação social e interação interpessoal.

### 7.7 Escore Total

**Dentro dos limites normais**

> A Pontuação Total do SRS-2 situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa na medida global de responsividade social avaliada pelo instrumento. Esse resultado não exclui a análise clínica quando houver queixas funcionais relevantes, mas não sugere, isoladamente, prejuízo global expressivo no SRS-2.

**Nível leve**

> A Pontuação Total do SRS-2 situou-se em nível leve, sugerindo dificuldades sutis, porém clinicamente relevantes, na responsividade social global. Esse resultado deve ser integrado à anamnese, observação clínica e demais instrumentos aplicados.

**Nível moderado**

> A Pontuação Total do SRS-2 situou-se em nível moderado, indicando comprometimento global clinicamente relevante da responsividade social, com impacto potencial na comunicação social recíproca, na interação interpessoal e/ou na flexibilidade comportamental.

**Nível severo**

> A Pontuação Total do SRS-2 situou-se em nível severo, sugerindo comprometimento global expressivo da responsividade social, com provável impacto funcional importante na comunicação social, interação interpessoal e flexibilidade comportamental.

## 8. Modelos de síntese por perfil global

### 8.1 Perfil global normal

Condição: `Escore Total ≤ 59`

> Em análise clínica, o perfil obtido no SRS-2 situou-se dentro dos limites normativos, com Pontuação Total sem elevação clinicamente significativa. Os domínios avaliados não indicam, neste instrumento, prejuízo global expressivo na responsividade social. Quando houver queixas clínicas, os achados devem ser compreendidos de forma integrada à anamnese, observação comportamental e demais instrumentos, pois resultado normativo no SRS-2 não exclui, por si só, a necessidade de investigação clínica.

### 8.2 Perfil global leve

Condição: `60 ≤ Escore Total ≤ 65`

> Em análise clínica, o perfil obtido no SRS-2 evidenciou elevação global em nível leve da responsividade social. Esse resultado sugere dificuldades sutis, porém clinicamente relevantes, na qualidade das interações interpessoais, na comunicação social recíproca e/ou na flexibilidade comportamental. A interpretação deve considerar se as elevações se distribuem de forma ampla ou se permanecem concentradas em domínios específicos.

### 8.3 Perfil global moderado

Condição: `66 ≤ Escore Total ≤ 75`

> Em análise clínica, o perfil obtido no SRS-2 evidenciou elevação global em nível moderado da responsividade social. Esse resultado indica comprometimento clinicamente relevante no funcionamento sociointeracional, podendo envolver prejuízos na comunicação social recíproca, na interpretação de situações interpessoais, no engajamento social e/ou na flexibilidade comportamental.

### 8.4 Perfil global severo

Condição: `Escore Total ≥ 76`

> Em análise clínica, o perfil obtido no SRS-2 evidenciou elevação global em nível severo da responsividade social. Esse resultado sugere comprometimento expressivo no funcionamento sociointeracional, com impacto funcional importante na comunicação social, na reciprocidade interpessoal e/ou na presença de padrões restritos e repetitivos. A interpretação deve ser realizada com cautela e sempre integrada ao histórico do desenvolvimento, observação clínica, funcionamento adaptativo e demais instrumentos.

## 9. Modelos para combinações clínicas

### 9.1 Escore Total normal com um domínio leve

> O Escore Total permaneceu dentro dos limites normativos, indicando ausência de elevação global clinicamente significativa no SRS-2. Observa-se, entretanto, elevação pontual em [domínio], classificada em nível leve. Esse achado deve ser interpretado como indicador específico e não como comprometimento global da responsividade social, exigindo correlação com queixas clínicas, observação comportamental e funcionamento adaptativo.

### 9.2 Escore Total normal com domínio moderado ou severo

> Embora o Escore Total esteja dentro dos limites normativos, observa-se elevação clinicamente relevante em [domínio]. Esse padrão sugere perfil heterogêneo, no qual uma área específica apresenta maior vulnerabilidade, sem configurar elevação global no instrumento. A interpretação deve ser cautelosa e integrada aos dados clínicos.

### 9.3 Comunicação social elevada sem padrões restritos elevados

> A elevação em Comunicação e Interação Social, na ausência de elevação em Padrões Restritos e Repetitivos, sugere dificuldades predominantemente relacionadas à reciprocidade social, comunicação interpessoal e manutenção de relações sociais. Esse perfil deve ser diferenciado de quadros em que há presença consistente de rigidez, repetitividade e interesses restritos, sendo necessária análise clínica integrada.

### 9.4 Padrões restritos elevados sem comunicação social elevada

> A elevação em Padrões Restritos e Repetitivos, com Comunicação e Interação Social dentro dos limites normativos, sugere presença de rigidez comportamental, repetitividade ou interesses restritos sem indicação, neste instrumento, de prejuízo global nas habilidades de comunicação e interação social. Esse padrão deve ser analisado qualitativamente e correlacionado ao funcionamento cotidiano.

### 9.5 Comunicação e Interação Social elevada + Padrões Restritos e Repetitivos elevado

> A elevação conjunta em Comunicação e Interação Social e Padrões Restritos e Repetitivos indica comprometimento nos dois grandes eixos sintomatológicos relacionados ao Transtorno do Espectro Autista, conforme descritos no DSM-5-TR™. Esse achado não estabelece diagnóstico isoladamente, mas fortalece a necessidade de investigação clínica de características associadas ao TEA, especialmente quando houver convergência com anamnese, observação clínica, histórico do desenvolvimento e prejuízos funcionais.

## 10. Regras para tabelas

### 10.1 Tabela de escores

Antes ou abaixo da tabela, inserir:

> A tabela de escores apresenta a pontuação bruta, o valor normativo em Escore T e a classificação clínica correspondente. A pontuação bruta representa a soma dos itens do domínio, enquanto o Escore T permite comparar o resultado com a amostra normativa da versão aplicada. Escores mais elevados indicam maior frequência ou intensidade de dificuldades associadas à responsividade social.

### 10.2 Leitura da tabela

A leitura deve conter:

1. Escore Total e classificação.
2. Domínios elevados.
3. Domínios dentro da normalidade.
4. Maior escore.
5. Síntese da distribuição.

Modelo:

> Em [nome], o Escore Total foi T=[valor], classificado como [classificação]. Os domínios elevados foram [listar domínios elevados]. Os domínios dentro dos limites normativos foram [listar domínios normais]. A maior elevação ocorreu em [domínio], com Escore T=[valor], classificado como [classificação]. O perfil sugere [síntese clínica].

### 10.3 Erro proibido na leitura da tabela

Não listar domínios normais como “domínios elevados”.

Exemplo proibido:

> Domínios elevados: Percepção Social, Cognição Social...

Se Percepção Social estiver com T=54, ela deve aparecer como domínio dentro da normalidade.

## 11. Regras para gráficos

### 11.1 Perfil dos escores T

> O gráfico de perfil organiza os escores T do SRS-2 em uma régua normativa de 20 a 80 pontos, com média fixada em T=50. No protocolo de [nome], o Escore Total foi T=[valor], classificado como [classificação]. A maior elevação entre os domínios aparece em [domínio], com T=[valor], classificada como [classificação]. O gráfico permite observar se o perfil é globalmente elevado ou se há discrepâncias específicas entre os domínios.

### 11.2 Radar clínico

O radar deve incluir apenas domínios principais:

- Percepção Social
- Cognição Social
- Comunicação Social
- Motivação Social
- Padrões Restritos e Repetitivos

Evitar colocar Escore Total dentro do radar, pois ele é índice global, não domínio primário.

> O radar apresenta a distribuição dos escores T entre os principais domínios do SRS-2. No protocolo de [nome], o Escore Total foi T=[valor] e o domínio mais elevado foi [domínio], com T=[valor]. O polígono sugere [perfil global normal/leve/moderado/severo], com maior expansão relativa em [domínio]. Esse gráfico auxilia a verificar se o perfil é homogêneo ou se existem picos específicos entre comunicação/interação social e padrões restritos ou repetitivos.

## 12. Regras para hipótese diagnóstica

### 12.1 Quando não levantar hipótese diagnóstica

Condição:

`Escore Total ≤ 59 e nenhum domínio ≥ 66`

> Os resultados do SRS-2 não sustentam, isoladamente, hipótese diagnóstica de Transtorno do Espectro Autista. Caso existam queixas clínicas relevantes, recomenda-se integração com anamnese, observação clínica, funcionamento adaptativo e demais instrumentos.

### 12.2 Quando indicar investigação cautelosa

Condição:

`Escore Total entre 60 e 65 ou um domínio moderado isolado`

> Os resultados indicam elevações que justificam investigação clínica complementar, sem sustentar diagnóstico isoladamente. Recomenda-se integrar os achados à anamnese, observação clínica, histórico do desenvolvimento e funcionamento adaptativo.

### 12.3 Quando indicar hipótese diagnóstica a ser investigada

Condição:

`Escore Total ≥ 66 ou Comunicação e Interação Social ≥ 66 ou Padrões Restritos e Repetitivos ≥ 66`

> Considerando exclusivamente os resultados do SRS-2, observa-se elevação clinicamente relevante na responsividade social. Esse achado não confirma diagnóstico isoladamente, mas sustenta a necessidade de investigar hipótese diagnóstica de Transtorno do Espectro Autista quando houver convergência com anamnese, observação clínica, histórico do desenvolvimento, funcionamento adaptativo e prejuízos funcionais.

### 12.4 Quando há elevação combinada nos dois eixos

Condição:

`Comunicação e Interação Social ≥ 66 e Padrões Restritos e Repetitivos ≥ 66`

> Considerando exclusivamente os resultados do SRS-2, observa-se elevação clinicamente relevante nos dois eixos centrais associados ao Transtorno do Espectro Autista: comunicação/interação social e padrões restritos e repetitivos. Esse achado não confirma diagnóstico isoladamente, mas fortalece a necessidade de investigar hipótese diagnóstica de Transtorno do Espectro Autista quando houver convergência com anamnese, observação clínica, histórico do desenvolvimento, funcionamento adaptativo e prejuízos funcionais.

## 13. Validador de coerência textual

Antes de finalizar o relatório, a IA deve aplicar estas verificações:

### 13.1 Se classificação for normal

Se qualquer domínio tiver `Escore T ≤ 59`, o texto desse domínio não pode conter:

- elevação;
- déficit;
- dificuldade;
- prejuízo;
- comprometimento;
- alteração clinicamente relevante.

Deve conter:

- dentro dos limites normativos;
- ausência de elevação clinicamente significativa;
- preservação relativa.

### 13.2 Se classificação for leve

Se qualquer domínio tiver `60 ≤ Escore T ≤ 65`, o texto deve conter:

- nível leve;
- dificuldades discretas;
- traços ou sinais leves;
- clinicamente relevante com cautela.

### 13.3 Se classificação for moderada

Se qualquer domínio tiver `66 ≤ Escore T ≤ 75`, o texto deve conter:

- nível moderado;
- clinicamente relevante;
- prejuízo ou dificuldade relevante.

### 13.4 Se classificação for severa

Se qualquer domínio tiver `Escore T ≥ 76`, o texto deve conter:

- nível severo;
- prejuízo expressivo;
- impacto funcional importante.

## 14. Erros proibidos

A IA deve impedir automaticamente:

1. “Elevação em nível dentro dos limites normais.”
2. “Dentro dos limites normais, indicando dificuldades.”
3. “Escore Total normal, mas perfil global alterado.”
4. “SRS-2 confirmou TEA.”
5. “Diagnóstico de TEA pelo SRS-2.”
6. “Autismo leve/moderado/severo” como conclusão diagnóstica.
7. Listar domínio com T≤59 como domínio elevado.
8. Usar “Em contraste” quando não houver contraste clínico real.
9. Usar “informante” em vez de “respondente”, “responsável” ou “pessoa que respondeu à escala”.
10. Usar texto sem acentuação em português.

## 15. Substituições automáticas recomendadas

| Texto problemático | Substituir por |
|---|---|
| elevação em nível dentro dos limites normais | situou-se dentro dos limites normativos |
| indicando dificuldades, quando T≤59 | indicando ausência de elevação clinicamente significativa |
| Em contraste, Padrões Restritos... | O domínio de Padrões Restritos e Repetitivos também... |
| alterações leves, quando há domínio moderado/severo | elevação global em [classificação], com destaque para [domínio] |
| confirmou diagnóstico | sustentou necessidade de investigação clínica |
| diagnostica TEA | auxilia no rastreio de indicadores associados ao TEA |
| autismo leve | Transtorno do Espectro Autista, conforme níveis de suporte, quando clinicamente aplicável |

## 16. Modelo completo para perfil moderado com Percepção Social normal

Use este modelo quando houver perfil semelhante ao exemplo Maria Eduarda:

- Percepção Social T=54, normal
- Cognição Social T=63, leve
- Comunicação Social T=71, moderado
- Motivação Social T=66, moderado
- Padrões Restritos e Repetitivos T=68, moderado
- Comunicação e Interação Social T=68, moderado
- Escore Total T=69, moderado

> A Escala de Responsividade Social – Segunda Edição (SRS-2) foi aplicada com o objetivo de investigar possíveis dificuldades na comunicação social, cognição social, motivação social, percepção social e presença de padrões restritos e repetitivos, auxiliando no rastreio de indicadores associados ao Transtorno do Espectro Autista (TEA).
>
> O perfil obtido no SRS-2 evidenciou elevação global em nível moderado da responsividade social, com Escore Total T=69. Esse resultado sugere prejuízos clinicamente relevantes na qualidade das interações interpessoais, na comunicação social recíproca, no engajamento social e na flexibilidade comportamental.
>
> O domínio de Percepção Social situou-se dentro dos limites normativos, indicando ausência de elevação clinicamente significativa, neste instrumento, quanto à percepção de pistas sociais básicas e captação de elementos relevantes do contexto interpessoal. O domínio de Cognição Social apresentou elevação em nível leve, sugerindo dificuldades discretas na compreensão de situações sociais e na inferência de intenções e estados mentais de outras pessoas. O domínio de Comunicação Social apresentou elevação em nível moderado, configurando o maior escore do protocolo, com Escore T=71, e indicando dificuldades clinicamente relevantes em sustentar trocas comunicativas recíprocas e ajustar a comunicação ao contexto.
>
> O domínio de Motivação Social apresentou elevação em nível moderado, sugerindo dificuldades clinicamente relevantes no interesse espontâneo, na iniciativa e no engajamento social. A escala de Comunicação e Interação Social situou-se em nível moderado, funcionando como síntese das alterações nos componentes centrais de reciprocidade social e comunicação interpessoal. O domínio de Padrões Restritos e Repetitivos também apresentou elevação em nível moderado, indicando maior rigidez comportamental, repetitividade e menor flexibilidade diante de mudanças.
>
> Em análise clínica, os resultados do SRS-2 fornecem uma estimativa padronizada do funcionamento sociointeracional, mas não são suficientes, de forma isolada, para sustentar conclusão diagnóstica de TEA. A elevação conjunta em Comunicação e Interação Social e Padrões Restritos e Repetitivos fortalece a necessidade de investigação clínica de características associadas ao Transtorno do Espectro Autista, sempre em integração com história do desenvolvimento, observação comportamental, funcionamento adaptativo e demais instrumentos da avaliação neuropsicológica.

## 17. Checklist final obrigatório

Antes de entregar o relatório, a IA deve verificar:

- [ ] O Escore Total foi classificado corretamente?
- [ ] A Classificação Global corresponde ao Escore Total?
- [ ] O maior escore foi identificado corretamente?
- [ ] Nenhum domínio normal foi interpretado como dificuldade?
- [ ] Nenhum domínio normal foi listado como domínio elevado?
- [ ] Os domínios elevados foram descritos conforme leve, moderado ou severo?
- [ ] Comunicação e Interação Social foi diferenciada de Padrões Restritos e Repetitivos?
- [ ] A hipótese diagnóstica foi formulada de forma cautelosa?
- [ ] O SRS-2 foi descrito como instrumento de rastreio?
- [ ] O texto está com acentuação correta?
- [ ] O texto não usa “confirmou diagnóstico”?
- [ ] O texto não usa “autismo leve/moderado/severo” como diagnóstico?
- [ ] O texto não usa “elevação em nível dentro dos limites normais”?
- [ ] O texto usa “Em análise clínica” na síntese?
