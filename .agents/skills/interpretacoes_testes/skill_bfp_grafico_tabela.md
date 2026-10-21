# Skill: BFP – Tabela de Resultados Gerais e Gráficos para Laudo Export

## Objetivo

Gerar, no sistema de laudos, a tabela de resultados gerais e os gráficos do teste BFP – Bateria Fatorial de Personalidade, seguindo um padrão visual limpo, técnico e editorial. Esta skill cobre a estrutura.tabular e gráfica para exportação em laudo, não a interpretação textual clínica.

## Quando Usar

Esta skill deve ser usada quando:
- O laudo requiere presenting BFP results in tabular format
- É necessário gerar gráficos de radar ou barras paravisualização dos 5 fatores
- O export DOCX requer dados formatados especificamentepara o BFP

---

# 1. TABLE STRUCTURE

## 1.1 Headers Obrigatórios

A tabela de resultados gerais do BFP deve conter as seguintes colunas:

| Coluna | Descrição |
|--------|----------|
| Fator | Nome por extenso do fator (com código entre parênteses) |
| Pts Bts | Escore bruto do fator |
| Percentil | Percentil calculado com base no z-score |
| Classificação | Classificação conforme banda normativa |

**Ordem fixa das colunas:** `Fator | Pts Bts | Percentil | Classificação`

## 1.2 Linhas de Fatores (5 fatores)

A tabela contém exatamente 5 linhas de fatores, nesta ordem fixa:

| Código | Nome Completo | Abreviação |
|--------|-------------|-----------|
| NN | Neuroticismo | NN |
| EE | Extroversão | EE |
| SS | Socialização | SS |
| RR | Realização | RR |
| AA | Abertura | AA |

**Nota:** A ordem deve ser sempre NN → EE → SS → RR → AA, nesta sequência exata.

## 1.3 Classification Bands (Faixas Normativas)

As classificações são atribuídas com base no percentil, conforme as seguintes fronteiras:

| Classificação | Limite Inferior | Limite Superior |
|---------------|----------------|----------------|
| Muito Baixo | p < 2.5 | p < 2.5 |
| Baixo | 2.5 ≤ p | p < 15 |
| Média Inferior | 15 ≤ p | p < 30 |
| Média | 30 ≤ p | p < 70 |
| Média Superior | 70 ≤ p | p < 85 |
| Superior | 85 ≤ p | p < 97.5 |
| Muito Superior | p ≥ 97.5 | p ≥ 97.5 |

### Fronteiras Exatas (em código)

```python
# calculators.py - classify_percentile()
def classify_percentile(percentile: float) -> str:
    if percentile >= 97.5:
        return "Muito Superior"
    if percentile >= 85:
        return "Superior"
    if percentile >= 70:
        return "Média Superior"
    if percentile >= 30:
        return "Média"
    if percentile >= 15:
        return "Média Inferior"
    if percentile >= 2.5:
        return "Baixo"
    return "Muito Baixo"
```

## 1.4 Significado das Classificações

| Classificação | Significado Clínico |
|-------------|-------------------|
| Muito Baixo | rastro muito reduzido em relação à amostra normativa |
| Baixo | rastro reduzido em relação à amostra normativa |
| Média Inferior | tendência discretamente reduzida, ainda próxima da faixa esperada |
| Média | funcionamento compatível com a média normativa |
| Média Superior | tendência aumentada em relação à média normativa |
| Superior | rastro elevado em relação à amostra normativa |
| Muito Superior | rastro muito elevado em relação à amostra normativa |

## 1.5 Color Coding (Opcional)

Se o sistema suportar formatação condicionada, aplicar cores por banda:

| Classificação | Cor (RGB Hex) | Sugestão |
|-------------|--------------|---------|
| Muito Baixo | #FF6B6B | Vermelho claro |
| Baixo | #FFA07A | Laranja avermelhado |
| Média Inferior | #FFD700 | Amarelo escuro |
| Média | #90EE90 | Verde claro |
| Média Superior | #87CEEB | Azul claro |
| Superior | #6495ED | Azul médio |
| Muito Superior | #9370DB | Roxo médio |

---

# 2. CHART STRUCTURE

## 2.1 Tipos de Gráfico Suportados

O BFP pode ser visualizado em dois formatos principais:

### 2.1.1 Radar Chart (Recomendado)

Gráfico radar (spider chart) com 5 eixos radiais:

- **Eixos:** Neuroticismo, Extroversão, Socialização, Realização, Abertura
- **Escala radial:** 0 a 100 (percentil)
- **Referência normativa:** linha no percentil 50 (todos os eixos)

