# Skill — Elaboração de Laudo Neuropsicológico com WASI

## 1. Objetivo da skill

Esta skill orienta a IA do sistema na elaboração completa de laudos neuropsicológicos quando a **Escala Wechsler Abreviada de Inteligência – WASI** estiver presente na avaliação. O objetivo é padronizar a estrutura do laudo, os títulos, as tabelas, os gráficos, as legendas e os textos interpretativos, mantendo linguagem técnica, coerência clínica e padrão de documento profissional.

A skill deve ser utilizada para gerar laudos com estrutura organizada, compatível com Word, com interpretação clínica integrada e com apresentação visual limpa, especialmente para os seguintes componentes da WASI:

- QI Verbal.
- QI de Execução.
- QI Total.
- Subteste Vocabulário.
- Subteste Semelhanças.
- Subteste Cubos.
- Subteste Raciocínio Matricial.
- Escala Verbal.
- Escala de Execução.
- Análise das facilidades e dificuldades cognitivas.
- Gráficos e legendas padronizados.

## 2. Princípios gerais de escrita

A elaboração do laudo deve seguir linguagem técnica, clara, objetiva e integrada. O texto deve evitar repetições excessivas, especialmente no início das frases. Sempre que possível, utilizar construções variadas e diretas.

Utilizar a expressão **“Em análise clínica”** nos fechamentos interpretativos, conforme padrão preferencial do sistema.

Evitar travessões longos no corpo do laudo. Utilizar vírgulas, dois-pontos ou parênteses quando necessário.

Nas seções descritivas e interpretações, utilizar apenas o primeiro nome do paciente, salvo quando a identificação ou a conclusão geral exigir o nome completo.

Não utilizar tabelas brutas após as referências bibliográficas. O documento deve terminar na última referência.

## 3. Configuração visual do documento

### 3.1. Página

- Papel: A4.
- Margem superior: 3 cm.
- Margem inferior: 2 cm.
- Margem esquerda: 2 cm.
- Margem direita: 2 cm.
- Fonte principal: Times New Roman, tamanho 12.
- Espaçamento entre linhas: 1,15 ou 1,5, conforme padrão do sistema.
- Alinhamento do texto: justificado.
- Recuo de primeira linha: 1,25 cm, quando aplicável.

### 3.2. Títulos

Os títulos principais devem ser em caixa alta, negrito e alinhados à esquerda.

Exemplo:

```text
5. ESCALA WECHSLER ABREVIADA DE INTELIGÊNCIA – WASI
```

Subtítulos devem seguir numeração progressiva, com negrito e alinhamento à esquerda.

Exemplo:

```text
5.1. Desempenho do paciente na WASI
5.2. Subescalas da WASI
5.2.1. Escala Verbal
5.2.2. Escala de Execução
```

### 3.3. Legendas

As legendas devem ficar abaixo das tabelas e dos gráficos, com fonte Times New Roman, tamanho 8, em itálico, centralizadas.

Modelo:

```text
Tabela 1. Resultados dos índices de QI da WASI.
```

```text
Gráfico 1. Resultados dos índices de QI da WASI.
```

Não utilizar legenda acima do elemento.

## 4. Estrutura geral do laudo com WASI

A estrutura mínima do laudo deve conter:

```text
1. IDENTIFICAÇÃO
1.1. Identificação do laudo
1.2. Identificação do paciente

2. DESCRIÇÃO DA DEMANDA
2.1. Motivo do encaminhamento

3. PROCEDIMENTOS
3.1. Instrumentos utilizados

4. ANÁLISE
4.1. Anamnese
4.2. Observações clínicas

5. ESCALA WECHSLER ABREVIADA DE INTELIGÊNCIA – WASI
5.1. Definição do instrumento
5.2. Desempenho do paciente na WASI
5.3. Gráfico dos índices de QI
5.4. Interpretação dos índices de QI
5.5. Subescalas da WASI
5.5.1. Escala Verbal
5.5.2. Escala de Execução
5.6. Análise das facilidades e dificuldades cognitivas

6. ANÁLISE INTEGRADA

7. CONCLUSÃO
7.1. Hipótese Diagnóstica

8. SUGESTÕES DE CONDUTA E ENCAMINHAMENTOS

9. CONSIDERAÇÕES FINAIS

10. REFERÊNCIAS BIBLIOGRÁFICAS
```

Quando outros testes estiverem presentes, a WASI deve ocupar o capítulo correspondente à eficiência intelectual ou capacidade cognitiva global, antes das seções de atenção, memória, funções executivas, personalidade e escalas comportamentais.

