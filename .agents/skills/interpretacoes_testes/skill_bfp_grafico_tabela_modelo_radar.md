# skill_bfp_grafico_tabela_modelo_radar.md

## 1. Objetivo da skill

Gerar automaticamente a **tabela de resultados gerais** e o **gráfico radar de avaliação das facetas** do teste **BFP – Bateria Fatorial de Personalidade**, seguindo o modelo visual apresentado pelo usuário.

A skill deve produzir:

1. Tabela organizada por domínio/fator do BFP.
2. Linhas de facetas com Escore Bruto, Percentil e Classificação.
3. Linha final de cada fator em destaque, com o total do domínio.
4. Gráfico radar com as facetas distribuídas ao redor do círculo.
5. Comparação visual entre:
   - Resultado do avaliado.
   - Amostra normativa.
6. Saídas prontas para uso no laudo em Word/PDF.

---

## 2. Entrada esperada

A IA deve receber os dados no seguinte formato estruturado:

```json
{
  "avaliado": "Nome do paciente",
  "teste": "BFP",
  "facetas": [
    {
      "dominio": "Abertura à Experiência",
      "faceta": "Criatividade",
      "escore_bruto": 11,
      "percentil": 20,
      "classificacao": "Muito baixa"
    },
    {
      "dominio": "Abertura à Experiência",
      "faceta": "Curiosidade",
      "escore_bruto": 6,
      "percentil": 1,
      "classificacao": "Muito baixa"
    }
  ],
  "dominios": [
    {
      "dominio": "Abertura à Experiência",
      "escore_bruto": 26,
      "percentil": 1,
      "classificacao": "Muito baixa"
    }
  ]
}
```

---

## 3. Ordem obrigatória dos domínios e facetas

A IA deve respeitar a seguinte ordem fixa na tabela e no gráfico:

```python
ORDEM_BFP = {
    "ABERTURA À EXPERIÊNCIA": [
        "Criatividade",
        "Curiosidade",
        "Excentricidade"
    ],
    "AMABILIDADE": [
        "Paciência",
        "Perdão",
        "Ternura"
    ],
    "CONSCIENCIOSIDADE": [
        "Organização",
        "Perfeccionismo",
        "Ponderação"
    ],
    "EMOTIVIDADE": [
        "Ansiedade",
        "Dependência",
        "Sensibilidade"
    ],
    "EXTROVERSÃO": [
        "Ousadia social",
        "Sociabilidade",
        "Vivacidade"
    ]
}
```

---

## 4. Regras de classificação

A IA deve utilizar a classificação já recebida do sistema. Caso o sistema envie apenas percentis, usar a seguinte regra auxiliar:

```python
def classificar_percentil_bfp(percentil: float) -> str:
    if percentil <= 20:
        return "Muito baixa"
    elif percentil <= 40:
        return "Baixa"
    elif percentil <= 60:
        return "Média"
    elif percentil <= 80:
        return "Alta"
    else:
        return "Muito alta"
```

Observação: se o manual ou tabela normativa do sistema tiver regra própria, a regra oficial do sistema deve prevalecer sobre esta regra auxiliar.

---

## 5. Modelo visual da tabela

A tabela deve seguir o padrão:

- Título: **Resultados gerais**.
- Título em azul.
- Fonte preferencial: Arial, Calibri ou Times New Roman, conforme padrão do laudo.
- Cabeçalho com quatro colunas:
  - Faceta/Dimensão
  - Escore Bruto
  - Percentil
  - Classificação
- Linhas das facetas em texto regular.
- Linha do domínio em negrito e caixa alta.
- Separação horizontal entre blocos de domínios.
- Sem excesso de cores.
- Layout limpo e auditável.

---

## 6. Código Python para gerar a tabela em imagem

