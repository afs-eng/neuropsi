import copy
import json
from unittest.mock import patch

import httpx2
from django.test import SimpleTestCase, TestCase, override_settings
from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from apps.reports import test_specialist_runs
from apps.reports.models import SpecialistReview, SpecialistRun
from apps.reports.services.bpa2_specialist import BPA2_INSTRUCTIONS, BPA2_VERSION, bpa2_reading_guide
from apps.reports.services.specialist_agent_service import SpecialistAgentService
from apps.reports.services.specialist_contracts import BPA2SpecialistOutput, validate_evidence
from apps.reports.services.specialist_input_service import SpecialistInputService
from apps.reports.services.specialist_review_service import SpecialistReviewService
from apps.reports.services.specialist_run_service import SpecialistRunService
from apps.tests.models import Instrument


CODES = ("ac", "ad", "aa", "ag")
MIXED = [(62, 10, "Inferior"), (85, 60, "Média"), (86, 40, "Média"), (233, 30, "Média Inferior")]
AVERAGE = [(75, 40, "Média"), (79, 60, "Média"), (88, 50, "Média"), (242, 50, "Média")]


def synthetic_facts(profile=MIXED):
    facts = {}
    for index, (code, (score, percentile, classification)) in enumerate(zip(CODES, profile)):
        facts[f"/computed_payload/{code}/total"] = score
        for field, value in {"codigo": code, "total": score, "percentil": percentile, "classificacao": classification}.items():
            facts[f"/classified_payload/subtestes/{index}/{field}"] = value
    return facts


def synthetic_output(facts):
    guide = bpa2_reading_guide(facts)["component_evidence_ids"]
    findings = [{
        "section": "introducao", "statement": "A BPA-2 investiga atenção concentrada, dividida e alternada, com medida agregada de atenção geral.",
        "evidence_ids": [guide["ac"]["escore_pontos"]],
    }]
    for code in CODES:
        refs = guide[code]
        score, percentile, classification = (facts[refs[key]] for key in ("escore_pontos", "percentil", "classificacao"))
        findings.append({
            "section": code,
            "statement": f"Nesta medida, o escore foi de {score} pontos, percentil {percentile}, classificação '{classification}'. O resultado descreve o desempenho nesta tarefa, sem generalização para o cotidiano.",
            "evidence_ids": list(refs.values()),
        })
    findings.append({
        "section": "analise_clinica",
        "statement": "Os resultados precisam ser contextualizados por modalidade e integrados à história clínica. Posição relativa no perfil não equivale a desempenho superior à média normativa.",
        "evidence_ids": [guide[code][key] for code in CODES for key in ("percentil", "classificacao")],
    })
    return {
        "findings": findings,
        "limitations": ["Escopo restrito à BPA-2; ausência de integração com anamnese e observações. Exige revisão profissional."],
        "review_questions": [],
    }


