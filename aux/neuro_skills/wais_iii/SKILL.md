---
name: wais-iii-interpretacao-subtestes
version: 2.0.0
description: Skill GoPsi para interpretar índices e os 14 subtestes do WAIS-III com rastreabilidade e cautela psicométrica.
---

# WAIS-III — índices, subtestes e análises por domínio

## Origem e limite do modelo
Base de organização: laudo Guilherme Cabral Costa, seções Capacidade Cognitiva Global e Subescalas WAIS III. O documento organiza análises de Linguagem (Semelhanças, Vocabulário, Compreensão), Gnosias e Praxias (Raciocínio Matricial, Cubos), Função Executiva (Semelhanças, Compreensão, Raciocínio Matricial), Memória e Aprendizagem (Sequência de Números e Letras, Dígitos; RAVLT separado). O catálogo dos demais subtestes é uma ampliação técnica da skill, não conteúdo observado no laudo. Nenhum resultado do paciente de referência é reutilizado como padrão.

## Entradas necessárias
- `paciente`: idade exata na avaliação, escolaridade, idioma, observações relevantes e condições de aplicação.
- `indices`: QIT, QIV, QIE, ICV, IOP, IMO, IVP, com escore composto, classificação e intervalo de confiança se disponível. Interpretar somente os índices efetivamente calculados.
- `subtestes`: nome canônico, aplicado/omitido, escore bruto opcional, escore ponderado, classificação validada, observações qualitativas e fonte normativa.
- `comparacoes`: pares comparados, diferença, significância estatística, taxa-base e referência normativa quando calculadas pelo backend.
- `validade`: normas/edição, substituições, condições de aplicação, advertências sobre interpretabilidade.

## Regras obrigatórias
1. A IA **não calcula** conversão bruto→ponderado, índices, normas, significância, frequência de discrepâncias ou classificações.
2. Nunca usar faixas de escore bruto do laudo de Guilherme como norma; classificações vêm do backend.
3. Texto narrativo sem percentis; valores compostos e ponderados só quando pertinentes.
4. Descrever QIT como estimativa global com cautela diante de heterogeneidade; não invalidar QIT automaticamente.
5. Não afirmar discrepância estatisticamente significativa, rara ou clinicamente relevante sem dados normativos e contexto suficientes.
6. Escores baixos são achados de desempenho, não prova isolada de transtorno; escores médios não descartam dificuldades reais.
7. Não equiparar Semelhanças, Compreensão e Raciocínio Matricial a medidas diretas de inibição, planejamento ou flexibilidade.
8. Não diagnosticar agnosia/apraxia com Cubos e Raciocínio Matricial, nem memória episódica com Dígitos e Sequência de Números e Letras.
9. O RAVLT é outro instrumento, analisado por sua própria skill; não o apresentar como subteste WAIS-III.
10. Não atribuir diagnóstico, CID, causalidade, ou funcionamento integralmente preservado com base em subtestes isolados.
11. Não preencher subtestes ausentes nem inventar escores, relato ou observações.
12. Não reproduzir itens, instruções ou tabelas normativas protegidas.
13. Conferir consistência entre versão, idade, subtestes administrados, índices calculados e classificações.
14. Atribuir descrições de fala espontânea apenas quando há observação clínica direta registrada.

## Ordem da interpretação
1. **QIT**, representatividade e heterogeneidade (quando comprovada).
2. **QIV e QIE**, se calculados; caracterizar verbal versus execução com cautela.
3. **ICV, IOP, IMO, IVP**, conforme disponíveis.
4. **Cada subteste efetivamente aplicado**, individualmente e sem repetição mecânica.
5. **Síntese por domínios** conforme modelo do laudo; indicar limites de inferência.
6. **Síntese integrativa** com forças, fragilidades relativas, dados clínicos fornecidos e pendências.

## Catálogo dos 14 subtestes

### Compreensão Verbal
- **Vocabulário:** conhecimento lexical, definição verbal e repertório conceitual; influências educacionais e socioculturais. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Semelhanças:** abstração verbal, categorização e formação de conceitos. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Informação:** conhecimentos gerais adquiridos e recuperação de informações consolidadas. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Compreensão:** raciocínio verbal aplicado a situações sociais e práticas; não equivale a teste de cognição social. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.

### Organização Perceptual
- **Completar Figuras:** reconhecimento de detalhes relevantes e análise visual. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Cubos:** organização visuoespacial e construção visuomotora, com possível influência do tempo. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Raciocínio Matricial:** raciocínio fluido não verbal e identificação de padrões. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Arranjo de Figuras:** sequenciamento visual de eventos e inferência de relações situacionais. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Armar Objetos:** organização perceptiva e síntese visuoconstrutiva. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.

### Memória Operacional
- **Aritmética:** cálculo mental com demandas de atenção, concentração e manipulação de informação. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Dígitos:** atenção auditiva imediata e memória de curto prazo; diferenciar direta/inversa se fornecidas. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Sequência de Números e Letras:** manutenção, ordenação e manipulação de estímulos auditivo-verbais. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.

### Velocidade de Processamento
- **Códigos:** rapidez de associação visuomotora, aprendizagem incidental e registro grafomotor. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.
- **Procurar Símbolos:** varredura visual, discriminação e velocidade de decisão. Descrever escore ponderado/classificação validados, implicações limitadas ao construto, possíveis fatores de desempenho e relação com outros achados quando sustentada.

## Módulos complementares conforme o laudo-modelo
### Linguagem
Semelhanças, Vocabulário e Compreensão: raciocínio, conhecimento e julgamento verbal. Não inferir integridade global da linguagem funcional ou pragmática. Fala espontânea é dado observacional separado.

### Gnosias e Praxias — indicadores visuoperceptivos/construtivos
Raciocínio Matricial e Cubos: análise visual, raciocínio abstrato e construção visuomotora. Não concluir preservação global de gnosias ou praxias.

### Função Executiva — indicadores indiretos
Semelhanças, Compreensão e Raciocínio Matricial: abstração, julgamento prático e resolução de problemas. Não substituir testes específicos de inibição, alternância ou flexibilidade.

### Memória e Aprendizagem — atenção e memória operacional
Sequência de Números e Letras e Dígitos: retenção imediata e manipulação mental. RAVLT, quando presente, deve ser analisado pela skill própria e apenas integrado posteriormente.

## Padrão de redação
Para cada subteste: “No subteste [nome], o desempenho foi classificado como [classificação], indicando [processo cognitivo específico]. Em conjunto com [dado efetivamente disponível], o achado [interpretação prudente].” Evitar parágrafos repetidos e afirmar apenas o que o escore sustenta.

## Contrato de saída JSON
```json
{
  "instrumento": "WAIS-III",
  "interpretacao_global": "",
  "interpretacoes_indices": {},
  "interpretacoes_subtestes": {},
  "sinteses_por_dominio": {
    "linguagem": "",
    "gnosias_praxias_indicadores": "",
    "funcoes_executivas_indicadores": "",
    "atencao_memoria_operacional": ""
  },
  "interpretacao": "",
  "achados_principais": [],
  "limitacoes": [],
  "pendencias": [],
  "alertas_consistencia": [],
  "diagnostico_automatico": false
}
```

## Auditoria automática
- Cada subteste na saída existe na entrada e tem resultado normativo válido.
- Índices e subtestes não são confundidos; bruto não é tratado como ponderado.
- Comparações normativas só são mencionadas quando recebidas.
- Nenhuma narrativa usa percentis; não há diagnóstico automático.
- A interpretação está pronta para revisão e assinatura por profissional habilitado.
