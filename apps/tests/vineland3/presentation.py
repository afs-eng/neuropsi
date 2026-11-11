from io import BytesIO


def docx_rows(data):
    if data.get("normative_results"):
        rows = [["Domínio", "Bruto / Soma", "Escore padrão", "Percentil", "IC95%", "Classificação"]]
        for row in data["domains"]:
            value = row.get("sum_standard_scores") if row["scale"] == "CCA" else row.get("sum_v_scale", row.get("raw_score"))
            rows.append([row["label"], str(value) if value is not None else "—",
                         str(row["standard_score"]), row["percentile"],
                         "–".join(map(str, row["confidence_interval"])) if row["confidence_interval"] else "—", row["classification"]])
        return rows
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
    if data.get("normative_results"):
        for index, row in enumerate(rows):
            ci = row.get("confidence_interval")
            if ci:
                ax.errorbar(row["standard_score"], index,
                            xerr=[[row["standard_score"] - ci[0]], [ci[1] - row["standard_score"]]],
                            fmt="none", color="#082d5f", capsize=4)
    ax.set_xlim(0, 160 if data.get("normative_results") else 150)
    ax.set_xlabel("Escore padrão — normas americanas (tabela: 20–140)")
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    output = BytesIO()
    fig.savefig(output, format="png", dpi=150)
    return output.getvalue()


def analysis_tables(data):
    result = data["normative_results"]
    appendix = {"entrevista": "B", "professores": "D"}.get(result.get("form"), "C")
    behavior_table = {"entrevista": "E.1", "professores": "E.3"}.get(result.get("form"), "E.2")

    def text(value):
        return "—" if value is None else str(value)

    behavior = [["Comportamento", "Bruto", "Escala-v", "Situação"]]
    for row in result["behavior"]:
        behavior.append([row["label"], text(row["raw_score"]), text(row["v_scale"]), row["unavailable_reason"] or "Calculado"])
    strengths = [["Domínio", "Escore padrão", "Diferença", "Valor crítico", "Força / fraqueza", "Taxa de base"]]
    for row in result["strengths"]:
        strengths.append([row["scale"], text(row["standard_score"]), text(row["difference"]), text(row["critical_value"]), row["finding"], text(row["base_rate"])])
    pairs = [["Domínios", "Diferença", "Valor crítico", "Significativa", "Taxa de base"]]
    for row in result["pairs"]:
        pairs.append([f"{row['first']} – {row['second']}", text(row["difference"]), text(row["critical_value"]),
                      "—" if row["significant"] is None else "Sim" if row["significant"] else "Não", text(row["base_rate"])])
    tables = [(f"Comportamento mal adaptativo — {behavior_table}", behavior),
            (f"Forças / fraquezas — {appendix}.4; média {text(result['mean_standard_score'])}; p = 0,05", strengths),
            (f"Diferenças emparelhadas — {appendix}.5; p = 0,05", pairs)]
    if result.get("form_level") != "extensivo":
        return tables
    subdomains = [["Domínio", "Subdomínio", "Bruto", "Escala-v", "Equiv. etário (a:m)", "VEC"]]
    for row in result["subdomains"]:
        subdomains.append([row["domain"], f"{row['label']} ({row['display_code']})", text(row["raw_score"]), text(row["v_scale"]),
                           text(row["age_equivalent"]), text(row["growth_value"])])
    sub_strengths = [["Subdomínio", "Escala-v", "Diferença", "Valor crítico", "Força / fraqueza", "Taxa de base"]]
    for row in result["subdomain_strengths"]:
        sub_strengths.append([row["label"], text(row["score"]), text(row["difference"]), text(row["critical_value"]), row["finding"], text(row["base_rate"])])
    tables = [("Subdomínios — equivalente etário não é idade global de desenvolvimento", subdomains), *tables[1:],
              (f"Forças / fraquezas de subdomínios — {appendix}.4; média escala-v {text(result['subdomain_mean_v_scale'])}", sub_strengths)]
    for within, label in ((True, "mesmo domínio"), (False, "domínios diferentes — análise exploratória")):
        rows = [["Subdomínios", "Diferença", "Valor crítico", "Significativa", "Taxa de base"]]
        for row in result["subdomain_pairs"]:
            if row["within_domain"] == within:
                first, second = ("CMD" if row[key] == "com" else row[key].upper() for key in ("first", "second"))
                rows.append([f"{first} – {second}", text(row["difference"]), text(row["critical_value"]),
                             "—" if row["significant"] is None else "Sim" if row["significant"] else "Não", text(row["base_rate"])])
        if len(rows) > 1:
            tables.append((f"Diferenças entre subdomínios — {appendix}.6; {label}; p = 0,05", rows))
    return tables


def build_subdomain_chart(data):
    from matplotlib.figure import Figure
    from .profile_chart import subdomain_profile

    result = data.get("normative_results") or {}
    if not result.get("subdomains"):
        return b""
    profile = subdomain_profile(result)
    fig = Figure(figsize=(9, 6), layout="constrained")
    ax = fig.subplots()
    columns = profile["columns"]
    ax.plot(range(len(columns)), [r["score"] if r["score"] is not None else float("nan") for r in columns],
            color="#0e7490", marker="o", markersize=4, linewidth=1.8)
    for index, row in enumerate(columns):
        if row["score"] is not None:
            ax.annotate(str(row["score"]), (index, row["score"]), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8)
    for tick in profile["ticks"]:
        ax.axhline(tick["value"], color="#475569" if tick["reference"] else "#e2e8f0",
                   linestyle="--" if tick["reference"] else "-", linewidth=1 if tick["reference"] else .5, zorder=0)
    for group in profile["groups"]:
        start = (group["x"] - 48) / 44 - .5
        width = group["width"] / 44
        ax.axvline(start, color="#94a3b8", linewidth=.7)
        ax.text(start + width / 2, 25, group["code"], ha="center", fontsize=10, fontweight="bold")
    ax.set(xlim=(-.5, len(columns) - .5), ylim=(1, 26), yticks=range(1, 25),
           xticks=range(len(columns)), xticklabels=[r["display_code"] for r in columns], ylabel="Escala-v")
    ax.set_xlabel("COM: Comunicação · AVD: Vida Diária · SOC: Socialização · HMOT: Motor\n"
                  "CMD = Comunidade · Tracejados: 15, 12, 9 e 6 (referências visuais)\n"
                  "Ausências interrompem a linha; não equivalem a zero.", fontsize=8)
    output = BytesIO()
    fig.savefig(output, format="png", dpi=150)
    return output.getvalue()
