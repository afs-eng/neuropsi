import copy
import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RequestUsage

from apps.reports import test_bpa2_specialist
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_errors import SpecialistGenerationError
from apps.reports.services.specialist_run_service import SpecialistRunService


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["bpa2"],
    SPECIALIST_AI_PROVIDER="openai", AI_PROVIDER="openai", OPENAI_API_KEY="not-real",
    SPECIALIST_AI_MODEL="offline-model", OPENAI_BASE_URL="https://offline.example/v1",
    SPECIALIST_OLLAMA_BASE_URL="http://127.0.0.1:11434/v1",
)
class SpecialistTokenLimitTests(TestCase):
    def setUp(self):
        test_bpa2_specialist.BPA2SpecialistWorkflowTests.setUp(self)

    def enqueue(self):
        return SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)[0][0]

    def generate_with_retry(self, run, tokens_per_response, calls):
        valid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid = copy.deepcopy(valid)
        invalid["findings"][4]["statement"] += " O subteste de Atenção Geral foi analisado."

        def respond(messages, info):
            calls.append(info.model_settings["max_tokens"])
            return ModelResponse(
                parts=[TextPart(json.dumps(invalid if len(calls) == 1 else valid))],
                usage=RequestUsage(input_tokens=100, output_tokens=tokens_per_response),
                finish_reason="stop",
            )

        with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False):
            return SpecialistAgentService.generate(run, model_override=FunctionModel(respond))

    @override_settings(SPECIALIST_AI_PROVIDER="ollama")
    def test_local_allows_two_responses_totaling_more_than_old_budget(self):
        run = self.enqueue()
        calls = []
        output, usage = self.generate_with_retry(run, 2500, calls)
        self.assertEqual(calls, [4000, 4000])
        self.assertEqual(usage["output_tokens"], 5000)
        self.assertEqual(usage["requests"], 2)
        self.assertEqual(len(output["findings"]), 6)

    def test_external_request_and_total_limits_are_not_increased(self):
        run = self.enqueue()
        calls = []
        with self.assertRaises(SpecialistGenerationError) as caught:
            self.generate_with_retry(run, 2500, calls)
        self.assertEqual(calls, [2000, 2000])
        self.assertEqual(caught.exception.code, "usage_limit_exceeded")

    @override_settings(SPECIALIST_AI_PROVIDER="ollama")
    def test_local_still_rejects_total_above_eight_thousand(self):
        run = self.enqueue()
        calls = []
        with self.assertRaises(SpecialistGenerationError) as caught:
            self.generate_with_retry(run, 4500, calls)
        self.assertEqual(caught.exception.code, "usage_limit_exceeded")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls, [4000, 4000])

    @override_settings(SPECIALIST_AI_PROVIDER="ollama")
    def test_new_policy_creates_new_run_without_reactivating_old_failure(self):
        old = self.enqueue()
        old.specialist_version = SpecialistRunService.version_for("bpa2", "openai")
        old.status, old.error_code = "failed", "output_truncated"
        old.save(update_fields=["specialist_version", "status", "error_code"])
        current = self.enqueue()
        self.assertNotEqual(current.pk, old.pk)
        self.assertTrue(current.specialist_version.endswith("-ollama-4k"))
        self.assertEqual(self.enqueue().pk, current.pk)
        old.refresh_from_db()
        self.assertEqual(old.status, "failed")
        self.assertEqual(old.error_code, "output_truncated")

    @override_settings(SPECIALIST_AI_PROVIDER="ollama")
    def test_old_valid_output_remains_current_under_same_clinical_contract(self):
        old = self.enqueue()
        old.specialist_version = SpecialistRunService.version_for("bpa2", "openai")
        old.status = "needs_review"
        old.output_payload = test_bpa2_specialist.synthetic_output(old.input_payload["facts"])
        old.save(update_fields=["specialist_version", "status", "output_payload"])
        self.assertTrue(SpecialistRunService.is_current(old))
        current = self.enqueue()
        self.assertNotEqual(current.pk, old.pk)
        old.refresh_from_db()
        self.assertTrue(SpecialistRunService.is_current(old))
        self.assertEqual(old.output_payload["findings"][0]["section"], "introducao")
        old.specialist_version = "pydantic-bpa2-2"
        self.assertFalse(SpecialistRunService.is_current(old))

    @override_settings(SPECIALIST_AI_PROVIDER="ollama")
    def test_old_queued_job_does_not_silently_use_new_budget(self):
        old = self.enqueue()
        old.specialist_version = SpecialistRunService.version_for("bpa2", "openai")
        old.save(update_fields=["specialist_version"])
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "stale")
        generate.assert_not_called()

    def test_external_version_is_unchanged_and_not_dependent_on_local_provider_setting(self):
        run = self.enqueue()
        self.assertFalse(run.specialist_version.endswith("-ollama-4k"))
        with override_settings(SPECIALIST_AI_PROVIDER="ollama"):
            self.assertTrue(SpecialistRunService.is_current(run))
