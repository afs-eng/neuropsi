from datetime import date
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from apps.patients.models import Patient
from apps.evaluations.models import Evaluation
from apps.tests.models.instruments import Instrument
from apps.tests.models.applications import TestApplication
from apps.tests.registry import get_test_module
from apps.tests.base.types import TestContext
from apps.tests.bpa2.interpreters import get_report_interpretation, get_synthesis
from apps.common.utils import get_param as _get_param


def _get_application(application_id):
    return get_object_or_404(
        TestApplication.objects.select_related(
            "evaluation", "evaluation__patient", "instrument"
        ),
        pk=application_id,
    )


def _get_existing_application(patient, instrument_code):
    existing_eval = Evaluation.objects.filter(
        patient=patient,
        test_applications__instrument__code=instrument_code,
        test_applications__is_validated=True,
    ).first()
    if existing_eval:
        return existing_eval.test_applications.filter(
            instrument__code=instrument_code, is_validated=True
        ).first(), existing_eval
    return None, None


def _get_reference_date(evaluation, evaluation_date=None):
    return (
        evaluation_date or evaluation.start_date or evaluation.end_date or date.today()
    )


def _calculate_age(birth_date, reference_date=None):
    base_date = reference_date or date.today()
    return base_date.year - birth_date.year - (
        (base_date.month, base_date.day) < (birth_date.month, birth_date.day)
    )


def _process_and_save_test(
    patient,
    evaluation,
    instrument_code,
    raw_scores,
    evaluation_date,
    extra_classify_kwargs=None,
):
    module = get_test_module(instrument_code)
    reviewed_scores = {}
    if hasattr(patient, "birth_date") and patient.birth_date:
        reviewed_scores["birth_date"] = str(patient.birth_date)
    reference_date = _get_reference_date(evaluation, evaluation_date)
    reviewed_scores["evaluation_date"] = str(reference_date)
    ctx = TestContext(
        patient_name=patient.full_name,
        evaluation_id=evaluation.pk if evaluation else 0,
        instrument_code=instrument_code,
        raw_scores=raw_scores,
        reviewed_scores=reviewed_scores,
    )

    errors = module.validate(ctx)
    if errors:
        return None, errors

    computed = module.compute(ctx)
    if extra_classify_kwargs:
        classified = module.classify(computed, **extra_classify_kwargs)
    else:
        classified = module.classify(computed)
    interpretation = module.interpret(ctx, {**computed, **classified})

    if not evaluation:
        evaluation, _ = Evaluation.objects.get_or_create(
            patient=patient,
            status="collecting_data",
            defaults={"referral_reason": "Avaliação neuropsicológica"},
        )

    instrument = Instrument.objects.get(code=instrument_code)
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

    return application, classified, interpretation


def test_list_view(request):
    return JsonResponse({"ok": True})


def apply_test_for_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    return JsonResponse({"patient_id": patient.id, "full_name": patient.full_name})


def add_test_to_evaluation(request, evaluation_id, instrument_code):
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    instrument = get_object_or_404(Instrument, code=instrument_code, is_active=True)

    app, _ = TestApplication.objects.get_or_create(
        evaluation=evaluation,
        instrument=instrument,
        defaults={"applied_on": _get_reference_date(evaluation)},
    )
    # For API mode return the created application id and a suggested next URL
    return JsonResponse(
        {
            "application_id": app.pk,
            "instrument_code": instrument_code,
            "next": f"/tests/{instrument_code}?application_id={app.pk}",
        },
        status=201,
    )


def test_result_view(request, application_id):
    application = _get_application(application_id)
    classified = application.classified_payload or {}
    data = {
        "patient_id": application.evaluation.patient.id,
        "evaluation_id": application.evaluation.id,
        "application_id": application.id,
        "evaluation_date": application.applied_on.isoformat()
        if application.applied_on
        else None,
        "classified": classified,
        "interpretation": application.interpretation_text or "",
        "raw_scores": application.raw_payload or {},
    }
    return JsonResponse(data)