### 2.1.2 Horizontal Bar Chart

Alternativa ao radar:

- **Eixo X:** Percentil (0 a 100)
- **Barras:** 5 barras horizontais (uma por fator)
- **Linha de referência:** vertical no percentil 50
- **Labels:** nomes dos fatores à esquerda das barras

## 2.2 Dados Representados no Gráfico

Cada barra/eixo representa o **percentil do fator**, não o escore bruto.

### Fórmula de Cálculo do Percentil

```python
# calculators.py
def normal_cdf(z_score: float) -> float:
    return 0.5 * (1 + math.erf(z_score / math.sqrt(2)))

def percentile_from_z(z_score: float) -> float:
    return normal_cdf(z_score) * 100

# Uso:
# z_score = (raw_score - mean) / sd
# percentile = percentile_from_z(z_score)
```

### Fórmula do Escore Ponderado (para display opcional)

O escore ponderado (média 10, DP 3) pode ser calculado:

```python
# calculators.py
def weighted_score_from_z(z_score: float) -> float:
    return 10 + (z_score * 3)
```

**Valor esperado:** média = 10, desvio padrão = 3

## 2.3 Elementos Visuais do Radar

### Dados do Gráfico

```python
# Exemplo de dados para radar
fatores_percentis = {
    "Neuroticismo": 99.0,
    "Extroversão": 4.8,
    "Socialização": 35.7,
    "Realização": 0.0,
    "Abertura": 14.8,
}
```

### Linha Normativa

```python
# Amostra normativa - sempre percentil 50
amostra_normativa = [50, 50, 50, 50, 50]
```

### Código de Geração (Matplotlib)

```python
import numpy as np
import matplotlib.pyplot as plt


def build_radar_chart_bfp(
    labels,
    values,
    title,
    output_path,
    normative_value=50,
    figsize=(7.2, 6.2),
    dpi=300,
):
    """
    Gera gráfico radar no modelo editorial para o BFP.

    labels: lista de rótulos dos eixos.
    values: lista de percentis do avaliado.
    title: título do gráfico.
    output_path: caminho do PNG final.
    normative_value: valor da amostra normativa, padrão percentil 50.
    """
    if len(labels) != len(values):
        raise ValueError("labels e values devem ter o mesmo tamanho.")

    values = [float(v) if v is not None else 0 for v in values]
    normative = [normative_value] * len(labels)

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()

    values_closed = values + values[:1]
    normative_closed = normative + normative[:1]
    angles_closed = angles + angles[:1]

    fig, ax = plt.subplots(figsize=figsize, subplot_kw={"polar": True})

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.plot(
        angles_closed,
        values_closed,
        linewidth=2.2,
        color="#3F8797",
        marker="o",
        markersize=4,
        label="Resultado do avaliado",
    )
    ax.fill(
        angles_closed,
        values_closed,
        color="#63AFC7",
        alpha=0.55,
    )

    ax.plot(
        angles_closed,
        normative_closed,
        linewidth=2.0,
        color="#F28C28",
        marker="o",
        markersize=3,
        label="Amostra normativa",
    )

    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color="#888888")
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8, color="#777777")

    ax.grid(True, color="#E6E6E6", linewidth=0.7)
    ax.spines["polar"].set_color("#E6E6E6")
    ax.spines["polar"].set_linewidth(0.8)

    ax.set_title(
        title,
        fontsize=13,
        fontweight="bold",
        color="#0070B8",
        pad=32,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=2,
        frameon=False,
        fontsize=8,
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", transparent=False)
    plt.close(fig)

    return output_path
```

## 2.4 Axis Labels e Classification Bands

### Labels dos Eixos

| Eixo | Label (Curto) | Label (Completo) |
|------|--------------|----------------|
| NN | N | Neuroticismo |
| EE | E | Extroversão |
| SS | S | Socialização |
| RR | R | Realização |
| AA | A | Abertura |

### Bandas de Classificação no Gráfico (Opcional)

Podem ser adicionadas zonas coloridas ao fundo:

- **Zona baixa:** percentis 0-30 (cor avermelhada suave)
- **Zona média:** percentis 30-70 (transparente/sem cor)
- **Zona alta:** percentis 70-100 (cor azulada suave)

---

# 3. MAPPING TABLE → CHART

## 3.1 Correspondência Linha→Barra

| Table Row (Fator) | Chart Bar (Eixo) |
|-----------------|----------------|
| Neuroticismo (NN) | Eixo 1 (topo, 0°) |
| Extroversão (EE) | Eixo 2 (72° clockwise) |
| Socialização (SS) | Eixo 3 (144° clockwise) |
| Realização (RR) | Eixo 4 (216° clockwise) |
| Abertura (AA) | Eixo 5 (288° clockwise) |

