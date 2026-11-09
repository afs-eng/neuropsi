from datetime import date
from typing import Any, Literal

from django.db import transaction
from ninja import Router, Schema
from pydantic import ConfigDict, Field

from apps.api.auth import bearer_auth
from apps.audit.services import AuditService
from apps.common.clinical_access import owned_evaluations
from apps.evaluations.models import Evaluation
from apps.tests.api.age_utils import get_reference_date
from apps.tests.api.catalog import ensure_required_instruments
from apps.tests.api.permissions import can_edit_tests, can_view_tests
from apps.tests.api.schemas import MessageOut
from apps.tests.api.serializers import serialize_test_application
from apps.tests.models import Instrument, TestApplication

from .calculators import compute_scores
from . import domain_protocol
from .domain_scoring import compute_domain_results
from .config import FORMS, SUBDOMAINS, TECHNICAL_NOTES
from .interpreters import interpret_results
from .item_protocol import PROTOCOL_ID, SOURCE, item_protocol, normalize_item_responses
from .norms import age_months, age_table, load_norms
from .validators import validate_input

router = Router(tags=["tests"])


def _is_empty_application(application):
    return (
        application.status != TestApplication.Status.LOCKED
        and not application.is_validated
        and not (application.interpretation_text or "").strip()
        and not any((application.raw_payload, application.computed_payload,
                     application.classified_payload, application.reviewed_payload))
    )


class Vineland3SubmitIn(Schema):
    model_config = ConfigDict(extra="forbid")

    evaluation_id: int
    application_id: int | None = None
    applied_on: date | None = None
    form: Literal["entrevista", "pais_cuidadores", "professores"] | None = None
    respondent: str = Field(min_length=1, max_length=200)
    entry_mode: Literal["totals", "items"] = "totals"
    raw_scores: dict[str, Any] = Field(default_factory=dict)
    item_responses: dict | None = None
    item_protocol_id: str | None = None
    general_observations: str = Field(default="", max_length=10000)
    finalize: bool = False


@router.get("/protocol", response={200: dict, 403: MessageOut}, auth=bearer_auth)
def protocol(request):
    if not can_view_tests(request.auth):
        return 403, {"message": "Você não tem permissão para visualizar testes."}
    forms = {}
    for code, label in FORMS.items():
        # Public configuration only: never expose the normative score tables.
        representative = age_table(code, "subdomains", 36)["scores"]
        tables = load_norms()["forms"][code]["subdomains"]
        applicability = {}
        for key in representative:
            applicable = [table for table in tables if table["scores"][key]]
            applicability[key] = {"min_months": applicable[0]["min_months"], "max_months": applicable[-1]["max_months"]}
        forms[code] = {"label": label, "scales": [
            {"code": key, "label": SUBDOMAINS[key], "max": entries[-1][1],
             "optional": key in {"cmg", "cmf"}, **applicability[key]}
            for key, entries in representative.items() if entries
        ]}
    return 200, {"forms": forms, "entry_modes": ["totals", "items"],
                 "item_protocol": domain_protocol.item_protocol(),
                 "legacy_item_protocol": item_protocol(), "technical_notes": TECHNICAL_NOTES}


