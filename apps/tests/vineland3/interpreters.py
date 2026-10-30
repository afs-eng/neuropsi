def interpret_results(data):
    if not data.get("domains"):
        return ""
    prefix = f"Vineland-3 — {data['form_label']}; respondente: {data['respondent']}."
    lines = [prefix]
    for row in data["domains"]:
        lines.append(f"{row['label']}: escore padrão {row['standard_score']}, percentil {row['percentile']}.")
    lines.append("Resultados obtidos com normas americanas. A classificação qualitativa não foi emitida nesta versão; requer revisão do profissional responsável.")
    return "\n".join(lines)