def _item_form_view(
    request, application_id, instrument_code, item_count, form_template
):
    patients = Patient.objects.all()
    application = None
    evaluation = None

    if application_id:
        application = _get_application(application_id)
        evaluation = application.evaluation
        patients = Patient.objects.filter(pk=evaluation.patient.pk)

    if request.method == "POST":
        patient_id = _get_param(request, "patient")
        evaluation_date = _get_param(request, "evaluation_date")
        patient = get_object_or_404(Patient, pk=patient_id)

        existing_app, existing_eval = _get_existing_application(
            patient, instrument_code
        )
        if existing_app and not application:
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": [
                        f"Paciente já possui teste aplicado em {existing_app.applied_on.strftime('%d/%m/%Y')}."
                    ],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                    "existing_app": {
                        "id": existing_app.id,
                        "applied_on": existing_app.applied_on.isoformat()
                        if existing_app.applied_on
                        else None,
                    },
                },
                status=400,
            )

        raw_scores = {}
        for i in range(1, item_count + 1):
            key = f"item_{i:02d}"
            raw_value = _get_param(request, key)
            raw_scores[key] = (
                int(raw_value) if raw_value is not None and raw_value != "" else 0
            )

        result = _process_and_save_test(
            patient, evaluation, instrument_code, raw_scores, evaluation_date
        )
        if isinstance(result[1], list):
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": result[1],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                },
                status=400,
            )

        app_result, classified, interpretation = result
        return JsonResponse(
            {
                "patient": patient.id,
                "evaluation": evaluation.id if evaluation else None,
                "application": app_result.id,
                "evaluation_date": evaluation_date,
                "classified": classified,
                "interpretation": interpretation,
                "raw_scores": raw_scores,
            }
        )

    existing_data = (
        application.raw_payload if application and application.raw_payload else None
    )
    return JsonResponse(
        {
            "patients": [p.id for p in patients],
            "evaluation": evaluation.id if evaluation else None,
            "application": application.id if application else None,
            "existing_data": existing_data,
        }
    )


def ebadep_a_form_view(request, application_id=None):
    return _item_form_view(
        request, application_id, "ebadep_a", 45, "tests/ebadep_a_form.html"
    )


def ebaped_ij_form_view(request, application_id=None):
    return _item_form_view(
        request, application_id, "ebadep_ij", 27, "tests/ebaped_ij_form.html"
    )


def bpa2_form_view(request, application_id=None):
    patients = Patient.objects.all()
    application = None
    evaluation = None

    if application_id:
        application = _get_application(application_id)
        evaluation = application.evaluation
        patients = Patient.objects.filter(pk=evaluation.patient.pk)

    if request.method == "POST":
        patient_id = _get_param(request, "patient")
        evaluation_date = _get_param(request, "evaluation_date")
        norm_type = _get_param(request, "norm_type", "idade")
        patient = get_object_or_404(Patient, pk=patient_id)

        existing_app, existing_eval = _get_existing_application(patient, "bpa2")
        if existing_app and not application:
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": [
                        f"Paciente já possui BPA-2 aplicado em {existing_app.applied_on.strftime('%d/%m/%Y')}."
                    ],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                    "existing_app": {
                        "id": existing_app.id,
                        "applied_on": existing_app.applied_on.isoformat()
                        if existing_app.applied_on
                        else None,
                    },
                },
                status=400,
            )

        raw_scores = {}
        for code in ["ac", "ad", "aa"]:
            raw_scores[code] = {
                "brutos": int(_get_param(request, f"{code}_brutos", 0)),
                "erros": int(_get_param(request, f"{code}_erros", 0)),
                "omissoes": int(_get_param(request, f"{code}_omissoes", 0)),
            }

        faixa = _get_age_group(patient, evaluation_date, norm_type)
        result = _process_and_save_test(
            patient,
            evaluation,
            "bpa2",
            raw_scores,
            evaluation_date,
            extra_classify_kwargs={"faixa": faixa},
        )
        if isinstance(result[1], list):
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": result[1],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                },
                status=400,
            )

        app_result, classified, interpretation = result
        classified["faixa"] = faixa
        classified["norm_type"] = norm_type
    return JsonResponse(
        {
            "patient": patient.id,
            "evaluation": evaluation.id if evaluation else None,
            "application": app_result.id,
            "evaluation_date": evaluation_date,
            "norm_type": norm_type,
            "faixa": faixa,
            "classified": classified,
            "interpretation": interpretation,
            "raw_scores": raw_scores,
        }
    )

    existing_data = (
        application.raw_payload if application and application.raw_payload else None
    )
    return JsonResponse(
        {
            "patients": [p.id for p in patients],
            "evaluation": evaluation.id if evaluation else None,
            "application": application.id if application else None,
            "existing_data": existing_data,
        }
    )


