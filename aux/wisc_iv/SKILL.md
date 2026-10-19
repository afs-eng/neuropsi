---
name: wisc-iv-interpretacao
version: 2.0.0
description: Interpretação clínica auditável dos índices e subtestes do WISC-IV para laudos neuropsicológicos no GoPsi.
---

# Skill — WISC-IV | Interpretação Neuropsicológica

## Objetivo
Produzir interpretação clínica em português brasileiro do WISC-IV com base **exclusiva** em escores, classificações, tabelas normativas, comparações estatísticas e observações efetivamente fornecidas pelo backend. A IA não calcula normas, não transforma escores brutos em ponderados e não estabelece diagnósticos.

## Referência de estrutura
Inspirada nas páginas 4–8 do laudo de Giovanni dos Santos Luz: perfil global QIT/ICV/IOP/IMO/IVP/GAI/CPI, seguido por análises complementares de funções executivas, linguagem, gnosias e praxias e memória/aprendizagem. A estrutura é reutilizável; os resultados de Giovanni **não são valores padrão**.

## Entradas mínimas
- `paciente`: idade na data de avaliação, escolaridade, contexto clínico relevante, observações de aplicação.
- `indices`: QIT, ICV, IOP, IMO, IVP; cada um com escore composto, classificação normativa, intervalo de confiança (se houver), validade e fonte normativa.
- `indices_complementares`: GAI e CPI somente se calculados validamente, com classificação e referência normativa.
- `subtestes`: nome, escore bruto (opcional), escore ponderado, classificação validada e notas qualitativas.
- `comparacoes`: diferenças entre índices, significância estatística, frequência/base rate, fonte normativa; campos opcionais.
- `contexto`: hipóteses e dados clínicos fornecidos para integração prudente; não converter relatos em fatos observados.

## Regras críticas de auditoria
1. Não inventar escores, classificações, intervalos, subtestes, comparações ou frequência de discrepâncias.
2. Não usar percentis no **texto interpretativo**; quando recebidos, reservar para tabela técnica ou metadados.
3. Descrever QIT como estimativa do funcionamento intelectual global **somente se interpretável**. Se houver heterogeneidade importante, avaliar a representatividade do QIT, sem invalidá-lo automaticamente.
4. Não chamar uma diferença de 'estatisticamente significativa', 'clinicamente relevante' ou 'rara' sem informação normativa e contextual suficiente. Pode-se dizer 'diferença numérica' ou 'melhor desempenho relativo'.
5. GAI e CPI não substituem automaticamente QIT; interpretar separadamente e apenas quando disponíveis e válidos. Não inferir diferença significativa GAI–CPI sem comparação formal.
6. Escores médios não provam ausência de dificuldades cotidianas; escores baixos isolados não provam transtornos.
7. Subtestes do WISC-IV oferecem **indicadores de processos cognitivos**, mas não medem isoladamente, de forma abrangente, inibição, flexibilidade, planejamento, gnosias, praxias, linguagem funcional ou memória episódica.
8. Não inferir funcionamento executivo global preservado ou comprometido apenas de Semelhanças, Conceitos Figurativos, Compreensão e Raciocínio Matricial.
9. Não inferir ausência de apraxia/agnosia apenas de Cubos e Raciocínio Matricial.
10. Não chamar Dígitos e Sequência de Números e Letras de medida suficiente da aprendizagem episódica; esses subtestes informam prioritariamente atenção auditiva imediata e memória operacional.
11. 'Fala espontânea dentro do esperado' só pode aparecer se sustentada por observação clínica explícita, não pelo WISC-IV.
12. Não atribuir causalidade a TDAH, TEA, ansiedade ou outras condições com base apenas no WISC-IV.
13. Evitar linguagem absoluta: 'demonstra', 'comprova', 'descarta'; preferir 'indica', 'sugere', 'é compatível com'.
14. Se houver incoerência entre classificação, índice e norma, interromper afirmações afetadas e registrar pendência.
15. Não reproduzir tabelas normativas protegidas, itens ou instruções de aplicação do instrumento.

## Módulos de interpretação

### 1. Funcionamento intelectual global
Ordem: QIT (valor/classificação e representatividade); ICV (formação de conceitos, compreensão e raciocínio verbal); IOP (raciocínio perceptual e visuoespacial); IMO (retenção/manipulação de informação, atenção imediata); IVP (eficiência em tarefas visuais simples com limite de tempo); GAI e CPI (quando presentes); síntese de forças e fragilidades **relativas**. Não usar a expressão 'perfil heterogêneo clinicamente relevante' sem sustentação das comparações.

