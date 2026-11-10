"""Totals entered from domain-level protocols; no questionnaire answers inferred."""

from datetime import date

from .config import FORMS
from .csv_tables import domain_form_norms
from .domain_scoring import SCALES, LABELS, _lookup, _table, compute_summary_results
from .norms import age_months

PROTOCOL_ID = "vineland3_domain_totals_v1"
FORM_LABELS = {"entrevista": "Entrevista", "pais_cuidadores": "Pais/Cuidadores", "professores": "Professores"}


def is_domain_application(application):
    raw = application.raw_payload or {}
    return application.instrument.code == "vineland3" and (
        raw.get("entry_mode") == "items" or raw.get("form_level") == "niveis_dominio")


def domain_total_scales(form):
    norms = domain_form_norms(form)
    scales = []
    for code, scale in SCALES.items():
        groups = norms["domains"] if scale in LABELS else norms["behavior"]
        available = [g for g in groups if g["scores"].get(scale)]
        scales.append({"code": scale, "label": LABELS.get(scale, "Internalizante (A)" if scale == "internalizante" else "Externalizante (B)"),
                       "optional": scale not in {"COM", "AVD", "SOC"},
                       "max": max(e[1] for g in available for e in g["scores"][scale]),
                       "min_months": available[0]["min_months"], "max_months": available[-1]["max_months"]})
    return scales


def compute_domain_totals(raw):
    if raw.get("entry_mode", "totals") != "totals" or raw.get("form_level") != "niveis_dominio":
        raise ValueError("Selecione Níveis de Domínio e entrada por totais.")
    if raw.get("form") not in FORMS:
        raise ValueError("Selecione Entrevista, Pais/Cuidadores ou Professores.")
    if raw.get("item_responses") is not None or raw.get("item_protocol_id") is not None:
        raise ValueError("Totais de domínio não podem conter respostas ou banco de perguntas.")
    if not isinstance(raw.get("respondent"), str) or not raw["respondent"].strip():
        raise ValueError("Identifique o respondente.")
    months = age_months(raw)
    if date.fromisoformat(raw["reference_date"]) > date.today():
        raise ValueError("A aplicação não pode estar no futuro.")
    norms = domain_form_norms(raw["form"])
    table = _table(norms["domains"], months)
    if not table or not all(table["scores"][s] for s in ("COM", "AVD", "SOC", "CCA")):
        raise ValueError("Sem norma de Níveis de Domínio para este formulário e idade.")
    scores = raw.get("raw_scores")
    if not isinstance(scores, dict):
        raise ValueError("Informe os totais brutos por domínio.")
    unknown = set(scores) - set(SCALES.values())
    if unknown:
        raise ValueError(f"Campos incompatíveis com Níveis de Domínio: {', '.join(sorted(unknown))}.")
    for scale in ("COM", "AVD", "SOC"):
        if scale not in scores:
            raise ValueError(f"Informe a pontuação bruta de {LABELS[scale]}.")
    btable = _table(norms["behavior"], months)
    sections = []
    for code, scale in SCALES.items():
        entries = table["scores"][scale] if scale in LABELS else btable["scores"][scale] if btable else []
        applied = scale in scores
        if applied and (type(scores[scale]) is not int or not _lookup(entries, scores[scale])):
            raise ValueError(f"{scale}: pontuação inválida ou sem conversão para este formulário/idade.")
        sections.append({"code": code, "label": LABELS.get(scale, "Internalizante (A)" if scale == "internalizante" else "Externalizante (B)"),
                         "kind": "adaptive" if scale in LABELS else "behavior", "applied": applied,
                         "raw_score": scores[scale] if applied else None})
    result = compute_summary_results({"sections": sections}, raw["birth_date"], raw["reference_date"], norms)
    return {**result, "protocol_id": PROTOCOL_ID, "form": raw["form"], "form_level": "niveis_dominio",
            "form_label": f"{FORM_LABELS[raw['form']]} — Níveis de Domínio", "table_codes": norms["table_codes"],
            "entry_mode": "totals"}


def totals_summary(result):
    """Presentation metadata only: totals contain no item counts or critical-item answers."""
    return {"sections": [{**row, "kind": kind, "answered": None, "total": None}
                         for kind, rows in (("adaptive", result["adaptive"]), ("behavior", result["behavior"])) for row in rows],
            "critical_items": []}
