import json
from datetime import date, timedelta
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from ninja.testing import TestClient
from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from apps.accounts.models import hash_api_token
from apps.evaluations.models import Evaluation
from apps.patients.models import Patient
from apps.reports.api.specialist_endpoints import router
from apps.reports.models import Report, ReportSection, SpecialistRun
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_contracts import SpecialistOutput, validate_evidence
from apps.reports.services.specialist_errors import SpecialistGenerationError
from apps.reports.services.specialist_input_service import SpecialistInputService
from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.tests.models import Instrument, TestApplication


VALID_OUTPUT = {
    "findings": [{
        "statement": "O resultado informado foi 100, classificado na faixa Média.",
        "evidence_ids": ["/computed_payload/qi", "/classified_payload/classificacao"],
    }],
    "limitations": ["A interpretação requer revisão profissional e integração com anamnese."],
    "review_questions": [],
}


@override_settings(
    SPECIALIST_AI_ENABLED=True,
    SPECIALIST_AI_INSTRUMENTS=["wisc4", "scared"],
    SPECIALIST_AI_MODEL="test-model",
    AI_PROVIDER="openai",
    OPENAI_API_KEY="test-secret-not-real",
    OPENAI_BASE_URL="https://provider.example/v1",
)
class SpecialistRunTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="specialist-owner", email="specialist-owner@example.com", role="neuropsychologist",
            api_token_hash=hash_api_token("owner-test-token"),
        )
        self.other = get_user_model().objects.create_user(
            username="specialist-other", email="specialist-other@example.com", role="admin",
            api_token_hash=hash_api_token("other-test-token"),
        )
        self.patient = Patient.objects.create(
            full_name="Paciente Exemplo", birth_date=date(2018, 2, 21), mother_name="Mãe Exemplo", created_by=self.owner,
        )
        self.evaluation = Evaluation.objects.create(patient=self.patient, examiner=self.owner, start_date=date(2026, 10, 16))
        self.report = Report.objects.create(
            patient=self.patient, evaluation=self.evaluation, author=self.owner,
            context_payload={"old_snapshot": True}, edited_text="Texto revisado que deve ser preservado.",
        )
        self.section = ReportSection.objects.create(report=self.report, key="capacidade_cognitiva_global", content_edited="Revisão humana.")
        self.instrument, _ = Instrument.objects.get_or_create(code="wisc4", defaults={"name": "WISC-IV"})
        self.application = TestApplication.objects.create(
            evaluation=self.evaluation, instrument=self.instrument, is_validated=True,
            computed_payload={"qi": 100}, classified_payload={"classificacao": "Média"},
            raw_payload={"respondent_name": "Mãe Exemplo", "answers": [1, 2, 3]},
            interpretation_text="Texto antigo: QI 120.",
        )
        self.client = TestClient(router)
        self.headers = {"Authorization": "Bearer owner-test-token"}
        self.other_headers = {"Authorization": "Bearer other-test-token"}

    def enqueue(self, **kwargs):
        runs, _ = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk, **kwargs)
        return runs[0]

    @override_settings(SPECIALIST_AI_INSTRUMENTS=["wais3"])
    def test_full_wais3_can_be_enqueued_and_reviewed_without_changing_human_text(self):
        from apps.tests.wais3.calculators import compute_wais3_payload
        from apps.tests.wais3.classifiers import classify_wais3_payload
        from apps.tests.wais3.constants import WAIS3_SUBTEST_ORDER

        self.application.instrument, _ = Instrument.objects.get_or_create(code="wais3", defaults={"name": "WAIS-III"})
        self.application.computed_payload = compute_wais3_payload({
            "idade": {"anos": 30, "meses": 0},
            "subtestes": {key: {"pontos_brutos": 10} for key in WAIS3_SUBTEST_ORDER},
        })
        self.application.classified_payload = classify_wais3_payload(self.application.computed_payload)
        self.application.save()
        with patch.object(SpecialistAgentService, "generate") as generate:
            run = self.enqueue()
            generate.assert_not_called()
        self.assertLessEqual(len(run.input_payload["facts"]), 600)
        self.assertEqual(self.enqueue().pk, run.pk)

        def generator(queued):
            fact_id = "/computed_payload/indices/qi_total/pontuacao_composta"
            score = queued.input_payload["facts"][fact_id]
            return {
                "findings": [{"statement": f"O QI total informado foi {score}.", "evidence_ids": [fact_id]}],
                "limitations": ["Exige revisão profissional."], "review_questions": [],
            }, {}

        SpecialistRunService.process_next(generator=generator)
        run.refresh_from_db()
        self.assertEqual(run.status, SpecialistRun.Status.NEEDS_REVIEW)
        self.section.refresh_from_db()
        self.report.refresh_from_db()
        self.assertEqual(self.section.content_edited, "Revisão humana.")
        self.assertEqual(self.report.edited_text, "Texto revisado que deve ser preservado.")

    @staticmethod
    def valid_generator(run):
        return VALID_OUTPUT, {"input_tokens": 20, "output_tokens": 30, "requests": 1}

    def test_uses_current_database_results_without_mutating_report_or_section(self):
        run = self.enqueue()
        self.assertEqual(run.input_payload["facts"]["/computed_payload/qi"], 100)
        self.report.refresh_from_db()
        self.section.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(self.report.context_payload, {"old_snapshot": True})
        self.assertEqual(self.section.content_edited, "Revisão humana.")
        self.assertEqual(self.application.interpretation_text, "Texto antigo: QI 120.")

    def test_same_request_deduplicates_without_spending_again(self):
        run = self.enqueue()
        SpecialistRunService.process_next(generator=self.valid_generator)
        self.assertEqual(self.enqueue().pk, run.pk)
        self.assertEqual(SpecialistRun.objects.count(), 1)
        with patch.object(SpecialistAgentService, "generate") as generate:
            self.assertIsNone(SpecialistRunService.process_next())
            generate.assert_not_called()

    def test_recorrrection_creates_new_run_and_previous_is_stale(self):
        old = self.enqueue()
        self.application.computed_payload = {"qi": 110}
        self.application.save()
        new = self.enqueue()
        self.assertNotEqual(old.pk, new.pk)
        self.assertFalse(SpecialistRunService.is_current(SpecialistRunService._load(old.pk)))

    def test_changed_or_unvalidated_source_does_not_call_model(self):
        run = self.enqueue()
        self.application.is_validated = False
        self.application.save()
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next()
            self.assertEqual(result.pk, run.pk)
            self.assertEqual(result.status, "stale")
            generate.assert_not_called()

    def test_change_during_generation_marks_result_stale(self):
        self.enqueue()
        def change_during_call(run):
            TestApplication.objects.filter(pk=run.application_id).update(computed_payload={"qi": 110})
            return self.valid_generator(run)
        run = SpecialistRunService.process_next(generator=change_during_call)
        self.assertEqual(run.status, "stale")

    def test_success_requires_review_and_does_not_replace_approved_text(self):
        self.enqueue()
        run = SpecialistRunService.process_next(generator=self.valid_generator)
        self.assertEqual(run.status, "needs_review")
        self.assertEqual(run.usage_payload["requests"], 1)
        self.report.refresh_from_db()
        self.assertEqual(self.report.edited_text, "Texto revisado que deve ser preservado.")
        self.assertEqual(self.report.status, "draft")

    def test_provider_failure_is_not_approval_and_does_not_store_sensitive_error(self):
        self.enqueue()
        def fail(run):
            raise ValueError("secret credential and clinical information")
        run = SpecialistRunService.process_next(generator=fail)
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.error_code, "generation_failed")
        self.assertEqual(run.output_payload, {})
        self.assertNotIn("secret", json.dumps(run.usage_payload))

    def test_invalid_generator_output_is_not_saved_as_reviewable(self):
        self.enqueue()
        run = SpecialistRunService.process_next(generator=lambda run: ({"diagnosis": "invalid"}, {}))
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.output_payload, {})

    def test_interrupted_run_fails_without_automatic_requeue(self):
        run = self.enqueue()
        SpecialistRun.objects.filter(pk=run.pk).update(status="running", started_at=timezone.now() - timedelta(minutes=11))
        self.assertEqual(SpecialistRunService.recover_interrupted(), 1)
        run.refresh_from_db()
        self.assertEqual(run.error_code, "worker_interrupted")
        self.assertEqual(run.status, "failed")
        self.assertIsNone(SpecialistRunService.process_next(generator=self.valid_generator))

    def test_claim_is_exclusive_and_does_not_claim_running_job(self):
        run = self.enqueue()
        self.assertEqual(SpecialistRunService._claim(), run.pk)
        self.assertIsNone(SpecialistRunService._claim())

    def test_deleting_application_removes_draft_runs_without_blocking_legacy_delete(self):
        self.enqueue()
        self.application.delete()
        self.assertFalse(SpecialistRun.objects.exists())

    def test_deletion_during_generation_does_not_crash_worker(self):
        self.enqueue()
        def delete_during_call(run):
            TestApplication.objects.filter(pk=run.application_id).delete()
            return self.valid_generator(run)
        self.assertIsNone(SpecialistRunService.process_next(generator=delete_during_call))

    def test_one_execution_per_informant_application(self):
        scared, _ = Instrument.objects.get_or_create(code="scared", defaults={"name": "SCARED"})
        apps = [TestApplication.objects.create(
            evaluation=self.evaluation, instrument=scared, is_validated=True,
            computed_payload={"total": score}, raw_payload={"form": form},
        ) for form, score in (("parent", 10), ("self", 20))]
        runs, skipped = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)
        self.assertEqual(len(runs), 3)
        self.assertEqual(skipped, [])
        self.assertEqual({r.application_id for r in runs}, {self.application.pk, *(a.pk for a in apps)})

    def test_unsupported_instrument_is_explicitly_skipped(self):
        unsupported = Instrument.objects.create(code="not_configured", name="Outro")
        app = TestApplication.objects.create(evaluation=self.evaluation, instrument=unsupported, is_validated=True, computed_payload={"total": 10})
        runs, skipped = SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)
        self.assertEqual(len(runs), 1)
        self.assertEqual(skipped[0]["application_id"], app.pk)
        self.assertEqual(skipped[0]["reason"], "not_enabled")

    def test_foreign_application_cannot_be_requested(self):
        other_eval = Evaluation.objects.create(patient=self.patient, examiner=self.other)
        other_app = TestApplication.objects.create(evaluation=other_eval, instrument=self.instrument, is_validated=True)
        with self.assertRaises(ValueError):
            self.enqueue(application_ids=[other_app.pk])
        self.assertFalse(SpecialistRun.objects.exists())

    def test_api_is_private_even_for_other_admin_and_anonymous(self):
        path = f"/{self.report.pk}/specialist-runs"
        self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get(path, headers=self.other_headers).status_code, 404)
        self.assertEqual(self.client.post(path, json={}, headers=self.other_headers).status_code, 404)
        response = self.client.post(path, json={}, headers=self.headers)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(response.json()["run_ids"]), 1)
        self.assertEqual(self.client.get(path, headers=self.headers).json()[0]["status"], "queued")

    def test_api_marks_later_correction_as_stale_without_erasing_history(self):
        self.enqueue()
        SpecialistRunService.process_next(generator=self.valid_generator)
        TestApplication.objects.filter(pk=self.application.pk).update(computed_payload={"qi": 110})
        response = self.client.get(f"/{self.report.pk}/specialist-runs", headers=self.headers)
        self.assertEqual(response.json()[0]["status"], "stale")
        self.assertTrue(response.json()[0]["output"])

    def test_readonly_cannot_enqueue_even_own_report(self):
        self.owner.role = "readonly"
        self.owner.save()
        response = self.client.post(f"/{self.report.pk}/specialist-runs", json={}, headers=self.headers)
        self.assertEqual(response.status_code, 403)

    @override_settings(SPECIALIST_AI_ENABLED=False)
    def test_disabled_feature_does_not_queue(self):
        with self.assertRaises(ValueError):
            self.enqueue()
        self.assertFalse(SpecialistRun.objects.exists())

    @override_settings(SPECIALIST_AI_MODEL="")
    def test_explicit_model_required(self):
        with self.assertRaises(ValueError):
            self.enqueue()

    def test_finalized_report_cannot_be_regenerated(self):
        self.report.status = "finalized"
        self.report.save()
        with self.assertRaises(ValueError):
            self.enqueue()

    def test_report_finalized_after_enqueue_does_not_call_provider(self):
        self.enqueue()
        Report.objects.filter(pk=self.report.pk).update(status="finalized")
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next()
            self.assertEqual(result.error_code, "report_closed")
            generate.assert_not_called()

    def test_changed_provider_does_not_silently_receive_queued_data(self):
        self.enqueue()
        with override_settings(OPENAI_BASE_URL="https://different.example/v1"):
            with patch.object(SpecialistAgentService, "generate") as generate:
                result = SpecialistRunService.process_next()
                self.assertEqual(result.error_code, "configuration_changed")
                generate.assert_not_called()

    def test_role_revoked_after_enqueue_does_not_call_provider(self):
        self.enqueue()
        get_user_model().objects.filter(pk=self.owner.pk).update(role="readonly")
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next()
            self.assertEqual(result.error_code, "permission_revoked")
            generate.assert_not_called()

    @override_settings(OPENAI_BASE_URL="http://external.example/v1")
    def test_remote_unencrypted_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            self.enqueue()

    @override_settings(SPECIALIST_AI_INSTRUMENTS=[])
    def test_removing_instrument_permission_prevents_provider_call(self):
        with override_settings(SPECIALIST_AI_INSTRUMENTS=["wisc4"]):
            self.enqueue()
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next()
            self.assertEqual(result.error_code, "instrument_disabled")
            generate.assert_not_called()

    def test_worker_command_processes_once_without_clinical_logging(self):
        self.enqueue()
        output = StringIO()
        with patch.object(SpecialistAgentService, "generate", side_effect=self.valid_generator):
            call_command("run_specialist_worker", once=True, stdout=output)
        self.assertIn("status=needs_review", output.getvalue())
        self.assertNotIn(self.patient.full_name, output.getvalue())

    def test_input_excludes_identifiers_raw_answers_and_old_interpretation(self):
        self.application.computed_payload.update({"full_name": self.patient.full_name, "clinical_interpretation": "Texto antigo", "extra": "Mãe Exemplo"})
        payload = SpecialistInputService.build(self.application)
        text = json.dumps(payload, ensure_ascii=False)
        for excluded in (self.patient.full_name, "Mãe Exemplo", "Texto antigo", "answers", "2018-02-21"):
            self.assertNotIn(excluded, text)
        self.assertEqual(payload["facts"]["/application/age_months"], 103)

    def test_missing_results_fail_closed_and_transaction_rolls_back(self):
        self.application.computed_payload = {}
        self.application.classified_payload = {}
        self.application.save()
        with self.assertRaises(ValueError):
            self.enqueue()
        self.assertFalse(SpecialistRun.objects.exists())

    def test_real_pydanticai_agent_with_offline_function_model(self):
        run = self.enqueue()
        def respond(messages, info):
            self.assertNotIn(self.patient.full_name, str(messages))
            return ModelResponse(parts=[TextPart(json.dumps(VALID_OUTPUT))])
        with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False):
            output, usage = SpecialistAgentService.generate(run, model_override=FunctionModel(respond))
        self.assertEqual(output, VALID_OUTPUT)
        self.assertEqual(usage["requests"], 1)

    def test_agent_rejects_unknown_evidence_even_with_well_formed_json(self):
        run = self.enqueue()
        wrong = {**VALID_OUTPUT, "findings": [{"statement": "Resultado sem suporte suficiente.", "evidence_ids": ["/made_up"]}]}
        model = FunctionModel(lambda messages, info: ModelResponse(parts=[TextPart(json.dumps(wrong))]))
        with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False), self.assertRaises(SpecialistGenerationError) as caught:
            SpecialistAgentService.generate(run, model_override=model)
        self.assertEqual(caught.exception.code, "output_validation_failed")
        self.assertEqual(caught.exception.diagnostics["validation_code"], "evidence_not_found")

    def test_invalid_model_json_has_bounded_retry_and_never_becomes_text_fallback(self):
        run = self.enqueue()
        calls = []
        def respond(messages, info):
            calls.append(1)
            return ModelResponse(parts=[TextPart("Texto solto, sem contrato nem evidências.")])
        model = FunctionModel(respond)
        with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False), self.assertRaises(Exception):
            SpecialistAgentService.generate(run, model_override=model)
        self.assertLessEqual(len(calls), 2)