**Ordem no radar:** NN → EE → SS → RR → AA (sentido horário)

## 3.2 Percentil → Posição no Chart

| Percentil | Posição Radar | Posição Barra |
|----------|--------------|-------------|
| 0 | centro | esquerda |
| 50 | linha média | posição média |
| 100 | borda externa | direita |

## 3.3 Classificação → Cor da Barra

| Classificação | Cor da Barra (Recomendada) |
|-------------|----------------------|
| Muito Baixo | #FF6B6B |
| Baixo | #FFA07A |
| Média Inferior | #FFD700 |
| Média | #90EE90 |
| Média Superior | #87CEEB |
| Superior | #6495ED |
| Muito Superior | #9370DB |

## 3.4 O que Destacar (Clinicamente Relevante)

O gráfico deve destacar os seguintes casos:

### 3.4.1 Extreme Superiores/inferiores

- **Muito Superior** (p ≥ 97.5): destacar com cor diferenciada
- **Muito Baixo** (p < 2.5): destacar com cor diferenciada

### 3.4.2 Diferenças Significativas da Média

- Fatores com percentil > 85 ou < 15 devem ter atenção visual

### 3.4.3 Sugestão de Destaque

```python
def get_bar_highlight_classification(percentil: float) -> bool:
    """Retorna True se o fator deve ser destacado."""
    return percentil >= 85 or percentil < 15
```

---

# 4. IMPLEMENTATION CODE

## 4.1 Função `_bfp_rows()` (report_export_service.py)

```python
# apps/reports/services/report_export_service.py:3866
@classmethod
def _bfp_rows(cls, test: dict | None):
    computed = (test or {}).get("computed_payload") or {}
    factors = computed.get("factors") or ((test or {}).get("structured_results") or {}).get("factors") or {}
    factor_order = computed.get("factor_order") or ["NN", "EE", "SS", "RR", "AA"]
    rows = [["Fator", "Pts Bts", "Percentil", "Classificação"]]
    for code in factor_order:
        factor = factors.get(code)
        if not factor:
            continue
        rows.append([
            f"{factor.get('name') or code} ({code})",
            cls._num(factor.get("raw_score")),
            cls._num(factor.get("percentile")),
            factor.get("classification") or "-",
        ])
    return rows if len(rows) > 1 else None
```

### Input Esperado (test)

```python
{
    "computed_payload": {
        "factors": {
            "NN": {"name": "Neuroticismo", "raw_score": 5.56, "percentile": 99.0, "classification": "Muito Superior"},
            "EE": {"name": "Extroversão", "raw_score": 3.20, "percentile": 4.8, "classification": "Muito Baixo"},
            "SS": {"name": "Socialização", "raw_score": 4.85, "percentile": 35.7, "classification": "Média"},
            "RR": {"name": "Realização", "raw_score": 3.50, "percentile": 0.0, "classification": "Muito Baixo"},
            "AA": {"name": "Abertura", "raw_score": 4.10, "percentile": 14.8, "classification": "Baixo"},
        },
        "factor_order": ["NN", "EE", "SS", "RR", "AA"]
    }
}
```

### Output (rows)

```python
[
    ["Fator", "Pts Bts", "Percentil", "Classificação"],
    ["Neuroticismo (NN)", "5.56", "99.0", "Muito Superior"],
    ["Extroversão (EE)", "3.20", "4.8", "Muito Baixo"],
    ["Socialização (SS)", "4.85", "35.7", "Média"],
    ["Realização (RR)", "3.50", "0.0", "Muito Baixo"],
    ["Abertura (AA)", "4.10", "14.8", "Baixo"]
]
```

## 4.2 Função `_with_table_title()` (Formatação)

```python
# apps/reports/services/report_export_service.py:2802
@classmethod
def _with_table_title(cls, rows: list[list[str]] | None, table_key: str | None):
    if not rows or not table_key:
        return rows
    title = cls._table_title_text(table_key)
    if not title:
        return rows
    return [[title, *([""] * (len(rows[0]) - 1))], *rows]
```

### Tabela com Título

```python
# Exemplo com título "BFP - RESULTADOS DOS FATORES"
[
    ["BFP - RESULTADOS DOS FATORES", "", "", ""],
    ["Fator", "Pts Bts", "Percentil", "Classificação"],
    ["Neuroticismo (NN)", "5.56", "99.0", "Muito Superior"],
    ...
]
```

## 4.3 Funções de Classificação (calculators.py)

