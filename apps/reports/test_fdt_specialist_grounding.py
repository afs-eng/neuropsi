import copy
import json
from unittest.mock import patch

import httpx2
from django.test import SimpleTestCase, TestCase, override_settings

from apps.reports import test_specialist_runs
from apps.reports.models import SpecialistRun
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_contracts import SpecialistOutput, fdt_generation_model, validate_evidence
from apps.reports.services.specialist_input_service import SpecialistInputService
from apps.reports.services.fdt_specialist import fdt_reading_guide
from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.tests.fdt import FDTModule
from apps.tests.base.types import TestContext
from apps.tests.models import Instrument


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["fdt"],
    SPECIALIST_AI_PROVIDER="ollama", SPECIALIST_AI_MODEL="qwen3.5:9b-16k",
    SPECIALIST_OLLAMA_BASE_URL="http://127.0.0.1:11434/v1",
    OPENAI_API_KEY="external-key-must-not-be-used",
)
class FDTGroundingTests(TestCase):
    def setUp(self):
        test_specialist_runs.SpecialistRunTests.setUp(self)
        instrument, _ = Instrument.objects.get_or_create(code="fdt", defaults={"name": "FDT"})
        module = FDTModule()
        computed = module.compute(TestContext(
            patient_name=self.patient.full_name, evaluation_id=self.evaluation.pk, instrument_code="fdt",
            raw_scores={
                "leitura": {"tempo": 30, "erros": 0}, "contagem": {"tempo": 40, "erros": 1},
                "escolha": {"tempo": 60, "erros": 2}, "alternancia": {"tempo": 80, "erros": 3},
            }, reviewed_scores={"age": 8},
        ))
        self.application.instrument = instrument
        self.application.computed_payload = computed
        self.application.classified_payload = module.classify(computed)
        self.application.save()

    def enqueue(self):
        return SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)[0][0]

    def valid_output(self):
        return {
            "findings": [{
                "statement": "Na Leitura, o tempo informado foi 30. Esse dado descreve a etapa, sem inferência sobre funcionamento global.",
                "evidence_ids": ["/computed_payload/stage_totals/leitura/tempo"],
            }],
            "limitations": ["O instrumento isolado exige revisão profissional e integração com história clínica."],
            "review_questions": [],
        }

    def mock_client(self, respond):
        def create(**kwargs):
            self.assertFalse(kwargs["trust_env"])
            self.assertFalse(kwargs["follow_redirects"])
            return httpx2.AsyncClient(transport=httpx2.MockTransport(respond), **kwargs)
        return patch("apps.reports.services.specialist_agent_service.DefaultAsyncHttpxClient", side_effect=create)

    @staticmethod
    def response(data, finish_reason="stop"):
        return httpx2.Response(200, json={
            "id": "synthetic", "object": "chat.completion", "created": 1, "model": "qwen3.5:9b-16k",
            "choices": [{"index": 0, "finish_reason": finish_reason, "message": {
                "role": "assistant", "content": data if isinstance(data, str) else json.dumps(data),
            }}], "usage": {"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200},
        })

    def test_native_schema_exposes_only_actual_application_fact_ids(self):
        run = self.enqueue()
        requests = []

        def respond(request):
            body = json.loads(request.content)
            requests.append(body)
            self.assertEqual(request.headers["authorization"], "Bearer ollama-local")
            self.assertNotIn("external-key-must-not-be-used", str(request.headers))
            self.assertEqual(str(request.url), "http://127.0.0.1:11434/v1/chat/completions")
            self.assertEqual(body.get("max_tokens", body.get("max_completion_tokens")), 4000)
            return self.response(self.valid_output())

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "needs_review", (result.error_code, result.usage_payload))
        self.assertEqual(len(requests), 1)
        schema = requests[0]["response_format"]["json_schema"]["schema"]
        finding = schema["properties"]["findings"]["items"]
        if "$ref" in finding:
            finding = schema["$defs"][finding["$ref"].rsplit("/", 1)[1]]
        self.assertEqual(finding["properties"]["evidence_ids"]["items"]["enum"], sorted(run.input_payload["facts"]))

    def test_unknown_reference_gets_one_explicit_correction_without_rewriting_ids(self):
        self.enqueue()
        invalid = copy.deepcopy(self.valid_output())
        invalid["findings"][0]["evidence_ids"] = ["/leitura/tempo"]
        requests = []

        def respond(request):
            body = json.loads(request.content)
            requests.append(body)
            if len(requests) == 2:
                correction = body["messages"][-1]["content"]
                self.assertIn("chaves EXATAS de facts", correction)
                self.assertIn("/computed_payload/stage_totals/leitura/tempo", correction)
            return self.response(invalid if len(requests) == 1 else self.valid_output())

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "needs_review", (result.error_code, result.usage_payload))
        self.assertEqual(len(requests), 2)
        self.assertEqual(result.usage_payload["requests"], 2)
        self.assertEqual(result.output_payload, self.valid_output())

    def test_repeated_unknown_evidence_remains_terminal_without_persisting_private_reference(self):
        run = self.enqueue()
        invalid = copy.deepcopy(self.valid_output())
        marker = "PRIVATE-UNKNOWN-REFERENCE"
        invalid["findings"][0]["evidence_ids"] = [marker]
        requests = []

        def respond(request):
            requests.append(1)
            return self.response(invalid)

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_code, "output_validation_failed")
        self.assertEqual(result.usage_payload["validation_code"], "evidence_not_found")
        self.assertEqual(result.usage_payload["requests"], 2)
        self.assertEqual(result.output_payload, {})
        self.assertNotIn(marker, json.dumps(result.usage_payload))
        self.assertEqual(self.enqueue().pk, run.pk)
        with patch.object(SpecialistAgentService, "generate") as generate:
            self.assertIsNone(SpecialistRunService.process_next(report_id=self.report.pk))
            generate.assert_not_called()
        self.assertEqual(len(requests), 2)

    def test_terminal_schema_failure_does_not_reuse_previous_evidence_error(self):
        self.enqueue()
        invalid = copy.deepcopy(self.valid_output())
        invalid["findings"][0]["evidence_ids"] = ["/reading_guide/leitura"]
        requests = []

        def respond(request):
            requests.append(1)
            return self.response(invalid if len(requests) == 1 else "invalid-json")

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "output_schema_invalid")
        self.assertNotIn("validation_code", result.usage_payload)
        self.assertEqual(result.output_payload, {})
        self.assertEqual(len(requests), 2)

    def test_truncated_valid_looking_response_cannot_be_saved(self):
        self.enqueue()
        with self.mock_client(lambda request: self.response(self.valid_output(), finish_reason="length")):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "output_truncated")
        self.assertEqual(result.output_payload, {})
        self.assertEqual(result.usage_payload["requests"], 1)

    def test_unavailable_local_provider_never_falls_back_to_external_service(self):
        self.enqueue()
        requests = []

        def respond(request):
            requests.append(str(request.url))
            raise httpx2.ConnectError("synthetic local offline", request=request)

        with self.mock_client(respond):
            result = SpecialistRunService.process_next(report_id=self.report.pk)
        self.assertEqual(result.error_code, "provider_connection")
        self.assertEqual(requests, ["http://127.0.0.1:11434/v1/chat/completions"])

    def test_new_version_requires_explicit_request_without_replaying_old_failure(self):
        old = self.enqueue()
        old.specialist_version = "pydantic-specialist-1-ollama-4k"
        old.status = SpecialistRun.Status.FAILED
        old.error_code = "output_validation_failed"
        old.save()
        with patch.object(SpecialistAgentService, "generate") as generate:
            self.assertIsNone(SpecialistRunService.process_next(report_id=self.report.pk))
            generate.assert_not_called()
        new = self.enqueue()
        self.assertNotEqual(new.pk, old.pk)
        self.assertEqual(new.specialist_version, "pydantic-fdt-2-ollama-4k")
        old.refresh_from_db()
        self.assertEqual(old.status, "failed")
        self.assertEqual(old.error_code, "output_validation_failed")

    def test_old_pending_job_is_not_silently_processed_under_new_policy(self):
        old = self.enqueue()
        old.specialist_version = "pydantic-specialist-1-ollama-4k"
        old.save()
        with patch.object(SpecialistAgentService, "generate") as generate:
            result = SpecialistRunService.process_next(report_id=self.report.pk)
            generate.assert_not_called()
        self.assertEqual(result.status, "stale")

    def test_successes_from_previous_grounding_remain_reviewable_with_current_sources(self):
        run = self.enqueue()
        run.status = SpecialistRun.Status.NEEDS_REVIEW
        for version in ("pydantic-specialist-1", "pydantic-specialist-1-ollama-4k"):
            run.specialist_version = version
            self.assertTrue(SpecialistRunService.is_current(run))
        run.save(update_fields=["status", "specialist_version"])
        self.application.is_validated = False
        self.application.save()
        self.assertFalse(SpecialistRunService.is_current(SpecialistRunService._load(run.pk)))

    def test_guide_uses_real_metric_indices_and_preserves_values_and_human_content(self):
        original = copy.deepcopy(self.application.computed_payload)
        payload = SpecialistInputService.build(self.application)
        metrics = payload["reading_guide"]["metric_evidence_ids"]
        for index, row in enumerate(original["metric_results"]):
            self.assertIn(f"/computed_payload/metric_results/{index}/valor", metrics[row["codigo"]]["valor"])
        self.assertIn("/computed_payload/erros/leitura/qtde_erros", metrics["leitura"]["qtde_erros"])
        self.assertEqual(payload["facts"]["/computed_payload/stage_totals/leitura/erros"], 0)
        self.assertEqual(original, self.application.computed_payload)
        self.enqueue()
        with self.mock_client(lambda request: self.response(self.valid_output())):
            SpecialistRunService.process_next(report_id=self.report.pk)
        self.section.refresh_from_db()
        self.report.refresh_from_db()
        self.assertEqual(self.section.content_edited, "Revisão humana.")
        self.assertEqual(self.report.edited_text, "Texto revisado que deve ser preservado.")


