from apps.tests.models import TestApplication
from apps.tests.base import TestContext
from apps.tests.registry import get_test_module
from apps.tests.services.report_payload_service import TestReportPayloadService


class TestScoringService:
    @staticmethod
    def process(application: TestApplication) -> dict:
        module = get_test_module(application.instrument.code)
        if not module:
            return {
                "ok": False,
                "errors": [f"Nenhum módulo registrado para {application.instrument.code}."],
            }

        raw_scores = application.raw_payload or {}
        if application.instrument.code == "vineland3":
            patient = application.evaluation.patient
            reference_date = application.applied_on or application.evaluation.start_date
            raw_scores = {
                **raw_scores,
                "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
                "reference_date": reference_date.isoformat() if reference_date else None,
            }
        context = TestContext(
            patient_name=application.evaluation.patient.full_name,
            evaluation_id=application.evaluation_id,
            instrument_code=application.instrument.code,
            patient_age=TestReportPayloadService._patient_age(application),
            raw_scores=raw_scores,
            reviewed_scores=application.reviewed_payload or {},
        )

        errors = module.validate(context)
        if errors:
            return {"ok": False, "errors": errors}

        computed = module.compute(context)
        classified = module.classify(computed)
        interpretation = module.interpret(context, {**computed, **classified})

        application.computed_payload = computed
        application.classified_payload = classified
        application.interpretation_text = interpretation
        application.save(
            update_fields=[
                "computed_payload",
                "classified_payload",
                "interpretation_text",
                "updated_at",
            ]
        )

        return {
            "ok": True,
            "computed_payload": computed,
            "classified_payload": classified,
            "interpretation_text": interpretation,
            "report_payload": TestReportPayloadService.build_for_application(application),
        }
