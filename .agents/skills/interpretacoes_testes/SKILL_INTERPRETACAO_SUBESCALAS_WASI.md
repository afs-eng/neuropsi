# SKILL_INTERPRETACAO_SUBESCALAS_WASI_PADRAO_OURO.md

## Objetivo
Gerar interpretação clínica padronizada, em nível internacional, das subescalas da Escala Wechsler Abreviada de Inteligência – WASI, contemplando análise técnica, integração dos domínios cognitivos e coerência com dados clínicos.

## Princípios técnicos

- Linguagem técnico-científica, clara e auditável
- Integração entre subtestes (não análise isolada)
- Interpretação funcional (impacto no comportamento)
- Coerência interna com o laudo completo
- Evitar inferências diagnósticas diretas
- Utilizar sempre “Em análise clínica” como fechamento

## Entrada esperada

```json
{
  "paciente": "Nome",
  "subescalas_wasi": {
    "vocabulário": {"escore_obtido": 56, "classificacao": "Média"},
    "semelhanças": {"escore_obtido": 50, "classificacao": "Média"},
    "cubos": {"escore_obtido": 56, "classificacao": "Média"},
    "raciocínio_matricial": {"escore_obtido": 51, "classificacao": "Média"}
  }
}
```

## Estrutura de geração

### 1. Abertura

A avaliação por meio da Escala Wechsler Abreviada de Inteligência – WASI possibilitou a análise do funcionamento cognitivo de {paciente} em domínios verbais e não verbais, abrangendo habilidades de linguagem, formação de conceitos, raciocínio abstrato, organização visuoespacial e solução de problemas. O perfil observado indica funcionamento intelectual global situado na faixa {classificacao_predominante}, com desempenho homogêneo entre os subtestes avaliados.

### 2. Escala Verbal

#### Vocabulário

No subteste Vocabulário, {paciente} apresentou desempenho classificado na faixa média, evidenciando repertório lexical adequado, capacidade funcional de nomeação, compreensão semântica e definição de palavras. Esse resultado sugere domínio preservado do conhecimento verbal adquirido, bem como organização do pensamento mediado pela linguagem, favorecendo a comunicação e a compreensão de conteúdos verbais estruturados.

#### Semelhanças

No subteste Semelhanças, observou-se desempenho na faixa média, indicando capacidade adequada de abstração verbal, formação de conceitos e identificação de relações entre estímulos. Esse desempenho reflete funcionamento preservado em processos de categorização, raciocínio lógico verbal e integração conceitual.

#### Integração verbal

Em análise clínica, os resultados da Escala Verbal indicam funcionamento compatível com o esperado para a faixa média, sugerindo preservação das habilidades de compreensão verbal, raciocínio abstrato mediado pela linguagem e organização conceitual. Esse perfil favorece a aprendizagem baseada em instruções verbais e a adaptação a contextos que demandam comunicação estruturada.

### 3. Escala de Execução

#### Cubos

No subteste Cubos, {paciente} apresentou desempenho classificado na faixa média, indicando organização visuoespacial adequada, análise perceptiva eficiente e coordenação visomotora preservada. Esse resultado sugere capacidade funcional de estruturar estímulos visuais, integrar partes em um todo e executar tarefas com demanda construtiva.

#### Raciocínio Matricial

No subteste Raciocínio Matricial, o desempenho na faixa média evidencia raciocínio lógico não verbal adequado, capacidade de identificar padrões, inferir regras e resolver problemas abstratos. Esse desempenho indica funcionamento preservado em tarefas que exigem análise visual e raciocínio fluido.

#### Integração não verbal

Em análise clínica, os resultados da Escala de Execução indicam funcionamento compatível com a média esperada, sugerindo preservação das habilidades de raciocínio não verbal, percepção de padrões, organização visuoespacial e resolução de problemas abstratos.

### 4. Integração global

Em análise clínica, o perfil cognitivo evidenciado pelas subescalas do WASI indica funcionamento globalmente homogêneo, sem discrepâncias clinicamente significativas entre os domínios verbal e não verbal. O padrão observado sugere equilíbrio entre habilidades linguísticas e perceptuais, favorecendo desempenho adaptativo em contextos acadêmicos e cotidianos que demandam integração dessas competências.

## Regras obrigatórias

- Utilizar apenas o primeiro nome do paciente
- Não utilizar tabelas na interpretação
- Não mencionar percentis se não fornecidos
- Não utilizar travessões longos
- Evitar repetições estruturais
- Manter coerência com demais testes do laudo
- Finalizar blocos com “Em análise clínica”

## Saída esperada

Texto contínuo, técnico, integrado, sem redundâncias, com padrão internacional de escrita neuropsicológica.