## 5. Procedimentos, modelo para listar a WASI

Na seção de procedimentos, utilizar o seguinte texto:

```text
• Escala Wechsler Abreviada de Inteligência – WASI, utilizada com o objetivo de estimar o funcionamento intelectual global, o Quociente de Inteligência Verbal, o Quociente de Inteligência de Execução e o Quociente de Inteligência Total, bem como analisar habilidades de compreensão verbal, formação de conceitos, raciocínio abstrato, organização visuoespacial e raciocínio não verbal.
```

Se a WASI for aplicada junto a outros instrumentos, manter a ordem lógica:

1. Entrevista/anamnese.
2. Instrumentos de inteligência.
3. Atenção.
4. Funções executivas.
5. Memória.
6. Escalas comportamentais.
7. Escalas emocionais.
8. Personalidade.
9. Instrumentos complementares.

## 6. Definição da WASI

Usar a definição abaixo como bloco padrão:

```text
A Escala Wechsler Abreviada de Inteligência – WASI é um instrumento destinado à estimativa do funcionamento intelectual global, permitindo a análise de habilidades verbais e não verbais por meio de subtestes que investigam compreensão verbal, formação de conceitos, raciocínio abstrato, organização visuoespacial e solução de problemas. A escala fornece indicadores do Quociente de Inteligência Verbal, do Quociente de Inteligência de Execução e do Quociente de Inteligência Total, contribuindo para a compreensão do perfil cognitivo do paciente e para a integração dos achados neuropsicológicos ao contexto clínico, acadêmico e funcional.
```

## 7. Dados necessários para gerar a seção WASI

O sistema deve receber, no mínimo:

```json
{
  "paciente_nome": "Mariana",
  "idade": "10 anos e 4 meses",
  "qiv": 83,
  "qiv_classificacao": "Média Inferior",
  "qie": 102,
  "qie_classificacao": "Média",
  "qit": 92,
  "qit_classificacao": "Média",
  "subtestes": {
    "vocabulario": {
      "escore_maximo": 80,
      "escore_medio": "40 - 60",
      "escore_minimo": 20,
      "escore_obtido": 56,
      "classificacao": "Média"
    },
    "semelhancas": {
      "escore_maximo": 80,
      "escore_medio": "40 - 60",
      "escore_minimo": 20,
      "escore_obtido": 50,
      "classificacao": "Média"
    },
    "cubos": {
      "escore_maximo": 80,
      "escore_medio": "40 - 60",
      "escore_minimo": 20,
      "escore_obtido": 56,
      "classificacao": "Média"
    },
    "raciocinio_matricial": {
      "escore_maximo": 80,
      "escore_medio": "40 - 60",
      "escore_minimo": 20,
      "escore_obtido": 51,
      "classificacao": "Média"
    }
  }
}
```

## 8. Classificação dos índices de QI

Utilizar a seguinte classificação para os índices compostos:

| Pontuação | Classificação |
|---:|---|
| 130 ou mais | Muito Superior |
| 120 a 129 | Superior |
| 110 a 119 | Média Superior |
| 90 a 109 | Média |
| 80 a 89 | Média Inferior |
| 70 a 79 | Limítrofe |
| 69 ou menos | Extremamente Baixo |

Legenda obrigatória:

```text
Tabela 1. Classificação dos índices compostos da WASI.
```

## 9. Tabela dos índices de QI da WASI

### 9.1. Estrutura da tabela

A tabela dos índices deve conter:

| Índice | Pontuação | Classificação |
|---|---:|---|
| QI Verbal | {{qiv}} | {{qiv_classificacao}} |
| QI de Execução | {{qie}} | {{qie_classificacao}} |
| QI Total | {{qit}} | {{qit_classificacao}} |

Legenda:

```text
Tabela 2. Resultados dos índices de QI da WASI.
```

### 9.2. Regras visuais da tabela

- Cabeçalho em negrito.
- Fonte Times New Roman, tamanho 12.
- Alinhamento central nas colunas numéricas.
- Alinhamento à esquerda na coluna textual.
- Preferir tabela limpa, com bordas horizontais discretas.
- Evitar excesso de linhas verticais.
- Não colorir a tabela de forma intensa.

## 10. Gráfico dos índices de QI da WASI

### 10.1. Objetivo do gráfico

O gráfico deve apresentar os três índices principais:

- QI Verbal.
- QI de Execução.
- QI Total.

O gráfico deve conter uma faixa de referência da média entre **90 e 110**, preferencialmente com barra ou área horizontal em rosa claro, conforme o modelo visual utilizado no sistema.

