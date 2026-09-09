from .config import SSRS_DOMAINS
from .norms import format_percentile_range, percentile_for_score, percentile_range_for_score


def interpret_percentile(domain: str, percentile: int | None) -> str:
    if percentile is None:
        return "Sem norma disponivel"
    if percentile >= 76:
        if domain == "behavior_problems":
            return "Acima da media superior"
        if domain == "academic_competence":
            return "Muito alta"
        return "Altamente elaborado"
    if percentile >= 66:
        if domain == "behavior_problems":
            return "Medio superior"
        if domain == "academic_competence":
            return "Alta"
        return "Elaborado"
    if percentile >= 36:
        if domain == "behavior_problems":
            return "Mediano"
        if domain == "academic_competence":
            return "Mediana"
        return "Bom repertorio"
    if percentile >= 26:
        if domain == "behavior_problems":
            return "Baixo"
        if domain == "academic_competence":
            return "Media inferior"
        return "Medio inferior"
    if domain == "behavior_problems":
        return "Muito baixo"
    if domain == "academic_competence":
        return "Abaixo da media inferior"
    return "Baixo"


def classify_ssrs_scores(computed: dict, gender: str = "F") -> dict:
    informant = computed.get("informant", "crianca")
    gender = gender if gender in {"F", "M"} else "F"
    resultados = []
    for domain, payload in computed.get("domains", {}).items():
        eg = payload.get("eg", 0)
        percentile = percentile_for_score(informant, gender, domain, "eg", eg)
        percentile_range = percentile_range_for_score(informant, gender, domain, "eg", eg)
        resultados.append({
            "domain": domain,
            "domain_name": SSRS_DOMAINS.get(domain, domain),
            "scale": "eg",
            "name": "Escore geral",
            "raw_score": eg,
            "percentile": percentile,
            "percentile_min": percentile_range[0] if percentile_range else None,
            "percentile_max": percentile_range[1] if percentile_range else None,
            "percentile_label": format_percentile_range(percentile_range),
            "classification": interpret_percentile(domain, percentile),
        })
        for code, factor in payload.get("factors", {}).items():
            score = factor.get("raw_score", 0)
            percentile = percentile_for_score(informant, gender, domain, code, score)
            percentile_range = percentile_range_for_score(informant, gender, domain, code, score)
            resultados.append({
                "domain": domain,
                "domain_name": SSRS_DOMAINS.get(domain, domain),
                "scale": code,
                "name": factor.get("name", code),
                "raw_score": score,
                "percentile": percentile,
                "percentile_min": percentile_range[0] if percentile_range else None,
                "percentile_max": percentile_range[1] if percentile_range else None,
                "percentile_label": format_percentile_range(percentile_range),
                "classification": interpret_percentile(domain, percentile),
            })
    return {"gender": gender, "informant": informant, "resultados": resultados}
