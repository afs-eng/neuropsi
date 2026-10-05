from math import erf, sqrt

from .config import SCALES
from .norms import GENERAL_TOTAL_MEAN, GENERAL_TOTAL_SD, lookup_subscale, lookup_total
from .schemas import THCPRawInput


def derived_scores(z_score: float | None) -> dict:
    if z_score is None:
        return {"z_score": None, "weighted_score": None, "percentile": None}
    return {
        "z_score": round(z_score, 4),
        "weighted_score": round(z_score * 3 + 10, 2),
        "percentile": round(50 * (1 + erf(z_score / sqrt(2))), 2),
    }


def compute_thcp_scores(raw: dict, age: int) -> dict:
    if not 4 <= age <= 7:
        raise ValueError("O THCP possui normas apenas entre 4 e 7 anos.")
    data = THCPRawInput.model_validate(raw)
    scores = data.model_dump(include={"hpm", "linguagem", "pq", "memoria"})
    scores["atencao"] = max(0, data.atencao_acertos - data.atencao_erros)
    scores["total"] = sum(scores.values())
    group = str(age) if data.norm_type == "idade" else "geral"
    results = []
    warnings = []
    for code, (label, maximum) in SCALES.items():
        score = scores[code]
        if code != "total":
            norm = lookup_subscale(group, code, score)
            z = (score - norm["mean"]) / norm["sd"]
            t_score = max(0, z * 10 + 50)
        elif group == "geral":
            norm = {"mean": GENERAL_TOTAL_MEAN, "sd": GENERAL_TOTAL_SD,
                    "manual_classification": None, "manual_percentile_band": None}
            z = (score - norm["mean"]) / norm["sd"]
            t_score = z * 10 + 50
        else:
            norm = lookup_total(group, score)
            t_score = norm["t_score"]
            z = (t_score - 50) / 10 if isinstance(t_score, (int, float)) else None
            if z is None:
                warnings.append(f"Escore Total: T-score {t_score}; métricas derivadas pontuais indisponíveis.")
            if group == "6" and score == 49:
                warnings.append("A fonte registra T-score < 28 para total 49 aos 6 anos (aba THCP-Normas, E206/B206); valor preservado, conferir o manual.")
        results.append({
            "code": code, "label": label, "raw_score": score, "max_score": maximum,
            **norm, "t_score": round(t_score, 2) if isinstance(t_score, (int, float)) else t_score,
            **derived_scores(z),
        })
    return {
        "age": age, "norm_type": data.norm_type,
        "norm_group": group, "norm_label": f"{age} anos" if group != "geral" else "Amostra Geral",
        "scores": scores, "results": results, "warnings": warnings,
    }
