# skill_bfp_grafico_radar_17_facetas.md

## Objetivo

Implementar, nos laudos neuropsicológicos do sistema, o gráfico radar do BFP utilizando obrigatoriamente as 17 facetas do instrumento, e não apenas os 5 fatores gerais.

O gráfico deve representar visualmente os percentis das facetas avaliadas, comparando o resultado do avaliado com a amostra normativa fixa no percentil 50.

## Regra principal

O gráfico radar do BFP deve ser construído sempre com as 17 facetas abaixo:

1. Vulnerabilidade
2. Instabilidade Emocional
3. Passividade
4. Depressão
5. Comunicação
6. Altivez
7. Dinamismo
8. Interações Sociais
9. Amabilidade
10. Pró-sociabilidade
11. Confiança nas Pessoas
12. Competência
13. Ponderação
14. Empenho
15. Abertura a Ideias
16. Liberalismo
17. Busca por Novidades

Nunca gerar o radar usando somente os fatores gerais:
- Neuroticismo
- Extroversão
- Socialização
- Realização
- Abertura

Os fatores gerais podem aparecer na tabela e na interpretação textual, mas não devem ser usados como eixos do gráfico radar principal.

## Dados obrigatórios de entrada

A IA deve receber ou extrair os seguintes campos para cada faceta:

```json
{
  "faceta": "Vulnerabilidade",
  "escore_bruto": 3.44,
  "percentil": 56.5,
  "classificacao": "Média"
}
```

O campo usado para plotagem deve ser sempre:

```json
"percentil"
```

## Estrutura esperada do payload

```json
{
  "instrumento": "BFP",
  "grafico": "radar_17_facetas",
  "titulo": "RADAR DE AVALIAÇÃO DAS FACETAS - BFP",
  "escala": {
    "min": 0,
    "max": 100,
    "referencia_normativa": 50
  },
  "facetas": [
    {
      "nome": "Vulnerabilidade",
      "percentil": 56.5,
      "classificacao": "Média"
    },
    {
      "nome": "Instabilidade Emocional",
      "percentil": 70.5,
      "classificacao": "Média Superior"
    }
  ]
}
```

## Ordem fixa dos eixos

A ordem dos eixos no gráfico deve ser sempre esta:

```python
BFP_FACETAS_RADAR = [
    "Vulnerabilidade",
    "Instabilidade Emocional",
    "Passividade",
    "Depressão",
    "Comunicação",
    "Altivez",
    "Dinamismo",
    "Interações Sociais",
    "Amabilidade",
    "Pró-sociabilidade",
    "Confiança nas Pessoas",
    "Competência",
    "Ponderação",
    "Empenho",
    "Abertura a Ideias",
    "Liberalismo",
    "Busca por Novidades",
]
```

## Valores normativos

A amostra normativa deve ser uma linha fixa no percentil 50:

```python
norma = [50] * 17
```

## Código Python recomendado para geração do gráfico

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path


BFP_FACETAS_RADAR = [
    "Vulnerabilidade",
    "Instabilidade\nEmocional",
    "Passividade",
    "Depressão",
    "Comunicação",
    "Altivez",
    "Dinamismo",
    "Interações\nSociais",
    "Amabilidade",
    "Pró-sociabilidade",
    "Confiança nas\nPessoas",
    "Competência",
    "Ponderação",
    "Empenho",
    "Abertura a\nIdeias",
    "Liberalismo",
    "Busca por\nNovidades",
]


