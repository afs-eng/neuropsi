"""Domain-level scoring, with informant-specific norms separate from extensive forms."""

from functools import lru_cache
from itertools import combinations
from datetime import date
from copy import deepcopy

from .domain_protocol import PROTOCOL_ID, build_item_summary
from .norms import age_months
from .csv_tables import domain_norms_from_csv

SCALES = {"comunicacao": "COM", "vida_diaria": "AVD", "socializacao": "SOC", "atividade_fisica": "HMOT",
          "comportamento_a": "internalizante", "comportamento_b": "externalizante"}
LABELS = {"COM": "Comunicação", "AVD": "Atividades de Vida Diária", "SOC": "Socialização",
          "HMOT": "Habilidades Motoras", "CCA": "Composto de Comportamento Adaptativo"}


@lru_cache(maxsize=1)
def load_domain_norms():
    return domain_norms_from_csv()


def _table(groups, months):
    return next((g for g in groups if g["min_months"] <= months
                 and (g["max_months"] is None or months <= g["max_months"])), None)


def _lookup(entries, raw):
    return next((e[2:] for e in entries if e[0] <= raw <= e[1]), None)


def _classification(score):
    # Manual, tabela de níveis adaptativos (página física 32).
    return next(label for lower, label in [(130, "Alto"), (115, "Moderadamente alto"), (86, "Adequado"),
                                          (71, "Moderadamente baixo"), (20, "Baixo")] if score >= lower)


def _base_rate(magnitude, cutoffs):
    if any(cutoff is None for cutoff in cutoffs):
        return None  # Missing published thresholds cannot be treated as zero or interpolated.
    previous = 0
    for percentage, cutoff in zip((2, 5, 10, 15, 25), cutoffs):
        if magnitude >= cutoff:
            return f"≤ {percentage}%" if previous == 0 else f"> {previous}% a ≤ {percentage}%"
        previous = percentage
    return "> 25%"


def compute_domain_results(responses, birth_date, reference_date):
    summary = build_item_summary(responses)
    return compute_summary_results(summary, birth_date, reference_date, load_domain_norms())


