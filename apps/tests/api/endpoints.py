from ninja import Router, Query
from ninja.errors import HttpError
from django.http import HttpResponse
from django.utils.text import slugify

from apps.api.auth import bearer_auth
from apps.accounts.models import UserRole
from apps.evaluations.models import Evaluation
from apps.tests.models import Instrument
from apps.tests.age_rules import get_instrument_age_rule
from apps.tests.api.schemas import (
    BFPSubmitIn,
    EPQJSubmitIn,
    RAVLTSubmitIn,
    SRS2SubmitIn,
    SCAREDSubmitIn,
    BAISubmitIn,
    MCHATSubmitIn,
    WASISubmitIn,
)
from apps.tests.selectors import (
    get_instrument_by_id,
    get_instruments,
    get_test_application_by_id,
    get_test_applications,
    get_test_applications_by_evaluation,
)
from apps.tests.services import (
    create_test_application,
    update_test_application,
    TestScoringService,
    TestReportPayloadService,
)
from apps.tests.fdt.pdf_service import FDTPdfService
from apps.tests.services.pdf_export_service import TestPdfExportService
from apps.audit.services import AuditService
from datetime import date as date_cls
from dateutil.relativedelta import relativedelta


def get_reference_date(evaluation, applied_on=None):
    return (
        applied_on or evaluation.start_date or evaluation.end_date or date_cls.today()
    )


def calcAge(birth_date, reference_date=None):
    base_date = reference_date or date_cls.today()
    return relativedelta(base_date, birth_date).years


def calc_age_parts(birth_date, reference_date=None) -> dict[str, int]:
    delta = relativedelta(reference_date or date_cls.today(), birth_date)
    return {"anos": delta.years, "meses": delta.months}


def get_faixa_wisc(age):
    if 6 <= age <= 7:
        return "6-7 anos"
    elif 8 <= age <= 9:
        return "8-9 anos"
    elif 10 <= age <= 11:
        return "10-11 anos"
    elif 12 <= age <= 13:
        return "12-13 anos"
    elif 14 <= age <= 15:
        return "14-15 anos"
    elif age == 16:
        return "16 anos"
    return "6-7 anos"


def validate_instrument_age(evaluation, instrument):
    patient = evaluation.patient
    if not patient or not patient.birth_date:
        return None

    rules = get_instrument_age_rule(instrument.code)
    if not rules:
        return None

    age = calcAge(patient.birth_date, get_reference_date(evaluation))
    min_age = rules.get("min_age")
    max_age = rules.get("max_age")

    if min_age is not None and age < min_age:
        return rules["message"]
    if max_age is not None and age > max_age:
        return rules["message"]
    return None


from .schemas import (
    FDTSubmitIn,
    BPA2SubmitIn,
    EBADEPIJSubmitIn,
    EBADEPASubmitIn,
    ETDAHADSubmitIn,
    ETDAHPAISSubmitIn,
    CARS2HFSubmitIn,
    InstrumentOut,
    InstrumentCreateIn,
    InstrumentUpdateIn,
    TestApplicationOut,
    TestApplicationCreateIn,
    TestApplicationUpdateIn,
    MessageOut,
    WISC4SubmitIn,
    WAIS3SubmitIn,
    SCAREDSubmitIn,
)


router = Router(tags=["tests"])


def can_view_tests(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
        UserRole.REVIEWER,
        UserRole.READONLY,
    }


def can_edit_tests(user) -> bool:
    return bool(user) and user.role in {
        UserRole.ADMIN,
        UserRole.NEUROPSYCHOLOGIST,
        UserRole.ASSISTANT,
    }


WAIS3_SUBTEST_PAYLOAD_FIELDS = [
    "vocabulario",
    "semelhancas",
    "aritmetica",
    "digitos",
    "informacao",
    "compreensao",
    "sequencia_numeros_letras",
    "completar_figuras",
    "codigos",
    "cubos",
    "raciocinio_matricial",
    "arranjo_figuras",
    "procurar_simbolos",
    "armar_objetos",
]


WAIS3_PROCESS_PAYLOAD_FIELDS = [
    "digitos_ordem_direta",
    "digitos_ordem_inversa",
    "maior_sequencia_digitos_direta",
    "maior_sequencia_digitos_inversa",
]


def _optional_int(value, label: str) -> tuple[int | None, str | None]:
    if value in (None, ""):
        return None, None
    try:
        return int(value), None
    except (TypeError, ValueError):
        return None, f"{label}: informe um número inteiro válido."


def _build_wais3_raw_scores(payload: WAIS3SubmitIn, age_parts: dict[str, int]) -> tuple[dict, list[str]]:
    errors: list[str] = []
    subtestes = {}
    for field in WAIS3_SUBTEST_PAYLOAD_FIELDS:
        value, error = _optional_int(getattr(payload, field), field)
        if error:
            errors.append(error)
        elif value is not None:
            subtestes[field] = {"pontos_brutos": value}

    process_scores = {}
    for field in WAIS3_PROCESS_PAYLOAD_FIELDS:
        value, error = _optional_int(getattr(payload, field), field)
        if error:
            errors.append(error)
        elif value is not None:
            process_scores[field] = value

    return {
        "idade": age_parts,
        "subtestes": subtestes,
        "process_scores": process_scores,
    }, errors


def serialize_instrument(instrument):
    age_rule = get_instrument_age_rule(instrument.code) or {}
    descriptions = {
        "bfp": "Avalia traços de personalidade nos cinco grandes fatores e suas facetas.",
        "wasi": "Estimativa abreviada de inteligencia verbal, de execucao e global por quatro subtestes.",
        "scared": "Triagem de sintomas de ansiedade em crianças e adolescentes.",
        "ravlt": "Avalia aprendizagem verbal, evocação e memória episódica.",
        "srs2": "Mensura responsividade social e traços associados ao espectro autista.",
        "bai": "Inventário de sintomas de ansiedade com foco em intensidade e gravidade.",
        "cars2_hf": "Escala clínica para perfil autista em alto funcionamento, com foco em reciprocidade social, comunicação e flexibilidade.",
        "mchat": "Triagem precoce para sinais compatíveis com TEA em crianças de 18 a 24 meses.",
    }
    return {
        "id": instrument.id,
        "code": instrument.code,
        "name": instrument.name,
        "category": instrument.category,
        "version": instrument.version,
        "description": descriptions.get(instrument.code, ""),
        "is_active": instrument.is_active,
        "min_age": age_rule.get("min_age"),
        "max_age": age_rule.get("max_age"),
        "age_message": age_rule.get("message", ""),
    }