### 10.2. Estrutura recomendada do gráfico

Tipo: gráfico de barras verticais.

Eixo X:

```text
QI Verbal | QI de Execução | QI Total
```

Eixo Y:

```text
Pontuação de QI
```

Faixa média:

```text
90 a 110
```

Título:

```text
WASI – Índices de QI
```

Legenda abaixo:

```text
Gráfico 1. Resultados dos índices de QI da WASI.
```

### 10.3. Regras visuais do gráfico

- Fundo branco.
- Fonte Times New Roman.
- Título centralizado.
- Barras com cores suaves.
- Faixa média entre 90 e 110 em rosa claro ou tom discreto.
- Eixo Y iniciando preferencialmente em 60 e indo até 140 ou 150.
- Exibir valores acima das barras.
- Evitar excesso de grade.
- O gráfico deve ser exportado em alta resolução para inserção no Word.
- Tamanho sugerido para docx: 14 cm de largura por 10 cm de altura.

### 10.4. Código Python sugerido para o gráfico

```python
import matplotlib.pyplot as plt


def gerar_grafico_wasi_indices(qiv, qie, qit, output_path):
    labels = ["QI Verbal", "QI de Execução", "QI Total"]
    values = [qiv, qie, qit]

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=300)

    ax.axhspan(90, 110, alpha=0.18, label="Faixa Média (90-110)")
    bars = ax.bar(labels, values, width=0.48)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1,
            str(value),
            ha="center",
            va="bottom",
            fontsize=10,
            fontname="Times New Roman"
        )

    ax.set_title("WASI – Índices de QI", fontsize=13, fontname="Times New Roman")
    ax.set_ylabel("Pontuação de QI", fontsize=11, fontname="Times New Roman")
    ax.set_ylim(60, 145)
    ax.tick_params(axis="x", labelsize=10)
    ax.tick_params(axis="y", labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
```

## 11. Interpretação dos índices de QI

### 11.1. Texto de abertura

```text
A avaliação neuropsicológica de {{paciente_nome}}, por meio da Escala Wechsler Abreviada de Inteligência – WASI, possibilitou a análise do funcionamento intelectual global e dos principais domínios cognitivos, fornecendo indicadores objetivos acerca de seu perfil intelectual.
```

### 11.2. Modelo para QI Verbal

```text
O Quociente de Inteligência Verbal (QI Verbal = {{qiv}} | Classificação: {{qiv_classificacao}}) indica desempenho {{interpretacao_resumida_qiv}} em habilidades relacionadas à compreensão linguística, vocabulário, formação de conceitos e raciocínio verbal. Esse resultado sugere {{analise_funcional_qiv}}, especialmente em tarefas que exigem interpretação, organização do pensamento por meio da linguagem, elaboração conceitual e expressão verbal.
```

### 11.3. Modelo para QI de Execução

```text
O Quociente de Inteligência de Execução (QI de Execução = {{qie}} | Classificação: {{qie_classificacao}}) revela desempenho {{interpretacao_resumida_qie}} em tarefas não verbais, envolvendo raciocínio visuoespacial, organização perceptual, análise de padrões e resolução de problemas práticos. Esse achado sugere {{analise_funcional_qie}}, principalmente em demandas que exigem percepção visual, raciocínio abstrato não verbal, integração visuoespacial e resposta prática organizada.
```

### 11.4. Modelo para QI Total

```text
O Quociente de Inteligência Total (QI Total = {{qit}} | Classificação: {{qit_classificacao}}) evidencia funcionamento intelectual global {{interpretacao_resumida_qit}} para a faixa etária, refletindo o nível geral de eficiência cognitiva observado na avaliação. Esse resultado deve ser compreendido a partir da integração entre os domínios verbal e não verbal, considerando tanto as potencialidades quanto as possíveis vulnerabilidades identificadas nos subtestes.
```

### 11.5. Fechamento integrado

```text
Em análise clínica, o perfil intelectual de {{paciente_nome}} evidencia funcionamento cognitivo global {{classificacao_global_descritiva}}, com {{descricao_equilibrio_ou_discrepancia}} entre os domínios avaliados. A comparação entre o QI Verbal ({{qiv}}) e o QI de Execução ({{qie}}) sugere {{analise_discrepancia}}, indicando que {{paciente_nome}} apresenta {{sintese_funcional_final}}.
```

## 12. Regras para interpretação automática por classificação

### 12.1. Muito Superior

Usar quando o índice for igual ou superior a 130.