def gerar_grafico_radar_bfp(percentis, output_path):
    """
    Gera gráfico radar do BFP com 17 facetas.

    Parâmetros:
        percentis: list[float]
            Lista com os 17 percentis das facetas, na ordem fixa definida em BFP_FACETAS_RADAR.
        output_path: str | Path
            Caminho final do arquivo PNG.
    """

    if len(percentis) != 17:
        raise ValueError("O gráfico radar do BFP exige exatamente 17 percentis, um para cada faceta.")

    output_path = Path(output_path)

    norma = [50] * 17
    n = len(BFP_FACETAS_RADAR)

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles_closed = angles + angles[:1]

    values = list(percentis) + [percentis[0]]
    norm_values = norma + [norma[0]]

    fig = plt.figure(figsize=(10, 10), dpi=180)
    ax = plt.subplot(111, polar=True)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.plot(
        angles_closed,
        values,
        linewidth=2.5,
        marker="o",
        label="Resultado do avaliado"
    )
    ax.fill(
        angles_closed,
        values,
        alpha=0.28
    )

    ax.plot(
        angles_closed,
        norm_values,
        linewidth=2.3,
        linestyle="-",
        label="Amostra normativa"
    )
    ax.fill(
        angles_closed,
        norm_values,
        alpha=0.03
    )

    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=9)

    ax.set_xticks(angles)
    ax.set_xticklabels(BFP_FACETAS_RADAR, fontsize=9)

    ax.grid(True, linewidth=0.8, alpha=0.35)
    ax.spines["polar"].set_alpha(0.25)

    plt.title(
        "RADAR DE AVALIAÇÃO DAS FACETAS - BFP",
        fontsize=17,
        fontweight="bold",
        pad=35
    )

    legend_elements = [
        Patch(
            facecolor="C0",
            edgecolor="C0",
            alpha=0.35,
            label="Resultado do avaliado"
        ),
        Patch(
            facecolor="none",
            edgecolor="C1",
            linewidth=2.5,
            label="Amostra normativa"
        ),
    ]

    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.15),
        ncol=2,
        frameon=False,
        fontsize=10,
    )

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close(fig)

    return output_path
```

## Exemplo de uso

```python
percentis_bfp = [
    56.5,
    70.5,
    71.6,
    97,
    31.9,
    40.8,
    50.8,
    24.7,
    20.4,
    5.8,
    14.5,
    4.4,
    19.9,
    41.7,
    17.1,
    24,
    58.7,
]

gerar_grafico_radar_bfp(
    percentis=percentis_bfp,
    output_path="grafico_radar_bfp_17_facetas.png"
)
```

## Inserção no laudo

O gráfico deve ser inserido após a tabela do BFP ou após a interpretação descritiva do instrumento.

Modelo recomendado de legenda:

```text
Figura X. Radar de avaliação das facetas do BFP. A área preenchida representa os percentis obtidos pelo avaliado nas 17 facetas do instrumento, enquanto o contorno normativo indica a referência média da amostra normativa no percentil 50.
```

## Padrão visual obrigatório

O gráfico deve conter:

- título centralizado em caixa alta;
- legenda superior com “Resultado do avaliado” e “Amostra normativa”;
- escala de 0 a 100;
- linha normativa fixa no percentil 50;
- área preenchida para o resultado do avaliado;
- eixos com as 17 facetas;
- saída em PNG com 300 DPI;
- tamanho adequado para inserção em Word ou PDF.

## Tamanho recomendado para Word

Para laudos em Word:

- largura: 14 cm;
- altura: aproximadamente 14 cm;
- alinhamento: centralizado;
- legenda abaixo do gráfico;
- legenda em Times New Roman, tamanho 8, itálico.

## Validações obrigatórias

Antes de gerar o gráfico, a IA deve verificar:

1. Se existem exatamente 17 facetas.
2. Se todas as facetas obrigatórias estão presentes.
3. Se cada faceta possui percentil numérico.
4. Se os percentis estão entre 0 e 100.
5. Se a ordem das facetas segue a ordem fixa definida na skill.
6. Se o gráfico não está usando os fatores gerais como eixos.

## Erros que devem ser impedidos

A IA nunca deve:

- gerar radar com apenas 5 fatores gerais;
- usar escore bruto como valor do radar;
- alterar a ordem das facetas;
- omitir facetas com percentil baixo;
- substituir facetas por dimensões gerais;
- usar escala diferente de 0 a 100;
- deixar de incluir a linha normativa no percentil 50.

## Interpretação associada ao gráfico

A interpretação do gráfico deve considerar que:

- percentis altos em Neuroticismo e suas facetas indicam maior vulnerabilidade emocional;
- percentis baixos em Extroversão indicam menor expansividade social, menor dinamismo ou menor interação social;
- percentis baixos em Socialização indicam possíveis dificuldades em confiança, cooperação e atitudes pró-sociais;
- percentis baixos em Realização indicam possíveis dificuldades em organização, competência, persistência e planejamento;
- percentis baixos em Abertura indicam menor flexibilidade para ideias, valores ou experiências novas.

A análise textual deve ser integrada aos demais achados clínicos, sem transformar o gráfico isoladamente em diagnóstico.

## Observação técnica

O gráfico é um recurso visual de apoio ao laudo. A conclusão clínica deve ser construída com base na integração entre entrevista, observação clínica, instrumentos aplicados, histórico funcional e resultados psicométricos.