```python
import pandas as pd
import matplotlib.pyplot as plt

AZUL_TITULO = "#0070B8"
CINZA_TEXTO = "#4A4A4A"
CINZA_LINHA = "#707070"

ORDEM_BFP = {
    "ABERTURA À EXPERIÊNCIA": ["Criatividade", "Curiosidade", "Excentricidade"],
    "AMABILIDADE": ["Paciência", "Perdão", "Ternura"],
    "CONSCIENCIOSIDADE": ["Organização", "Perfeccionismo", "Ponderação"],
    "EMOTIVIDADE": ["Ansiedade", "Dependência", "Sensibilidade"],
    "EXTROVERSÃO": ["Ousadia social", "Sociabilidade", "Vivacidade"]
}


def gerar_tabela_bfp(dados_facetas, dados_dominios, caminho_saida="tabela_bfp.png"):
    """
    Gera uma tabela visual dos resultados gerais do BFP.

    dados_facetas: lista de dicionários com:
        dominio, faceta, escore_bruto, percentil, classificacao

    dados_dominios: lista de dicionários com:
        dominio, escore_bruto, percentil, classificacao
    """

    facetas_df = pd.DataFrame(dados_facetas)
    dominios_df = pd.DataFrame(dados_dominios)

    linhas = []

    for dominio, facetas in ORDEM_BFP.items():
        for faceta in facetas:
            item = facetas_df[facetas_df["faceta"].str.lower() == faceta.lower()]
            if not item.empty:
                row = item.iloc[0]
                linhas.append({
                    "Faceta/Dimensão": row["faceta"],
                    "Escore Bruto": row["escore_bruto"],
                    "Percentil": row["percentil"],
                    "Classificação": row["classificacao"],
                    "tipo": "faceta"
                })

        dominio_item = dominios_df[dominios_df["dominio"].str.upper() == dominio.upper()]
        if not dominio_item.empty:
            row = dominio_item.iloc[0]
            linhas.append({
                "Faceta/Dimensão": dominio,
                "Escore Bruto": row["escore_bruto"],
                "Percentil": row["percentil"],
                "Classificação": row["classificacao"],
                "tipo": "dominio"
            })

        linhas.append({
            "Faceta/Dimensão": "",
            "Escore Bruto": "",
            "Percentil": "",
            "Classificação": "",
            "tipo": "espaco"
        })

    if linhas and linhas[-1]["tipo"] == "espaco":
        linhas.pop()

    tabela_df = pd.DataFrame(linhas)
    tabela_exibicao = tabela_df[["Faceta/Dimensão", "Escore Bruto", "Percentil", "Classificação"]]

    altura = max(6, len(tabela_exibicao) * 0.38)
    fig, ax = plt.subplots(figsize=(10, altura))
    ax.axis("off")

    ax.text(
        0.0,
        1.04,
        "Resultados gerais",
        transform=ax.transAxes,
        fontsize=18,
        fontweight="bold",
        color=AZUL_TITULO,
        ha="left",
        va="bottom"
    )

    table = ax.table(
        cellText=tabela_exibicao.values,
        colLabels=tabela_exibicao.columns,
        cellLoc="center",
        colLoc="center",
        loc="upper center",
        bbox=[0, 0, 1, 0.98]
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(CINZA_LINHA)
        cell.set_linewidth(0.6)
        cell.set_facecolor("white")
        cell.get_text().set_color(CINZA_TEXTO)

        if row == 0:
            cell.get_text().set_fontweight("bold")
            cell.set_linewidth(0.8)

        if row > 0:
            tipo = tabela_df.iloc[row - 1]["tipo"]
            if tipo == "dominio":
                cell.get_text().set_fontweight("bold")
                cell.get_text().set_text(str(cell.get_text().get_text()).upper())
            elif tipo == "espaco":
                cell.set_linewidth(0)
                cell.get_text().set_text("")

    table.auto_set_column_width(col=list(range(4)))

    plt.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return caminho_saida
```

---

## 7. Modelo visual do gráfico radar

O gráfico radar deve seguir o modelo:

- Título centralizado: **RADAR DE AVALIAÇÃO DAS FACETAS**.
- Título em azul.
- Polígono preenchido azul para o resultado do avaliado.
- Linha azul/verde escura ao redor do resultado do avaliado.
- Linha laranja para a amostra normativa.
- Marcadores circulares nos pontos.
- Legenda superior:
  - Resultado do avaliado.
  - Amostra normativa.
- Facetas distribuídas no perímetro do radar.
- Grade radial clara e discreta.
- Escala sugerida: 0 a 100, usando percentis.

A amostra normativa pode ser representada por percentil 50 em todas as facetas, salvo quando o sistema possuir uma média normativa específica por faceta.

---

## 8. Código Python para gerar o gráfico radar

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

AZUL_TITULO = "#0070B8"
AZUL_PREENCHIMENTO = "#67A9CF"
AZUL_LINHA = "#2F7F8F"
LARANJA = "#FF7F00"
CINZA_LABEL = "#8A8A8A"
CINZA_GRID = "#E8E8E8"

ORDEM_FACETAS_RADAR = [
    "Criatividade",
    "Sinceridade",
    "Modéstia",
    "Vivacidade",
    "Sociabilidade",
    "Ousadia social",
    "Sensibilidade",
    "Dependência",
    "Ansiedade",
    "Ponderação",
    "Perfeccionismo",
    "Organização",
    "Ternura",
    "Perdão",
    "Paciência",
    "Excentricidade",
    "Curiosidade"
]