class SpecialistContractTests(SimpleTestCase):
    def test_extra_fields_and_missing_evidence_rejected(self):
        with self.assertRaises(ValidationError):
            SpecialistOutput.model_validate({**VALID_OUTPUT, "diagnosis": "invented"})
        with self.assertRaises(ValidationError):
            SpecialistOutput.model_validate({**VALID_OUTPUT, "findings": [{"statement": "Sem suporte clínico.", "evidence_ids": []}]})

    def test_ungrounded_numbers_rejected(self):
        output = SpecialistOutput.model_validate(VALID_OUTPUT)
        with self.assertRaises(ValueError):
            validate_evidence(output, {"/computed_payload/qi": 110, "/classified_payload/classificacao": "Média"})

    def test_current_numbers_are_accepted(self):
        validate_evidence(SpecialistOutput.model_validate(VALID_OUTPUT), {"/computed_payload/qi": 100, "/classified_payload/classificacao": "Média"})

    def test_instrument_number_is_not_confused_with_a_score(self):
        output = SpecialistOutput.model_validate({**VALID_OUTPUT, "findings": [{
            "statement": "Na SRS-2, o escore informado foi 100.", "evidence_ids": ["/score"],
        }]})
        validate_evidence(output, {"/score": 100}, "srs2")

    def test_negative_number_cannot_be_invented_from_positive_score(self):
        output = SpecialistOutput.model_validate({**VALID_OUTPUT, "findings": [{
            "statement": "O escore informado foi -100.", "evidence_ids": ["/score"],
        }]})
        with self.assertRaises(ValueError):
            validate_evidence(output, {"/score": 100})

    def test_limits_empty_results_and_identity_only_input(self):
        application = SimpleNamespace(
            evaluation=SimpleNamespace(patient=SimpleNamespace(full_name="Exemplo", mother_name="", father_name="", responsible_name="")),
            raw_payload={}, computed_payload={"full_name": "Exemplo"}, classified_payload={},
        )
        with self.assertRaises(ValueError):
            SpecialistInputService.build(application)