def wisc4_form_view(request, application_id=None):
    patients = Patient.objects.all()
    application = None
    evaluation = None

    if application_id:
        application = _get_application(application_id)
        evaluation = application.evaluation
        patients = Patient.objects.filter(pk=evaluation.patient.pk)

    if request.method == "POST":
        patient_id = _get_param(request, "patient")
        evaluation_date = _get_param(request, "evaluation_date")
        patient = get_object_or_404(Patient, pk=patient_id)

        existing_app, existing_eval = _get_existing_application(patient, "wisc4")
        if existing_app and not application:
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": [
                        f"Paciente já possui WISC-IV aplicado em {existing_app.applied_on.strftime('%d/%m/%Y')}."
                    ],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                    "existing_app": {
                        "id": existing_app.id,
                        "applied_on": existing_app.applied_on.isoformat()
                        if existing_app.applied_on
                        else None,
                    },
                },
                status=400,
            )

        raw_scores = {}
        subtest_codes = [
            "cubos",
            "semelhancas",
            "digitos",
            "conceitos",
            "codigos",
            "vocabulario",
            "sequencias",
            "matricial",
            "compreensao",
            "procura_simbolos",
        ]
        for code in subtest_codes:
            raw_value = _get_param(request, code)
            raw_scores[code] = (
                int(raw_value) if raw_value is not None and raw_value != "" else 0
            )

        confidence_level = _get_param(request, "confidence_level", "95")

        result = _process_and_save_test(
            patient,
            evaluation,
            "wisc4",
            raw_scores,
            evaluation_date,
            extra_classify_kwargs={"faixa": confidence_level},
        )
        if isinstance(result[1], list):
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": result[1],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                },
                status=400,
            )

        app_result, classified, interpretation = result
        return JsonResponse(
            {
                "patient": patient.id,
                "evaluation": evaluation.id if evaluation else None,
                "application": app_result.id,
                "evaluation_date": evaluation_date,
                "classified": classified,
                "interpretation": interpretation,
                "raw_scores": raw_scores,
            }
        )

    existing_data = (
        application.raw_payload if application and application.raw_payload else None
    )
    return JsonResponse(
        {
            "patients": [p.id for p in patients],
            "evaluation": evaluation.id if evaluation else None,
            "application": application.id if application else None,
            "existing_data": existing_data,
        }
    )