```python
# apps/tests/bfp/calculators.py

def classify_percentile(percentile: float) -> str:
    if percentile >= 97.5:
        return "Muito Superior"
    if percentile >= 85:
        return "Superior"
    if percentile >= 70:
        return "Média Superior"
    if percentile >= 30:
        return "Média"
    if percentile >= 15:
        return "Média Inferior"
    if percentile >= 2.5:
        return "Baixo"
    return "Muito Baixo"


def weighted_score_from_z(z_score: float) -> float:
    return 10 + (z_score * 3)


def percentile_from_z(z_score: float) -> float:
    import math
    return 0.5 * (1 + math.erf(z_score / math.sqrt(2))) * 100
```

## 4.4 Função para Gerar Radar dos Fatores

```python
def generate_bfp_factor_radar(results, output_path):
    by_code = {item["codigo"]: item for item in results}

    labels = ["Neuroticismo", "Extroversão", "Socialização", "Realização", "Abertura"]
    codes = ["NN", "EE", "SS", "RR", "AA"]
    values = [by_code[code]["percentil"] for code in codes if code in by_code]

    return build_radar_chart_bfp(
        labels=labels,
        values=values,
        title="RADAR DE AVALIAÇÃO DOS FATORES",
        output_path=output_path,
    )
```

---

# 5. EXAMPLE OUTPUT

## 5.1 Exemplo de Dados de Input

```python
test_input = {
    "computed_payload": {
        "factors": {
            "NN": {
                "name": "Neuroticismo",
                "raw_score": 5.56,
                "percentile": 99.0,
                "classification": "Muito Superior",
                "z_score": 2.329,
                "weighted_score": 17.0,
            },
            "EE": {
                "name": "Extroversão",
                "raw_score": 3.20,
                "percentile": 4.8,
                "classification": "Muito Baixo",
                "z_score": -2.04,
                "weighted_score": 3.9,
            },
            "SS": {
                "name": "Socialização",
                "raw_score": 4.85,
                "percentile": 35.7,
                "classification": "Média",
                "z_score": -0.41,
                "weighted_score": 8.8,
            },
            "RR": {
                "name": "Realização",
                "raw_score": 3.50,
                "percentile": 0.0,
                "classification": "Muito Baixo",
                "z_score": -2.85,
                "weighted_score": 1.5,
            },
            "AA": {
                "name": "Abertura",
                "raw_score": 4.10,
                "percentile": 14.8,
                "classification": "Baixo",
                "z_score": -1.24,
                "weighted_score": 6.3,
            },
        },
        "factor_order": ["NN", "EE", "SS", "RR", "AA"],
    }
}
```

## 5.2 Tabela Resultante

| Fator | Pts Bts | Percentil | Classificação |
|-------|---------|-----------|----------------|
| Neuroticismo (NN) | 5.56 | 99.0 | Muito Superior |
| Extroversão (EE) | 3.20 | 4.8 | Muito Baixo |
| Socialização (SS) | 4.85 | 35.7 | Média |
| Realização (RR) | 3.50 | 0.0 | Muito Baixo |
| Abertura (AA) | 4.10 | 14.8 | Baixo |

## 5.3 Descrição do Grafico Correspondente

### Radar

