def interpret_ssrs_results(merged_data: dict) -> str:
    rows = merged_data.get("resultados") or []
    general = [row for row in rows if row.get("scale") == "eg"]
    if not general:
        return "O SSRS foi computado, mas nao ha resultados normativos disponiveis para interpretacao."

    parts = []
    for row in general:
        parts.append(
            f"{row['domain_name']}: escore bruto {row['raw_score']}, percentil {row.get('percentile')}, classificacao {str(row.get('classification')).lower()}"
        )
    return "No SSRS, os resultados gerais foram: " + "; ".join(parts) + ". A interpretacao deve considerar informante, sexo e contexto clinico/educacional."
