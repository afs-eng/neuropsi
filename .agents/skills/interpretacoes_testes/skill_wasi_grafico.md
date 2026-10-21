# Skill: Gráfico WASI com faixa média destacada

## Objetivo
Gerar o gráfico dos quocientes intelectuais da WASI com uma faixa horizontal rosa representando a zona de desempenho médio, entre 90 e 110 pontos.

## Dados de entrada esperados
```json
{
  "titulo": "WASI QIs",
  "qi_verbal": 83,
  "qi_execucao": 59,
  "qi_total": 68,
  "classificacoes": {
    "qi_verbal": "Média Inferior",
    "qi_execucao": "Extremamente Baixa",
    "qi_total": "Extremamente Baixa"
  }
}
```

## Regra visual obrigatória
O gráfico deve conter uma faixa horizontal rosa clara entre os valores 90 e 110 no eixo Y, indicando a faixa normativa de desempenho médio.

Essa faixa deve ser inserida antes das barras, usando `ax.axhspan(90, 110, ...)`, para ficar ao fundo do gráfico.

## Padrão visual
- Título: `WASI QIs`
- Fonte: Times New Roman
- Cor do título: verde escuro
- Eixo Y: iniciar em 10 e terminar em 130
- Marcas do eixo Y: 10, 30, 50, 70, 90, 110, 130
- Barras:
  - QI verbal: azul
  - QI Execução: laranja
  - QI Total: verde
- Valores devem aparecer acima de cada barra
- A linha inferior do gráfico deve permanecer discreta
- Não utilizar grade vertical
- Inserir legenda visual da faixa média no canto direito, com rótulo “Média”

## Código base em Python
```python
import matplotlib.pyplot as plt


def gerar_grafico_wasi(qi_verbal, qi_execucao, qi_total, output_path="wasi_qis.png"):
    labels = ["QI verbal", "QI Execução", "QI Total"]
    valores = [qi_verbal, qi_execucao, qi_total]
    cores = ["#4472C4", "#ED7D31", "#70AD47"]

    plt.rcParams["font.family"] = "Times New Roman"

    fig, ax = plt.subplots(figsize=(9.8, 4.0), dpi=300)

    # Faixa normativa média: 90 a 110
    ax.axhspan(90, 110, color="#F4C2F4", alpha=0.35, zorder=0)

    barras = ax.bar(labels, valores, color=cores, width=0.32, zorder=2)

    for barra, valor in zip(barras, valores):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            valor + 3,
            str(valor),
            ha="center",
            va="bottom",
            fontsize=10,
            color="#333333",
        )

    ax.set_title("WASI QIs", fontsize=18, color="#2F4F1F", pad=10)
    ax.set_ylim(10, 130)
    ax.set_yticks([10, 30, 50, 70, 90, 110, 130])

    ax.tick_params(axis="x", labelsize=10, colors="#4D4D4D")
    ax.tick_params(axis="y", labelsize=9, colors="#4D4D4D", length=0)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#CFCFCF")
    ax.spines["bottom"].set_linewidth(0.8)

    ax.grid(False)

    # Legenda visual da faixa média
    ax.plot([2.18, 2.48], [74, 74], color="#F4A3F4", linewidth=5, solid_capstyle="butt")
    ax.text(
        2.33,
        61,
        "Média",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="#CFCFCF", boxstyle="square,pad=0.45"),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return output_path
```

## Exemplo de uso
```python
gerar_grafico_wasi(
    qi_verbal=83,
    qi_execucao=59,
    qi_total=68,
    output_path="wasi_qis.png"
)
```

## Integração no laudo
A imagem gerada deve ser inserida no documento Word centralizada, com largura aproximada de 14 cm.

Legenda abaixo do gráfico, em Times New Roman, tamanho 8, itálico:

**Figura X. Desempenho nos quocientes intelectuais da WASI. A faixa rosa representa o intervalo médio esperado, entre 90 e 110 pontos.**

## Regra interpretativa do gráfico
- Valores entre 90 e 110 devem ser visualmente compreendidos como faixa média.
- Valores abaixo de 90 indicam desempenho inferior à média normativa.
- Valores acima de 110 indicam desempenho acima da média normativa.
- A faixa rosa não representa resultado do paciente, mas apenas referência normativa.

## Observação obrigatória para a IA
Sempre que gerar o gráfico da WASI, manter a faixa rosa entre 90 e 110, independentemente dos valores do paciente.