def gerar_radar_bfp(dados_facetas, caminho_saida="radar_bfp.png", valor_normativo=50):
    """
    Gera gráfico radar das facetas do BFP usando percentis.

    dados_facetas: lista de dicionários com:
        faceta, percentil

    valor_normativo: valor usado para a amostra normativa.
        Padrão: 50.
    """

    df = pd.DataFrame(dados_facetas)
    df["faceta_lower"] = df["faceta"].str.lower()

    valores_avaliado = []
    for faceta in ORDEM_FACETAS_RADAR:
        item = df[df["faceta_lower"] == faceta.lower()]
        if item.empty:
            valores_avaliado.append(0)
        else:
            valores_avaliado.append(float(item.iloc[0]["percentil"]))

    valores_normativos = [valor_normativo] * len(ORDEM_FACETAS_RADAR)

    valores_avaliado += valores_avaliado[:1]
    valores_normativos += valores_normativos[:1]

    n = len(ORDEM_FACETAS_RADAR)
    angulos = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angulos += angulos[:1]

    fig = plt.figure(figsize=(9, 9))
    ax = plt.subplot(111, polar=True)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.plot(
        angulos,
        valores_avaliado,
        color=AZUL_LINHA,
        linewidth=2.6,
        marker="o",
        markersize=5,
        label="Resultado do avaliado"
    )
    ax.fill(
        angulos,
        valores_avaliado,
        color=AZUL_PREENCHIMENTO,
        alpha=0.65
    )

    ax.plot(
        angulos,
        valores_normativos,
        color=LARANJA,
        linewidth=2.6,
        marker="o",
        markersize=5,
        label="Amostra normativa"
    )

    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(ORDEM_FACETAS_RADAR, fontsize=9, color=CINZA_LABEL)

    ax.set_ylim(0, 100)
    ax.set_yticks([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    ax.set_yticklabels([])

    ax.grid(color=CINZA_GRID, linewidth=0.9)
    ax.spines["polar"].set_color(CINZA_GRID)
    ax.spines["polar"].set_linewidth(1)

    ax.set_title(
        "RADAR DE AVALIAÇÃO DAS FACETAS",
        fontsize=18,
        fontweight="bold",
        color=AZUL_TITULO,
        pad=34
    )

    legenda = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.17),
        ncol=2,
        frameon=False,
        fontsize=10
    )

    for text in legenda.get_texts():
        text.set_color(CINZA_LABEL)

    plt.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return caminho_saida
```

---

## 9. Código completo de exemplo com os dados da imagem

```python
facetas_bfp = [
    {"dominio": "Abertura à Experiência", "faceta": "Criatividade", "escore_bruto": 11, "percentil": 20, "classificacao": "Muito baixa"},
    {"dominio": "Abertura à Experiência", "faceta": "Curiosidade", "escore_bruto": 6, "percentil": 1, "classificacao": "Muito baixa"},
    {"dominio": "Abertura à Experiência", "faceta": "Excentricidade", "escore_bruto": 9, "percentil": 20, "classificacao": "Muito baixa"},

    {"dominio": "Amabilidade", "faceta": "Paciência", "escore_bruto": 8, "percentil": 20, "classificacao": "Muito baixa"},
    {"dominio": "Amabilidade", "faceta": "Perdão", "escore_bruto": 8, "percentil": 40, "classificacao": "Baixa"},
    {"dominio": "Amabilidade", "faceta": "Ternura", "escore_bruto": 10, "percentil": 20, "classificacao": "Muito baixa"},

    {"dominio": "Conscienciosidade", "faceta": "Organização", "escore_bruto": 10, "percentil": 50, "classificacao": "Média"},
    {"dominio": "Conscienciosidade", "faceta": "Perfeccionismo", "escore_bruto": 15, "percentil": 80, "classificacao": "Alta"},
    {"dominio": "Conscienciosidade", "faceta": "Ponderação", "escore_bruto": 19, "percentil": 90, "classificacao": "Muito alta"},

    {"dominio": "Emotividade", "faceta": "Ansiedade", "escore_bruto": 13, "percentil": 30, "classificacao": "Baixa"},
    {"dominio": "Emotividade", "faceta": "Dependência", "escore_bruto": 11, "percentil": 50, "classificacao": "Média"},
    {"dominio": "Emotividade", "faceta": "Sensibilidade", "escore_bruto": 8, "percentil": 10, "classificacao": "Muito baixa"},

    {"dominio": "Extroversão", "faceta": "Ousadia social", "escore_bruto": 11, "percentil": 60, "classificacao": "Média"},
    {"dominio": "Extroversão", "faceta": "Sociabilidade", "escore_bruto": 10, "percentil": 30, "classificacao": "Baixa"},
    {"dominio": "Extroversão", "faceta": "Vivacidade", "escore_bruto": 9, "percentil": 30, "classificacao": "Baixa"}
]