@router.post("/submit", response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut}, auth=bearer_auth)
def submit(request, payload: Vineland3SubmitIn):
    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}
    evaluation = owned_evaluations(Evaluation.objects.select_related("patient"), request.auth).filter(pk=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}
    if not evaluation.patient.birth_date:
        return 400, {"message": "Informe a data de nascimento do paciente."}
    reference = get_reference_date(evaluation, payload.applied_on)
    if reference > date.today():
        return 400, {"message": "A aplicação não pode estar no futuro."}
    raw = payload.model_dump(exclude={"evaluation_id", "application_id", "applied_on", "finalize"})
    if "general_observations" not in payload.model_fields_set:
        raw.pop("general_observations", None)
    raw.update(birth_date=evaluation.patient.birth_date.isoformat(), reference_date=reference.isoformat())
    try:
        age_months(raw)
        if not payload.respondent.strip():
            raise ValueError("Identifique o respondente.")
        if payload.entry_mode == "items":
            if payload.item_protocol_id not in {PROTOCOL_ID, domain_protocol.PROTOCOL_ID}:
                raise ValueError("Identificador do banco de itens inválido.")
            if payload.form is not None or payload.raw_scores:
                raise ValueError("Registro item a item não pode ser associado às normas ou totais dos formulários extensivos.")
            if payload.item_protocol_id == domain_protocol.PROTOCOL_ID:
                raw["item_responses"] = domain_protocol.normalize_item_responses(payload.item_responses)
                raw.update(item_source=domain_protocol.SOURCE, item_pdf_source=domain_protocol.PDF_SOURCE,
                           edition_verified=True, scoring_enabled=False)
                raw["completion_status"] = "finalized" if payload.finalize else "partial"
                if payload.finalize:
                    raw["item_summary"] = domain_protocol.build_item_summary(raw["item_responses"])
                    raw["scoring_enabled"] = compute_domain_results(
                        raw["item_responses"], raw["birth_date"], raw["reference_date"])["normative_scoring"]
            else:
                if payload.finalize:
                    raise ValueError("O banco parcial legado não permite finalização. Preserve o protocolo original.")
                raw["item_responses"] = normalize_item_responses(payload.item_responses)
                raw.update(item_source=SOURCE, edition_verified=False, scoring_enabled=False)
            computed = {}
        else:
            if payload.item_protocol_id is not None:
                raise ValueError("O banco parcial não pode ser utilizado na correção normativa.")
            errors = validate_input(raw)
            if errors:
                raise ValueError("; ".join(errors))
            computed = compute_scores(raw)
    except ValueError as error:
        return 400, {"message": str(error)}
    ensure_required_instruments()
    instrument = Instrument.objects.filter(code="vineland3", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento Vineland-3 não encontrado ou inativo."}
    with transaction.atomic():
        if payload.application_id is not None:
            application = TestApplication.objects.select_for_update().filter(
                pk=payload.application_id, evaluation=evaluation, instrument=instrument,
            ).first()
            if not application:
                return 404, {"message": "Aplicação Vineland-3 não encontrada nesta avaliação."}
            if application.status == TestApplication.Status.LOCKED:
                return 403, {"message": "Esta aplicação está travada e não pode ser editada."}
            empty_application = _is_empty_application(application)
            if not empty_application and (application.raw_payload or {}).get("entry_mode", "totals") != payload.entry_mode:
                return 400, {"message": "Crie uma aplicação separada para mudar o modo de entrada; preserve o registro original."}
            if not empty_application and payload.entry_mode == "items" and ((application.raw_payload or {}).get("item_protocol_id") or PROTOCOL_ID) != payload.item_protocol_id:
                return 400, {"message": "Crie uma aplicação separada para usar outro banco de perguntas; preserve o protocolo original."}
            if "general_observations" not in payload.model_fields_set and "general_observations" in (application.raw_payload or {}):
                raw["general_observations"] = application.raw_payload["general_observations"]
        else:
            application = TestApplication(evaluation=evaluation, instrument=instrument)
        application.applied_on = reference
        application.raw_payload = raw
        application.computed_payload = computed
        application.classified_payload = {"classification_status": "pending_manual_verification"} if computed else {}
        application.interpretation_text = interpret_results(computed) if computed else ""
        application.reviewed_payload = {}
        application.is_validated = False
        application.save()
        AuditService.track_create(request, "test_application", str(application.pk), {
            "evaluation_id": evaluation.pk, "instrument": "vineland3", "edited": payload.application_id is not None,
            "entry_mode": payload.entry_mode,
            "finalized": payload.finalize,
        })
    return 200, {"application_id": application.pk, **serialize_test_application(application)}