def serialize_test_application(application):
    patient = application.evaluation.patient if application.evaluation else None
    return {
        "id": application.id,
        "evaluation_id": application.evaluation_id,
        "patient_name": patient.full_name if patient else None,
        "patient_sex": patient.sex if patient else None,
        "patient_schooling": patient.schooling if patient else None,
        "instrument_id": application.instrument_id,
        "instrument_code": application.instrument.code,
        "instrument_name": application.instrument.name,
        "applied_on": application.applied_on,
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
        "reviewed_payload": application.reviewed_payload or {},
        "interpretation_text": application.interpretation_text or "",
        "report_payload": TestReportPayloadService.build_for_application(application),
        "is_validated": application.is_validated,
        "status": application.status,
        "status_display": application.get_status_display(),
    }


@router.get("/instruments", response=list[InstrumentOut], auth=bearer_auth)
def list_instruments(request) -> list[dict]:
    # Auto-seed essencial após reset de banco
    required = [
        {
            "code": "bfp",
            "name": "BFP - Bateria Fatorial de Personalidade",
            "category": "Personalidade",
        },
        {
            "code": "wasi",
            "name": "WASI - Escala Wechsler Abreviada de Inteligência",
            "category": "Inteligência",
        },
        {
            "code": "scared",
            "name": "SCARED - Screen for Child Anxiety",
            "category": "Ansiedade",
        },
        {"code": "ravlt", "name": "RAVLT - Memória Auditiva", "category": "Memoria"},
        {
            "code": "srs2",
            "name": "SRS-2 - Escala de Responsividade Social",
            "category": "Social / Autismo",
        },
        {
            "code": "bai",
            "name": "BAI - Inventário de Ansiedade de Beck",
            "category": "Ansiedade",
        },
        {
            "code": "cars2_hf",
            "name": "CARS2-HF - Childhood Autism Rating Scale – Second Edition, High Functioning Version",
            "category": "Social / Autismo",
        },
        {
            "code": "mchat",
            "name": "M-CHAT - Modified Checklist for Autism in Toddlers",
            "category": "Social / Autismo",
        },
    ]
    for item in required:
        Instrument.objects.get_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "category": item["category"],
                "is_active": True,
            },
        )

    return [serialize_instrument(item) for item in get_instruments()]


@router.post(
    "/instruments/", response={201: InstrumentOut, 403: MessageOut}, auth=bearer_auth
)
def create_instrument_endpoint(
    request, payload: InstrumentCreateIn
) -> tuple[int, dict]:
    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para criar instrumentos."}

    instrument = Instrument.objects.create(**payload.dict())
    return 201, serialize_instrument(instrument)