```text
desempenho muito acima da média esperada, sugerindo recursos cognitivos altamente desenvolvidos nesse domínio, com facilidade expressiva para lidar com demandas complexas, abstratas e de maior exigência intelectual.
```

### 12.2. Superior

Usar quando o índice estiver entre 120 e 129.

```text
desempenho acima da média esperada, indicando recursos cognitivos bem desenvolvidos, com boa eficiência para aprendizagem, raciocínio, resolução de problemas e adaptação a demandas intelectuais mais complexas.
```

### 12.3. Média Superior

Usar quando o índice estiver entre 110 e 119.

```text
desempenho discretamente acima da média esperada, indicando habilidades preservadas e bem desenvolvidas, com recursos consistentes para lidar com demandas cognitivas compatíveis com sua faixa etária.
```

### 12.4. Média

Usar quando o índice estiver entre 90 e 109.

```text
desempenho dentro da média esperada, sugerindo funcionamento cognitivo preservado e compatível com sua faixa etária, com recursos adequados para lidar com demandas intelectuais cotidianas, acadêmicas ou funcionais.
```

### 12.5. Média Inferior

Usar quando o índice estiver entre 80 e 89.

```text
desempenho abaixo da média esperada, embora ainda preservado em nível funcional, sugerindo maior esforço diante de demandas cognitivas mais complexas, abstratas ou que exijam maior eficiência nesse domínio.
```

### 12.6. Limítrofe

Usar quando o índice estiver entre 70 e 79.

```text
desempenho significativamente abaixo da média esperada, indicando vulnerabilidade cognitiva relevante nesse domínio, com possível impacto em situações que exigem maior autonomia, abstração, velocidade de raciocínio ou resolução de problemas.
```

### 12.7. Extremamente Baixo

Usar quando o índice for igual ou inferior a 69.

```text
desempenho muito abaixo da média esperada, sugerindo prejuízo importante no domínio avaliado, com provável repercussão funcional em contextos acadêmicos, adaptativos ou cotidianos que dependam dessa habilidade.
```

## 13. Subescalas da WASI

A seção de subescalas deve ser organizada em duas partes:

1. Escala Verbal.
2. Escala de Execução.

## 14. Tabela da Escala Verbal

### 14.1. Estrutura da tabela

| Testes Utilizados | Escore Máximo | Escore Médio | Escore Mínimo | Escore Obtido | Classificação |
|---|---:|---:|---:|---:|---|
| Vocabulário | {{vocabulario_escore_maximo}} | {{vocabulario_escore_medio}} | {{vocabulario_escore_minimo}} | {{vocabulario_escore_obtido}} | {{vocabulario_classificacao}} |
| Semelhanças | {{semelhancas_escore_maximo}} | {{semelhancas_escore_medio}} | {{semelhancas_escore_minimo}} | {{semelhancas_escore_obtido}} | {{semelhancas_classificacao}} |

Legenda:

```text
Tabela 3. Resultados da Escala Verbal da WASI.
```

## 15. Interpretação da Escala Verbal

### 15.1. Texto de abertura

```text
A avaliação da Escala Verbal de {{paciente_nome}} foi realizada por meio dos subtestes Vocabulário e Semelhanças da Escala Wechsler Abreviada de Inteligência – WASI, permitindo examinar aspectos relacionados ao raciocínio verbal, amplitude lexical, conhecimento semântico, formação de conceitos e capacidade de abstração mediada pela linguagem.
```

### 15.2. Interpretação do subteste Semelhanças

```text
No subteste Semelhanças (Escore Obtido = {{semelhancas_escore_obtido}} | Classificação: {{semelhancas_classificacao}}), observou-se desempenho {{descricao_classificacao_semelhancas}}, indicando {{analise_semelhancas}}. Esse resultado reflete a capacidade de estabelecer relações conceituais entre estímulos verbais, identificar categorias comuns, abstrair propriedades essenciais e organizar o pensamento de forma lógica por meio da linguagem.
```

### 15.3. Interpretação do subteste Vocabulário

```text
No subteste Vocabulário (Escore Obtido = {{vocabulario_escore_obtido}} | Classificação: {{vocabulario_classificacao}}), o desempenho foi {{descricao_classificacao_vocabulario}}, sugerindo {{analise_vocabulario}}. Esse achado está relacionado à amplitude lexical, ao conhecimento verbal adquirido, à precisão conceitual e à capacidade de expressar significados de forma organizada.
```

### 15.4. Fechamento da Escala Verbal

