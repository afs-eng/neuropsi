"""Explicit, signed review of current Vineland results, extensive or domain-level."""

import hashlib
import json

from django.core import signing

from apps.accounts.models import UserRole

from .domain_scoring import results_for_application
from .domain_protocol import build_item_summary

SALT = "vineland3.domain-review.v1"
CORRECTION_VERSION = 1
EXTENSIVE_CORRECTION_VERSION = 2


def can_review(user):
    return bool(user) and user.role in {UserRole.ADMIN, UserRole.NEUROPSYCHOLOGIST, UserRole.REVIEWER}


def review_state(application, result=None):
    """Fail closed on missing/changed data, without writing or trusting is_validated."""
    try:
        result = results_for_application(application) if result is None else result
    except ValueError as error:
        return {"eligible": False, "validated": False, "reason": str(error)}
    if not result or not result.get("normative_scoring"):
        return {"eligible": False, "validated": False,
                "reason": "Conclua uma aplicação com resultados normativos disponíveis para o formulário e idade."}
    patient = application.evaluation.patient
    version = EXTENSIVE_CORRECTION_VERSION if result.get("form_level") == "extensivo" else CORRECTION_VERSION
    material = {"version": version, "application": application.pk, "evaluation": getattr(application, "evaluation_id", None),
                "patient": patient.pk, "patient_name": patient.full_name, "birth_date": str(patient.birth_date),
                "applied_on": str(application.applied_on), "raw": application.raw_payload, "results": result}
    fingerprint = hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    state = {"eligible": True, "validated": False, "fingerprint": fingerprint,
             "reason": "Revisão profissional pendente ou invalidada por alteração dos dados/normas."}
    if not getattr(application, "is_validated", False):
        return state
    token = (application.reviewed_payload or {}).get("vineland_domain_review")
    try:
        review = signing.loads(token, salt=SALT) if isinstance(token, str) else {}
    except signing.BadSignature:
        return state
    if not isinstance(review, dict) or review.get("fingerprint") != fingerprint:
        return state
    return {**state, "validated": True, "reason": "Revisado para inclusão no laudo.",
            "reviewer": review["reviewer"], "reviewed_at": review["reviewed_at"], "clinical_note": review["clinical_note"]}


def report_data(application):
    result = results_for_application(application)
    state = review_state(application, result)
    if not state["validated"]:
        return {}
    rows = [row for row in result["adaptive"] + [result["cca"]] if row["standard_score"] is not None]
    totals = (application.raw_payload or {}).get("entry_mode", "totals") == "totals"
    form_label = result.get("form_label", "Pais/Cuidadores — Níveis de Domínio")
    extensive = result.get("form_level") == "extensivo"
    return {"form_label": form_label, "respondent": application.raw_payload.get("respondent", ""),
            "domains": rows, "results": result.get("subdomains", []) + rows + [r for r in result["behavior"] if r["v_scale"] is not None],
            "normative_results": result, "clinical_review": state, "domain_level": not extensive,
            "subdomains": result.get("subdomains", []),
            "general_observations": application.raw_payload.get("general_observations", ""),
            "critical_items": [] if totals else build_item_summary(application.raw_payload.get("item_responses"))["critical_items"],
            "technical_notes": [f"Normas americanas de {form_label}; IC 95%; p = 0,05.",
                                *(["Entrada por totais do protocolo; sem respostas item a item ou avaliação individual de itens críticos neste registro."] if totals else []),
                                "Itens críticos exigem análise individual; o instrumento não estabelece diagnóstico isoladamente."]}


def report_summary(data):
    lines = [f"Vineland-3 — {data['form_label']}; respondente: {data['respondent']}."]
    for row in data["domains"]:
        ci = "–".join(map(str, row["confidence_interval"])) if row["confidence_interval"] else "indisponível"
        lines.append(f"{row['label']}: escore padrão {row['standard_score']}, percentil {row['percentile']}, IC95% {ci}; {row['classification']}.")
    lines.extend(data["technical_notes"])
    for row in data["normative_results"]["behavior"]:
        if row["v_scale"] is not None:
            lines.append(f"{row['label']}: bruto {row['raw_score']}, escala-v {row['v_scale']}.")
    for row in data["critical_items"]:
        lines.append(f"Item crítico {row['id']}, resposta {row['response']}: {row['text']}")
    if data.get("general_observations"):
        lines.append(f"Observações gerais: {data['general_observations']}")
    lines.append(f"Revisão profissional: {data['clinical_review']['clinical_note']}")
    return "\n".join(lines)