@router.patch(
    "/instruments/{instrument_id}",
    response={200: InstrumentOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_instrument_endpoint(
    request, instrument_id: int, payload: InstrumentUpdateIn
) -> tuple[int, dict]:
    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para editar instrumentos."}

    instrument = get_instrument_by_id(instrument_id)
    if not instrument:
        return 404, {"message": "Instrumento não encontrado."}

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(instrument, field, value)
    instrument.save()

    return 200, serialize_instrument(instrument)


@router.get("/applications", response=list[TestApplicationOut], auth=bearer_auth)
def list_test_applications(
    request, 
    evaluation_id: int | None = Query(default=None),
    instrument_code: str | None = Query(default=None),
) -> list[dict]:
    if not can_view_tests(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar aplicações de teste."
        )

    applications = (
        get_test_applications_by_evaluation(evaluation_id)
        if evaluation_id
        else get_test_applications()
    )
    
    if instrument_code:
        applications = applications.filter(instrument__code=instrument_code)
    
    return [serialize_test_application(item) for item in applications]


@router.get(
    "/applications/{application_id}",
    response={200: TestApplicationOut, 404: MessageOut},
    auth=bearer_auth,
)
def get_test_application_endpoint(request, application_id: int) -> tuple[int, dict]:
    if not can_view_tests(request.auth):
        raise HttpError(
            403, "Você não tem permissão para visualizar aplicações de teste."
        )

    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    return 200, serialize_test_application(application)


@router.post(
    "/applications",
    response={
        201: TestApplicationOut,
        400: MessageOut,
        403: MessageOut,
        404: MessageOut,
    },
    auth=bearer_auth,
)
def create_test_application_endpoint(
    request, payload: TestApplicationCreateIn
) -> tuple[int, dict]:
    if not can_edit_tests(request.auth):
        return 403, {
            "message": "Você não tem permissão para criar aplicações de teste."
        }

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    instrument = Instrument.objects.filter(
        id=payload.instrument_id, is_active=True
    ).first()
    if not instrument:
        return 404, {"message": "Instrumento não encontrado."}

    age_error = validate_instrument_age(evaluation, instrument)
    if age_error:
        return 400, {"message": age_error}

    application = create_test_application(
        evaluation=evaluation,
        instrument=instrument,
        applied_on=payload.applied_on,
        raw_payload=payload.raw_payload or {},
        reviewed_payload=payload.reviewed_payload or {},
        interpretation_text=payload.interpretation_text or "",
        is_validated=payload.is_validated,
        status=payload.status or None,
    )
    AuditService.track_create(
        request,
        "test_application",
        str(application.pk),
        {"evaluation_id": evaluation.id, "instrument": instrument.code},
    )
    return 201, serialize_test_application(application)


@router.patch(
    "/applications/{application_id}",
    response={200: TestApplicationOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def update_test_application_endpoint(
    request, application_id: int, payload: TestApplicationUpdateIn
) -> tuple[int, dict]:
    if not can_edit_tests(request.auth):
        return 403, {
            "message": "Você não tem permissão para editar aplicações de teste."
        }

    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    data = payload.dict(exclude_unset=True)

    if "evaluation_id" in data:
        evaluation = Evaluation.objects.filter(id=data["evaluation_id"]).first()
        if not evaluation:
            return 404, {"message": "Avaliação não encontrada."}
        data["evaluation"] = evaluation
        del data["evaluation_id"]

    if "instrument_id" in data:
        instrument = Instrument.objects.filter(
            id=data["instrument_id"], is_active=True
        ).first()
        if not instrument:
            return 404, {"message": "Instrumento não encontrado."}
        age_error = validate_instrument_age(application.evaluation, instrument)
        if age_error:
            return 400, {"message": age_error}
        data["instrument"] = instrument
        del data["instrument_id"]

    application = update_test_application(application, **data)
    AuditService.track_update(
        request,
        "test_application",
        str(application.pk),
        {},
        data,
    )
    return 200, serialize_test_application(application)


@router.delete(
    "/applications/{application_id}",
    response={200: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def delete_test_application_endpoint(request, application_id: int) -> tuple[int, dict]:
    if not can_edit_tests(request.auth):
        return 403, {
            "message": "Você não tem permissão para remover aplicações de teste."
        }

    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    AuditService.track_delete(
        request,
        "test_application",
        str(application.pk),
        {
            "evaluation_id": application.evaluation_id,
            "instrument": application.instrument.code,
        },
    )
    application.delete()
    return 200, {"message": "Teste removido com sucesso."}


@router.post(
    "/applications/{application_id}/process",
    response={
        200: TestApplicationOut,
        400: MessageOut,
        403: MessageOut,
        404: MessageOut,
    },
    auth=bearer_auth,
)
def process_test_application_endpoint(request, application_id: int) -> tuple[int, dict]:
    if not can_edit_tests(request.auth):
        return 403, {
            "message": "Você não tem permissão para processar aplicações de teste."
        }

    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    result = TestScoringService.process(application)
    if not result["ok"]:
        return 400, {"message": "; ".join(result["errors"])}

    application.refresh_from_db()
    AuditService.log(
        request,
        "process",
        "test_application",
        resource_id=str(application.pk),
        metadata={"instrument": application.instrument.code},
    )
    return 200, serialize_test_application(application)


@router.post(
    "/ebadep-a/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def ebadep_a_submit(request, payload: EBADEPASubmitIn) -> tuple[int, dict]:
    from datetime import date as date_cls
    from apps.tests.ebadep_a import EBADEPAModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.evaluations.models import Evaluation
    from apps.tests.base.types import TestContext

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = {}
    for i in range(1, 46):
        key = f"item_{i:02d}"
        raw_scores[key] = getattr(payload, key, 0)

    module = EBADEPAModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="ebadep_a",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="ebadep_a", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento EBADEP-A não encontrado."}

    reference_date = get_reference_date(
        evaluation, getattr(payload, "applied_on", None)
    )

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    items_criticos = classified.get("items_criticos", [])

    return 200, {
        "application_id": application.pk,
        "escore_total": classified.get("escore_total", 0),
        "percentil": classified.get("percentil", 0),
        "classificacao": classified.get("classificacao", ""),
        "sintese": classified.get("sintese", ""),
        "items_criticos": [d.get("item") for d in items_criticos],
        "interpretation": interpretation,
    }


@router.get(
    "/ebadep-a/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def ebadep_a_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    if application.instrument.code != "ebadep_a":
        return 404, {"message": "Aplicação não é do tipo EBADEP-A."}

    classified = application.classified_payload or {}
    items_criticos = classified.get("items_criticos", [])

    return 200, {
        "application_id": application.pk,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "escore_total": classified.get("escore_total", 0),
        "percentil": classified.get("percentil", 0),
        "classificacao": classified.get("classificacao", ""),
        "sintese": classified.get("sintese", ""),
        "items_criticos": [d.get("item") for d in items_criticos],
        "detalhe_itens": classified.get("result", {}).get("detalhe_itens", []),
        "interpretation": application.interpretation_text or "",
    }


# --- EBADEP-IJ ---


@router.post(
    "/ebadep-ij/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
@router.post(
    "/ebaped-ij/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def ebadep_ij_submit(request, payload: EBADEPIJSubmitIn) -> tuple[int, dict]:
    from datetime import date as date_cls
    from apps.tests.ebaped_ij import EBADEPIJModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.evaluations.models import Evaluation

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = {}
    for i in range(1, 28):
        key = f"item_{i:02d}"
        raw_scores[key] = getattr(payload, key, 0)

    module = EBADEPIJModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="ebadep_ij",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(
        code__in=["ebadep_ij", "ebaped_ij"], is_active=True
    ).first()
    if not instrument:
        return 404, {"message": "Instrumento EBADEP-IJ não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "pontuacao_total": classified.get("pontuacao_total", 0),
        "classificacao": classified.get("classificacao", ""),
        "sintese": classified.get("sintese", ""),
        "normas": classified.get("normas"),
        "interpretation": interpretation,
    }


@router.get(
    "/ebadep-ij/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
@router.get(
    "/ebaped-ij/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def ebadep_ij_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}
    if application.instrument.code not in {"ebadep_ij", "ebaped_ij"}:
        return 404, {"message": "Aplicação não é do tipo EBADEP-IJ."}

    classified = application.classified_payload or {}
    return 200, {
        "application_id": application.pk,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "pontuacao_total": classified.get("pontuacao_total", 0),
        "classificacao": classified.get("classificacao", ""),
        "sintese": classified.get("sintese", ""),
        "normas": classified.get("normas"),
        "items_criticos": [d.get("item") for d in classified.get("items_criticos", [])],
        "detalhe_itens": classified.get("result", {}).get("detalhe_itens", []),
        "interpretation": application.interpretation_text or "",
    }


# --- BPA-2 ---


# --- FDT ---


@router.post(
    "/fdt/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def fdt_submit(request, payload: FDTSubmitIn) -> tuple[int, dict]:
    from apps.tests.base.types import TestContext
    from apps.tests.fdt import FDTModule
    from apps.tests.models.applications import TestApplication
    from apps.tests.models.instruments import Instrument

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    patient = evaluation.patient
    if not patient.birth_date:
        return 400, {"message": "Paciente não tem data de nascimento."}

    reference_date = get_reference_date(evaluation, payload.applied_on)
    age = calcAge(patient.birth_date, reference_date)
    raw_scores = {
        "leitura": {"tempo": payload.leitura.tempo, "erros": payload.leitura.erros},
        "contagem": {"tempo": payload.contagem.tempo, "erros": payload.contagem.erros},
        "escolha": {"tempo": payload.escolha.tempo, "erros": payload.escolha.erros},
        "alternancia": {
            "tempo": payload.alternancia.tempo,
            "erros": payload.alternancia.erros,
        },
    }

    module = FDTModule()
    ctx = TestContext(
        patient_name=patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="fdt",
        raw_scores=raw_scores,
        reviewed_scores={"age": age},
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, classified)

    instrument = Instrument.objects.filter(code="fdt", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento FDT não encontrado."}

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "faixa": classified.get("faixa", ""),
        "idade": classified.get("idade", age),
        "metric_results": classified.get("metric_results", []),
        "derived_scores": classified.get("derived_scores", {}),
        "interpretation": interpretation,
    }


@router.get(
    "/applications/{application_id}/export-pdf",
    response={403: MessageOut, 404: MessageOut, 500: MessageOut},
    auth=bearer_auth,
)
def export_test_application_pdf(request, application_id: int, report_type: str = "summary"):
    if not can_view_tests(request.auth):
        return 403, {"message": "Você não tem permissão para visualizar testes."}

    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    try:
        payload = TestPdfExportService.build_pdf_bytes(application, report_type=report_type)
    except ValueError as exc:
        return 404, {"message": str(exc)}
    except Exception as exc:
        return 500, {"message": f"Erro ao exportar PDF: {exc}"}

    patient_name = application.evaluation.patient.full_name if application.evaluation_id else f"test-{application_id}"
    if application.instrument.code == "srs2" and report_type == "complete":
        suffix = "completo"
    elif application.instrument.code == "ebadep_a":
        suffix = "completo"
    else:
        suffix = "resumido"
    filename = f"{application.instrument.code.upper()}-{slugify(patient_name)}-{suffix}.pdf"
    response = HttpResponse(payload, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


@router.get(
    "/fdt/{application_id}/export-pdf",
    response={403: MessageOut, 404: MessageOut, 500: MessageOut},
    auth=bearer_auth,
)
def export_fdt_pdf(request, application_id: int):
    return export_test_application_pdf(request, application_id)


@router.post(
    "/bpa2/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def bpa2_submit(request, payload: BPA2SubmitIn) -> tuple[int, dict]:
    from datetime import date as date_cls
    from apps.tests.bpa2 import BPA2Module
    from apps.tests.base.types import TestContext
    from apps.tests.bpa2.calculators import get_age_group
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = {
        "ac": {
            "brutos": payload.ac.brutos,
            "erros": payload.ac.erros,
            "omissoes": payload.ac.omissoes,
        },
        "ad": {
            "brutos": payload.ad.brutos,
            "erros": payload.ad.erros,
            "omissoes": payload.ad.omissoes,
        },
        "aa": {
            "brutos": payload.aa.brutos,
            "erros": payload.aa.erros,
            "omissoes": payload.aa.omissoes,
        },
    }

    module = BPA2Module()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="bpa2",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    patient = evaluation.patient
    norm_type = payload.norm_type or "idade"

    if norm_type == "escolaridade":
        faixa = patient.schooling or "5 anos"
    else:
        if not patient.birth_date:
            faixa = "15-17 anos"
        else:
            eval_date = get_reference_date(evaluation, payload.applied_on)
            age = eval_date.year - patient.birth_date.year
            if (eval_date.month, eval_date.day) < (
                patient.birth_date.month,
                patient.birth_date.day,
            ):
                age -= 1
            faixa = get_age_group(age)

    computed = module.compute(ctx)
    classified = module.classify(computed, faixa=faixa)
    classified["faixa"] = faixa
    classified["norm_type"] = norm_type
    interpretation = module.interpret(ctx, classified)

    instrument = Instrument.objects.filter(code="bpa2", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento BPA-2 não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    ag = next(
        (s for s in classified.get("subtestes", []) if s.get("codigo") == "ag"), {}
    )

    return 200, {
        "application_id": application.pk,
        "subtestes": classified.get("subtestes", []),
        "pontos_fortes": classified.get("pontos_fortes", []),
        "pontos_fragilizados": classified.get("pontos_fragilizados", []),
        "faixa": faixa,
        "norm_type": norm_type,
        "ag_classificacao": ag.get("classificacao", ""),
        "interpretation": interpretation,
    }


@router.get(
    "/bpa2/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def bpa2_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}
    if application.instrument.code != "bpa2":
        return 404, {"message": "Aplicação não é do tipo BPA-2."}

    classified = application.classified_payload or {}
    ag = next(
        (s for s in classified.get("subtestes", []) if s.get("codigo") == "ag"), {}
    )

    return 200, {
        "application_id": application.pk,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "subtestes": classified.get("subtestes", []),
        "pontos_fortes": classified.get("pontos_fortes", []),
        "pontos_fragilizados": classified.get("pontos_fragilizados", []),
        "faixa": classified.get("faixa", ""),
        "norm_type": classified.get("norm_type", ""),
        "ag_classificacao": ag.get("classificacao", ""),
        "interpretation": application.interpretation_text or "",
    }


# --- WISC-IV ---


@router.post(
    "/wisc4/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def wisc4_submit(request, payload: WISC4SubmitIn) -> tuple[int, dict]:
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from datetime import timedelta

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    patient = evaluation.patient
    if not patient.birth_date:
        return 400, {"message": "Paciente não tem data de nascimento."}

    reference_date = get_reference_date(evaluation, payload.applied_on)
    age = calcAge(patient.birth_date, reference_date)

    # WISC-IV é indicado para pacientes de 6 anos até 16 anos e 11 meses
    today = reference_date
    max_age_date = patient.birth_date + timedelta(
        days=16 * 365 + 364
    )  # 16 anos e 364 dias
    min_age_date = patient.birth_date + timedelta(days=6 * 365)  # 6 anos

    if today < min_age_date:
        return 400, {"message": "WISC-IV é indicado para pacientes a partir de 6 anos."}
    if today > max_age_date:
        return 400, {
            "message": "WISC-IV é indicado para pacientes de até 16 anos e 11 meses."
        }
    raw_scores = {
        "cubos": int(payload.cb) if payload.cb else None,
        "semelhancas": int(payload.sm) if payload.sm else None,
        "digitos": int(payload.dg) if payload.dg else None,
        "conceitos": int(payload.cn) if payload.cn else None,
        "codigos": int(payload.cd) if payload.cd else None,
        "vocabulario": int(payload.vc) if payload.vc else None,
        "sequencias": int(payload.snl) if payload.snl else None,
        "matricial": int(payload.rm) if payload.rm else None,
        "compreensao": int(payload.co) if payload.co else None,
        "procura_simbolos": int(payload.ps) if payload.ps else None,
        "cf": int(payload.cf) if payload.cf else None,
        "ca": int(payload.ca) if payload.ca else None,
        "in": int(payload.in_) if payload.in_ else None,
        "ar": int(payload.ar) if payload.ar else None,
        "rp": int(payload.rp) if payload.rp else None,
        "cusb": int(payload.cusb) if payload.cusb else None,
        "diod": int(payload.diod) if payload.diod else None,
        "dioi": int(payload.dioi) if payload.dioi else None,
        "caa": int(payload.caa) if payload.caa else None,
        "cae": int(payload.cae) if payload.cae else None,
        "udiod": int(payload.udiod) if payload.udiod else None,
        "udioi": int(payload.udioi) if payload.udioi else None,
    }

    faixa = get_faixa_wisc(age)

    from apps.tests.wisc4 import WISC4Module
    from apps.tests.base.types import TestContext

    reviewed_scores = {
        "birth_date": str(patient.birth_date),
        "evaluation_date": str(reference_date),
        "confidence_level": "95",
    }

    ctx = TestContext(
        patient_name=patient.full_name,
        evaluation_id=evaluation.id,
        instrument_code="wisc4",
        raw_scores=raw_scores,
        reviewed_scores=reviewed_scores,
    )

    wisc_module = WISC4Module()
    computed = wisc_module.compute(ctx)
    classified = wisc_module.classify(computed, faixa="95")
    interpretation = wisc_module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="wisc4", is_active=True).first()
    if not instrument:
        instrument = Instrument.objects.filter(code="WISC-IV", is_active=True).first()
    if not instrument:
        instrument = Instrument.objects.filter(code="WISC-4", is_active=True).first()
    if not instrument:
        instrument = Instrument.objects.filter(
            code__icontains="wisc", is_active=True
        ).first()

    if not instrument:
        return 404, {"message": "Instrumento WISC-IV não encontrado."}

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.id,
        "age": age,
        "faixa": faixa,
        "scores": raw_scores,
         "classified": classified,
     }


@router.post(
    "/wais3/preview",
    response={200: dict, 400: MessageOut},
    auth=bearer_auth,
)
def wais3_preview(request, payload: WAIS3SubmitIn) -> tuple[int, dict]:
    """Preview WAIS-III results without saving to database.
    
    This endpoint is used for real-time preview as user types values.
    """
    from apps.evaluations.models import Evaluation
    
    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 400, {"message": "Avaliação não encontrada."}
    
    patient = evaluation.patient
    if not patient.birth_date:
        return 400, {"message": "Paciente não tem data de nascimento."}
    
    reference_date = get_reference_date(evaluation, payload.applied_on)
    age_parts = calc_age_parts(patient.birth_date, reference_date)
    age = age_parts["anos"]
    if age < 16 or age > 89:
        return 400, {"message": "WAIS-III é indicado para pacientes entre 16 e 89 anos."}
    raw_scores, input_errors = _build_wais3_raw_scores(payload, age_parts)
    if input_errors:
        return 400, {"message": "; ".join(input_errors)}

    from apps.tests.wais3 import WAIS3Module
    from apps.tests.wais3.classifiers import classify_wais3_payload

    wais3_module = WAIS3Module()
    errors = wais3_module.validate(TestContext(
        patient_name=patient.full_name,
        evaluation_id=evaluation.id,
        instrument_code="wais3",
        raw_scores=raw_scores,
    ))
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = wais3_module.compute(TestContext(
        patient_name=patient.full_name,
        evaluation_id=evaluation.id,
        instrument_code="wais3",
        raw_scores=raw_scores,
    ))
    classified = classify_wais3_payload(computed)
    
    return 200, {
        "age": age,
        "age_months": age_parts["meses"],
        "age_range": computed.get("idade_normativa"),
        "indices": computed.get("indices", {}),
        "subtestes": computed.get("subtestes", {}),
        "facilidades_dificuldades_tabela": computed.get("facilidades_dificuldades_tabela", {}),
        "discrepancias_tabela": computed.get("discrepancias_tabela", {}),
        "render_ready_tables": computed.get("render_ready_tables", {}),
        "digitos": computed.get("digitos", {}),
        "warnings": computed.get("warnings", []),
    }


@router.post(
    "/wais3/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def wais3_submit(request, payload: WAIS3SubmitIn) -> tuple[int, dict]:
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.tests.wais3 import WAIS3Module
    from apps.tests.base.types import TestContext

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    patient = evaluation.patient
    if not patient.birth_date:
        return 400, {"message": "Paciente não tem data de nascimento."}

    reference_date = get_reference_date(evaluation, payload.applied_on)
    age_parts = calc_age_parts(patient.birth_date, reference_date)
    age = age_parts["anos"]
    if age < 16 or age > 89:
        return 400, {"message": "WAIS-III é indicado para pacientes entre 16 e 89 anos."}

    raw_scores, input_errors = _build_wais3_raw_scores(payload, age_parts)
    if input_errors:
        return 400, {"message": "; ".join(input_errors)}

    ctx = TestContext(
        patient_name=patient.full_name,
        evaluation_id=evaluation.id,
        instrument_code="wais3",
        raw_scores=raw_scores,
        reviewed_scores={
            "birth_date": str(patient.birth_date),
            "evaluation_date": str(reference_date),
        },
    )

    wais3_module = WAIS3Module()
    errors = wais3_module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = wais3_module.compute(ctx)
    classified = wais3_module.classify(computed)
    interpretation = wais3_module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="wais3", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento WAIS-III não encontrado."}

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.id,
        "age": age,
        "scores": raw_scores,
        "classified": classified,
    }


# --- Generic Application Result ---


@router.get(
    "/applications/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def get_application_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    return 200, {
        "application_id": application.pk,
        "evaluation_id": application.evaluation_id,
        "patient_name": application.evaluation.patient.full_name,
        "patient_birth_date": application.evaluation.patient.birth_date,
        "patient_sex": application.evaluation.patient.sex,
        "patient_schooling": application.evaluation.patient.schooling,
        "instrument_code": application.instrument.code,
        "instrument_name": application.instrument.name,
        "applied_on": application.applied_on,
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
        "interpretation_text": application.interpretation_text or "",
        "is_validated": application.is_validated,
        "status": application.status,
        "status_display": application.get_status_display(),
        "report_payload": TestReportPayloadService.build_for_application(application),
    }


# --- EPQ-J ---


@router.post(
    "/bfp/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def bfp_submit(request, payload: BFPSubmitIn) -> tuple[int, dict]:
    from apps.tests.bfp import BFPModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    instrument = Instrument.objects.filter(code="bfp", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento BFP não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)
    raw_scores = {
        "sample": payload.sample or "geral",
        "responses": payload.responses,
    }

    module = BFPModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="bfp",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )
    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "computed_payload": computed,
        "classified_payload": classified,
        "interpretation_text": interpretation,
    }


@router.post(
    "/wasi/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def wasi_submit(request, payload: WASISubmitIn) -> tuple[int, dict]:
    from apps.tests.wasi import WASIModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}
    if not evaluation.patient or not evaluation.patient.birth_date:
        return 400, {"message": "A avaliação precisa ter data de nascimento do paciente para corrigir o WASI."}

    instrument = Instrument.objects.filter(code="wasi", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento WASI não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)
    raw_scores = {
        "vc": payload.vc,
        "sm": payload.sm,
        "cb": payload.cb,
        "rm": payload.rm,
        "birth_date": evaluation.patient.birth_date.isoformat(),
        "applied_on": reference_date.isoformat(),
        "confidence_level": payload.confidence_level or "95",
    }

    module = WASIModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="wasi",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )
    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "computed_payload": computed,
        "classified_payload": classified,
        "interpretation_text": interpretation,
    }


@router.post(
    "/epq-j/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def epq_j_submit(request, payload: EPQJSubmitIn) -> tuple[int, dict]:
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.tests.epq_j.calculators import (
        calcular_escore,
        obter_percentil_e_classificacao,
    )
    from datetime import date as date_cls

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    instrument = Instrument.objects.filter(code="epq_j", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento EPQ-J não encontrado."}

    raw_scores = {}
    for i in range(1, 61):
        key = f"item_{i:02d}"
        raw_scores[key] = getattr(payload, key, 0) or 0

    escores = calcular_escore(raw_scores)
    resultados = obter_percentil_e_classificacao(
        escores["P"], escores["E"], escores["N"], escores["S"], payload.sexo
    )

    reference_date = get_reference_date(evaluation, payload.applied_on)

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = {
        "escore_bruto": escores,
        "resultados": resultados,
        "sexo": payload.sexo,
    }
    application.classified_payload = {
        "fatores": resultados,
        "sexo": payload.sexo,
    }
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "escore_bruto": escores,
        "resultados": resultados,
    }


# --- ETDAH-AD ---


@router.post(
    "/etdah-ad/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def etdah_ad_submit(request, payload: ETDAHADSubmitIn) -> tuple[int, dict]:
    from datetime import date as date_cls
    from apps.tests.etdah_ad import ETDAHADModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.evaluations.models import Evaluation

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    patient = evaluation.patient
    examiner = evaluation.examiner
    reference_date = get_reference_date(evaluation, payload.applied_on)

    responses = {}
    for i in range(1, 70):
        key = f"item_{i:02d}"
        responses[i] = getattr(payload, key, 0)

    raw_scores = {
        "patient_id": patient.pk,
        "examiner_id": examiner.pk if examiner else None,
        "age": calcAge(patient.birth_date, reference_date) if patient.birth_date else 0,
        "schooling": patient.schooling or "elementary",
        "responses": responses,
    }

    module = ETDAHADModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="etdah_ad",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="etdah_ad", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento ETDAH-AD não encontrado."}

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    results = classified.get("results", {})

    return 200, {
        "application_id": application.pk,
        "raw_scores": classified.get("raw_scores", {}),
        "results": results,
        "interpretation": interpretation,
    }


@router.get(
    "/etdah-ad/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def etdah_ad_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    if application.instrument.code != "etdah_ad":
        return 404, {"message": "Aplicação não é do tipo ETDAH-AD."}

    classified = application.classified_payload or {}

    return 200, {
        "application_id": application.pk,
        "evaluation_id": application.evaluation_id,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "raw_scores": classified.get("raw_scores", {}),
        "results": classified.get("results", {}),
        "interpretation": application.interpretation_text or "",
        "interpretation_text": application.interpretation_text or "",
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
        "report_payload": TestReportPayloadService.build_for_application(application),
        "status": getattr(application, "status", None),
        "status_display": application.get_status_display(),
    }


# --- ETDAH-PAIS ---


@router.post(
    "/etdah-pais/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def etdah_pais_submit(request, payload: ETDAHPAISSubmitIn) -> tuple[int, dict]:
    from datetime import date as date_cls
    from apps.tests.etdah_pais import ETDAHPAISModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.evaluations.models import Evaluation

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    patient = evaluation.patient
    examiner = evaluation.examiner
    reference_date = get_reference_date(evaluation, payload.applied_on)

    responses = {}
    for i in range(1, 59):
        key = f"item_{i:02d}"
        responses[i] = getattr(payload, key, 0)

    raw_scores = {
        "patient_id": patient.pk,
        "examiner_id": examiner.pk if examiner else None,
        "age": calcAge(patient.birth_date, reference_date) if patient.birth_date else 0,
        "sex": payload.sex,
        "schooling": patient.schooling or "elementary",
        "responses": responses,
    }

    module = ETDAHPAISModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="etdah_pais",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="etdah_pais", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento ETDAH-PAIS não encontrado."}

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    results = classified.get("results", {})

    return 200, {
        "application_id": application.pk,
        "raw_scores": classified.get("raw_scores", {}),
        "results": results,
        "interpretation": interpretation,
    }


@router.get(
    "/etdah-pais/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def etdah_pais_result(request, application_id: int) -> tuple[int, dict]:
    from apps.tests.etdah_pais.interpreters import generate_report

    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    if application.instrument.code != "etdah_pais":
        return 404, {"message": "Aplicação não é do tipo ETDAH-PAIS."}

    classified = application.classified_payload or {}
    computed = application.computed_payload or {}
    interpretation = application.interpretation_text or ""

    if not interpretation:
        raw_scores = classified.get("raw_scores") or computed.get("raw_scores") or {}
        age = classified.get("age") or computed.get("age") or (application.raw_payload or {}).get("age")
        sex = classified.get("sex") or computed.get("sex") or (application.raw_payload or {}).get("sex")

        if raw_scores and age and sex:
            interpretation = generate_report(
                raw_scores,
                int(age),
                str(sex),
                patient_name=application.evaluation.patient.full_name,
            )
            application.interpretation_text = interpretation
            application.save(update_fields=["interpretation_text"])

    return 200, {
        "application_id": application.pk,
        "evaluation_id": application.evaluation_id,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "raw_scores": classified.get("raw_scores", {}),
        "results": classified.get("results", {}),
        "interpretation": interpretation,
        "interpretation_text": interpretation,
        "raw_payload": application.raw_payload or {},
        "computed_payload": computed,
        "classified_payload": application.classified_payload or {},
        "report_payload": TestReportPayloadService.build_for_application(application),
        "status": getattr(application, "status", None),
        "status_display": application.get_status_display(),
    }


# --- RAVLT ---


@router.post(
    "/ravlt/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def ravlt_submit(request, payload: RAVLTSubmitIn) -> tuple[int, dict]:
    from datetime import date as date_cls
    from apps.tests.ravlt import RAVLTModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.evaluations.models import Evaluation

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    patient = evaluation.patient
    examiner = evaluation.examiner
    reference_date = get_reference_date(evaluation, payload.applied_on)

    raw_scores = {
        "a1": int(payload.a1 or 0),
        "a2": int(payload.a2 or 0),
        "a3": int(payload.a3 or 0),
        "a4": int(payload.a4 or 0),
        "a5": int(payload.a5 or 0),
        "b": int(payload.b or 0),
        "a6": int(payload.a6 or 0),
        "a7": int(payload.a7 or 0),
        "reconhecimento": int(payload.reconhecimento or 0),
    }

    idade = 25
    try:
        if patient.birth_date and reference_date:
            anos = reference_date.year - patient.birth_date.year
            if (reference_date.month, reference_date.day) < (
                patient.birth_date.month,
                patient.birth_date.day,
            ):
                anos -= 1
            if anos > 0:
                idade = anos
    except Exception:
        idade = 25

    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="ravlt",
        raw_scores=raw_scores,
        patient_age=idade,
    )

    module = RAVLTModule()
    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed, idade=idade)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="ravlt", is_active=True).first()
    if not instrument:
        instrument = Instrument.objects.create(
            name="RAVLT",
            code="ravlt",
            is_active=True,
        )

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.id,
        "computed": computed,
        "classified": classified,
        "interpretation": interpretation,
    }


@router.get(
    "/ravlt/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def ravlt_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    if application.instrument.code != "ravlt":
        return 404, {"message": "Aplicação não é do tipo RAVLT."}

    classified = application.classified_payload or {}

    return 200, {
        "application_id": application.pk,
        "evaluation_id": application.evaluation_id,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "status": application.status,
        "status_display": application.get_status_display(),
        "report_payload": TestReportPayloadService.build_for_application(application),
        "results": classified,
        "interpretation": application.interpretation_text or "",
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
    }


@router.get(
    "/srs2/items",
    response={200: dict},
    # auth=bearer_auth,  # Temporarily disabled for testing
)
def srs2_get_items(request) -> tuple[int, dict]:
    import json
    import os

    items_file = os.path.join(os.path.dirname(__file__), "..", "srs2", "items.json")
    with open(items_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    forms = [
        "pre_escola",
        "idade_escolar",
        "adulto_autorrelato",
        "adulto_heterorrelato",
    ]
    result = {}
    for form in forms:
        items = data.get(form, [])
        result[form] = [
            {"item": i["item"], "fator": i["fator"], "pergunta": i.get("pergunta", "")}
            for i in items
        ]

    return 200, result


@router.post(
    "/srs2/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def srs2_submit(request, payload: SRS2SubmitIn) -> tuple[int, dict]:
    from apps.tests.srs2 import SRS2Module
    from apps.tests.base.types import TestContext
    from apps.tests.models.applications import TestApplication

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = {
        "form": payload.form,
        "gender": payload.gender,
        "age": payload.age,
        "respondent_name": payload.respondent_name,
        "responses": payload.responses or {},
    }

    patient = evaluation.patient
    age = payload.age
    if not age and patient.birth_date:
        eval_date = get_reference_date(evaluation, payload.applied_on)
        age = eval_date.year - patient.birth_date.year
        if (eval_date.month, eval_date.day) < (
            patient.birth_date.month,
            patient.birth_date.day,
        ):
            age -= 1

    module = SRS2Module()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="srs2",
        patient_age=age or 10,
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed, age=age or 10, gender=payload.gender or "M")
    interpretation = module.interpret(ctx, classified)

    instrument = Instrument.objects.filter(code="srs2", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento SRS-2 não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "computed": computed,
        "classified": classified,
        "interpretation": interpretation,
    }


@router.get(
    "/srs2/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def srs2_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    if application.instrument.code != "srs2":
        return 404, {"message": "Aplicação não é do tipo SRS-2."}

    classified = application.classified_payload or {}

    return 200, {
        "application_id": application.pk,
        "evaluation_id": application.evaluation_id,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "status": application.status,
        "status_display": application.get_status_display(),
        "report_payload": TestReportPayloadService.build_for_application(application),
        "results": classified,
        "interpretation": application.interpretation_text or "",
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
    }


# --- SCARED ---


@router.get(
    "/scared/items",
    response={200: dict, 403: MessageOut},
    auth=bearer_auth,
)
def scared_get_items(request) -> tuple[int, dict]:
    from apps.tests.scared.config import SCARED_FORMS, SCARED_ITEMS_BY_FORM

    if not can_view_tests(request.auth):
        return 403, {"message": "User not authorized"}

    result = {}
    for form_key, items in SCARED_ITEMS_BY_FORM.items():
        result[form_key] = {
            "label": SCARED_FORMS.get(form_key, form_key),
            "items": [
                {"item": item_number, "pergunta": question}
                for item_number, question in items.items()
            ],
        }

    return 200, result


@router.post(
    "/scared/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def scared_submit(request, payload: SCAREDSubmitIn) -> tuple[int, dict]:
    from apps.tests.scared import SCAREDModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.applications import TestApplication

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = {
        "form": payload.form,
        "gender": payload.gender,
        "age": payload.age,
        "responses": payload.responses or {},
    }

    patient = evaluation.patient
    idade = payload.age
    if not idade and patient.birth_date:
        reference_date = get_reference_date(evaluation, payload.applied_on)
        idade = calcAge(patient.birth_date, reference_date)

    module = SCAREDModule()
    ctx = TestContext(
        patient_name=patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="scared",
        patient_age=idade or 10,
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed, idade=idade or 10)
    interpretation = module.interpret(ctx, classified)

    instrument = Instrument.objects.filter(code="scared", is_active=True).first()
    if not instrument:
        instrument = Instrument.objects.create(
            name="SCARED",
            code="scared",
            is_active=True,
        )

    reference_date = get_reference_date(evaluation, payload.applied_on)

    if payload.application_id:
        application = TestApplication.objects.filter(
            pk=payload.application_id,
            evaluation=evaluation,
            instrument=instrument,
        ).first()
        if not application:
            return 404, {"message": "Aplicação SCARED não encontrada."}
    else:
        application = TestApplication(evaluation=evaluation, instrument=instrument)

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "computed": computed,
        "classified": classified,
        "interpretation": interpretation,
    }


@router.get(
    "/scared/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def scared_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    if application.instrument.code != "scared":
        return 404, {"message": "Aplicação não é do tipo SCARED."}

    classified = application.classified_payload or {}

    return 200, {
        "application_id": application.pk,
        "evaluation_id": application.evaluation_id,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "status": application.status,
        "status_display": application.get_status_display(),
        "report_payload": TestReportPayloadService.build_for_application(application),
        "results": classified,
        "interpretation": application.interpretation_text or "",
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
    }


# --- BAI ---


@router.post(
    "/bai/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def bai_submit(request, payload: BAISubmitIn) -> tuple[int, dict]:
    from apps.tests.bai import BAIModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.applications import TestApplication

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = {}
    for i in range(1, 22):
        key = f"item_{i:02d}"
        raw_scores[key] = getattr(payload, key, 0)

    module = BAIModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="bai",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="bai", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento BAI não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    classificacao = classified.get("classificacao") or {
        "raw": classified.get("classificacao_raw"),
        "t_score": classified.get("classificacao_t"),
        "label": classified.get("faixa_normativa", ""),
        "interpretation": classified.get("interpretacao_faixa", ""),
    }

    return 200, {
        "application_id": application.pk,
        "escore_total": classified.get("escore_total", 0),
        "classificacao": classificacao,
        "interpretation": interpretation,
    }


@router.get(
    "/bai/result/{application_id}",
    response={200: dict, 404: MessageOut},
    auth=bearer_auth,
)
def bai_result(request, application_id: int) -> tuple[int, dict]:
    application = get_test_application_by_id(application_id)
    if not application:
        return 404, {"message": "Aplicação de teste não encontrada."}

    if application.instrument.code != "bai":
        return 404, {"message": "Aplicação não é do tipo BAI."}

    classified = application.classified_payload or {}
    classificacao = classified.get("classificacao") or {
        "raw": classified.get("classificacao_raw"),
        "t_score": classified.get("classificacao_t"),
        "label": classified.get("faixa_normativa", ""),
        "interpretation": classified.get("interpretacao_faixa", ""),
    }

    return 200, {
        "application_id": application.pk,
        "evaluation_id": application.evaluation_id,
        "patient_name": application.evaluation.patient.full_name,
        "applied_on": application.applied_on,
        "status": application.status,
        "status_display": application.get_status_display(),
        "report_payload": TestReportPayloadService.build_for_application(application),
        "escore_total": classified.get("escore_total", 0),
        "classificacao": classificacao,
        "interpretation": application.interpretation_text or "",
        "raw_payload": application.raw_payload or {},
        "computed_payload": application.computed_payload or {},
        "classified_payload": application.classified_payload or {},
    }


# --- CARS2-HF ---


@router.post(
    "/cars2-hf/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def cars2_hf_submit(request, payload: CARS2HFSubmitIn) -> tuple[int, dict]:
    from apps.tests.cars2_hf import CARS2HFModule
    from apps.tests.base.types import TestContext
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.evaluations.models import Evaluation

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = payload.model_dump(exclude={"evaluation_id", "applied_on"})

    module = CARS2HFModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="CARS2_HF",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="cars2_hf", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento CARS2-HF não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)
    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "computed_payload": computed,
        "classified_payload": classified,
        "interpretation": interpretation,
    }


# --- M-CHAT ---


@router.post(
    "/mchat/submit",
    response={200: dict, 400: MessageOut, 403: MessageOut, 404: MessageOut},
    auth=bearer_auth,
)
def mchat_submit(request, payload: MCHATSubmitIn) -> tuple[int, dict]:
    from apps.tests.base.types import TestContext
    from apps.tests.mchat import MCHATModule
    from apps.tests.models.instruments import Instrument
    from apps.tests.models.applications import TestApplication
    from apps.evaluations.models import Evaluation

    if not can_edit_tests(request.auth):
        return 403, {"message": "Você não tem permissão para submeter testes."}

    evaluation = Evaluation.objects.filter(id=payload.evaluation_id).first()
    if not evaluation:
        return 404, {"message": "Avaliação não encontrada."}

    raw_scores = payload.model_dump(exclude={"evaluation_id", "applied_on"})

    module = MCHATModule()
    ctx = TestContext(
        patient_name=evaluation.patient.full_name,
        evaluation_id=evaluation.pk,
        instrument_code="MCHAT",
        raw_scores=raw_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return 400, {"message": "; ".join(errors)}

    computed = module.compute(ctx)
    classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    instrument = Instrument.objects.filter(code="mchat", is_active=True).first()
    if not instrument:
        return 404, {"message": "Instrumento M-CHAT não encontrado."}

    reference_date = get_reference_date(evaluation, payload.applied_on)

    application, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": reference_date},
    )

    application.raw_payload = raw_scores
    application.computed_payload = computed
    application.classified_payload = classified
    application.interpretation_text = interpretation
    application.is_validated = True
    application.applied_on = reference_date
    application.save()

    return 200, {
        "application_id": application.pk,
        "computed_payload": computed,
        "classified_payload": classified,
        "interpretation": interpretation,
    }