### 2. Funções executivas — indicadores indiretos
Subtestes de referência do modelo: Semelhanças, Conceitos Figurativos, Compreensão, Raciocínio Matricial. Descrever abstração, categorização, julgamento prático e raciocínio lógico, **sem equipará-los a testes específicos de inibição, alternância ou planejamento**. Encerrar indicando necessidade de integração com tarefas executivas dedicadas e observação clínica.

### 3. Linguagem — habilidades verbais avaliadas
Subtestes: Semelhanças, Vocabulário, Compreensão. Descrever abstração verbal, conhecimento lexical e compreensão/julgamento verbal. Distinguir de avaliação fonoaudiológica de linguagem pragmática, fonologia, articulação e fluência. Só mencionar fala espontânea quando houver registro observacional.

### 4. Habilidades visuoperceptivas e construtivas
Subtestes: Raciocínio Matricial e Cubos. Descrever raciocínio visual, análise de padrões, organização espacial e construção visomotora, sem concluir integridade global das gnosias e praxias.

### 5. Atenção auditiva imediata e memória operacional
Subtestes: Dígitos e Sequência de Números e Letras. Descrever retenção sequencial, manipulação mental e controle atencional conforme os resultados. Não concluir sobre consolidação, evocação tardia ou aprendizagem episódica.


## Catálogo individual dos subtestes WISC-IV
A IA deve gerar uma interpretação **individual para cada subteste efetivamente aplicado**, antes da síntese por domínio. A ausência de subteste não autoriza criar resultado. Não confundir escore bruto com escore ponderado nem usar faixas de escore bruto do laudo de referência como normas gerais. Os agrupamentos abaixo são organizacionais, não equivalem a escalas clínicas independentes.

### Compreensão Verbal (ICV)
- **Semelhanças:** formação de conceitos, abstração e raciocínio verbal; não mede isoladamente flexibilidade executiva.
- **Vocabulário:** conhecimento lexical, desenvolvimento conceitual e expressão de definições; considerar oportunidades educacionais e linguísticas.
- **Compreensão:** raciocínio verbal aplicado a situações práticas e convenções sociais; não equivale a medida abrangente de cognição social.
- **Informação (suplementar):** conhecimento geral adquirido e recuperação de informações aprendidas; contextualizar escolaridade e exposição cultural.
- **Raciocínio com Palavras (suplementar):** inferência verbal a partir de pistas e formação de conceitos.

### Organização Perceptual (IOP)
- **Cubos:** análise e organização visuoespacial e construção com material visual; desempenho pode envolver demandas visuomotoras e temporais.
- **Conceitos Figurativos:** categorização visual e identificação de relações conceituais entre figuras.
- **Raciocínio Matricial:** raciocínio abstrato não verbal, reconhecimento de padrões e relações visuais.
- **Completar Figuras (suplementar):** atenção a detalhes e reconhecimento de elementos visuais ausentes; não concluir diagnóstico de agnosia.

### Memória Operacional (IMO)
- **Dígitos:** atenção auditiva imediata e memória de curto prazo; quando disponíveis, diferenciar ordem direta e inversa sem inventar subtotais.
- **Sequência de Números e Letras:** manutenção e reorganização mental de informações auditivo-verbais.
- **Aritmética (suplementar):** cálculo mental sob exigência de atenção e memória operacional; considerar habilidades matemáticas e ansiedade de desempenho.

### Velocidade de Processamento (IVP)
- **Código:** rapidez e precisão de associação visual e registro grafomotor sob limite de tempo; considerar coordenação motora e familiaridade com a tarefa.
- **Procurar Símbolos:** varredura visual, discriminação perceptiva e rapidez de decisão em estímulos simples.
- **Cancelamento (suplementar):** busca visual seletiva sob tempo, com componentes de atenção e velocidade; não equiparar diretamente a medida clínica global de atenção.

### Seções complementares do modelo de Giovanni
Quando solicitado, organizar as interpretações individuais nas seções **Funções Executivas — indicadores indiretos** (Semelhanças, Conceitos Figurativos, Compreensão, Raciocínio Matricial), **Linguagem** (Semelhanças, Vocabulário, Compreensão, observação de fala espontânea apenas se fornecida), **Gnosias e Praxias — indicadores visuoperceptivos e construtivos** (Raciocínio Matricial, Cubos) e **Memória e Aprendizagem — especificamente atenção e memória operacional** (Dígitos, Sequência de Números e Letras). Se um mesmo subteste aparecer em mais de uma seção, mudar o foco interpretativo sem repetir literalmente o parágrafo. Essas seções são um formato de laudo e não substituem testes específicos dos respectivos domínios.

