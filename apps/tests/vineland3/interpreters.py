def interpret_results(data):
    if not data.get("domains"):
        return ""
    prefix = f"Vineland-3 — {data['form_label']}; respondente: {data['respondent']}."
    lines = [prefix]
    for row in data["domains"]:
        ci = "–".join(map(str, row["confidence_interval"])) if row.get("confidence_interval") else "indisponível"
        lines.append(f"{row['label']}: escore padrão {row['standard_score']}, percentil {row['percentile']}, IC95% {ci}; {row.get('classification', 'indisponível')}.")
    lines.append("Resultados obtidos com normas americanas; requerem revisão profissional e não estabelecem diagnóstico isoladamente.")
    return "\n".join(lines)