def compute_summary_results(summary, birth_date, reference_date, norms):
    months = age_months({"birth_date": birth_date, "reference_date": reference_date})
    table = _table(norms["domains"], months)
    adaptive, behavior = [], []
    for section in summary["sections"]:
        if section["kind"] == "critical":
            continue
        scale = SCALES[section["code"]]
        row = {"code": section["code"], "scale": scale, "label": LABELS.get(scale, section["label"]),
               "raw_score": section["raw_score"], "applied": section["applied"], "standard_score": None,
               "percentile": None, "confidence_interval": None, "classification": None, "v_scale": None,
               "unavailable_reason": "Seção não aplicada" if not section["applied"] else "Sem norma para a idade"}
        if section["kind"] == "adaptive":
            entries = table["scores"][scale] if table else []
            found = _lookup(entries, section["raw_score"]) if section["applied"] else None
            if found:
                score, percentile = found
                margin = table["ci"]["95"][scale]
                row.update(standard_score=score, percentile=percentile, classification=_classification(score),
                           confidence_interval=[score - margin, score + margin] if margin is not None else None,
                           unavailable_reason=None)
            adaptive.append(row)
        else:
            btable = _table(norms["behavior"], months)
            found = _lookup(btable["scores"][scale], section["raw_score"]) if btable and section["applied"] else None
            if found:
                row.update(v_scale=found[0], unavailable_reason=None)
            behavior.append(row)
    core = adaptive[:3]
    total = sum(row["standard_score"] for row in core) if all(row["standard_score"] is not None for row in core) else None
    cca = {"code": "cca", "scale": "CCA", "label": LABELS["CCA"], "raw_score": None, "applied": True,
           "sum_standard_scores": total, "standard_score": None, "percentile": None,
           "confidence_interval": None, "classification": None, "unavailable_reason": "Sem norma para a idade"}
    found = _lookup(table["scores"]["CCA"], total) if table and total is not None else None
    if found:
        score, percentile = found
        margin = table["ci"]["95"]["CCA"]
        cca.update(standard_score=score, percentile=percentile, classification=_classification(score),
                   confidence_interval=[score - margin, score + margin] if margin is not None else None, unavailable_reason=None)
    available = [row for row in adaptive if row["standard_score"] is not None]
    mean = sum(row["standard_score"] for row in available) / len(available) if len(available) >= 3 else None
    strengths = []
    stable = _table(norms["strengths"], months)
    for row in adaptive:
        numbers = stable["rows"].get(row["scale"], []) if stable else []
        diff = row["standard_score"] - mean if row["standard_score"] is not None and mean is not None else None
        critical = numbers[1] if numbers else None  # p = .05; independent of the score's CI.
        significant = abs(diff) >= critical if diff is not None and critical is not None else None
        strengths.append({"scale": row["scale"], "standard_score": row["standard_score"],
                          "difference": round(diff, 2) if diff is not None else None, "critical_value": critical,
                          "finding": ("Força" if diff > 0 else "Fraqueza") if significant else "Não significativa" if significant is False else "Não disponível",
                          "base_rate": _base_rate(abs(diff), numbers[2:]) if diff is not None and numbers else None})
    pairs = []
    for first, second in combinations(adaptive, 2):
        diff = first["standard_score"] - second["standard_score"] if all(r["standard_score"] is not None for r in (first, second)) else None
        key = f"{first['scale']}{'>' if diff is not None and diff >= 0 else '<'}{second['scale']}"
        if "pairs_by_age" in norms:
            ptable = _table(norms["pairs_by_age"], months)
            values = ptable["rows"].get(key, [None] * 7) if ptable else [None] * 7
        else:
            values = norms["pairs"][key]
            values = values[:7] if months < 84 else values[7:]
        pairs.append({"first": first["scale"], "second": second["scale"],
                       "difference": diff, "critical_value": values[1] if diff is not None else None,
                       "significant": abs(diff) >= values[1] if diff is not None and values[1] is not None else None,
                      "base_rate": _base_rate(abs(diff), values[2:]) if diff is not None else None})
    return {"normative_scoring": cca["standard_score"] is not None, "protocol_id": PROTOCOL_ID,
            "confidence_level": 95, "significance_level": .05, "age_months": months,
            "population": norms["population"], "source_version": norms["version"], "sources": deepcopy(norms["sources"]),
            "normative_age_range": {"min_months": table["min_months"], "max_months": table["max_months"]} if table else None,
            "source_pages": table["pages"] if table else [], "adaptive": adaptive, "cca": cca, "behavior": behavior,
            "mean_standard_score": round(mean, 2) if mean is not None else None, "mean_domain_count": len(available),
            "strengths": strengths, "pairs": pairs, "requires_clinical_review": True}


def results_for_application(application):
    raw = application.raw_payload or {}
    if (application.instrument.code == "vineland3" and raw and raw.get("entry_mode", "totals") == "totals"
            and raw.get("form_level", "extensivo") == "extensivo"):
        from .calculators import compute_scores

        if not application.applied_on or application.applied_on > date.today():
            raise ValueError("Informe uma data de aplicação válida, não futura.")
        if raw.get("item_protocol_id") is not None:
            raise ValueError("Totais extensivos não podem conter banco de perguntas.")
        patient = application.evaluation.patient
        return compute_scores({**raw, "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
                               "reference_date": application.applied_on.isoformat()})["analysis"]
    if application.instrument.code == "vineland3" and raw.get("entry_mode") == "totals" and raw.get("form_level") == "niveis_dominio":
        from .domain_totals import compute_domain_totals

        if raw.get("completion_status") != "finalized":
            return None
        patient = application.evaluation.patient
        return compute_domain_totals({**raw, "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
                                      "reference_date": application.applied_on.isoformat() if application.applied_on else None})
    if (application.instrument.code != "vineland3" or raw.get("entry_mode") != "items"
            or raw.get("item_protocol_id") != PROTOCOL_ID or raw.get("completion_status") != "finalized"):
        return None
    patient = application.evaluation.patient
    if application.applied_on and application.applied_on > date.today():
        raise ValueError("A aplicação não pode estar no futuro.")
    return compute_domain_results(raw.get("item_responses"), patient.birth_date.isoformat() if patient.birth_date else None,
                                  application.applied_on.isoformat() if application.applied_on else None)