## Formato obrigatório de cada subteste
Produzir `nome`, `grupo`, `escore_ponderado`, `classificacao`, `interpretacao`, `evidencias` e `alertas`. Em `interpretacao`, apresentar: habilidade-alvo, desempenho classificado segundo norma fornecida, força ou fragilidade **relativa** quando comparações válidas existirem, e limitações. Se faltar escore ponderado ou classificação, usar `status: pendente` para aquele subteste, sem completar lacunas por inferência. Não incluir percentis no texto narrativo.

## Auditoria ampliada
- Confirmar quais subtestes são principais ou suplementares e quais efetivamente compuseram cada índice, conforme o protocolo corrigido pelo profissional.
- Não somar escores ponderados nem recalcular índices pela IA; isso pertence ao motor psicométrico validado.
- Para GAI e CPI, exigir cálculo e norma específicos; não deduzir apenas dos índices primários.
- Registrar condições de aplicação, adaptações, interrupções e dados de validade que possam afetar o resultado.
- Não generalizar escores de velocidade como prova de déficit atencional ou escores verbais como prova de linguagem funcional intacta.
- Confrontar a classificação de cada subteste com a classificação validada pelo backend; nunca inferir classificação a partir de escores brutos.

## Estilo do texto final
- Redigir em terceira pessoa, tom técnico, coeso, sem listas no corpo do laudo.
- Para cada índice ou subteste disponível: nome, escore composto/ponderado se pertinente, classificação recebida, habilidade investigada, implicação cautelosa.
- Não repetir o mesmo significado em vários parágrafos; evitar 'recursos adequados para' repetidamente.
- Fechar cada seção com uma síntese integrativa proporcional às evidências.
- Não inserir percentis nos parágrafos interpretativos.
- Não acrescentar diagnóstico ou CID.

## Contrato JSON
```json
{
  "instrumento": "WISC-IV",
  "status": "ok|pendente|inconsistente",
  "interpretacao_global": "Texto pronto para o laudo ou null",
  "subtestes_individuais": [{"nome": "Semelhanças", "grupo": "ICV", "status": "ok|pendente", "escore_ponderado": null, "classificacao": null, "interpretacao": null, "evidencias": [], "alertas": []}],
  "secoes": {
    "funcoes_executivas_indicadores": "Texto ou null",
    "linguagem_habilidades_verbais": "Texto ou null",
    "habilidades_visuoperceptivas_construtivas": "Texto ou null",
    "atencao_memoria_operacional": "Texto ou null"
  },
  "forcas_relativas": [],
  "fragilidades_relativas": [],
  "alertas_consistencia": [],
  "dados_faltantes": [],
  "limitacoes": [],
  "diagnostico_automatico": false
}
```

## Verificações antes da entrega
- QIT, ICV, IOP, IMO, IVP e índices complementares correspondem exatamente à entrada.
- Nenhuma classificação foi criada a partir de faixas presumidas.
- Discrepâncias significativas só são mencionadas com evidência estatística fornecida.
- Nenhum percentil consta da interpretação narrativa.
- As seções opcionais só aparecem quando existem dados.
- A saída é JSON válido e cada afirmação tem rastreabilidade aos dados recebidos.

## Exemplo de interpretação global — exclusivamente com os dados do laudo de referência
"O desempenho no WISC-IV indicou funcionamento intelectual global na faixa média (QIT = 104), com melhor resultado relativo no Índice de Compreensão Verbal (ICV = 119, média superior). Os índices de Organização Perceptual (IOP = 92), Memória Operacional (IMO = 100) e Velocidade de Processamento (IVP = 97) situaram-se na faixa média. O Índice de Habilidade Geral (GAI = 106) e o Índice de Proficiência Cognitiva (CPI = 98) também se encontraram na faixa média. O conjunto sugere maior facilidade relativa nas tarefas de raciocínio e compreensão verbal, enquanto os demais domínios avaliados apresentaram desempenho dentro do esperado. A interpretação da magnitude e da relevância das diferenças entre índices depende das comparações normativas pertinentes." 

Este exemplo serve **somente** como demonstração de estilo; não deve ser reutilizado para outros pacientes.