class BPA2ContractTests(SimpleTestCase):
    def test_both_synthetic_profiles_have_ordered_sections_and_supported_scores(self):
        for profile in (MIXED, AVERAGE):
            with self.subTest(profile=profile):
                facts = synthetic_facts(profile)
                output = BPA2SpecialistOutput.model_validate(synthetic_output(facts))
                validate_evidence(output, facts, "bpa2")
                self.assertEqual(output.findings[1].section, "ac")
                self.assertIn(profile[0][2], output.findings[1].statement)

    def test_missing_duplicate_or_shuffled_sections_are_rejected(self):
        for mutation in ("missing", "duplicate", "shuffle"):
            data = synthetic_output(synthetic_facts())
            if mutation == "missing":
                data["findings"].pop()
            elif mutation == "duplicate":
                data["findings"][2]["section"] = "ac"
            else:
                data["findings"][1], data["findings"][2] = data["findings"][2], data["findings"][1]
            with self.subTest(mutation=mutation), self.assertRaises(ValidationError):
                BPA2SpecialistOutput.model_validate(data)

    def test_known_semantic_errors_are_rejected_even_with_valid_numbers(self):
        facts = synthetic_facts()
        for section, suffix in [
            (1, " Foram avaliados 62 itens."),
            (4, " Trata-se do subteste de Atenção Geral."),
            (5, " A WAIS-III demonstrou memória operacional muito superior."),
        ]:
            data = synthetic_output(facts)
            data["findings"][section]["statement"] += suffix
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                validate_evidence(BPA2SpecialistOutput.model_validate(data), facts, "bpa2")

    def test_other_modality_evidence_cannot_replace_required_component_facts(self):
        facts = synthetic_facts()
        data = synthetic_output(facts)
        data["findings"][1]["evidence_ids"] = data["findings"][2]["evidence_ids"]
        with self.assertRaises(ValueError):
            validate_evidence(BPA2SpecialistOutput.model_validate(data), facts, "bpa2")

    def test_equivalent_classified_score_evidence_is_accepted(self):
        facts = synthetic_facts()
        data = synthetic_output(facts)
        for index, code in enumerate(CODES):
            finding = data["findings"][index + 1]
            finding["evidence_ids"] = [
                f"/classified_payload/subtestes/{index}/total" if key == f"/computed_payload/{code}/total" else key
                for key in finding["evidence_ids"]
            ]
        validate_evidence(BPA2SpecialistOutput.model_validate(data), facts, "bpa2")

    def test_natural_percentile_wording_is_accepted_without_changing_values(self):
        facts = synthetic_facts()
        data = synthetic_output(facts)
        data["findings"][1]["statement"] = data["findings"][1]["statement"].replace("percentil 10", "percentil de 10")
        validate_evidence(BPA2SpecialistOutput.model_validate(data), facts, "bpa2")

    def test_synthesis_cannot_hide_ac_and_ag_evidence(self):
        facts = synthetic_facts()
        data = synthetic_output(facts)
        data["findings"][5]["evidence_ids"] = data["findings"][2]["evidence_ids"]
        with self.assertRaises(ValueError):
            validate_evidence(BPA2SpecialistOutput.model_validate(data), facts, "bpa2")

    def test_example_scores_cannot_be_copied_into_different_results(self):
        data = synthetic_output(synthetic_facts(AVERAGE))
        with self.assertRaises(ValueError):
            validate_evidence(BPA2SpecialistOutput.model_validate(data), synthetic_facts(MIXED), "bpa2")

    def test_wrong_classification_and_swapped_score_percentile_are_rejected(self):
        facts = synthetic_facts()
        for old, new in [("'Inferior'", "'Média'"), ("62 pontos, percentil 10", "10 pontos, percentil 62")]:
            data = synthetic_output(facts)
            data["findings"][1]["statement"] = data["findings"][1]["statement"].replace(old, new)
            with self.subTest(new=new), self.assertRaises(ValueError):
                validate_evidence(BPA2SpecialistOutput.model_validate(data), facts, "bpa2")

    def test_conflicting_scores_or_duplicate_classified_rows_fail_closed(self):
        facts = synthetic_facts()
        facts["/classified_payload/subtestes/0/total"] = 75
        with self.assertRaises(ValueError):
            bpa2_reading_guide(facts)
        facts = synthetic_facts()
        facts["/classified_payload/subtestes/4/codigo"] = "ac"
        with self.assertRaises(ValueError):
            bpa2_reading_guide(facts)

    def test_missing_results_remain_missing_not_zero(self):
        guide = bpa2_reading_guide({"/computed_payload/ac/total": 0})["component_evidence_ids"]
        self.assertEqual(guide["ac"]["escore_pontos"], "/computed_payload/ac/total")
        self.assertIsNone(guide["ac"]["percentil"])
        self.assertIsNone(guide["ag"]["escore_pontos"])


