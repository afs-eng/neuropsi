from io import BytesIO


def docx_rows(data):
    rows = [["Domínio / Subdomínio", "Bruto / Soma", "Escala-v", "Escore padrão", "Percentil"]]
    for row in data.get("subdomains", []):
        rows.append([row["label"], str(row["raw_score"]), str(row["v_scale"]), "—", "—"])
    for row in data.get("domains", []):
        rows.append([row["label"], str(row.get("sum_v_scale", row.get("sum_standard_scores"))),
                     "—", str(row["standard_score"]), row["percentile"]])
    return rows


def build_chart(data):
    from matplotlib.figure import Figure

    rows = data.get("domains", [])
    if not rows:
        return b""
    fig = Figure(figsize=(8, 3.5), layout="constrained")
    ax = fig.subplots()
    bars = ax.barh(["CCA" if row["scale"] == "ABC" else row["scale"] for row in rows],
                   [row["standard_score"] for row in rows], color="#0e7490")
    ax.bar_label(bars, padding=3)
    ax.set_xlim(0, 150)
    ax.set_xlabel("Escore padrão — normas americanas (tabela: 20–140)")
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    output = BytesIO()
    fig.savefig(output, format="png", dpi=150)
    return output.getvalue()