dominios_bfp = [
    {"dominio": "Abertura à Experiência", "escore_bruto": 26, "percentil": 1, "classificacao": "Muito baixa"},
    {"dominio": "Amabilidade", "escore_bruto": 26, "percentil": 20, "classificacao": "Muito baixa"},
    {"dominio": "Conscienciosidade", "escore_bruto": 44, "percentil": 90, "classificacao": "Muito alta"},
    {"dominio": "Emotividade", "escore_bruto": 32, "percentil": 30, "classificacao": "Baixa"},
    {"dominio": "Extroversão", "escore_bruto": 30, "percentil": 40, "classificacao": "Baixa"}
]

gerar_tabela_bfp(facetas_bfp, dominios_bfp, "tabela_bfp.png")
gerar_radar_bfp(facetas_bfp, "radar_bfp.png", valor_normativo=50)
```

---

## 10. Instrução para integração no sistema

Ao gerar o laudo, a IA deve executar o seguinte fluxo:

1. Receber os dados brutos e percentílicos do BFP.
2. Validar se todas as facetas obrigatórias estão presentes.
3. Organizar os dados na ordem fixa do BFP.
4. Gerar a tabela em imagem ou em estrutura HTML/Markdown, conforme o motor de exportação do sistema.
5. Gerar o gráfico radar em PNG com 300 DPI.
6. Inserir o gráfico antes da tabela ou após a tabela, conforme o modelo do laudo.
7. Inserir legenda abaixo dos elementos, em fonte tamanho 8, itálica, quando exportado para Word.

Legenda sugerida para o gráfico:

> Figura X. Radar de avaliação das facetas do BFP, comparando o resultado do avaliado com a amostra normativa.

Legenda sugerida para a tabela:

> Tabela X. Resultados gerais do BFP, apresentados por facetas e dimensões fatoriais.

---

## 11. Regras de qualidade visual

A IA deve garantir:

- Imagem em alta resolução, mínimo 300 DPI.
- Título centralizado e em azul.
- Legenda clara e sem poluição visual.
- Textos legíveis quando inseridos no Word.
- Gráfico sem excesso de cores.
- Tabela com linhas horizontais limpas.
- Domínios em negrito e caixa alta.
- Ausência de informações não fornecidas pelo sistema.
- Ausência de interpretação clínica dentro da tabela e do gráfico.

---

## 12. Saídas esperadas

```json
{
  "outputs": {
    "grafico_radar": "radar_bfp.png",
    "tabela_resultados": "tabela_bfp.png"
  },
  "legendas": {
    "grafico": "Figura X. Radar de avaliação das facetas do BFP, comparando o resultado do avaliado com a amostra normativa.",
    "tabela": "Tabela X. Resultados gerais do BFP, apresentados por facetas e dimensões fatoriais."
  }
}
```

---

## 13. Comando final para a IA

Sempre que o usuário solicitar gráfico e tabela do BFP neste modelo, gerar:

1. Gráfico radar de facetas.
2. Tabela de resultados gerais.
3. Arquivos PNG em 300 DPI.
4. Legendas padronizadas para laudo.
5. Organização por domínio e faceta conforme a ordem oficial definida nesta skill.

Nunca alterar percentis, classificações ou escores sem base nos dados recebidos do sistema.

---

# 14. ANÁLISE AUTOMATIZADA (MODELO DE INSERÇÃO NO LAUDO)

Para padronizar a redação do laudo, recomenda-se incluir no backend uma função que gere um resumo preliminar a partir dos percentis/classificações. A saída é um rascunho que deve ser revisado pelo avaliador.

Elementos produzidos pela função:

- Parágrafo síntese curto (1-2 frases).
- Lista de fatores relevantes com sinalização de "relevante" ou "extremo".
- Mensagens predefinidas para combinações clínicas relevantes (ex.: NN elevado + RR reduzido).
- Recomendações de integração clínica.

Exemplo mínimo (pseudocódigo):

```python
def summarize_bfp_for_report(results: dict) -> dict:
    # Reaproveitar a função de summarize presente em skill_bfp_grafico_tabela.md
    return summarize_bfp_for_report(results)
```

Aviso: sempre use linguagem condicional ("sugere", "pode indicar") e revise o texto automaticamente gerado antes de inseri-lo no laudo final.