- **Eixo NN (topo):** percentil 99 (borda externa, cor #9370DB)
- **Eixo EE:** percentil 4.8 (próximo ao centro, cor #FF6B6B)
- **Eixo SS:** percentil 35.7 (zona média-baixa, cor #90EE90)
- **Eixo RR:** percentil 0 (centro, cor #FF6B6B)
- **Eixo AA:** percentil 14.8 (zona baixa, cor #FFA07A)

### Linha normativa

Linha circular no percentil 50 (laranja #F28C28) como referência.

### Destaques clínicos relevantes

1. **Neuroticismo Muito Superior:** padrão de alta reatividade emocional
2. **Extroversão Muito Baixa:** reserva interpessoal significativa
3. **Realização Muito Baixa:** possível impacto em organização/persistência

---

# 6. CRITÉRIOS DE QUALIDADE

A geração só deve ser considerada correta se:

- [ ] A ordem dos fatores estiver correta (NN → EE → SS → RR → AA)
- [ ] Os percentis estiverem preservados sem alteração
- [ ] As classificações corresponderem às fronteiras normativas exatas
- [ ] A tabela não conter colunas desnecessárias no laudo
- [ ] O radar tiver escala de 0 a 100
- [ ] A linha normativa estiver no percentil 50
- [ ] A legenda estiver correta (se aplicável)

---

# 7. OBSERVAÇÃO CLÍNICA

Esta skill não substitui a análise psicológica. Ela apenas organiza os resultados gráficos e tabulares do BFP para apresentação no laudo. A interpretação clínica deve considerar anamnese, observação comportamental, demais instrumentos aplicados e integração dos achados.

---

# 8. ANÁLISE AUTOMATIZADA PARA INSERÇÃO NO LAUDO

Esta seção apresenta um conjunto mínimo de regras e uma função exemplo que produzem um resumo interpretativo curto (para inclusão no laudo) a partir dos resultados numéricos já calculados (percentis e classificações). A saída é pensada para ser revista pelo avaliador antes da inserção final.

Regras principais usadas na análise automática:

- Destacar fatores com percentil >= 85 (elevado/superior) ou < 15 (baixo/muito baixo).
- Marcar como "extremo" percentis >= 97.5 ou < 2.5.
- Sinalizar combinações clinicamente relevantes (ex.: Neuroticismo elevado + Realização reduzida).
- Não gerar diagnóstico — usar linguagem condicional ("sugere", "pode indicar").

Exemplo de função (pseudocódigo / Python para implementação no backend):

```python
def summarize_bfp_for_report(results: dict) -> dict:
    """Gera um resumo curto, lista de fatores relevantes e recomendações de destaque.

    Input expected format:
    {
        'NN': {'percentile': 99.0, 'classification': 'Muito Superior'},
        'EE': {'percentile': 4.8, 'classification': 'Muito Baixo'},
        ...
    }
    Output example:
    {
        'summary': 'Perfil com elevação em Neuroticismo e redução em Extroversão...',
        'relevant': [{'code':'NN','percentile':99.0,'flag':'Muito Superior'}...],
        'recommendations': ['Integrar com anamnese','Verificar sintomas ansiosos']
    }
    """
    thresholds = {'highlight_low':15, 'highlight_high':85, 'extreme_low':2.5, 'extreme_high':97.5}
    mapping = {
        'NN':'Neuroticismo','EE':'Extroversão','SS':'Socialização','RR':'Realização','AA':'Abertura'
    }

    relevant = []
    for code, data in (results or {}).items():
        p = float(data.get('percentile') or 0)
        classification = data.get('classification') or '-'
        flag = None
        if p >= thresholds['extreme_high'] or p < thresholds['extreme_low']:
            flag = 'extremo'
        elif p >= thresholds['highlight_high'] or p < thresholds['highlight_low']:
            flag = 'relevante'

        if flag:
            relevant.append({'code':code,'name':mapping.get(code,code),'percentile':p,'classification':classification,'flag':flag})

    # Síntese simples
    elev = [r for r in relevant if r['percentile'] >= thresholds['highlight_high']]
    reduz = [r for r in relevant if r['percentile'] < thresholds['highlight_low']]

    parts = []
    if elev:
        parts.append('elevação em ' + ', '.join([f"{r['name']} ({r['classification']})" for r in elev]))
    if reduz:
        parts.append('redução em ' + ', '.join([f"{r['name']} ({r['classification']})" for r in reduz]))

    summary = 'Perfil sem alterações significativas.' if not parts else ('; '.join(parts) + '.')

    # Regras de combinação (exemplos úteis para laudo)
    combos = []
    codes = {r['code']:r for r in relevant}
    if 'NN' in codes and 'RR' in codes:
        if codes['NN']['percentile'] >= 85 and codes['RR']['percentile'] < 30:
            combos.append('Neuroticismo elevado associado a Realização reduzida pode sugerir impacto emocional na organização e manutenção de metas.')
    if 'NN' in codes and 'EE' in codes:
        if codes['NN']['percentile'] >= 85 and codes['EE']['percentile'] < 30:
            combos.append('Neuroticismo elevado com Extroversão reduzida pode indicar vivência interna de sofrimento com menor busca por apoio social.')

    recommendations = ['Integrar achados à anamnese e observação clínica', 'Confrontar com instrumentos de humor/ansiedade quando aplicáveis']

    return {'summary': summary, 'relevant': relevant, 'combinations': combos, 'recommendations': recommendations}
```

Observação: a função acima é um ponto de partida. Ajustes locais (linguagem, limiares normativos, nomes dos códigos) devem ser aplicados conforme o padrão da base normativa do sistema.

# Referências

- `apps/reports/services/report_export_service.py` (linhas 3866-3881): `_bfp_rows()`
- `apps/tests/bfp/calculators.py`: `classify_percentile()`, `weighted_score_from_z()`, `percentile_from_z()`
- `apps/tests/bfp/config.py`: `BFP_CLASSIFICATION_MEANING`, `FACTOR_DEFINITIONS`, `NORMS`