```text
Em análise clínica, os achados da Escala Verbal indicam funcionamento {{nivel_funcionamento_verbal}} das habilidades linguísticas e conceituais, com {{facilidades_ou_vulnerabilidades_verbais}}. Esse perfil tende a repercutir em tarefas que exigem compreensão verbal, argumentação, aprendizagem mediada pela linguagem, organização de ideias e elaboração conceitual.
```

## 16. Tabela da Escala de Execução

### 16.1. Estrutura da tabela

| Testes Utilizados | Escore Máximo | Escore Médio | Escore Mínimo | Escore Obtido | Classificação |
|---|---:|---:|---:|---:|---|
| Cubos | {{cubos_escore_maximo}} | {{cubos_escore_medio}} | {{cubos_escore_minimo}} | {{cubos_escore_obtido}} | {{cubos_classificacao}} |
| Raciocínio Matricial | {{raciocinio_escore_maximo}} | {{raciocinio_escore_medio}} | {{raciocinio_escore_minimo}} | {{raciocinio_escore_obtido}} | {{raciocinio_classificacao}} |

Legenda:

```text
Tabela 4. Resultados da Escala de Execução da WASI.
```

## 17. Interpretação da Escala de Execução

### 17.1. Texto de abertura

```text
A avaliação da Escala de Execução de {{paciente_nome}} foi realizada por meio dos subtestes Cubos e Raciocínio Matricial da Escala Wechsler Abreviada de Inteligência – WASI, permitindo examinar habilidades de raciocínio visuoespacial, análise de padrões, integração perceptual, organização motora e resolução de problemas não verbais.
```

### 17.2. Interpretação do subteste Cubos

```text
No subteste Cubos (Escore Obtido = {{cubos_escore_obtido}} | Classificação: {{cubos_classificacao}}), observou-se desempenho {{descricao_classificacao_cubos}}, sugerindo {{analise_cubos}}. Esse resultado está associado à capacidade de organizar estímulos visuais, reproduzir padrões, integrar percepção visual e resposta motora, além de planejar soluções construtivas sob demanda de tempo.
```

### 17.3. Interpretação do subteste Raciocínio Matricial

```text
No subteste Raciocínio Matricial (Escore Obtido = {{raciocinio_escore_obtido}} | Classificação: {{raciocinio_classificacao}}), o desempenho foi {{descricao_classificacao_raciocinio}}, indicando {{analise_raciocinio}}. Esse achado reflete a capacidade de identificar relações entre estímulos visuais, reconhecer padrões, inferir regras subjacentes e resolver problemas abstratos sem mediação verbal direta.
```

### 17.4. Fechamento da Escala de Execução

```text
Em análise clínica, os achados da Escala de Execução indicam funcionamento {{nivel_funcionamento_execucao}} das habilidades perceptuais, visuoespaciais e não verbais, com {{facilidades_ou_vulnerabilidades_execucao}}. Esse perfil tende a favorecer ou limitar, conforme os resultados obtidos, tarefas que exigem análise visual, raciocínio fluido, organização espacial, planejamento perceptivo e resolução de problemas práticos.
```

## 18. Gráfico das subescalas da WASI

### 18.1. Objetivo

O gráfico das subescalas deve apresentar os quatro subtestes:

- Vocabulário.
- Semelhanças.
- Cubos.
- Raciocínio Matricial.

Deve haver uma faixa média entre 40 e 60, conforme o padrão dos escores utilizados pelo sistema.

### 18.2. Título

```text
WASI – Subtestes
```

### 18.3. Legenda

```text
Gráfico 2. Resultados dos subtestes da WASI.
```

### 18.4. Código Python sugerido

```python
import matplotlib.pyplot as plt


def gerar_grafico_wasi_subtestes(subtestes, output_path):
    labels = ["Vocabulário", "Semelhanças", "Cubos", "Raciocínio\nMatricial"]
    values = [
        subtestes["vocabulario"]["escore_obtido"],
        subtestes["semelhancas"]["escore_obtido"],
        subtestes["cubos"]["escore_obtido"],
        subtestes["raciocinio_matricial"]["escore_obtido"]
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=300)

    ax.axhspan(40, 60, alpha=0.18, label="Faixa Média (40-60)")
    bars = ax.bar(labels, values, width=0.48)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1,
            str(value),
            ha="center",
            va="bottom",
            fontsize=10,
            fontname="Times New Roman"
        )

    ax.set_title("WASI – Subtestes", fontsize=13, fontname="Times New Roman")
    ax.set_ylabel("Escore Obtido", fontsize=11, fontname="Times New Roman")
    ax.set_ylim(20, 85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
```

