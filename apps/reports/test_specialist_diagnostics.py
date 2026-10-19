import json
from io import StringIO
from unittest.mock import patch

import httpx2
from django.core.management import call_command
from django.test import TestCase, override_settings
from pydantic_ai.usage import RunUsage

from apps.reports import test_bpa2_specialist
from apps.reports.models import SpecialistRun
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_errors import SpecialistGenerationError, safe_diagnostics
from apps.reports.services.specialist_run_service import SpecialistRunService


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["bpa2"],
    SPECIALIST_AI_PROVIDER="ollama", SPECIALIST_AI_MODEL="qwen3.5:9b",
    SPECIALIST_OLLAMA_BASE_URL="http://127.0.0.1:11434/v1",
)
class SpecialistDiagnosticTests(TestCase):
    def setUp(self):
        test_bpa2_specialist.BPA2SpecialistWorkflowTests.setUp(self)

    def enqueue(self):
        return SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)[0][0]

    def mock_client(self, respond):
        def create(**kwargs):
            return httpx2.AsyncClient(transport=httpx2.MockTransport(respond), **kwargs)
        return patch("apps.reports.services.specialist_agent_service.DefaultAsyncHttpxClient", side_effect=create)

    @staticmethod
    def response(content, *, finish_reason="stop"):
        return httpx2.Response(200, json={
            "id": "synthetic", "object": "chat.completion", "created": 1, "model": "qwen3.5:9b",
            "choices": [{"index": 0, "finish_reason": finish_reason, "message": {
                "role": "assistant", "content": content,
            }}], "usage": {"prompt_tokens": 100, "completion_tokens": 300, "total_tokens": 400},
        })

    def test_two_http_200_responses_can_fail_semantic_validation_with_safe_reason(self):
        run = self.enqueue()
        invalid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid["findings"][4]["statement"] += " O subteste de Atenção Geral foi analisado."
        calls = []

        def respond(request):
            calls.append(1)
            return self.response(json.dumps(invalid))

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "output_validation_failed")
        self.assertEqual(result.usage_payload["validation_code"], "bpa2_semantics")
        self.assertEqual(result.usage_payload["requests"], 2)
        self.assertEqual(result.usage_payload["finish_reason"], "stop")
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.output_payload, {})

    def test_unknown_reference_retry_lists_exact_ids_and_can_recover(self):
        run = self.enqueue()
        valid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid = json.loads(json.dumps(valid))
        invalid["findings"][1]["evidence_ids"] = ["/reading_guide/ac/percentil"]
        calls = []

        def respond(request):
            body = json.loads(request.content)
            calls.append(body)
            if len(calls) == 2:
                correction = body["messages"][-1]["content"]
                self.assertIn("chaves EXATAS de facts", correction)
                self.assertIn("/computed_payload/ac/total", correction)
                self.assertIn("/classified_payload/subtestes/0/percentil", correction)
            return self.response(json.dumps(invalid if len(calls) == 1 else valid))

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "needs_review")
        self.assertEqual(result.output_payload, valid)
        self.assertEqual(result.usage_payload["requests"], 2)

    def test_missing_component_and_synthesis_evidence_retry_names_all_gaps(self):
        run = self.enqueue()
        valid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid = json.loads(json.dumps(valid))
        # Existing IDs, correct text/numbers; omissions are genuinely missing citations.
        invalid["findings"][1]["evidence_ids"].remove("/classified_payload/subtestes/0/classificacao")
        invalid["findings"][5]["evidence_ids"] = ["/classified_payload/subtestes/0/percentil"]
        calls = []

        def respond(request):
            body = json.loads(request.content)
            calls.append(body)
            if len(calls) == 2:
                correction = body["messages"][-1]["content"]
                self.assertIn('"ac"', correction)
                self.assertIn('"analise_clinica"', correction)
                self.assertIn("/classified_payload/subtestes/0/classificacao", correction)
                self.assertIn("/classified_payload/subtestes/3/percentil", correction)
                self.assertIn("/classified_payload/subtestes/3/classificacao", correction)
            return self.response(json.dumps(invalid if len(calls) == 1 else valid))

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "needs_review")
        self.assertEqual(result.output_payload, valid)
        self.assertEqual(len(calls), 2)

    def test_missing_synthesis_evidence_stays_blocked_and_records_only_safe_section(self):
        run = self.enqueue()
        invalid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid["findings"][5]["evidence_ids"] = ["/classified_payload/subtestes/0/percentil"]
        with self.mock_client(lambda request: self.response(json.dumps(invalid))):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.usage_payload["requests"], 2)
        self.assertEqual(result.usage_payload["validation_code"], "bpa2_missing_evidence")
        self.assertEqual(result.usage_payload["validation_section"], "analise_clinica")
        self.assertEqual(result.output_payload, {})
        self.assertNotIn("/classified_payload", json.dumps(result.usage_payload))
        self.assertNotIn("Os resultados", json.dumps(result.usage_payload))

    def test_later_schema_failure_does_not_inherit_section_from_missing_evidence(self):
        run = self.enqueue()
        invalid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid["findings"][5]["evidence_ids"] = ["/classified_payload/subtestes/0/percentil"]
        calls = []

        def respond(request):
            calls.append(1)
            return self.response(json.dumps(invalid) if len(calls) == 1 else "invalid-json")

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "output_schema_invalid")
        self.assertNotIn("validation_section", result.usage_payload)
        self.assertNotIn("validation_code", result.usage_payload)
        self.assertEqual(len(calls), 2)

    def test_repeated_unknown_references_remain_blocked_without_clinical_output(self):
        run = self.enqueue()
        invalid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        marker = "UNKNOWN-PRIVATE-REFERENCE"
        invalid["findings"][1]["evidence_ids"] = [marker]
        calls = []

        def respond(request):
            calls.append(1)
            return self.response(json.dumps(invalid))

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result.error_code, "output_validation_failed")
        self.assertEqual(result.usage_payload["validation_code"], "evidence_not_found")
        self.assertNotIn(marker, json.dumps(result.usage_payload))
        self.assertEqual(result.output_payload, {})

    def test_valid_looking_truncated_json_is_never_accepted(self):
        run = self.enqueue()
        valid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        with self.mock_client(lambda request: self.response(json.dumps(valid), finish_reason="length")):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "output_truncated")
        self.assertEqual(result.usage_payload["finish_reason"], "length")
        self.assertEqual(result.usage_payload["requests"], 1)
        self.assertEqual(result.output_payload, {})

    def test_truncated_partial_json_is_distinguished_from_schema_error(self):
        self.enqueue()
        with self.mock_client(lambda request: self.response('{"findings": [', finish_reason="length")):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "output_truncated")
        self.assertLessEqual(result.usage_payload["requests"], 2)
        self.assertEqual(result.output_payload, {})

    def test_filtered_response_cannot_pass_even_with_valid_looking_json(self):
        run = self.enqueue()
        valid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        with self.mock_client(lambda request: self.response(json.dumps(valid), finish_reason="content_filter")):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "provider_refusal")
        self.assertEqual(result.output_payload, {})

    def test_invalid_schema_does_not_persist_returned_clinical_text(self):
        self.enqueue()
        marker = "SENSITIVE-CLINICAL-CONTENT-AND-SECRET"
        with self.mock_client(lambda request: self.response(marker)):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "output_schema_invalid")
        self.assertEqual(result.usage_payload["requests"], 2)
        self.assertNotIn(marker, json.dumps(result.usage_payload))
        self.assertEqual(result.output_payload, {})

    def test_final_schema_failure_does_not_reuse_first_attempt_semantic_error(self):
        run = self.enqueue()
        invalid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid["findings"][1]["evidence_ids"] = ["/missing"]
        calls = []

        def respond(request):
            calls.append(1)
            return self.response(json.dumps(invalid) if len(calls) == 1 else "invalid-json")

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "output_schema_invalid")
        self.assertNotIn("validation_code", result.usage_payload)
        self.assertEqual(len(calls), 2)

    def test_provider_errors_are_classified_without_body_or_retries(self):
        for status, code in [(401, "provider_auth"), (429, "provider_rate_limit"), (503, "provider_error")]:
            with self.subTest(status=status), override_settings(SPECIALIST_AI_MODEL=f"synthetic-{status}"):
                self.enqueue()
                calls = []

                def respond(request):
                    calls.append(1)
                    return httpx2.Response(status, json={"error": {"message": "SECRET-CLINICAL-TEXT"}})

                with self.mock_client(respond):
                    result = SpecialistRunService.process_next(report_id=self.report.pk)
                self.assertEqual(result.error_code, code)
                self.assertEqual(len(calls), 1)
                self.assertNotIn("SECRET", json.dumps(result.usage_payload))
                self.assertEqual(result.output_payload, {})

    def test_local_timeout_is_distinguished_from_validation_failure(self):
        self.enqueue()

        def timeout(request):
            raise httpx2.ReadTimeout("SECRET-CLINICAL-TEXT", request=request)

        with self.mock_client(timeout):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "provider_timeout")
        self.assertEqual(result.output_payload, {})
        self.assertNotIn("SECRET", json.dumps(result.usage_payload))

    def test_network_error_on_retry_does_not_inherit_previous_validation_reason(self):
        run = self.enqueue()
        invalid = test_bpa2_specialist.synthetic_output(run.input_payload["facts"])
        invalid["findings"][1]["evidence_ids"] = ["/missing"]
        calls = []

        def respond(request):
            calls.append(1)
            if len(calls) == 1:
                return self.response(json.dumps(invalid))
            raise httpx2.ConnectError("SECRET-CLINICAL-TEXT", request=request)

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "provider_connection")
        self.assertNotIn("validation_code", result.usage_payload)
        self.assertNotIn("finish_reason", result.usage_payload)
        self.assertEqual(len(calls), 2)

    def test_worker_prints_safe_codes_and_does_not_repeat_failed_job(self):
        run = self.enqueue()
        failure = SpecialistGenerationError(
            "output_validation_failed", usage=RunUsage(requests=2),
            finish_reason="stop", validation_code="bpa2_missing_evidence", validation_section="analise_clinica",
        )
        stdout = StringIO()
        with patch.object(SpecialistAgentService, "generate", side_effect=failure) as generate:
            call_command("run_specialist_worker", once=True, report_id=self.report.pk, stdout=stdout)
            call_command("run_specialist_worker", once=True, report_id=self.report.pk, stdout=stdout)
        self.assertEqual(generate.call_count, 1)
        self.assertIn("error_code=output_validation_failed", stdout.getvalue())
        self.assertIn("validation_code=bpa2_missing_evidence", stdout.getvalue())
        self.assertIn("validation_section=analise_clinica", stdout.getvalue())
        self.assertNotIn(self.patient.full_name, stdout.getvalue())
        run.refresh_from_db()
        self.assertEqual(run.status, SpecialistRun.Status.FAILED)

    def test_unknown_exception_is_redacted(self):
        self.enqueue()
        stdout = StringIO()
        with patch.object(SpecialistAgentService, "generate", side_effect=RuntimeError("SECRET-CLINICAL-TEXT")):
            call_command("run_specialist_worker", once=True, report_id=self.report.pk, stdout=stdout)
        run = SpecialistRun.objects.get()
        self.assertEqual(run.error_code, "generation_failed")
        self.assertNotIn("SECRET", stdout.getvalue() + json.dumps(run.usage_payload))

    def test_diagnostic_fields_are_allowlisted(self):
        diagnostics = safe_diagnostics(
            RunUsage(requests=2, input_tokens=100, output_tokens=200),
            finish_reason="SECRET-CLINICAL-TEXT", validation_code="SECRET-CLINICAL-TEXT",
            validation_section="SECRET-CLINICAL-TEXT",
        )
        self.assertEqual(diagnostics, {"requests": 2, "input_tokens": 100, "output_tokens": 200})
        self.assertEqual(safe_diagnostics(validation_code="bpa2_missing_evidence", validation_section="SECRET"), {"validation_code": "bpa2_missing_evidence"})
        self.assertEqual(safe_diagnostics(validation_section="ac"), {})