@override_settings(
    SPECIALIST_AI_ENABLED=True, SPECIALIST_AI_INSTRUMENTS=["bpa2"],
    SPECIALIST_AI_PROVIDER="openai", AI_PROVIDER="openai", OPENAI_API_KEY="not-real",
    SPECIALIST_AI_MODEL="offline-model", OPENAI_BASE_URL="https://offline.example/v1",
)
class BPA2SpecialistWorkflowTests(TestCase):
    def setUp(self):
        test_specialist_runs.SpecialistRunTests.setUp(self)
        self.owner.crp = "00/12345"
        self.owner.save(update_fields=["crp"])
        instrument, _ = Instrument.objects.get_or_create(code="bpa2", defaults={"name": "BPA-2"})
        self.application.instrument = instrument
        self.application.computed_payload = {code: {"total": row[0]} for code, row in zip(CODES, MIXED)}
        self.application.classified_payload = {"subtestes": [
            {"codigo": code, "total": score, "percentil": percentile, "classificacao": classification}
            for code, (score, percentile, classification) in zip(CODES, MIXED)
        ]}
        self.application.save()

    def enqueue(self):
        return SpecialistRunService.enqueue(user=self.owner, report_id=self.report.pk)[0][0]

    def test_input_guide_is_grounded_and_does_not_include_patient_or_other_tests(self):
        payload = SpecialistInputService.build(self.application)
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertIn("não é quantidade de itens", serialized)
        self.assertIn("/computed_payload/ag/total", serialized)
        for forbidden in [self.patient.full_name, "Mãe Exemplo", "Texto antigo", "WAIS", "Guilherme"]:
            self.assertNotIn(forbidden, serialized)

    def test_version_change_preserves_old_output_and_allows_new_request(self):
        old = self.enqueue()
        old.specialist_version = SpecialistRunService.VERSION
        old.output_payload = {"previous": "retained"}
        old.save(update_fields=["specialist_version", "output_payload"])
        current = self.enqueue()
        self.assertNotEqual(old.pk, current.pk)
        self.assertEqual(current.specialist_version, BPA2_VERSION)
        self.assertFalse(SpecialistRunService.is_current(old))
        self.assertTrue(SpecialistRunService.is_current(current))
        old.refresh_from_db()
        self.assertEqual(old.output_payload, {"previous": "retained"})
        self.assertEqual(SpecialistRunService.version_for("wais3"), SpecialistRunService.VERSION)

    def test_agent_uses_approved_structure_and_retries_semantic_error_once(self):
        run = self.enqueue()
        valid = synthetic_output(run.input_payload["facts"])
        invalid = copy.deepcopy(valid)
        invalid["findings"][1]["statement"] += " Foram avaliados 62 itens."
        calls = []

        def respond(messages, info):
            calls.append(messages)
            self.assertIn(BPA2_INSTRUCTIONS, info.instructions)
            self.assertNotIn(self.patient.full_name, str(messages))
            return ModelResponse(parts=[TextPart(json.dumps(invalid if len(calls) == 1 else valid))])

        with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False):
            output, usage = SpecialistAgentService.generate(run, model_override=FunctionModel(respond))
        self.assertEqual(output, valid)
        self.assertEqual(usage["requests"], 2)
        self.assertEqual(len(calls), 2)

    def test_worker_and_professional_review_preserve_sections_and_human_text(self):
        run = self.enqueue()
        valid = synthetic_output(run.input_payload["facts"])
        result = SpecialistRunService.process_next(generator=lambda run: (valid, {}), report_id=self.report.pk)
        self.assertEqual(result.status, SpecialistRun.Status.NEEDS_REVIEW)
        self.assertEqual(result.output_payload, valid)
        review = SpecialistReviewService.review(
            user=self.owner, report_id=self.report.pk, run_id=run.pk, decision="approved", notes="Revisão sintética",
            source_sha256=result.source_sha256, output_sha256=SpecialistReviewService.output_fingerprint(result),
        )
        self.assertEqual(review.decision, SpecialistReview.Decision.APPROVED)
        self.section.refresh_from_db()
        self.assertEqual(self.section.content_edited, "Revisão humana.")
        self.application.refresh_from_db()
        self.assertEqual(self.application.interpretation_text, "Texto antigo: QI 120.")

    @override_settings(
        SPECIALIST_AI_PROVIDER="ollama", SPECIALIST_AI_MODEL="qwen3.5:9b",
        SPECIALIST_OLLAMA_BASE_URL="http://127.0.0.1:11434/v1",
    )
    def test_native_ollama_transport_uses_bpa2_schema_and_no_external_key(self):
        run = self.enqueue()
        valid = synthetic_output(run.input_payload["facts"])
        calls = []

        def respond(request):
            calls.append(request)
            body = json.loads(request.content)
            self.assertEqual(body["response_format"]["type"], "json_schema")
            self.assertIn("analise_clinica", json.dumps(body["response_format"]))
            self.assertEqual(body["reasoning_effort"], "none")
            self.assertEqual(body["model"], "qwen3.5:9b")
            self.assertEqual(request.headers["authorization"], "Bearer ollama-local")
            self.assertNotIn(self.patient.full_name, request.content.decode())
            return httpx2.Response(200, json={
                "id": "synthetic", "object": "chat.completion", "created": 1, "model": "qwen3.5:9b",
                "choices": [{"index": 0, "finish_reason": "stop", "message": {
                    "role": "assistant", "content": json.dumps(valid),
                }}], "usage": {"prompt_tokens": 100, "completion_tokens": 300, "total_tokens": 400},
            })

        def create_client(**kwargs):
            return httpx2.AsyncClient(transport=httpx2.MockTransport(respond), **kwargs)

        with patch("apps.reports.services.specialist_agent_service.DefaultAsyncHttpxClient", side_effect=create_client):
            output, usage = SpecialistAgentService.generate(run)
        self.assertEqual(output, valid)
        self.assertEqual(usage["requests"], 1)
        self.assertEqual(len(calls), 1)

    def test_repeated_semantic_error_stops_after_two_requests(self):
        run = self.enqueue()
        invalid = synthetic_output(run.input_payload["facts"])
        invalid["findings"][4]["statement"] += " O subteste de Atenção Geral foi analisado."
        calls = []

        def respond(messages, info):
            calls.append(1)
            return ModelResponse(parts=[TextPart(json.dumps(invalid))])

        with patch("pydantic_ai.models.ALLOW_MODEL_REQUESTS", False), self.assertRaises(Exception):
            SpecialistAgentService.generate(run, model_override=FunctionModel(respond))
        self.assertEqual(len(calls), 2)

    def test_invalid_bpa2_output_cannot_be_persisted_as_reviewable(self):
        self.enqueue()
        result = SpecialistRunService.process_next(
            generator=lambda run: (test_specialist_runs.VALID_OUTPUT, {}), report_id=self.report.pk,
        )
        self.assertEqual(result.status, SpecialistRun.Status.FAILED)
        self.assertEqual(result.output_payload, {})