## 19. Análise de discrepância entre QI Verbal e QI de Execução

### 19.1. Regra objetiva

Calcular:

```text
Diferença = |QI Verbal - QI de Execução|
```

Interpretação sugerida:

| Diferença | Interpretação |
|---:|---|
| 0 a 9 pontos | Perfil equilibrado, sem discrepância clinicamente relevante. |
| 10 a 14 pontos | Discrepância discreta, deve ser interpretada com cautela. |
| 15 a 22 pontos | Discrepância relevante, sugere diferença funcional entre os domínios. |
| 23 pontos ou mais | Discrepância expressiva, sugere heterogeneidade cognitiva importante. |

### 19.2. Texto para perfil equilibrado

```text
A proximidade entre o QI Verbal ({{qiv}}) e o QI de Execução ({{qie}}) sugere perfil cognitivo equilibrado, sem discrepância clinicamente significativa entre os domínios avaliados. Esse padrão indica que {{paciente_nome}} dispõe de recursos relativamente homogêneos tanto para compreender, organizar e expressar conteúdos por via verbal quanto para analisar estímulos visuais, reconhecer padrões e resolver problemas de natureza prática e abstrata.
```

### 19.3. Texto para predomínio verbal

```text
A diferença entre o QI Verbal ({{qiv}}) e o QI de Execução ({{qie}}) sugere predomínio das habilidades verbais sobre as não verbais. Esse padrão indica maior facilidade em tarefas mediadas pela linguagem, compreensão conceitual, expressão verbal e aprendizagem verbal, enquanto demandas que exigem organização visuoespacial, análise perceptual e resolução prática de problemas podem representar maior esforço relativo.
```

### 19.4. Texto para predomínio não verbal

```text
A diferença entre o QI Verbal ({{qiv}}) e o QI de Execução ({{qie}}) sugere predomínio das habilidades não verbais sobre as verbais. Esse padrão indica maior facilidade em tarefas de raciocínio visuoespacial, análise de padrões, organização perceptual e resolução de problemas práticos, enquanto demandas que exigem elaboração verbal, definição conceitual ou expressão linguística mais refinada podem representar maior esforço relativo.
```

## 20. Análise das facilidades e dificuldades cognitivas

Esta seção deve ser gerada após as interpretações dos índices e subescalas.

### 20.1. Modelo de abertura

```text
A análise do perfil cognitivo obtido na WASI permite identificar áreas de maior facilidade e possíveis vulnerabilidades no funcionamento intelectual de {{paciente_nome}}, considerando a comparação entre os índices compostos e o desempenho nos subtestes verbais e não verbais.
```

### 20.2. Facilidades cognitivas

Gerar conforme os maiores resultados.

Modelo:

```text
As principais facilidades cognitivas observadas concentram-se em {{dominios_de_maior_desempenho}}, indicando recursos mais desenvolvidos para {{descricao_funcional_das_facilidades}}. Esses achados sugerem que {{paciente_nome}} tende a apresentar melhor rendimento em situações que envolvem {{contextos_funcionais_favoraveis}}.
```

### 20.3. Vulnerabilidades cognitivas

Gerar conforme os menores resultados.

Modelo:

```text
As principais vulnerabilidades relativas foram observadas em {{dominios_de_menor_desempenho}}, sugerindo maior esforço em tarefas que exigem {{descricao_funcional_das_dificuldades}}. Tais achados não devem ser interpretados isoladamente como déficit, mas como indicadores de menor eficiência relativa quando comparados às demais habilidades avaliadas.
```

### 20.4. Fechamento

```text
Em análise clínica, o perfil cognitivo de {{paciente_nome}} deve ser compreendido de forma integrada, considerando que o desempenho intelectual global representa uma estimativa do funcionamento cognitivo atual e deve ser interpretado em conjunto com a anamnese, observações clínicas, histórico escolar, funcionamento adaptativo e demais instrumentos aplicados.
```

## 21. Regras para hipótese diagnóstica

A WASI isoladamente não deve ser utilizada para fechar diagnóstico clínico. Quando o perfil intelectual estiver rebaixado, heterogêneo ou muito elevado, a IA deve usar formulação cautelosa.

### 21.1. Quando QIT for superior ou muito superior

```text
Os resultados obtidos na WASI indicam funcionamento intelectual global acima da média esperada. Esses achados podem contribuir para a investigação de potencial cognitivo elevado, especialmente quando integrados ao histórico acadêmico, desenvolvimento de habilidades específicas, criatividade, produtividade, autonomia intelectual e evidências funcionais de desempenho superior em uma ou mais áreas.
```