class FDTReferenceContractTests(SimpleTestCase):
    def test_guide_never_guesses_metric_order_or_creates_missing_results(self):
        facts = {
            "/computed_payload/metric_results/8/codigo": "leitura",
            "/computed_payload/metric_results/8/valor": 30.0,
            "/computed_payload/metric_results/2/codigo": "inibicao",
            "/computed_payload/derived_scores/inibicao": 10.0,
        }
        guide = fdt_reading_guide(facts)["metric_evidence_ids"]
        self.assertEqual(guide["leitura"]["valor"], ["/computed_payload/metric_results/8/valor"])
        self.assertNotIn("classificacao", guide["leitura"])
        self.assertNotIn("flexibilidade", guide)
        self.assertEqual(fdt_reading_guide({}), {"metric_evidence_ids": {}})

    def test_schema_is_application_scoped_and_providers_cannot_bypass_validation(self):
        def ids(facts):
            return fdt_generation_model(facts).model_json_schema()["$defs"]["FDTGroundedFinding"]["properties"]["evidence_ids"]["items"]["enum"]
        self.assertEqual(ids({"/first": 1}), ["/first"])
        self.assertEqual(ids({"/second": 2}), ["/second"])
        with self.assertRaises(ValueError):
            fdt_generation_model({})
        data = {"findings": [{"statement": "Achado sem referência válida.", "evidence_ids": ["/invalid"]}], "limitations": ["Necessita revisão profissional."]}
        output = fdt_generation_model({"/valid": 1}).model_validate(data)
        with self.assertRaises(ValueError):
            validate_evidence(output, {"/valid": 1}, "fdt")

    def test_numeric_display_equivalence_is_valid_but_changed_or_negative_scores_are_not(self):
        for value, text in ((30.0, "30"), (30.5, "30,5"), (0.0, "0")):
            output = SpecialistOutput.model_validate({
                "findings": [{"statement": f"O tempo informado foi {text} segundos.", "evidence_ids": ["/time"]}],
                "limitations": ["Exige revisão profissional."],
            })
            validate_evidence(output, {"/time": value}, "fdt")
            for wrong in (-value if value else 1, value + 0.01):
                with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                    validate_evidence(output, {"/time": wrong}, "fdt")