def wais3_form_view(request, application_id=None):
    patients = Patient.objects.all()
    application = None
    evaluation = None

    if application_id:
        application = _get_application(application_id)
        evaluation = application.evaluation
        patients = Patient.objects.filter(pk=evaluation.patient.pk)

    if request.method == "POST":
        patient_id = _get_param(request, "patient")
        evaluation_date = _get_param(request, "evaluation_date")
        patient = get_object_or_404(Patient, pk=patient_id)

        existing_app, existing_eval = _get_existing_application(patient, "wais3")
        if existing_app and not application:
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": [
                        f"Paciente já possui WAIS-III aplicado em {existing_app.applied_on.strftime('%d/%m/%Y')}."
                    ],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                    "existing_app": {
                        "id": existing_app.id,
                        "applied_on": existing_app.applied_on.isoformat() if existing_app.applied_on else None,
                    },
                },
                status=400,
            )

        age = 0
        if patient.birth_date:
            age = _calculate_age(patient.birth_date, _get_reference_date(evaluation, evaluation_date))

        subtest_codes = [
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
        raw_scores = {"idade": {"anos": age, "meses": 0}, "subtestes": {}}
        for code in subtest_codes:
            raw_value = _get_param(request, code)
            if raw_value is not None and raw_value != "":
                raw_scores["subtestes"][code] = {"pontos_brutos": int(raw_value)}

        result = _process_and_save_test(
            patient,
            evaluation,
            "wais3",
            raw_scores,
            evaluation_date,
        )
        if isinstance(result[1], list):
            return JsonResponse(
                {
                    "patients": [p.id for p in patients],
                    "errors": result[1],
                    "evaluation": evaluation.id if evaluation else None,
                    "application": application.id if application else None,
                },
                status=400,
            )

        app_result, classified, interpretation = result
        return JsonResponse(
            {
                "patient": patient.id,
                "evaluation": evaluation.id if evaluation else None,
                "application": app_result.id,
                "evaluation_date": evaluation_date,
                "classified": classified,
                "interpretation": interpretation,
                "raw_scores": raw_scores,
            }
        )

    existing_data = application.raw_payload if application and application.raw_payload else None
    return JsonResponse(
        {
            "patients": [p.id for p in patients],
            "evaluation": evaluation.id if evaluation else None,
            "application": application.id if application else None,
            "existing_data": existing_data,
        }
    )


def bpa2_report_view(request, application_id):
    application = _get_application(application_id)
    patient = application.evaluation.patient
    classified = application.classified_payload or {}

    subtestes = []
    for st in classified.get("subtestes", []):
        code = st.get("codigo", "")
        classificacao = st.get("classificacao", "")
        badge_class = "badge-media"
        if "Superior" in classificacao and "Média" not in classificacao:
            badge_class = "badge-superior"
        elif "Média Superior" in classificacao:
            badge_class = "badge-media-sup"
        elif "Média Inferior" in classificacao:
            badge_class = "badge-media-inf"
        elif "Inferior" in classificacao and "Muito" not in classificacao:
            badge_class = "badge-inferior"
        elif "Muito Inferior" in classificacao:
            badge_class = "badge-muito-inf"

        subtestes.append(
            {
                **st,
                "badge_class": badge_class,
                "interpretacao_completa": get_report_interpretation(
                    code, classificacao, patient.full_name
                ),
            }
        )

    ag_st = next(
        (s for s in classified.get("subtestes", []) if s.get("codigo") == "ag"), {}
    )
    examiner = application.evaluation.examiner
    faixa = classified.get("faixa", "-")
    norm_type = classified.get("norm_type", "idade")

    return JsonResponse(
        {
            "patient": patient.id,
            "evaluation": application.evaluation.id,
            "application": application.id,
            "evaluation_date": application.applied_on.isoformat()
            if application.applied_on
            else None,
            "faixa": faixa,
            "referencia_normativa": f"Percentis - 2022 - {faixa}{' de escolaridade' if norm_type == 'escolaridade' else ''} - Brasil",
            "subtestes": subtestes,
            "ag_classificacao": ag_st.get("classificacao", "Média"),
            "sintese_atencional": get_synthesis(ag_st.get("classificacao", "Média")),
            "examiner_name": examiner.get_full_name() if examiner else "-",
            "raw_scores": application.raw_payload or {},
        }
    )


def ebaped_ij_report_view(request, application_id):
    application = _get_application(application_id)
    examiner = application.evaluation.examiner
    return JsonResponse(
        {
            "patient": application.evaluation.patient.id,
            "evaluation": application.evaluation.id,
            "application": application.id,
            "evaluation_date": application.applied_on.isoformat()
            if application.applied_on
            else None,
            "classified": application.classified_payload or {},
            "interpretation": application.interpretation_text or "",
            "examiner_name": examiner.get_full_name() if examiner else "-",
            "raw_scores": application.raw_payload or {},
        }
    )


def ebadep_a_report_view(request, application_id):
    application = _get_application(application_id)
    examiner = application.evaluation.examiner
    return JsonResponse(
        {
            "patient": application.evaluation.patient.id,
            "evaluation": application.evaluation.id,
            "application": application.id,
            "evaluation_date": application.applied_on.isoformat()
            if application.applied_on
            else None,
            "classified": application.classified_payload or {},
            "interpretation_text": application.interpretation_text or "",
            "examiner_name": examiner.get_full_name() if examiner else "-",
            "raw_scores": application.raw_payload or {},
        }
    )


def _get_age_group(patient, evaluation_date_str, norm_type):
    from apps.tests.bpa2.calculators import get_age_group

    if norm_type == "escolaridade":
        return patient.schooling or "5 anos"

    if not patient.birth_date:
        return "15-17 anos"

    try:
        eval_date = date.fromisoformat(evaluation_date_str)
    except (ValueError, TypeError):
        eval_date = date.today()

    age = eval_date.year - patient.birth_date.year
    if (eval_date.month, eval_date.day) < (
        patient.birth_date.month,
        patient.birth_date.day,
    ):
        age -= 1

    return get_age_group(age)