### 21.2. Quando QIT for limítrofe ou extremamente baixo

```text
Os resultados obtidos na WASI indicam funcionamento intelectual global significativamente abaixo da média esperada, devendo ser interpretados em conjunto com avaliação adaptativa, histórico do desenvolvimento, desempenho escolar, autonomia funcional e demais instrumentos neuropsicológicos, a fim de verificar a extensão clínica e funcional das dificuldades observadas.
```

### 21.3. Quando houver discrepância importante

```text
A presença de discrepância relevante entre os domínios verbal e não verbal sugere perfil cognitivo heterogêneo, indicando que o QI Total deve ser interpretado com cautela, pois pode não representar de forma homogênea as habilidades cognitivas de {{paciente_nome}}.
```

## 22. Modelo completo de seção WASI

```text
5. ESCALA WECHSLER ABREVIADA DE INTELIGÊNCIA – WASI

A Escala Wechsler Abreviada de Inteligência – WASI é um instrumento destinado à estimativa do funcionamento intelectual global, permitindo a análise de habilidades verbais e não verbais por meio de subtestes que investigam compreensão verbal, formação de conceitos, raciocínio abstrato, organização visuoespacial e solução de problemas. A escala fornece indicadores do Quociente de Inteligência Verbal, do Quociente de Inteligência de Execução e do Quociente de Inteligência Total, contribuindo para a compreensão do perfil cognitivo do paciente e para a integração dos achados neuropsicológicos ao contexto clínico, acadêmico e funcional.

5.1. Desempenho do paciente na WASI

[INSERIR TABELA DOS ÍNDICES]

Tabela 2. Resultados dos índices de QI da WASI.

[INSERIR GRÁFICO DOS ÍNDICES]

Gráfico 1. Resultados dos índices de QI da WASI.

Interpretação: A avaliação neuropsicológica de {{paciente_nome}}, por meio da Escala Wechsler Abreviada de Inteligência – WASI, possibilitou a análise do funcionamento intelectual global e dos principais domínios cognitivos, fornecendo indicadores objetivos acerca de seu perfil intelectual.

O Quociente de Inteligência Verbal (QI Verbal = {{qiv}} | Classificação: {{qiv_classificacao}}) indica desempenho {{interpretacao_resumida_qiv}} em habilidades relacionadas à compreensão linguística, vocabulário, formação de conceitos e raciocínio verbal.

O Quociente de Inteligência de Execução (QI de Execução = {{qie}} | Classificação: {{qie_classificacao}}) revela desempenho {{interpretacao_resumida_qie}} em tarefas não verbais, envolvendo raciocínio visuoespacial, organização perceptual, análise de padrões e resolução de problemas práticos.

O Quociente de Inteligência Total (QI Total = {{qit}} | Classificação: {{qit_classificacao}}) evidencia funcionamento intelectual global {{interpretacao_resumida_qit}} para a faixa etária.

Em análise clínica, o perfil intelectual de {{paciente_nome}} evidencia funcionamento cognitivo global {{classificacao_global_descritiva}}, com {{descricao_equilibrio_ou_discrepancia}} entre os domínios avaliados.

5.2. Subescalas da WASI

5.2.1. Escala Verbal

[INSERIR TABELA DA ESCALA VERBAL]

Tabela 3. Resultados da Escala Verbal da WASI.

Interpretação: A avaliação da Escala Verbal de {{paciente_nome}} foi realizada por meio dos subtestes Vocabulário e Semelhanças da Escala Wechsler Abreviada de Inteligência – WASI, permitindo examinar aspectos relacionados ao raciocínio verbal, amplitude lexical, conhecimento semântico, formação de conceitos e capacidade de abstração mediada pela linguagem.

[INSERIR INTERPRETAÇÃO DOS SUBTESTES VERBAIS]

Em análise clínica, os achados da Escala Verbal indicam funcionamento {{nivel_funcionamento_verbal}} das habilidades linguísticas e conceituais, com {{facilidades_ou_vulnerabilidades_verbais}}.

5.2.2. Escala de Execução

[INSERIR TABELA DA ESCALA DE EXECUÇÃO]

Tabela 4. Resultados da Escala de Execução da WASI.

Interpretação: A avaliação da Escala de Execução de {{paciente_nome}} foi realizada por meio dos subtestes Cubos e Raciocínio Matricial da Escala Wechsler Abreviada de Inteligência – WASI, permitindo examinar habilidades de raciocínio visuoespacial, análise de padrões, integração perceptual, organização motora e resolução de problemas não verbais.

[INSERIR INTERPRETAÇÃO DOS SUBTESTES DE EXECUÇÃO]

Em análise clínica, os achados da Escala de Execução indicam funcionamento {{nivel_funcionamento_execucao}} das habilidades perceptuais, visuoespaciais e não verbais, com {{facilidades_ou_vulnerabilidades_execucao}}.

5.3. Análise das facilidades e dificuldades cognitivas

A análise do perfil cognitivo obtido na WASI permite identificar áreas de maior facilidade e possíveis vulnerabilidades no funcionamento intelectual de {{paciente_nome}}, considerando a comparação entre os índices compostos e o desempenho nos subtestes verbais e não verbais.

[INSERIR ANÁLISE DAS FACILIDADES]

[INSERIR ANÁLISE DAS VULNERABILIDADES]

Em análise clínica, o perfil cognitivo de {{paciente_nome}} deve ser compreendido de forma integrada, considerando que o desempenho intelectual global representa uma estimativa do funcionamento cognitivo atual e deve ser interpretado em conjunto com a anamnese, observações clínicas, histórico escolar, funcionamento adaptativo e demais instrumentos aplicados.
```

