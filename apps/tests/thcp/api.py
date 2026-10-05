from django.db import transaction
from ninja import Router

from apps.api.auth import bearer_auth
from apps.evaluations.models import Evaluation
from apps.tests.api.age_utils import calcAge, get_reference_date
from apps.tests.api.catalog import ensure_required_instruments
from apps.tests.api.permissions import can_edit_tests, can_view_tests
from apps.tests.api.schemas import MessageOut, THCPSubmitIn
from apps.tests.api.serializers import serialize_test_application
from apps.tests.base.types import TestContext
from apps.tests.models import Instrument, TestApplication
from apps.tests.selectors import get_test_application_by_id
from apps.audit.services import AuditService

from . import THCPModule

router = Router(tags=["tests"])


@router.post("/submit", response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut}, auth=bearer_auth)
def thcp_submit(request, payload: THCPSubmitIn) -> tuple[int, dict]:
    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}
    evaluation = Evaluation.objects.select_related("patient").filter(pk=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}
    patient = evaluation.patient
    if not patient.birth_date:
        return 400, {"message": "Informe a data de nascimento do paciente para corrigir o THCP."}
    reference_date = get_reference_date(evaluation, payload.applied_on)
    raw = payload.model_dump(exclude={"evaluation_id", "application_id", "applied_on"})
    context = TestContext(
        patient_name=patient.full_name, evaluation_id=evaluation.pk, instrument_code="thcp",
        patient_age=calcAge(patient.birth_date, reference_date), raw_scores=raw,
    )
    module = THCPModule()
    errors = module.validate(context)
    if errors:
        return 400, {"message": "; ".join(errors)}
    ensure_required_instruments()
    instrument = Instrument.objects.filter(code="thcp", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento THCP não encontrado ou inativo."}
    computed = module.compute(context)
    classified = module.classify(computed)
    interpretation = module.interpret(context, {**computed, **classified})
    with transaction.atomic():
        if payload.application_id is not None:
            application = TestApplication.objects.select_for_update().filter(
                pk=payload.application_id, evaluation=evaluation, instrument=instrument,
            ).first()
            if not application:
                return 404, {"message": "Aplicação THCP não encontrada nesta avaliação."}
            if application.status == TestApplication.Status.LOCKED:
                return 403, {"message": "Esta aplicação está travada e não pode ser editada."}
        else:
            application = TestApplication(evaluation=evaluation, instrument=instrument)
        application.applied_on = reference_date
        application.raw_payload = raw
        application.computed_payload = computed
        application.classified_payload = classified
        application.interpretation_text = interpretation
        application.reviewed_payload = {}
        application.is_validated = True
        application.save()
        AuditService.track_create(
            request, "test_application", str(application.pk),
            {"evaluation_id": evaluation.pk, "instrument": "thcp", "edited": payload.application_id is not None},
        )
    return 200, {"application_id": application.pk, **serialize_test_application(application)}


@router.get("/result/{application_id}", response={200: dict, 403: MessageOut, 404: MessageOut}, auth=bearer_auth)
def thcp_result(request, application_id: int) -> tuple[int, dict]:
    if not can_view_tests(request.auth):
        return 403, {"message": "Você não tem permissão para visualizar testes."}
    application = get_test_application_by_id(application_id)
    if not application or application.instrument.code != "thcp":
        return 404, {"message": "Aplicação THCP não encontrada."}
    return 200, {"application_id": application.pk, **serialize_test_application(application)}
