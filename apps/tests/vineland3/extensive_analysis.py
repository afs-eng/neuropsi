"""Normative analysis of one extensive protocol; never domain-level columns."""

from itertools import combinations

from .csv_tables import load_table
from .domain_scoring import _classification
from .norms import age_table, domain_members

APPENDICES = {"entrevista": "B", "pais_cuidadores": "C", "professores": "D"}


def base_rate_range(magnitude, row):
    """Bound by published thresholds only; missing cells never become zero."""
    thresholds = [(p, float(row[f"base_{p}"])) for p in (2, 5, 10, 15, 25) if row.get(f"base_{p}")]
    if not thresholds:
        return None
    lower = max((p for p, cutoff in thresholds if magnitude < cutoff), default=0)
    upper = min((p for p, cutoff in thresholds if magnitude >= cutoff), default=None)
    if upper is not None and lower >= upper:
        return None  # Inconsistent thresholds: do not fabricate an interval.
    if upper is None:
        return f"> {lower}%"
    return f"> {lower}% a ≤ {upper}%" if lower else f"≤ {upper}%"


def strengths(rows, reference):
    available = [row for row in rows if row["score"] is not None]
    mean = sum(row["score"] for row in available) / len(available) if available else None
    output = []
    for row in rows:
        norm = reference.get(row["scale"], {})
        diff = row["score"] - mean if row["score"] is not None and mean is not None else None
        critical = float(norm["critico_p05"]) if norm.get("critico_p05") else None
        significant = abs(diff) >= critical if diff is not None and critical is not None else None
        output.append({"scale": row["scale"], "label": row["label"], "score": row["score"],
                       "standard_score": row["score"], "difference": round(diff, 2) if diff is not None else None,
                       "critical_value": critical, "significant": significant,
                       "finding": ("Força" if diff > 0 else "Fraqueza") if significant else "Não significativa" if significant is False else "Não disponível",
                       "base_rate": base_rate_range(abs(diff), norm) if diff is not None else None,
                       "source_page": int(norm["pagina"]) if norm else None})
    return output, round(mean, 2) if mean is not None else None, len(available)


def pairs(rows, reference):
    output = []
    for first, second in combinations(rows, 2):
        diff = first["score"] - second["score"] if first["score"] is not None and second["score"] is not None else None
        direction = ">" if diff is not None and diff >= 0 else "<"
        norm = reference.get((first["scale"], second["scale"], direction), {})
        critical = float(norm["critico_p05"]) if norm.get("critico_p05") else None
        output.append({"first": first["scale"], "second": second["scale"],
                       "first_label": first["label"], "second_label": second["label"],
                       "first_score": first["score"], "second_score": second["score"],
                       "relation": "=" if diff == 0 else direction if diff is not None else None,
                       "difference": diff, "critical_value": critical,
                       "significant": abs(diff) >= critical if diff is not None and critical is not None else None,
                       "base_rate": base_rate_range(abs(diff), norm) if diff is not None else None,
                       "within_domain": first.get("domain") == second.get("domain"),
                       "source_page": int(norm["pagina"]) if norm else None})
    return output


def enrich_extensive(result):
    appendix = APPENDICES[result["form"]]
    months = result["age_months"]
    ci = {row["escala"]: int(row["margem"]) if row["margem"] else None
          for row in load_table(f"{appendix}.3", kind="ic", level="extensivo", months=months) if row["confianca"] == "95"}
    for row in result["domains"]:
        margin = ci.get("CCA" if row["scale"] == "ABC" else row["scale"])
        row.update(confidence_interval=[row["standard_score"] - margin, row["standard_score"] + margin] if margin is not None else None,
                   classification=_classification(row["standard_score"]))
    by_scale = {row["scale"]: row for row in result["domains"]}
    applicable = age_table(result["form"], "domains", months)["scores"]
    adaptive = []
    for code, label in (("COM", "Comunicação"), ("AVD", "Atividades de Vida Diária"), ("SOC", "Socialização"), ("HMOT", "Habilidades Motoras")):
        row = by_scale.get(code)
        adaptive.append({**row, "code": code, "raw_score": None, "applied": True, "unavailable_reason": None} if row else {
            "code": code, "scale": code, "label": label, "raw_score": None, "sum_v_scale": None,
            "standard_score": None, "percentile": None, "confidence_interval": None, "classification": None,
            "applied": False, "unavailable_reason": "Não informado" if applicable.get(code) else "Sem norma para a idade"})
    members = domain_members(result["form"])
    order = [key for group in members.values() for key in group]
    subdomains = sorted((dict(row) for row in result["subdomains"]), key=lambda row: order.index(row["scale"]))
    equivalent_rows = {(r["escala"], r["bruto"]): r for r in load_table(f"{appendix}.2", level="extensivo")}
    for row in subdomains:
        norm = equivalent_rows.get((row["scale"], str(row["raw_score"])), {})
        row.update(domain=next(key for key, group in members.items() if row["scale"] in group),
                   display_code="CMD" if row["scale"] == "com" else row["scale"].upper(),
                   age_equivalent=norm.get("equivalente_idade") or None,
                   growth_value=int(norm["vec"]) if norm.get("vec") else None,
                   equivalent_source_page=int(norm["pagina"]) if norm else None)
    norms = load_table(f"{appendix}.4", level="extensivo", months=months)
    domain_strengths, mean, count = strengths(
        [{"scale": r["scale"], "label": r["label"], "score": r["standard_score"]} for r in adaptive],
        {r["escala"]: r for r in norms if r["categoria"] == "dominio"})
    sub_strengths, sub_mean, sub_count = strengths(
        [{**r, "score": r["v_scale"]} for r in subdomains],
        {r["escala"]: r for r in norms if r["categoria"] == "subdominio"})

    def pair_reference(number):
        return {(r["escala"], r["outra_escala"], r["direcao"]): r
                for r in load_table(f"{appendix}.{number}", level="extensivo", months=months)}

    analysis = {"normative_scoring": True, "form_level": "extensivo", "entry_mode": "totals",
                "form": result["form"], "form_label": result["form_label"], "age_months": months,
                "confidence_level": 95, "significance_level": .05, "correction_version": 2,
                "population": "Normas americanas", "sources": [result["norm_source"]],
                "table_codes": f"{appendix}.1–{appendix}.6 (Extensivo)",
                "adaptive": adaptive, "cca": {**by_scale["ABC"], "scale": "CCA", "code": "cca", "raw_score": None,
                                             "applied": True, "unavailable_reason": None},
                "subdomains": subdomains, "behavior": [], "strengths": domain_strengths,
                "mean_standard_score": mean, "mean_domain_count": count,
                "subdomain_strengths": sub_strengths, "subdomain_mean_v_scale": sub_mean, "subdomain_count": sub_count,
                "pairs": pairs([{"scale": r["scale"], "label": r["label"], "score": r["standard_score"]} for r in adaptive], pair_reference(5)),
                "subdomain_pairs": pairs([{**r, "score": r["v_scale"]} for r in subdomains], pair_reference(6)),
                "requires_clinical_review": True}
    return {**result, "analysis": analysis}