## 23. Referências bibliográficas obrigatórias quando a WASI estiver no laudo

Incluir, no mínimo:

```text
NASCIMENTO, E. WASI: Escala Wechsler Abreviada de Inteligência – Manual Técnico. São Paulo: Pearson Clinical Brasil, 2021.
```

Quando houver fundamentação neuropsicológica adicional, incluir:

```text
LEZAK, M. D.; HOWIESON, D. B.; BIGLER, E. D.; TRANEL, D. Neuropsychological Assessment. 5. ed. Oxford: Oxford University Press, 2012.
```

Quando o laudo for documento psicológico, incluir referência normativa:

```text
CONSELHO FEDERAL DE PSICOLOGIA (CFP). Resolução CFP nº 06, de 29 de março de 2019. Institui regras para a elaboração de documentos escritos produzidos pela(o) psicóloga(o) no exercício profissional. Brasília: CFP, 2019.
```

## 24. Checklist de qualidade antes de finalizar

Antes de finalizar o laudo, a IA deve verificar:

- O nome do paciente está correto.
- Nas seções interpretativas, foi usado apenas o primeiro nome, quando essa for a regra do caso.
- O QI Verbal, QI de Execução e QI Total estão coerentes com suas classificações.
- A análise de discrepância entre QI Verbal e QI de Execução foi incluída.
- As tabelas possuem título, cabeçalho e legenda.
- Os gráficos possuem fundo branco, faixa média e valores visíveis.
- As legendas estão abaixo dos elementos.
- A interpretação dos subtestes não contradiz a classificação obtida.
- O QI Total não foi usado isoladamente para fechar diagnóstico.
- A conclusão integra a WASI aos demais dados clínicos.
- A seção “Hipótese Diagnóstica” foi incluída dentro da conclusão, quando houver formulação diagnóstica.
- Não há tabelas brutas ou dados soltos após as referências bibliográficas.
- O documento termina na última referência.

## 25. Padrão de saída esperado da skill

A IA deve entregar, para o sistema:

```json
{
  "section_key": "wasi",
  "title": "ESCALA WECHSLER ABREVIADA DE INTELIGÊNCIA – WASI",
  "tables": [
    "wasi_qi_indices_table",
    "wasi_verbal_scale_table",
    "wasi_execution_scale_table"
  ],
  "charts": [
    "wasi_qi_indices_chart",
    "wasi_subtests_chart"
  ],
  "captions": [
    "Tabela 1. Resultados dos índices de QI da WASI.",
    "Gráfico 1. Resultados dos índices de QI da WASI.",
    "Tabela 2. Resultados da Escala Verbal da WASI.",
    "Tabela 3. Resultados da Escala de Execução da WASI.",
    "Gráfico 2. Resultados dos subtestes da WASI."
  ],
  "interpretation_blocks": [
    "definition",
    "qi_indices_interpretation",
    "verbal_scale_interpretation",
    "execution_scale_interpretation",
    "discrepancy_analysis",
    "strengths_and_weaknesses_analysis",
    "clinical_synthesis"
  ]
}
```

## 26. Observação final para implementação

Esta skill deve funcionar como módulo específico de geração da seção WASI dentro do laudo neuropsicológico. Ela não substitui o raciocínio clínico, mas organiza a saída do sistema para que a interpretação seja tecnicamente consistente, visualmente limpa e compatível com o padrão profissional esperado em avaliação neuropsicológica.
